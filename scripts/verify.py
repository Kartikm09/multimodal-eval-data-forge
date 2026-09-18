"""Verify real corpus files and independently known seeded failures."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from multimodal_eval_forge.business_review import review_bundle, verify_redaction


def main():
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT
    )
    if result.returncode:
        return result.returncode
    base = ROOT / "examples/business-review"
    expected = {
        "reference": set(),
        "candidate-a": {
            "unsupported_claim",
            "omitted_requirement",
            "stale_value",
            "wrong_formula",
        },
        "candidate-b": {"inconsistent_units", "clipping", "contradictory_conclusion"},
    }
    reports = {}
    for variant, codes in expected.items():
        result = review_bundle(base / variant, base / "source.json")
        observed = {issue["code"] for issue in result["issues"]}
        if observed != codes:
            raise AssertionError((variant, codes, observed))
        stored = json.loads((base / variant / "issues.json").read_text())
        if stored != result:
            raise AssertionError("Stale committed issue report: " + variant)
        reports[variant] = {
            "status": "PASS" if not codes else "EXPECTED NEGATIVE CASE",
            "detected_codes": sorted(observed),
        }
    labels = json.loads((base / "privacy/labels.json").read_text())
    privacy = verify_redaction(
        base / "privacy/redacted.pdf",
        labels["sensitive_values"],
        labels["preserve_values"],
    )
    if privacy["leaks"] or privacy["lost_public_text"]:
        raise AssertionError(privacy)
    print(
        json.dumps(
            {
                "classification": "synthetic",
                "bundles": reports,
                "redaction": privacy,
                "human_review": "Still required; automation is not certification",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
