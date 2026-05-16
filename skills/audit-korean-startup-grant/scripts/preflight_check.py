#!/usr/bin/env python3
"""Run deterministic preflight checks for a Korean startup grant package."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


PRIVACY_PATTERNS = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("phone", re.compile(r"\b(?:0\d{1,2})-\d{3,4}-\d{4}\b")),
    ("business_registration_number", re.compile(r"\b\d{3}-\d{2}-\d{5}\b")),
    ("resident_registration_like", re.compile(r"\b\d{6}-[1-4]\d{6}\b")),
]
CONFIRMATION_TERMS = ("미정", "추후 확정", "협의 필요", "TBD", "확인 필요")


@dataclass
class Issue:
    code: str
    severity: str
    message: str
    evidence: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
        }


def normalize_label(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\.[a-z0-9]+$", "", value)
    return re.sub(r"[^0-9a-z가-힣]", "", value)


def parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def money(value: int) -> str:
    return f"{value:,}원"


def mask_value(kind: str, value: str) -> str:
    if kind == "email":
        local, _, domain = value.partition("@")
        return f"{local[:1]}***@{domain}"
    if kind == "phone":
        return re.sub(r"(\d{2,3})-\d{3,4}-(\d{4})", r"\1-****-\2", value)
    if kind == "business_registration_number":
        return re.sub(r"(\d{3})-\d{2}-(\d{5})", r"\1-**-\2", value)
    if kind == "resident_registration_like":
        return re.sub(r"(\d{6})-[1-4]\d{6}", r"\1-*******", value)
    return "***"


def load_package(input_dir: Path) -> dict[str, Any]:
    rules_path = input_dir / "check-rules.json"
    if not rules_path.exists():
        raise FileNotFoundError(f"missing {rules_path}")

    return {
        "rules": json.loads(rules_path.read_text(encoding="utf-8")),
        "notice": (input_dir / "notice.md").read_text(encoding="utf-8"),
        "application": (input_dir / "application.md").read_text(encoding="utf-8"),
        "submission_files": (input_dir / "submission-files.txt").read_text(encoding="utf-8").splitlines(),
        "budget_rows": read_budget(input_dir / "budget.csv"),
    }


def read_budget(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_documents(required_documents: list[str], submitted_files: list[str]) -> list[Issue]:
    submitted_normalized = [normalize_label(file_name) for file_name in submitted_files if file_name.strip()]
    issues: list[Issue] = []
    for document in required_documents:
        normalized = normalize_label(document)
        if not any(normalized in file_name for file_name in submitted_normalized):
            issues.append(
                Issue(
                    code="MISSING_DOCUMENT",
                    severity="high",
                    message=f"필수 제출서류가 누락되었습니다: {document}",
                    evidence=f"submitted_files={submitted_files}",
                )
            )
    return issues


def check_deadline(deadline_value: str, today: date) -> tuple[dict[str, Any], list[Issue]]:
    deadline = parse_iso_date(deadline_value)
    if deadline is None:
        return {"deadline": deadline_value, "status": "unknown", "days_left": None}, [
            Issue("UNKNOWN_DEADLINE", "medium", "접수마감일을 구조적으로 확인할 수 없습니다.", "check-rules.json application_deadline")
        ]

    days_left = (deadline - today).days
    status = "open"
    issues: list[Issue] = []
    if days_left < 0:
        status = "closed"
        issues.append(Issue("DEADLINE_PASSED", "high", "접수마감일이 지났습니다.", f"deadline={deadline.isoformat()}, today={today.isoformat()}"))
    elif days_left <= 3:
        status = "urgent"
        issues.append(Issue("DEADLINE_URGENT", "medium", "접수마감까지 3일 이하로 남았습니다.", f"deadline={deadline.isoformat()}, days_left={days_left}"))
    return {"deadline": deadline.isoformat(), "status": status, "days_left": days_left}, issues


def parse_amount(value: str) -> int | None:
    cleaned = re.sub(r"[^0-9-]", "", value or "")
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def check_budget(rows: list[dict[str, str]], max_total: int, max_single_item: int) -> tuple[dict[str, Any], list[Issue]]:
    issues: list[Issue] = []
    total = 0
    normalized_rows: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        amount = parse_amount(row.get("amount_krw", ""))
        if amount is None:
            issues.append(Issue("INVALID_BUDGET_AMOUNT", "high", "예산 금액을 숫자로 읽을 수 없습니다.", f"row={index}"))
            amount = 0
        if amount <= 0:
            issues.append(Issue("NON_POSITIVE_BUDGET_AMOUNT", "medium", "예산 금액이 0 이하입니다.", f"row={index}, amount={amount}"))
        if max_single_item and amount > max_single_item:
            issues.append(
                Issue(
                    "SINGLE_ITEM_OVER_LIMIT",
                    "medium",
                    f"단일 예산 항목이 한도 {money(max_single_item)}를 초과했습니다.",
                    f"row={index}, item={row.get('item', '')}, amount={money(amount)}",
                )
            )
        total += amount
        normalized_rows.append({**row, "amount_krw": amount})

    if max_total and total > max_total:
        issues.append(
            Issue(
                "TOTAL_BUDGET_OVER_LIMIT",
                "high",
                f"신청 예산 총액이 한도 {money(max_total)}를 초과했습니다.",
                f"total={money(total)}, limit={money(max_total)}",
            )
        )

    return {"total_krw": total, "max_total_budget": max_total, "max_single_item_budget": max_single_item, "rows": normalized_rows}, issues


def check_privacy(text: str) -> list[Issue]:
    issues: list[Issue] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        masked_line = line
        matches: list[str] = []
        for kind, pattern in PRIVACY_PATTERNS:
            for match in pattern.finditer(line):
                raw = match.group(0)
                masked = mask_value(kind, raw)
                masked_line = masked_line.replace(raw, masked)
                matches.append(kind)
        if matches:
            issues.append(
                Issue(
                    "PRIVACY_PATTERN_FOUND",
                    "medium",
                    f"개인정보 또는 내부 식별정보 패턴이 감지되었습니다: {', '.join(sorted(set(matches)))}",
                    f"application.md:{line_number}: {masked_line.strip()}",
                )
            )
    return issues


def check_confirmation_needed(text: str) -> list[Issue]:
    issues: list[Issue] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        matched_terms = [term for term in CONFIRMATION_TERMS if term.lower() in line.lower()]
        if matched_terms:
            issues.append(
                Issue(
                    "CONFIRMATION_NEEDED",
                    "medium",
                    "확정되지 않은 계획 또는 근거가 있습니다.",
                    f"application.md:{line_number}: {line.strip()}",
                )
            )
    return issues


def run_check(input_dir: Path, today: date | None = None) -> dict[str, Any]:
    package = load_package(input_dir)
    rules = package["rules"]
    today = today or date.today()

    document_issues = check_documents(rules.get("required_documents", []), package["submission_files"])
    deadline, deadline_issues = check_deadline(str(rules.get("application_deadline", "")), today)
    budget, budget_issues = check_budget(
        package["budget_rows"],
        int(rules.get("max_total_budget") or 0),
        int(rules.get("max_single_item_budget") or 0),
    )
    privacy_issues = check_privacy(package["application"])
    confirmation_issues = check_confirmation_needed(package["application"])

    issues = document_issues + deadline_issues + budget_issues + privacy_issues + confirmation_issues
    high_count = sum(1 for issue in issues if issue.severity == "high")
    medium_count = sum(1 for issue in issues if issue.severity == "medium")

    return {
        "source": {
            "title": rules.get("source_title", ""),
            "url": rules.get("source_url", ""),
        },
        "checked_at": datetime.now().replace(microsecond=0).isoformat(),
        "today": today.isoformat(),
        "passed": high_count == 0,
        "summary": {
            "high": high_count,
            "medium": medium_count,
            "low": sum(1 for issue in issues if issue.severity == "low"),
            "missing_required_documents": sum(1 for issue in document_issues if issue.code == "MISSING_DOCUMENT"),
            "privacy_findings": len(privacy_issues),
            "confirmation_needed": len(confirmation_issues),
        },
        "deadline": deadline,
        "budget": budget,
        "issues": [issue.as_dict() for issue in issues],
        "recommended_next_actions": build_next_actions(issues),
    }


def build_next_actions(issues: list[Issue]) -> list[str]:
    actions: list[str] = []
    if any(issue.code == "MISSING_DOCUMENT" for issue in issues):
        actions.append("누락된 필수서류를 제출파일 목록에 추가하고 파일명을 공고 서류명과 맞추세요.")
    if any(issue.code == "DEADLINE_PASSED" for issue in issues):
        actions.append("접수 가능 여부를 공고 담당기관에 확인하세요.")
    if any(issue.code == "TOTAL_BUDGET_OVER_LIMIT" for issue in issues):
        actions.append("총 신청 예산을 지원 한도 이하로 조정하세요.")
    if any(issue.code == "SINGLE_ITEM_OVER_LIMIT" for issue in issues):
        actions.append("단일 예산 항목을 분리하거나 한도 이하로 조정하세요.")
    if any(issue.code == "PRIVACY_PATTERN_FOUND" for issue in issues):
        actions.append("제출 전 개인정보와 내부 식별정보를 필요한 범위만 남기고 마스킹하세요.")
    if any(issue.code == "CONFIRMATION_NEEDED" for issue in issues):
        actions.append("미정 또는 협의 필요 항목의 담당자, 일정, 근거를 확정하세요.")
    return actions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="Package directory containing notice/application/budget/files/rules")
    parser.add_argument("--out", required=True, help="JSON result output path")
    parser.add_argument("--today", help="Override today's date as YYYY-MM-DD for reproducible tests")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    today = parse_iso_date(args.today) if args.today else None
    result = run_check(Path(args.input_dir), today=today)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "PASS" if result["passed"] else "REVIEW_NEEDED"
    print(f"{status}: wrote {out_path} with {len(result['issues'])} issue(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
