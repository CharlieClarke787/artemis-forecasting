import os
import sqlite3
import tempfile
import unittest

from analytics import calculate_analytics
from export_forecasts import export_to_csv
from report_drafts import generate_draft, import_report, parse_report


REPORT = """<html><head><title>Risk Briefing</title></head><body>
<p>Published: 2026-09-01</p>
<p>Forecast watch: Will event X happen? 60-80%.</p>
<p>Forecast-watch: Event &lt;Y&gt; occurs by year end, 0.2 to 0.4.</p>
</body></html>"""


class ReportDraftTests(unittest.TestCase):
    def test_parse_and_deterministic_generation(self):
        items = parse_report(REPORT, "https://example.test/report")
        self.assertEqual(len(items), 2)
        self.assertEqual(generate_draft(items[0]), generate_draft(items[0]))
        self.assertEqual(generate_draft(items[0])["probability"], 0.7)

    def test_validation_and_missing_report(self):
        with self.assertRaises(ValueError):
            generate_draft({"question": "bad", "low": -0.1, "high": 0.2})
        with self.assertRaises(FileNotFoundError):
            import_report("does-not-exist.html", ":memory:")

    def test_idempotent_import(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as database:
            db_path = database.name
        try:
            first = import_report(self._report_path(), db_path)
            second = import_report(self._report_path(), db_path)
            self.assertEqual(first["added"], 2)
            self.assertEqual(second["added"], 0)
            conn = sqlite3.connect(db_path)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM draft_forecasts").fetchone()[0], 2)
            conn.execute("CREATE TABLE questions (id INTEGER PRIMARY KEY, text TEXT, source TEXT)")
            conn.execute("CREATE TABLE forecasts (id INTEGER PRIMARY KEY, question_id INTEGER, forecaster TEXT, probability REAL, rationale TEXT, created_at TEXT)")
            conn.execute("CREATE TABLE ground_truth (id INTEGER PRIMARY KEY, question_id INTEGER, outcome INTEGER, resolved_at TEXT)")
            conn.close()
            export_path = db_path + ".csv"
            export_to_csv(db_path, export_path)
            with open(export_path, encoding="utf-8") as exported:
                self.assertIn("UNAPPROVED", exported.read())
            os.unlink(export_path)
        finally:
            os.unlink(db_path)

    def test_drafts_are_excluded_from_analytics(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as database:
            db_path = database.name
        try:
            import_report(self._report_path(), db_path)
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE questions (id INTEGER PRIMARY KEY, text TEXT, source TEXT)")
            conn.execute("CREATE TABLE forecasts (id INTEGER PRIMARY KEY, question_id INTEGER, forecaster TEXT, probability REAL, created_at TEXT)")
            conn.execute("CREATE TABLE ground_truth (id INTEGER PRIMARY KEY, question_id INTEGER, outcome INTEGER)")
            conn.execute("CREATE TABLE gjo_consensus (question_id INTEGER, median_probability REAL)")
            conn.commit()
            conn.close()
            old = os.getcwd()
            os.chdir(os.path.dirname(db_path))
            try:
                self.assertEqual(calculate_analytics(db_path)["total"], 0)
            finally:
                os.chdir(old)
        finally:
            os.unlink(db_path)

    @staticmethod
    def _report_path():
        handle, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(REPORT)
        return path


if __name__ == "__main__":
    unittest.main()
