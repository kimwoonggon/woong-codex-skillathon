#!/usr/bin/env python3
"""Render a visual HTML review page from preflight JSON and package inputs."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def money(value: int) -> str:
    return f"{value:,}원"


def read_optional(path: Path, limit: int = 1600) -> str:
    if not path.exists():
        return "파일이 없습니다."
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text[:limit] + ("\n..." if len(text) > limit else "")


def severity_class(severity: str) -> str:
    return {
        "high": "sev-high",
        "medium": "sev-medium",
        "low": "sev-low",
    }.get(severity, "sev-low")


def issue_cards(issues: list[dict[str, str]]) -> str:
    if not issues:
        return '<p class="empty">감지된 위험 항목이 없습니다.</p>'
    cards = []
    for issue in issues:
        severity = html.escape(issue.get("severity", ""))
        code = html.escape(issue.get("code", ""))
        message = html.escape(issue.get("message", ""))
        evidence = html.escape(issue.get("evidence", ""))
        cards.append(
            f"""
            <article class="issue {severity_class(severity)}">
              <div class="issue-top">
                <span>{severity}</span>
                <code>{code}</code>
              </div>
              <p>{message}</p>
              <small>{evidence}</small>
            </article>
            """
        )
    return "\n".join(cards)


def render(result: dict[str, Any], package_dir: Path | None) -> str:
    source = result.get("source", {})
    summary = result.get("summary", {})
    budget = result.get("budget", {})
    deadline = result.get("deadline", {})
    issues = result.get("issues", [])
    status = "제출 가능" if result.get("passed") else "검토 필요"
    status_class = "pass" if result.get("passed") else "review"

    if package_dir:
        notice = read_optional(package_dir / "notice.md")
        application = read_optional(package_dir / "application.md")
        files = read_optional(package_dir / "submission-files.txt")
    else:
        notice = application = files = "패키지 폴더가 지정되지 않았습니다."

    actions = result.get("recommended_next_actions", [])
    action_html = "\n".join(f"<li>{html.escape(action)}</li>" for action in actions) or "<li>현재 스크립트 기준 필수 수정 항목은 없습니다.</li>"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>지원사업 신청 패키지 점검 리포트</title>
  <style>
    @font-face {{
      font-family: "Noto Sans KR Local";
      src: url("../assets/fonts/NotoSansCJKkr-Regular.otf") format("opentype");
      font-weight: 400;
      font-style: normal;
    }}
    :root {{
      --ink: #17202a;
      --muted: #667085;
      --line: #d7dde8;
      --paper: #ffffff;
      --bg: #f6f8fb;
      --brand: #166534;
      --danger: #b42318;
      --warn: #b54708;
      --ok: #027a48;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Noto Sans KR Local", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    header {{
      padding: 28px 36px 18px;
      background: #0f1f17;
      color: #fff;
      border-bottom: 4px solid #39a96b;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    h3 {{ margin: 0 0 10px; font-size: 15px; }}
    .meta {{ color: #c7d7cb; margin: 0; }}
    main {{ padding: 24px 36px 36px; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .span-4 {{ grid-column: span 4; }}
    .span-6 {{ grid-column: span 6; }}
    .span-8 {{ grid-column: span 8; }}
    .span-12 {{ grid-column: span 12; }}
    .status {{
      display: inline-flex;
      align-items: center;
      height: 32px;
      padding: 0 12px;
      border-radius: 999px;
      font-weight: 700;
    }}
    .status.review {{ background: #fee4e2; color: var(--danger); }}
    .status.pass {{ background: #d1fadf; color: var(--ok); }}
    .metric {{ display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid #edf1f7; }}
    .metric:last-child {{ border-bottom: 0; }}
    .metric span:first-child {{ color: var(--muted); }}
    pre {{
      font-family: "Noto Sans KR Local", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 360px;
      overflow: auto;
      margin: 0;
      padding: 14px;
      background: #f9fafb;
      border: 1px solid #e4e7ec;
      border-radius: 6px;
      font-size: 13px;
    }}
    code {{
      font-family: "Noto Sans KR Local", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .issue {{
      border: 1px solid var(--line);
      border-left-width: 5px;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      background: #fff;
    }}
    .issue-top {{ display: flex; justify-content: space-between; gap: 12px; font-weight: 700; }}
    .issue p {{ margin: 8px 0; }}
    .issue small {{ color: var(--muted); }}
    .sev-high {{ border-left-color: var(--danger); }}
    .sev-medium {{ border-left-color: var(--warn); }}
    .sev-low {{ border-left-color: #475467; }}
    ul {{ margin: 0; padding-left: 18px; }}
    .empty {{ color: var(--muted); margin: 0; }}
    @media (max-width: 900px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .span-4, .span-6, .span-8 {{ grid-column: span 12; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>지원사업 신청 패키지 점검 리포트</h1>
    <p class="meta">{html.escape(str(source.get("title", "")))} · {html.escape(str(result.get("today", "")))}</p>
  </header>
  <main class="grid">
    <section class="panel span-4">
      <h2>처리 결과</h2>
      <p><span class="status {status_class}">{status}</span></p>
      <div class="metric"><span>High</span><strong>{summary.get("high", 0)}</strong></div>
      <div class="metric"><span>Medium</span><strong>{summary.get("medium", 0)}</strong></div>
      <div class="metric"><span>누락 필수서류</span><strong>{summary.get("missing_required_documents", 0)}</strong></div>
      <div class="metric"><span>개인정보 패턴</span><strong>{summary.get("privacy_findings", 0)}</strong></div>
      <div class="metric"><span>확인 필요</span><strong>{summary.get("confirmation_needed", 0)}</strong></div>
    </section>
    <section class="panel span-4">
      <h2>기한</h2>
      <div class="metric"><span>마감일</span><strong>{html.escape(str(deadline.get("deadline", "")))}</strong></div>
      <div class="metric"><span>상태</span><strong>{html.escape(str(deadline.get("status", "")))}</strong></div>
      <div class="metric"><span>남은 일수</span><strong>{html.escape(str(deadline.get("days_left", "")))}</strong></div>
    </section>
    <section class="panel span-4">
      <h2>예산</h2>
      <div class="metric"><span>신청 총액</span><strong>{money(int(budget.get("total_krw") or 0))}</strong></div>
      <div class="metric"><span>총액 한도</span><strong>{money(int(budget.get("max_total_budget") or 0))}</strong></div>
      <div class="metric"><span>단일 항목 한도</span><strong>{money(int(budget.get("max_single_item_budget") or 0))}</strong></div>
    </section>
    <section class="panel span-6">
      <h2>문서 이전: 공고/제출 목록</h2>
      <h3>공고 요약</h3>
      <pre>{html.escape(notice)}</pre>
      <h3>제출 파일</h3>
      <pre>{html.escape(files)}</pre>
    </section>
    <section class="panel span-6">
      <h2>문서 이전: 신청서</h2>
      <pre>{html.escape(application)}</pre>
    </section>
    <section class="panel span-8">
      <h2>문서 처리 결과</h2>
      {issue_cards(issues)}
    </section>
    <section class="panel span-4">
      <h2>제출 전 액션아이템</h2>
      <ul>{action_html}</ul>
    </section>
    <section class="panel span-12">
      <h2>출처</h2>
      <p>{html.escape(str(source.get("url", "")))}</p>
      <p class="empty">이 HTML은 제출 전 형식과 리스크 점검용입니다. 최종 판단은 담당기관 공고와 전문가 검토를 따르세요.</p>
    </section>
  </main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, help="Preflight JSON result path")
    parser.add_argument("--out", required=True, help="HTML output path")
    parser.add_argument("--package-dir", help="Optional package directory to show before/after source text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    package_dir = Path(args.package_dir) if args.package_dir else None
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(result, package_dir), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
