---
name: audit-korean-startup-grant
description: Korean startup grant application package audit workflow. Use when Codex needs to review Korean government startup support notices, application drafts, budget CSV files, and submission file lists for missing documents, deadline risk, budget-limit issues, privacy exposure, and "confirmation needed" items before a mock or real grant submission.
---

# Audit Korean Startup Grant

## Overview

Use this skill to turn a Korean startup grant application package into a submission-readiness report. Prefer deterministic script results for crawl, mock generation, and preflight checks, then use judgment only to explain risks and next actions.

## Inputs

Accept any of these inputs:

- A public Korean grant notice URL.
- A folder containing `notice.md`, `application.md`, `budget.csv`, `submission-files.txt`, and optional `check-rules.json`.
- PDF files for the notice or application draft, when a local PDF text extractor is available.
- A user's pasted Korean notice, application draft, budget table, or file list.

If the user provides real company data, first warn that the workflow may surface personal or internal information. Ask whether to anonymize before quoting details.

## Workflow

1. Locate this skill directory and inspect `references/grant-check-rules.md` if the package rules are unclear.
2. If the user provides a public notice URL, run:

```bash
python3 skills/audit-korean-startup-grant/scripts/crawl_notice.py --url <notice-url> --out data/crawled-notice.json
```

3. If a reproducible demo package is needed, run:

```bash
python3 skills/audit-korean-startup-grant/scripts/build_mock_package.py --notice data/crawled-notice.json --out-dir data/mock-package
```

4. If the user provides PDFs, prepare text inputs before running the checker:

```bash
python3 skills/audit-korean-startup-grant/scripts/prepare_pdf_inputs.py --input-dir raw-pdfs --out-dir data/pdf-package
```

Use this only when `pdftotext` or a supported Python PDF package is installed locally. If extraction is unavailable, ask the user to export PDFs to text or Markdown.

5. Run the deterministic preflight checker:

```bash
python3 skills/audit-korean-startup-grant/scripts/preflight_check.py --input-dir data/mock-package --out outputs/preflight-result.json
```

6. Render a Korean Markdown report when an output artifact is requested:

```bash
python3 skills/audit-korean-startup-grant/scripts/render_report.py --result outputs/preflight-result.json --out outputs/example-report.md
```

7. Render an HTML review page when the user wants a visual before/after result:

```bash
python3 skills/audit-korean-startup-grant/scripts/render_html.py --result outputs/preflight-result.json --package-dir data/mock-package --out outputs/example-report.html
```

8. Use the JSON result as evidence. Do not invent eligibility, budget, or document requirements that are not present in the notice, rules file, or user-provided context.

## Report Requirements

Write the final report in Korean Markdown with these sections:

- `지원 적합성 요약`
- `공고 및 입력 출처`
- `누락/위험 항목`
- `예산 점검`
- `개인정보 및 내부정보 노출`
- `제출 전 액션아이템`
- `확인 필요`

Mark unknown or ambiguous items as `확인 필요`. Do not convert them into confident recommendations.

## Guardrails

- Treat this as a pre-submission checklist, not legal, accounting, tax, or government-agency advice.
- Do not upload, transmit, or preserve real confidential data unless the user explicitly asks and the destination is clear.
- Mask phone numbers, business registration numbers, resident-registration-like numbers, and email addresses in user-facing reports.
- If live crawling fails, use a saved `data/crawled-notice.json` only if it clearly records `source_url` and `fetched_at`.
- Keep generated mock data visibly synthetic and do not claim it is an actual submitted application.

## Resources

- `scripts/crawl_notice.py`: Crawl a public notice page and extract structured fields.
- `scripts/build_mock_package.py`: Build a synthetic package from crawled notice metadata.
- `scripts/preflight_check.py`: Run deterministic checks and output JSON.
- `scripts/render_report.py`: Convert JSON results into Korean Markdown.
- `scripts/render_html.py`: Create a visual HTML before/after review page.
- `scripts/download_public_pdf.py`: Download a public PDF notice for reproducible PDF validation.
- `scripts/prepare_pdf_inputs.py`: Extract PDF text into package-ready Markdown when local tools are available.
- `references/grant-check-rules.md`: Check rules, severity guidance, and report conventions.
