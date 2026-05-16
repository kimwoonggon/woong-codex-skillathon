#!/usr/bin/env python3
"""Build a synthetic grant application package from crawled notice metadata."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


REQUIRED_DOCUMENTS = [
    "사업신청서",
    "사업계획서",
    "사업자등록증명",
    "중소기업확인서",
    "개인정보 수집 이용 동의서",
]


def parse_period_end(period: str) -> str:
    match = re.search(r"20\d{2}\.\d{2}\.\d{2}\s*~\s*(20\d{2})\.(\d{2})\.(\d{2})", period)
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def parse_max_budget(text: str) -> int:
    match = re.search(r"최대\s*([0-9.]+)\s*억", text)
    if not match:
        return 100_000_000
    return int(float(match.group(1)) * 100_000_000)


def write_notice(out_dir: Path, notice: dict[str, object], max_budget: int, deadline: str) -> None:
    overview = notice.get("overview") or []
    if isinstance(overview, list):
        overview_text = "\n".join(f"- {line}" for line in overview)
    else:
        overview_text = f"- {overview}"

    content = f"""# {notice.get("title") or "초기창업패키지 모집 공고 기반 mock 공고"}

> 이 문서는 공개 공고에서 추출한 메타데이터를 바탕으로 만든 교육용 mock 공고입니다.

## 공개 출처

- URL: {notice.get("source_url", "")}
- 수집 시각: {notice.get("fetched_at", "")}
- 소관부처: {notice.get("ministry", "")}
- 사업수행기관: {notice.get("agency", "")}
- 신청기간: {notice.get("application_period", "")}

## 사업개요

{overview_text}

## 지원대상

- 창업 후 3년 이내 초기창업기업
- 중소기업 대표자가 신청해야 함

## 지원내용

- 사업화 자금 최대 {max_budget:,}원
- 창업 프로그램 및 멘토링

## 필수 제출서류

"""
    content += "\n".join(f"- {document}" for document in REQUIRED_DOCUMENTS)
    content += f"""

## 접수 기준

- 접수마감일: {deadline or "확인 필요"}
- 온라인 접수 후 제출완료 상태 확인 필요
"""
    (out_dir / "notice.md").write_text(content, encoding="utf-8")


def write_application(out_dir: Path) -> None:
    content = """# 샘플AI 주식회사 정부지원사업 신청서

> 이 신청서는 검증 데모를 위한 합성 데이터입니다. 실제 기업 또는 개인 정보가 아닙니다.

## 기업 개요

- 기업명: 샘플AI 주식회사
- 업력: 2년 4개월
- 사업분야: 고객지원 자동화 SaaS
- 대표자: 홍길동(가명)
- 테스트용 대표 연락처: 010-1234-5678 / founder@example.com
- 테스트용 사업자등록번호: 123-45-67890

## 과제 목표

소상공인 고객센터 문의를 자동 분류하고, 반복 문의 답변 초안을 생성하는 한국어 AI 상담 운영 도구를 고도화한다.

## 추진 일정

- 1개월차: VOC 분류 모델 개선
- 2개월차: 상담 템플릿 추천 기능 개발
- 3개월차: 베타 고객 5곳 실증
- 해외 인증 일정은 추후 확정

## 예산 설명

총 110,000,000원의 사업화 자금을 신청한다. 클라우드 인프라, 외주 개발, 마케팅 실증비를 포함한다.

## 확인 필요

신규 보안인증 취득 여부는 협의 필요 상태다.
"""
    (out_dir / "application.md").write_text(content, encoding="utf-8")


def write_budget(out_dir: Path) -> None:
    rows = [
        {"category": "개발비", "item": "AI 분류 모델 고도화 외주", "amount_krw": "55000000", "execution_month": "2026-06", "note": "단일 항목 한도 초과 데모"},
        {"category": "인프라", "item": "클라우드 사용료", "amount_krw": "25000000", "execution_month": "2026-07", "note": "실증 환경"},
        {"category": "마케팅", "item": "베타 고객 온보딩 캠페인", "amount_krw": "20000000", "execution_month": "2026-08", "note": "시장 검증"},
        {"category": "인증", "item": "보안 컨설팅", "amount_krw": "10000000", "execution_month": "2026-09", "note": "일정 확인 필요"},
    ]
    with (out_dir / "budget.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "item", "amount_krw", "execution_month", "note"])
        writer.writeheader()
        writer.writerows(rows)


def write_submission_files(out_dir: Path) -> None:
    files = [
        "01_사업신청서.pdf",
        "02_사업계획서.pdf",
        "03_사업자등록증명.pdf",
        "04_개인정보 수집 이용 동의서.pdf",
        "05_발표자료.pdf",
    ]
    (out_dir / "submission-files.txt").write_text("\n".join(files) + "\n", encoding="utf-8")


def write_rules(out_dir: Path, notice: dict[str, object], deadline: str, max_budget: int) -> None:
    rules = {
        "source_url": notice.get("source_url", ""),
        "source_title": notice.get("title", ""),
        "required_documents": REQUIRED_DOCUMENTS,
        "optional_documents": ["발표자료", "디자인 또는 설계도면"],
        "application_deadline": deadline,
        "max_total_budget": max_budget,
        "max_single_item_budget": 50_000_000,
        "currency": "KRW",
    }
    (out_dir / "check-rules.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notice", required=True, help="Crawled notice JSON path")
    parser.add_argument("--out-dir", required=True, help="Output directory for mock package")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notice = json.loads(Path(args.notice).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    support_text = " ".join(str(value) for value in [notice.get("support_content", ""), *(notice.get("overview") or [])])
    max_budget = parse_max_budget(support_text)
    deadline = parse_period_end(str(notice.get("application_period", "")))

    write_notice(out_dir, notice, max_budget, deadline)
    write_application(out_dir)
    write_budget(out_dir)
    write_submission_files(out_dir)
    write_rules(out_dir, notice, deadline, max_budget)

    metadata = {
        "generated_from": str(args.notice),
        "source_url": notice.get("source_url", ""),
        "package_note": "Synthetic package for Skillathon validation; not a real application.",
    }
    (out_dir / "source-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote mock package to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
