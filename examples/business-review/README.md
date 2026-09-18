# Fictional artifact review

Alder Refill Cooperative is fictional. The source brief, names, contacts, account references, prices, documents and reviewer cases are synthetic portfolio fixtures authored on 18 September 2026. They are not client work, historical media or evidence of external review acceptance.

The [source brief](source-brief.md) and [versioned facts](source.json) define a 120-unit pilot. Current unit price is USD 25, unit cost USD 15, and package mass 125 g. Independently calculated revenue is USD 3,000, cost USD 1,800, and contribution USD 1,200. Contribution excludes overhead and is not net profit. There is no evidence of measured demand.

| Bundle | Deliberate differences |
| --- | --- |
| reference | Matches known source facts, required fields and arithmetic. Human writing review still required. |
| candidate-a | Invented guaranteed demand, missing Risk field, superseded USD 30 price, addition in revenue formula instead of multiplication. |
| candidate-b | Package mass expressed in kg instead of g, slide rejects the pilot while report approves it, package textbox outside the slide. |

Each bundle contains actual editable DOCX/PPTX/XLSX files, a PDF report, a claim manifest, structured findings, and rendered previews. The DOCX and PDF report contain the same authored text; they are separate exports. `previews/docx/report.pdf` is the actual DOCX-to-PDF render. Slides are two pages, with each full-size render saved under `previews/slides/`. Candidate B's visible clipping is an intended negative case; do not fix its artifact or replace the finding with a success.

## Run the checks

From the repository root, with Python 3.11 or later:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-review.txt
PYTHONPATH=src python scripts/verify.py
```

The verifier runs the full Python suite, checks the actual files, compares computed findings with the committed structured reports, and requires exactly the intended defect categories. Its overall exit code is zero only when reference success and both negative cases behave as expected.

To review one bundle directly:

```sh
PYTHONPATH=src python -m multimodal_eval_forge.business_review examples/business-review/reference --source examples/business-review/source.json
```

Candidate A/B return exit 1 with structured findings. This is expected. Required source references cannot be omitted, and claim metadata must encode the declared report text. The implementation reads XLSX formulas and evaluates bounded arithmetic and cell references independently of cached values. The oracle uses source facts, not another evaluation of the same formula.

## Human review queue

```sh
python3 -m http.server 8767 --bind 127.0.0.1 --directory examples/business-review
```

Open `http://127.0.0.1:8767`. Eight cases cover three business bundles, correct/missed/excessive redaction, Unicode formatting, and an ambiguous contact reference. Search the queue, inspect linked originals and rendered evidence, then record a decision with written evidence. Saves append revisions in browser local storage. Export a JSON history before clearing that storage. There is no backend authorization or tamper-resistant audit claim; use this local interface only for the supplied synthetic material.

Node 22 or later runs the review-state and actual Chromium tests:

```sh
npm ci --ignore-scripts
npm test
npx playwright install chromium
npm run test:browser
```

Playwright 1.61.1 pins Chromium revision 1228; tests set en-US, UTC and a fixed clock for the desktop review. Mobile verification uses 390×844. Screenshots are execution evidence, not cross-platform pixel baselines. Browser tests save and reload a judgment, export its real JSON, exercise keyboard focus, and load an actual privacy preview.

## Privacy labels and removal

All contacts use fictional names and `.test` addresses. `privacy/original.pdf` is retained separately. `redacted.pdf` is rebuilt from sanitized text in this simple text-only synthetic template: no original page objects, metadata, form fields or attachments are copied. It is not a general layout-preserving PDF redactor. Image, annotation and form-bearing PDFs are rejected. Extracted text and visible output must both be reviewed.

`painted-only.pdf` deliberately paints black boxes over extractable private text and fails verification. `missed.pdf` leaves the account reference. `overredacted.pdf` also removes the public kit model. The detector uses the supplied known values, Unicode compatibility normalization and original-text character offsets. It does not claim to discover every name, contact or PII type.

| Known-label case | Precision | Recall |
| --- | ---: | ---: |
| exact | 1 | 1 |
| missed-account | 1 | 2/3 |
| overredacted-model | 3/4 | 1 |
| unicode-formatting | 1 | 1 |

Scoring uses exact `(start, end)` span equality against authored synthetic gold labels; unmatched predictions and labels count false positives and false negatives. `span-cases.json` records source text, gold labels, predictions and metrics. These tiny fixtures do not estimate real-world detection quality. The ambiguous Jordan reference has no automated gold label or score.

## Scope and provenance

Checks cover declared source claims, required report fields, the report/slide conclusion, simple textbox bounds and three spreadsheet result cells in this fixed corpus. They do not infer every possible claim, detect all visual layout errors, implement Excel, assess prose quality, or issue legal/compliance certification. Only trusted fixture documents are supported; this is not a hostile-document parser sandbox.

DOCX authoring used python-docx 1.2.0; PDFs used ReportLab 4.4.9; PPTX/XLSX used the Codex Artifact Tool. Actual DOCX/slides were rendered with bundled headless LibreOffice and Poppler; spreadsheets were recalculated and rendered by Artifact Tool. Rendered fonts can differ from native Office rendering. Committed files are the fixed input corpus; ordinary verification requires only the pinned Python packages and optional Node browser tests. No paid service, model account or live organization is involved. All newly authored fixture content is covered by this repository's existing MIT license.

Actual UI screenshots: [desktop](../../../docs/screenshots/linux-arm64/reviewer-desktop.png) and [mobile](../../../docs/screenshots/linux-arm64/privacy-mobile.png). PDF verification uses pypdf 6.16.1; the pinned dependency set had no known advisories in the 18 September 2026 audit.
