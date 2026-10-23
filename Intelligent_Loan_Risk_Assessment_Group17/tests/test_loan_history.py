import csv
import tempfile
import unittest
from pathlib import Path

from src.loan_history import chart_position, load_loan_history
from src.risk_utils import risk_suggestions


class LoanHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "loans.csv"
        with self.csv_path.open("w", newline="", encoding="utf-8") as history_file:
            writer = csv.DictWriter(
                history_file,
                fieldnames=["person_income", "loan_amnt", "loan_status"],
            )
            writer.writeheader()
            for index in range(40):
                group = index // 10
                writer.writerow({
                    "person_income": 50000 + group * 10000,
                    "loan_amnt": 10000 + group * 1000,
                    "loan_status": index % 2,
                })

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_history_returns_aggregates_without_individual_records(self):
        history = load_loan_history(self.csv_path)

        self.assertEqual(history["record_count"], 40)
        self.assertEqual(history["default_rate"], 50.0)
        self.assertTrue(history["cells"])
        self.assertNotIn("records", history)
        self.assertTrue(all(cell["count"] >= 10 for cell in history["cells"]))

    def test_chart_position_marks_values_outside_historical_range(self):
        history = load_loan_history(self.csv_path)

        position = chart_position(1_000_000, 500_000, history)

        self.assertEqual(position["x"], 1.0)
        self.assertEqual(position["y"], 1.0)
        self.assertTrue(position["outside_history"])

    def test_small_loan_to_income_group_hides_default_rate(self):
        with self.csv_path.open("w", newline="", encoding="utf-8") as history_file:
            writer = csv.DictWriter(
                history_file,
                fieldnames=["person_income", "loan_amnt", "loan_status"],
            )
            writer.writeheader()
            writer.writerows([
                {"person_income": 100000, "loan_amnt": 10000, "loan_status": 0}
                for _ in range(12)
            ])

        history = load_loan_history(self.csv_path)

        self.assertIsNone(history["loan_to_income_bands"][0]["default_rate"])

    def test_risk_suggestions_use_neutral_human_review_language(self):
        suggestions = risk_suggestions(
            {
                "loan_amnt": 50000,
                "person_income": 100000,
                "existing_debt": 40000,
                "cb_person_default_on_file": "Y",
                "credit_score": 620,
                "cb_person_cred_hist_length": 2,
            },
            {"risk_category": "HIGH RISK"},
        )

        self.assertEqual(len(suggestions), 3)
        self.assertTrue(any("human review" in item for item in suggestions))
        self.assertTrue(any("inaccurate information" in item for item in suggestions))


if __name__ == "__main__":
    unittest.main()
