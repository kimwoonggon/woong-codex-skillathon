#!/usr/bin/env python3
"""Crawl a public Korean startup grant notice into structured JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FIELD_LABELS = (
    "소관부처",
    "소관부처·지자체",
    "사업수행기관",
    "신청기간",
    "사업개요",
    "사업신청 방법",
    "문의처",
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag in {"p", "br", "li", "div", "tr", "h1", "h2", "h3", "dt", "dd"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "li", "div", "tr", "h1", "h2", "h3", "dt", "dd"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def fetch_html(url: str, timeout: int) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 audit-korean-startup-grant/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_lines(html: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html)
    lines = []
    for line in parser.text().splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def first_matching_line(lines: Iterable[str], pattern: str) -> str:
    regex = re.compile(pattern)
    for line in lines:
        if regex.search(line):
            return line
    return ""


def line_after_label(lines: list[str], labels: tuple[str, ...]) -> str:
    for index, line in enumerate(lines):
        if any(label in line for label in labels):
            for candidate in lines[index + 1 : index + 6]:
                if candidate not in FIELD_LABELS and not any(label in candidate for label in FIELD_LABELS):
                    return candidate
    return ""


def extract_section(lines: list[str], start_label: str, stop_labels: tuple[str, ...], limit: int = 8) -> list[str]:
    for index, line in enumerate(lines):
        if start_label in line:
            section: list[str] = []
            for candidate in lines[index + 1 :]:
                if any(stop in candidate for stop in stop_labels):
                    break
                if candidate and candidate not in FIELD_LABELS:
                    section.append(candidate)
                if len(section) >= limit:
                    break
            return section
    return []


def extract_title(lines: list[str]) -> str:
    focused = [
        line
        for line in lines
        if "초기창업패키지" in line and "공고" in line and len(line) <= 100
    ]
    if focused:
        return focused[0]
    title_candidates = [
        line
        for line in lines
        if "공고" in line and len(line) <= 100 and not line.startswith("사업공고")
    ]
    if title_candidates:
        return title_candidates[0]
    return lines[0] if lines else ""


def extract_application_period(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if "신청기간" in line:
            joined = " ".join(lines[index + 1 : index + 5])
            match = re.search(r"20\d{2}\.\d{2}\.\d{2}\s*~\s*20\d{2}\.\d{2}\.\d{2}", joined)
            if match:
                return match.group(0)
    return first_matching_line(lines, r"20\d{2}\.\d{2}\.\d{2}\s*~\s*20\d{2}\.\d{2}\.\d{2}")


def extract_notice(url: str, html: str) -> dict[str, object]:
    lines = html_to_lines(html)
    period = extract_application_period(lines)
    overview_lines = extract_section(lines, "사업개요", ("사업신청 방법", "문의처", "첨부파일"), limit=10)

    return {
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "title": extract_title(lines),
        "published_date": first_matching_line(lines, r"20\d{2}\.\d{2}\.\d{2}"),
        "ministry": line_after_label(lines, ("소관부처", "소관부처·지자체")),
        "agency": line_after_label(lines, ("사업수행기관",)),
        "application_period": period,
        "application_method": line_after_label(lines, ("사업신청 방법",)),
        "contact": line_after_label(lines, ("문의처",)),
        "overview": overview_lines,
        "support_target": first_matching_line(overview_lines, r"창업.*기업|예비창업자|지원대상"),
        "support_content": first_matching_line(overview_lines, r"자금|프로그램|지원"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Public notice URL to crawl")
    parser.add_argument("--out", required=True, help="Path for crawled JSON output")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        html = fetch_html(args.url, args.timeout)
        notice = extract_notice(args.url, html)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"crawl failed: {exc}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(notice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
