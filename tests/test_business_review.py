import json
from pathlib import Path
import tempfile
import unittest
import shutil

from multimodal_eval_forge.business_review import (
    evaluate_formula,
    pii_metrics,
    find_sensitive_spans,
    review_bundle,
    redact_text_pdf,
    verify_redaction,
)

ROOT = Path(__file__).resolve().parents[1] / "examples" / "business-review"


class FormulaTests(unittest.TestCase):
    def test_uses_formula_behavior_not_cached_value(self):
        cells = {"B3": 120, "B4": 25, "B8": "=B3*B4"}
        self.assertEqual(evaluate_formula("B8", cells), 3000)
        self.assertEqual(evaluate_formula("B8", dict(cells, B8="=B4*B3")), 3000)
        self.assertEqual(evaluate_formula("B8", dict(cells, B8="=B3+B4")), 145)

    def test_rejects_cycles_and_executable_expressions(self):
        for cells in ({"A1": "=A1+1"}, {"A1": '=__import__("os")'}, {"A1": "=1/0"}):
            with self.subTest(cells=cells), self.assertRaises(ValueError):
                evaluate_formula("A1", cells)

    def test_nonfinite_values_never_pass_numeric_checks(self):
        for value in [float("nan"), float("inf"), -float("inf"), "=1e999"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                evaluate_formula("B8", {"B8": value})


class BundleTests(unittest.TestCase):
    def test_reference_artifacts_match_sources_and_requirements(self):
        result = review_bundle(ROOT / "reference", ROOT / "source.json")
        self.assertEqual(result["issues"], [])
        self.assertTrue(result["requires_human_review"])

    def test_seeded_candidate_a_errors_are_detected_from_actual_files(self):
        issues = {
            x["code"]
            for x in review_bundle(ROOT / "candidate-a", ROOT / "source.json")["issues"]
        }
        self.assertTrue(
            {"unsupported_claim", "omitted_requirement", "stale_value", "wrong_formula"}
            <= issues
        )

    def test_seeded_candidate_b_units_clipping_and_contradiction(self):
        issues = {
            x["code"]
            for x in review_bundle(ROOT / "candidate-b", ROOT / "source.json")["issues"]
        }
        self.assertTrue(
            {"inconsistent_units", "clipping", "contradictory_conclusion"} <= issues
        )

    def test_missing_artifact_is_not_a_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                review_bundle(Path(directory), ROOT / "source.json")

    def test_removing_claim_manifest_cannot_hide_known_source_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "candidate"
            shutil.copytree(ROOT / "candidate-a", target)
            manifest = json.loads((target / "manifest.json").read_text())
            manifest["claims"] = []
            (target / "manifest.json").write_text(json.dumps(manifest))
            issues = review_bundle(target, ROOT / "source.json")["issues"]
            self.assertEqual(
                len([issue for issue in issues if issue["code"] == "missing_claim"]), 4
            )

    def test_manifest_cannot_relabel_stale_report_text_as_current(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "candidate"
            shutil.copytree(ROOT / "candidate-a", target)
            manifest = json.loads((target / "manifest.json").read_text())
            manifest["claims"][1].update(value=25, version="v2")
            (target / "manifest.json").write_text(json.dumps(manifest))
            issues = review_bundle(target, ROOT / "source.json")["issues"]
            self.assertIn(
                "claim_metadata_mismatch", {issue["code"] for issue in issues}
            )


class PrivacyTests(unittest.TestCase):
    def test_known_corpus_metrics_and_unicode_coordinates(self):
        cases = json.loads((ROOT / "privacy" / "span-cases.json").read_text())["cases"]
        expected = {
            "exact": (1, 1),
            "missed-account": (1, 2 / 3),
            "overredacted-model": (0.75, 1),
            "unicode-formatting": (1, 1),
        }
        for case in cases:
            result = pii_metrics(
                [(s["start"], s["end"]) for s in case["predicted_spans"]],
                [(s["start"], s["end"]) for s in case["gold_spans"]],
            )
            self.assertEqual(
                (result["precision"], result["recall"]), expected[case["id"]]
            )
            self.assertEqual(result, case["metrics"])

    def test_missed_and_overredacted_pdf_have_distinct_failures(self):
        values = ["Asha Example", "asha@example.test", "ACCT-SYN-1042"]
        missed = verify_redaction(
            ROOT / "privacy" / "missed.pdf", values, ["Kit model 1042"]
        )
        over = verify_redaction(
            ROOT / "privacy" / "overredacted.pdf", values, ["Kit model 1042"]
        )
        self.assertEqual(missed["leaks"], ["ACCT-SYN-1042"])
        self.assertEqual(missed["lost_public_text"], [])
        self.assertEqual(over["leaks"], [])
        self.assertEqual(over["lost_public_text"], ["Kit model 1042"])

    def test_unicode_formatting_keeps_original_span_coordinates(self):
        text = "Owner Asha\u00a0Example email ａｓｈａ＠ｅｘａｍｐｌｅ．ｔｅｓｔ uses ACCT-\u200bSYN-1042."
        spans = find_sensitive_spans(
            text, ["Asha Example", "asha@example.test", "ACCT-SYN-1042"]
        )
        self.assertEqual(len(spans), 3)
        self.assertIn("Asha\u00a0Example", [text[x["start"] : x["end"]] for x in spans])

    def test_missed_and_over_redaction_have_distinct_metrics(self):
        gold = [(0, 4), (10, 15)]
        result = pii_metrics([(0, 4), (20, 25)], gold)
        self.assertEqual(
            result,
            {
                "precision": 0.5,
                "recall": 0.5,
                "true_positive": 1,
                "false_positive": 1,
                "false_negative": 1,
            },
        )

    def test_true_redaction_preserves_original_and_nonprivate_text(self):
        original = ROOT / "privacy" / "original.pdf"
        before = original.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "redacted.pdf"
            redact_text_pdf(
                original, output, ["Asha Example", "asha@example.test", "ACCT-SYN-1042"]
            )
            result = verify_redaction(
                output,
                ["Asha Example", "asha@example.test", "ACCT-SYN-1042"],
                ["Kit model 1042", "Demand remains uncertain"],
            )
            self.assertEqual(result["leaks"], [])
            self.assertEqual(result["lost_public_text"], [])
        self.assertEqual(original.read_bytes(), before)

    def test_painted_overlay_does_not_count_as_redaction(self):
        result = verify_redaction(
            ROOT / "privacy" / "painted-only.pdf",
            ["Asha Example", "asha@example.test", "ACCT-SYN-1042"],
            [],
        )
        self.assertEqual(len(result["leaks"]), 3)

    def test_redaction_refuses_to_overwrite_original(self):
        path = ROOT / "privacy" / "original.pdf"
        with self.assertRaises(ValueError):
            redact_text_pdf(path, path, ["Asha Example"])


if __name__ == "__main__":
    unittest.main()
