#!/usr/bin/env python3
"""Render a Korean Markdown report from a preflight JSON result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def money(value: int) -> str:
    return f"{value:,}원"


def issue_table(issues: list[dict[str, str]]) -> str:
    if not issues:
        return "감지된 위험 항목이 없습니다.\n"
    lines = ["| 심각도 | 코드 | 내용 | 근거 |", "|---|---|---|---|"]
    for issue in issues:
        lines.append(f"| {issue['severity']} | `{issue['code']}` | {issue['message']} | {issue['evidence']} |")
    return "\n".join(lines) + "\n"


def render(result: dict[str, Any]) -> str:
    status = "검토 필요" if not result.get("passed") else "제출 가능"
    source = result.get("source", {})
    summary = result.get("summary", {})
    budget = result.get("budget", {})
    deadline = result.get("deadline", {})
    issues = result.get("issues", [])
    privacy_issues = [issue for issue in issues if issue.get("code") == "PRIVACY_PATTERN_FOUND"]
    confirmation_issues = [issue for issue in issues if issue.get("code") == "CONFIRMATION_NEEDED"]

    report = f"""# 지원사업 신청 패키지 사전 점검 리포트

## 지원 적합성 요약

- 판정: **{status}**
- High: {summary.get("high", 0)}
- Medium: {summary.get("medium", 0)}
- 누락 필수서류: {summary.get("missing_required_documents", 0)}
- 개인정보 패턴: {summary.get("privacy_findings", 0)}
- 확인 필요 항목: {summary.get("confirmation_needed", 0)}

## 공고 및 입력 출처

- 공고명: {source.get("title", "")}
- URL: {source.get("url", "")}
- 점검 기준일: {result.get("today", "")}
- 접수마감일: {deadline.get("deadline", "")}
- 마감 상태: {deadline.get("status", "")}

## 누락/위험 항목

{issue_table([issue for issue in issues if issue.get("code") not in {"PRIVACY_PATTERN_FOUND", "CONFIRMATION_NEEDED"}])}
## 예산 점검

- 신청 예산 총액: {money(int(budget.get("total_krw") or 0))}
- 총액 한도: {money(int(budget.get("max_total_budget") or 0))}
- 단일 항목 한도: {money(int(budget.get("max_single_item_budget") or 0))}

## 개인정보 및 내부정보 노출

{issue_table(privacy_issues)}
## 제출 전 액션아이템

"""
    actions = result.get("recommended_next_actions", [])
    if actions:
        report += "\n".join(f"- {action}" for action in actions) + "\n"
    else:
        report += "- 현재 스크립트 기준 필수 수정 항목은 없습니다.\n"

    report += f"""
## 확인 필요

{issue_table(confirmation_issues)}
> 이 리포트는 제출 전 형식과 리스크 점검용입니다. 최종 지원 가능성, 회계 인정 여부, 법률 판단은 담당기관 공고와 전문가 검토를 따르세요.
"""
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, help="Preflight JSON result path")
    parser.add_argument("--out", required=True, help="Markdown report output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(result), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
