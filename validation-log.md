# Validation Log

This file records reproducible validation results for the Skillathon submission.

## Planned Commands

```bash
python3 skills/audit-korean-startup-grant/scripts/crawl_notice.py --url "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117819" --out data/crawled-notice.json
python3 skills/audit-korean-startup-grant/scripts/build_mock_package.py --notice data/crawled-notice.json --out-dir data/mock-package
python3 skills/audit-korean-startup-grant/scripts/preflight_check.py --input-dir data/mock-package --out outputs/preflight-result.json --today 2026-05-16
python3 skills/audit-korean-startup-grant/scripts/render_report.py --result outputs/preflight-result.json --out outputs/example-report.md
python3 skills/audit-korean-startup-grant/scripts/render_html.py --result outputs/preflight-result.json --package-dir data/mock-package --out outputs/example-report.html
python3 skills/audit-korean-startup-grant/scripts/download_public_pdf.py --url "https://grant-documents.thevc.kr/download/289472_%28%EA%B3%B5%EA%B3%A0%EB%AC%B8%292026%EB%85%84%EC%A0%84%EB%B6%81%ED%98%95%EC%B0%BD%EC%97%85%ED%8C%A8%ED%82%A4%EC%A7%80%EC%B0%BD%EC%97%85%EA%B8%B0%EC%97%85%EB%AA%A8%EC%A7%91%EA%B3%B5%EA%B3%A0%EB%AC%B8_%EA%B5%AD%EB%A6%BD%EA%B5%B0%EC%82%B0%EB%8C%80%ED%95%99%EA%B5%90.pdf" --out data/source-pdfs/notice.pdf
python3 skills/audit-korean-startup-grant/scripts/prepare_pdf_inputs.py --input-dir data/pdf-inputs --out-dir data/pdf-package --source-url "https://grant-documents.thevc.kr/download/289472_%28%EA%B3%B5%EA%B3%A0%EB%AC%B8%292026%EB%85%84%EC%A0%84%EB%B6%81%ED%98%95%EC%B0%BD%EC%97%85%ED%8C%A8%ED%82%A4%EC%A7%80%EC%B0%BD%EC%97%85%EA%B8%B0%EC%97%85%EB%AA%A8%EC%A7%91%EA%B3%B5%EA%B3%A0%EB%AC%B8_%EA%B5%AD%EB%A6%BD%EA%B5%B0%EC%82%B0%EB%8C%80%ED%95%99%EA%B5%90.pdf" --copy-budget-from data/pdf-inputs/budget.csv --copy-files-from data/pdf-inputs/submission-files.txt
python3 skills/audit-korean-startup-grant/scripts/preflight_check.py --input-dir data/pdf-package --out outputs/pdf-preflight-result.json --today 2026-05-16
python3 skills/audit-korean-startup-grant/scripts/render_report.py --result outputs/pdf-preflight-result.json --out outputs/pdf-report.md
python3 skills/audit-korean-startup-grant/scripts/render_html.py --result outputs/pdf-preflight-result.json --package-dir data/pdf-package --out outputs/pdf-report.html
python3 -m unittest discover -s tests
python3 /home/kimwoonggon/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/audit-korean-startup-grant
```

## Results

- HTML notice crawl: passed. `data/crawled-notice.json` generated from the Bizinfo public notice.
- Mock package generation: passed. `data/mock-package` contains `notice.md`, `application.md`, `budget.csv`, `submission-files.txt`, and `check-rules.json`.
- Mock preflight: passed with expected `REVIEW_NEEDED`; generated `outputs/preflight-result.json` with 9 issue(s).
- Mock reports: passed. Generated `outputs/example-report.md` and `outputs/example-report.html`.
- Public PDF download: passed. Generated `data/source-pdfs/notice.pdf` from the public Jeonbuk startup package PDF URL.
- PDF extraction: passed using temporary local `pypdf` during validation. Generated `data/pdf-package/notice.md` and inferred `check-rules.json`.
- PDF preflight: passed with expected `REVIEW_NEEDED`; generated `outputs/pdf-preflight-result.json` with 9 issue(s).
- PDF reports: passed. Generated `outputs/pdf-report.md` and `outputs/pdf-report.html`.
- Unit tests: passed. `Ran 2 tests ... OK`.
- Skill validation: passed. `Skill is valid!`.
- Startup application PDF demo: passed. Generated `data/startup-application-pdf/application.pdf`, extracted it into `data/startup-pdf-package`, produced `outputs/startup-pdf-report.html`, and captured `outputs/startup-pdf-report.png` with embedded Korean font rendering.
