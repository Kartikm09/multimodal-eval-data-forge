"""Checks for the bounded, fictional business-review corpus.

Not a general spreadsheet engine, PII detector, legal opinion or certification.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import operator
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile


N = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
}


def evaluate_formula(cell, cells, _visiting=None):
    """Evaluate bounded arithmetic/reference formulas without executing code or reading cached results."""
    visiting = set() if _visiting is None else set(_visiting)
    if cell in visiting or len(visiting) > 100:
        raise ValueError("cyclic or excessively deep formula")
    visiting.add(cell)
    value = cells.get(cell)
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite numeric cell")
        return value
    if not isinstance(value, str) or not value.startswith("=") or len(value) > 1000:
        raise ValueError("missing numeric cell or unsupported formula")
    try:
        tree = ast.parse(value[1:].replace("$", ""), mode="eval")

        def calculate(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                return node.value
            if isinstance(node, ast.Name) and re.fullmatch(
                r"[A-Z]{1,3}[1-9][0-9]{0,5}", node.id
            ):
                return evaluate_formula(node.id, cells, visiting)
            if isinstance(node, ast.BinOp) and type(node.op) in (
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
            ):
                fn = {
                    ast.Add: operator.add,
                    ast.Sub: operator.sub,
                    ast.Mult: operator.mul,
                    ast.Div: operator.truediv,
                }[type(node.op)]
                return fn(calculate(node.left), calculate(node.right))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return -calculate(node.operand)
            raise ValueError("unsupported formula expression")

        result = calculate(tree.body)
        if not math.isfinite(result):
            raise ValueError("nonfinite formula result")
        return result
    except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError("invalid arithmetic formula") from exc


def _safe_file(bundle, name):
    base = Path(bundle).resolve()
    path = (base / name).resolve()
    if (
        not path.is_relative_to(base)
        or not path.is_file()
        or path.stat().st_size > 10_000_000
    ):
        raise ValueError("missing, out-of-bounds or oversized artifact")
    return path


def _xml(archive, name):
    info = archive.getinfo(name)
    if info.file_size > 10_000_000:
        raise ValueError("oversized XML part")
    return ET.fromstring(archive.read(name))


def docx_text(path):
    with zipfile.ZipFile(path) as archive:
        root = _xml(archive, "word/document.xml")
        return "\n".join(
            "".join(t.text or "" for t in p.findall(".//w:t", N))
            for p in root.findall(".//w:p", N)
        )


def slide_evidence(path):
    text = []
    clipped = []
    with zipfile.ZipFile(path) as archive:
        size = _xml(archive, "ppt/presentation.xml").find("p:sldSz", N)
        width, height = int(size.attrib["cx"]), int(size.attrib["cy"])
        for name in sorted(
            n
            for n in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
        ):
            root = _xml(archive, name)
            for shape in root.findall(".//p:sp", N):
                content = " ".join(t.text or "" for t in shape.findall(".//a:t", N))
                text.append(content)
                transform = shape.find("p:spPr/a:xfrm", N)
                if transform is None:
                    continue
                offset = transform.find("a:off", N)
                extent = transform.find("a:ext", N)
                if offset is None or extent is None:
                    continue
                x, y = int(offset.attrib["x"]), int(offset.attrib["y"])
                w, h = int(extent.attrib["cx"]), int(extent.attrib["cy"])
                if min(x, y) < 0 or x + w > width or y + h > height:
                    clipped.append(
                        {"part": name, "text": content, "bounds": [x, y, w, h]}
                    )
    return "\n".join(text), clipped


def workbook_cells(path):
    with zipfile.ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = [
                "".join(t.text or "" for t in item.findall(".//s:t", N))
                for item in _xml(archive, "xl/sharedStrings.xml").findall("s:si", N)
            ]
        root = _xml(archive, "xl/worksheets/sheet1.xml")
        cells = {}
        for cell in root.findall(".//s:c", N):
            formula = cell.find("s:f", N)
            value = cell.find("s:v", N)
            if formula is not None:
                cells[cell.attrib["r"]] = "=" + (formula.text or "")
            elif value is not None:
                cells[cell.attrib["r"]] = (
                    strings[int(value.text)]
                    if cell.get("t") == "s"
                    else value.text
                    if cell.get("t") == "str"
                    else float(value.text)
                )
            elif cell.get("t") == "inlineStr":
                cells[cell.attrib["r"]] = "".join(
                    t.text or "" for t in cell.findall(".//s:t", N)
                )
        return cells


def pdf_text(path):
    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def review_bundle(bundle, source_path):
    source = json.loads(Path(source_path).read_text())
    manifest = json.loads(_safe_file(bundle, "manifest.json").read_text())
    reports = docx_text(_safe_file(bundle, "report.docx"))
    pdf = pdf_text(_safe_file(bundle, "report.pdf"))
    slides, clipped = slide_evidence(_safe_file(bundle, "slides.pptx"))
    cells = workbook_cells(_safe_file(bundle, "workbook.xlsx"))
    issues = []

    def issue(code, file, detail, source_ref=None, expected=None, actual=None):
        issues.append(
            {
                "id": f"issue-{len(issues) + 1}",
                "code": code,
                "file": file,
                "detail": detail,
                "source_ref": source_ref,
                "expected": expected,
                "actual": actual,
                "severity": "error",
            }
        )

    declared = {claim.get("source_ref") for claim in manifest.get("claims", [])}
    for ref in source["facts"]:
        if ref not in declared:
            issue(
                "missing_claim",
                "manifest.json",
                "Required source fact lacks a traceable claim",
                ref,
            )
    for claim in manifest.get("claims", []):
        text = claim["text"]
        ref = claim["source_ref"]
        fact = source["facts"].get(ref)
        if text not in reports or text not in pdf:
            issue(
                "missing_evidence",
                "report.docx/report.pdf",
                "Declared claim does not appear in both submitted reports",
                ref,
                actual=text,
            )
            continue
        if fact is None:
            issue(
                "unsupported_claim",
                "report.docx",
                "No source supports this claim",
                ref,
                actual=text,
            )
            continue
        canonical = f"{fact['label']}: {claim['value']} {claim['unit']} ({ref} {claim['version']})"
        if text != canonical:
            issue(
                "claim_metadata_mismatch",
                "manifest.json",
                "Claim metadata does not encode the actual declared text",
                ref,
                canonical,
                text,
            )
        if claim["version"] != fact["version"] or claim["value"] != fact["value"]:
            issue(
                "stale_value",
                "report.docx",
                "Claim disagrees with current source value or version",
                ref,
                fact,
                claim,
            )
        if claim["unit"] != fact["unit"]:
            issue(
                "inconsistent_units",
                "report.docx",
                "Claim unit differs from source unit",
                ref,
                fact["unit"],
                claim["unit"],
            )
    for required in source["requirements"]:
        if required + ":" not in reports or required + ":" not in pdf:
            issue(
                "omitted_requirement",
                "report.docx/report.pdf",
                f"Missing required field {required}",
            )
    report_decision = re.search(r"^Decision:\s*(.+)", reports, re.M)
    slide_decision = re.search(r"^Decision:\s*(.+)", slides, re.M)
    if not report_decision or not slide_decision:
        issue(
            "missing_evidence",
            "slides.pptx",
            "Decision must appear in report and slides",
        )
    elif report_decision[1].strip() != slide_decision[1].strip():
        issue(
            "contradictory_conclusion",
            "slides.pptx",
            "Report and slide conclusions differ",
            expected=report_decision[1].strip(),
            actual=slide_decision[1].strip(),
        )
    for item in clipped:
        issue(
            "clipping", "slides.pptx", "Text shape extends outside slide", actual=item
        )
    facts = source["facts"]
    revenue = facts["S1"]["value"] * facts["S2"]["value"]
    cost = facts["S1"]["value"] * facts["S3"]["value"]
    for cell, expected in {"B8": revenue, "B9": cost, "B10": revenue - cost}.items():
        try:
            actual = evaluate_formula(cell, cells)
        except ValueError as exc:
            issue("invalid_formula", "workbook.xlsx", str(exc), actual=cell)
            continue
        if abs(actual - expected) > 0.005:
            issue(
                "wrong_formula",
                "workbook.xlsx",
                f"{cell} differs from independently calculated source expectation",
                expected=expected,
                actual=actual,
            )
    return {
        "schema_version": 1,
        "classification": "synthetic",
        "bundle_id": manifest["bundle_id"],
        "source_version": source["version"],
        "issues": issues,
        "requires_human_review": True,
        "automated_status": "review" if issues else "no_known_fixture_errors",
        "human_review_topics": ["writing quality", "ambiguous privacy context"],
        "certification": False,
    }


def _normalized(text):
    chars = []
    offsets = []
    for i, char in enumerate(text):
        if unicodedata.category(char) == "Cf":
            continue
        for normalized in unicodedata.normalize("NFKC", char).casefold():
            chars.append(" " if normalized.isspace() else normalized)
            offsets.append(i)
    return "".join(chars), offsets


def find_sensitive_spans(text, values):
    normalized, offsets = _normalized(text)
    spans = []
    for value in values:
        needle, _ = _normalized(value)
        if not needle:
            continue
        start = 0
        while (index := normalized.find(needle, start)) >= 0:
            spans.append(
                {
                    "start": offsets[index],
                    "end": offsets[index + len(needle) - 1] + 1,
                    "label": value,
                }
            )
            start = index + len(needle)
    return sorted(spans, key=lambda item: (item["start"], item["end"]))


def pii_metrics(predicted, gold):
    predictions = set(map(tuple, predicted))
    expected = set(map(tuple, gold))
    tp = len(predictions & expected)
    fp = len(predictions - expected)
    fn = len(expected - predictions)
    return {
        "precision": tp / (tp + fp) if tp + fp else 1.0,
        "recall": tp / (tp + fn) if tp + fn else 1.0,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
    }


def redact_text_pdf(source, destination, sensitive_values):
    """Rebuild the text-only synthetic template; no original page objects survive.

    This deliberately does not promise arbitrary PDF layout preservation.
    """
    from pypdf import PdfReader
    from reportlab.pdfgen.canvas import Canvas

    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError("redaction must create a new file and preserve originals")
    reader = PdfReader(source)
    if reader.get_fields() or any(
        page.images or page.get("/Annots") for page in reader.pages
    ):
        raise ValueError("only simple text-only synthetic PDFs are supported")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    for span in reversed(find_sensitive_spans(text, sensitive_values)):
        text = text[: span["start"]] + "[REDACTED]" + text[span["end"] :]
    canvas = Canvas(str(destination), pagesize=(612, 792), invariant=1)
    canvas.setTitle("Synthetic privacy review redacted copy")
    y = 744
    for line in text.splitlines():
        if y < 48:
            canvas.showPage()
            y = 744
        canvas.setFont("Helvetica", 11)
        canvas.drawString(48, y, line)
        y -= 20
    canvas.save()


def verify_redaction(path, sensitive_values, preserve_values):
    text = pdf_text(path)
    return {
        "leaks": [
            span["label"] for span in find_sensitive_spans(text, sensitive_values)
        ],
        "lost_public_text": [value for value in preserve_values if value not in text],
        "visible_review_required": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = review_bundle(args.bundle, args.source)
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    print(text)
    return 1 if result["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
