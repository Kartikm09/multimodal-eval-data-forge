"""Render validation reports."""

from __future__ import annotations

from .validator import ValidationReport


def render_validation(report: ValidationReport) -> str:
    lines = [
        "Multimodal Eval Data Forge",
        f"Status: {report.status}",
        f"Records: {report.passed_records}/{report.total_records} passed",
    ]
    if report.findings:
        lines.append("")
        lines.append("Findings")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} {finding.record_id}: {finding.message}")
    return "\n".join(lines)
