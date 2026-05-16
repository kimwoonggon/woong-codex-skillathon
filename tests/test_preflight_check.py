from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "skills" / "audit-korean-startup-grant" / "scripts" / "preflight_check.py"
SPEC = importlib.util.spec_from_file_location("preflight_check", SCRIPT_PATH)
preflight_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["preflight_check"] = preflight_check
SPEC.loader.exec_module(preflight_check)


class PreflightCheckTests(unittest.TestCase):
    def write_package(
        self,
        root: Path,
        *,
        submitted_files: list[str],
        budget_rows: list[dict[str, str]],
        application_extra: str = "",
        deadline: str = "2026-05-20",
    ) -> None:
        rules = {
            "source_url": "https://example.com/notice",
            "source_title": "테스트 지원사업",
            "required_documents": ["사업신청서", "사업계획서", "중소기업확인서"],
            "application_deadline": deadline,
            "max_total_budget": 100000000,
            "max_single_item_budget": 50000000,
        }
        (root / "check-rules.json").write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
        (root / "notice.md").write_text("# 테스트 공고\n", encoding="utf-8")
        (root / "application.md").write_text("# 테스트 신청서\n" + application_extra, encoding="utf-8")
        (root / "submission-files.txt").write_text("\n".join(submitted_files) + "\n", encoding="utf-8")
        with (root / "budget.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["category", "item", "amount_krw", "execution_month", "note"])
            writer.writeheader()
            writer.writerows(budget_rows)

    def test_detects_missing_document_budget_privacy_and_confirmation_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_package(
                root,
                submitted_files=["사업신청서.pdf", "사업계획서.pdf"],
                budget_rows=[
                    {"category": "개발", "item": "외주", "amount_krw": "60000000", "execution_month": "2026-05", "note": ""},
                    {"category": "마케팅", "item": "캠페인", "amount_krw": "50000000", "execution_month": "2026-06", "note": ""},
                ],
                application_extra="담당자 연락처 010-1234-5678, test@example.com\n일정은 추후 확정\n",
                deadline="2026-05-10",
            )

            result = preflight_check.run_check(root, today=date(2026, 5, 16))
            codes = {issue["code"] for issue in result["issues"]}

            self.assertFalse(result["passed"])
            self.assertIn("MISSING_DOCUMENT", codes)
            self.assertIn("DEADLINE_PASSED", codes)
            self.assertIn("TOTAL_BUDGET_OVER_LIMIT", codes)
            self.assertIn("SINGLE_ITEM_OVER_LIMIT", codes)
            self.assertIn("PRIVACY_PATTERN_FOUND", codes)
            self.assertIn("CONFIRMATION_NEEDED", codes)

    def test_clean_package_passes_when_required_items_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_package(
                root,
                submitted_files=["사업신청서.pdf", "사업계획서.pdf", "중소기업확인서.pdf"],
                budget_rows=[
                    {"category": "개발", "item": "내부 개발", "amount_krw": "30000000", "execution_month": "2026-05", "note": ""},
                    {"category": "인프라", "item": "클라우드", "amount_krw": "10000000", "execution_month": "2026-06", "note": ""},
                ],
            )

            result = preflight_check.run_check(root, today=date(2026, 5, 16))

            self.assertTrue(result["passed"])
            self.assertEqual(result["summary"]["high"], 0)
            self.assertEqual(result["summary"]["missing_required_documents"], 0)


if __name__ == "__main__":
    unittest.main()
