# Multimodal Eval Data Forge

Synthetic dataset generator and validator for multimodal AI evaluation tasks.

This repository creates portfolio-safe JSONL evaluation tasks for:

- Video editing and post-production workflows
- UI tool-use tasks
- Image and graphic QA
- Audio review tasks
- Voice-agent interaction checks
- Agent red-team scenarios

It also validates task records for rubric completeness, artifact expectations, and risk tags.

## Why It Exists

AI evaluation work depends on clean, reviewable, well-scoped tasks. Real client datasets are often confidential, so portfolio projects need synthetic examples that still show evaluator judgment.

This forge creates realistic public-safe tasks that can be used in demos, QA pipelines, model-eval harnesses, and reviewer calibration exercises.

## Quick Start

Generate a small dataset:

```bash
PYTHONPATH=src python3 -m multimodal_eval_forge.cli generate --domain video --count 5
```

Write generated records to JSONL:

```bash
PYTHONPATH=src python3 -m multimodal_eval_forge.cli generate --domain mixed --count 12 --output generated_tasks.jsonl
```

Validate a JSONL file:

```bash
PYTHONPATH=src python3 -m multimodal_eval_forge.cli validate examples/dataset.jsonl
```

Run tests (the artifact checks require the pinned review dependencies):

```bash
python3 -m pip install -r requirements-review.txt
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Record Shape

Each task record includes:

- `id`
- `domain`
- `prompt`
- `input_assets`
- `expected_artifacts`
- `rubric`
- `risk_tags`
- `reviewer_notes`

## Portfolio Signal

This project demonstrates:

- Synthetic AI evaluation dataset design
- Multimodal QA thinking
- Rubric and reviewer-calibration design
- JSONL validation
- Python CLI development
- Public-safe AI training portfolio work

## Business document and privacy review

The [fictional Alder review corpus](examples/business-review/README.md) adds actual DOCX/PDF reports, slides, formula workbooks, two deliberately flawed candidates, known-label privacy checks, and a local human review queue. Run `PYTHONPATH=src python scripts/verify.py` after installing the pinned review dependencies. No automated finding is a certification.
