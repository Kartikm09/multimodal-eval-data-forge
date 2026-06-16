import unittest

from multimodal_eval_forge.forge import generate_dataset
from multimodal_eval_forge.validator import validate_records


class EvalDataForgeTests(unittest.TestCase):
    def test_generated_records_validate(self):
        records = generate_dataset("mixed", 8, seed=3)
        report = validate_records(records)
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.passed_records, 8)

    def test_unknown_domain_raises(self):
        with self.assertRaises(ValueError):
            generate_dataset("unknown", 1)

    def test_bad_record_fails(self):
        report = validate_records([{"id": "bad", "prompt": "short"}])
        self.assertEqual(report.status, "fail")


if __name__ == "__main__":
    unittest.main()
