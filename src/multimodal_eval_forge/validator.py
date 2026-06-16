"""Validate synthetic multimodal evaluation task records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_FIELDS = ("id", "domain", "prompt", "input_assets", "expected_artifacts", "rubric", "risk_tags", "reviewer_notes")


@dataclass(frozen=True)
class RecordFinding:
    record_id: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"record_id": self.record_id, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class ValidationReport:
    total_records: int
    passed_records: int
    findings: list[RecordFinding]

    @property
    def status(self) -> str:
        return "pass" if not any(item.severity == "error" for item in self.findings) else "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "total_records": self.total_records,
            "passed_records": self.passed_records,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def validate_records(records: list[dict[str, Any]]) -> ValidationReport:
    findings: list[RecordFinding] = []
    for record in records:
        record_id = str(record.get("id", "unknown"))
        for field in REQUIRED_FIELDS:
            if field not in record:
                findings.append(RecordFinding(record_id, "error", f"missing field: {field}"))
        if len(str(record.get("prompt", "")).split()) < 8:
            findings.append(RecordFinding(record_id, "warn", "prompt is too short for evaluator calibration"))
        if not isinstance(record.get("rubric"), dict) or len(record.get("rubric", {})) < 3:
            findings.append(RecordFinding(record_id, "error", "rubric must include at least three scoring dimensions"))
        if not record.get("expected_artifacts"):
            findings.append(RecordFinding(record_id, "error", "expected_artifacts must not be empty"))
        if not record.get("risk_tags"):
            findings.append(RecordFinding(record_id, "warn", "risk_tags should identify the evaluation surface"))

    error_ids = {finding.record_id for finding in findings if finding.severity == "error"}
    return ValidationReport(len(records), len(records) - len(error_ids), findings)
