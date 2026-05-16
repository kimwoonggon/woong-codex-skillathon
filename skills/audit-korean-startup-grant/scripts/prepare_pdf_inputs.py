#!/usr/bin/env python3
"""Prepare package text files from PDFs or text files when local extractors exist."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


PACKAGE_NAMES = {
    "notice": "notice.md",
    "application": "application.md",
}


def extract_with_pdftotext(source: Path) -> str:
    if shutil.which("pdftotext") is None:
        raise RuntimeError("pdftotext command is not installed")
    completed = subprocess.run(
        ["pdftotext", "-layout", str(source), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


def extract_with_python_package(source: Path) -> str:
    try:
        import pypdf  # type: ignore
    except ImportError:
        try:
            import PyPDF2 as pypdf  # type: ignore
        except ImportError as exc:
            raise RuntimeError("no supported Python PDF package is installed") from exc

    reader = pypdf.PdfReader(str(source))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def read_document(source: Path) -> str:
    if source.suffix.lower() == ".pdf":
        try:
            return extract_with_pdftotext(source)
        except Exception:
            return extract_with_python_package(source)
    return source.read_text(encoding="utf-8", errors="replace")


def find_source(input_dir: Path, stem: str) -> Path | None:
    candidates = [
        input_dir / f"{stem}.pdf",
        input_dir / f"{stem}.md",
        input_dir / f"{stem}.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def first_content_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            match = re.search(r".{1,80}?모집\s*공고", cleaned)
            if match:
                return re.sub(r"\s+", " ", match.group(0)).strip()
            match = re.search(r".{1,80}?공고", cleaned)
            if match:
                return re.sub(r"\s+", " ", match.group(0)).strip()
            return cleaned
    return "PDF 기반 지원사업 공고"


def parse_pdf_deadline(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text)
    range_match = re.search(r"[’']?(\d{2})\.\s*(\d{2})\.\s*(\d{2}).{0,20}[~∼-]\s*(\d{2})\.\s*(\d{2})", normalized)
    if range_match:
        year = 2000 + int(range_match.group(1))
        return f"{year:04d}-{int(range_match.group(4)):02d}-{int(range_match.group(5)):02d}"
    iso_match = re.search(r"(20\d{2})[.\-]\s*(\d{2})[.\-]\s*(\d{2})", normalized)
    if iso_match:
        return f"{iso_match.group(1)}-{iso_match.group(2)}-{iso_match.group(3)}"
    return ""


def parse_pdf_budget_limit(text: str) -> int:
    normalized = re.sub(r"\s+", " ", text)
    match = re.search(r"최대\s*([0-9]+)\s*백만원", normalized)
    if match:
        return int(match.group(1)) * 1_000_000
    match = re.search(r"최대\s*([0-9.]+)\s*억원", normalized)
    if match:
        return int(float(match.group(1)) * 100_000_000)
    return 100_000_000


def write_inferred_rules(out_dir: Path, notice_text: str, source_url: str) -> None:
    max_total = parse_pdf_budget_limit(notice_text)
    rules = {
        "source_url": source_url,
        "source_title": first_content_line(notice_text),
        "required_documents": [
            "사업신청서",
            "사업계획서",
            "사업자등록증명",
            "중소기업확인서",
            "개인정보 수집 이용 동의서",
        ],
        "optional_documents": ["발표자료", "아이템 도면", "설계도"],
        "application_deadline": parse_pdf_deadline(notice_text),
        "max_total_budget": max_total,
        "max_single_item_budget": min(max_total, 50_000_000),
        "currency": "KRW",
        "rule_note": "Inferred from PDF text for mock validation; confirm against the official notice before real submission.",
    }
    (out_dir / "check-rules.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="Directory containing notice/application PDFs or text files")
    parser.add_argument("--out-dir", required=True, help="Output package directory")
    parser.add_argument("--source-url", default="", help="Public source URL for inferred rules")
    parser.add_argument("--copy-budget-from", help="Optional budget.csv path")
    parser.add_argument("--copy-files-from", help="Optional submission-files.txt path")
    parser.add_argument("--copy-rules-from", help="Optional check-rules.json path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted: dict[str, str] = {}
    for stem, output_name in PACKAGE_NAMES.items():
        source = find_source(input_dir, stem)
        if source is None:
            raise FileNotFoundError(f"missing {stem}.pdf, {stem}.md, or {stem}.txt in {input_dir}")
        text = read_document(source)
        extracted[stem] = text
        (out_dir / output_name).write_text(text.strip() + "\n", encoding="utf-8")

    copy_pairs = [
        (args.copy_budget_from, "budget.csv"),
        (args.copy_files_from, "submission-files.txt"),
        (args.copy_rules_from, "check-rules.json"),
    ]
    for source_value, output_name in copy_pairs:
        if source_value:
            shutil.copyfile(source_value, out_dir / output_name)

    if not args.copy_rules_from:
        write_inferred_rules(out_dir, extracted["notice"], args.source_url)

    print(f"prepared package text files in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
