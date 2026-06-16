---
name: eval-data-forge
description: Create or validate synthetic public-safe AI evaluation tasks for multimodal model review, including video, UI, image, audio, voice-agent, and red-team workflows.
---

# Eval Data Forge

Use this skill when preparing synthetic AI evaluation data for portfolio demos, QA harnesses, reviewer calibration, or model-eval workflows.

## Workflow

1. Define the evaluation domain: video, UI, image, audio, voice, red-team, or mixed.
2. Write prompts that require observable workflow judgment instead of vague preference.
3. Include input asset names as synthetic references, never private files or real client data.
4. Define expected artifacts such as scorecards, failure points, edit notes, or handoff gaps.
5. Use at least three rubric dimensions with clear point weights.
6. Add risk tags that identify the evaluation surface.
7. Validate each JSONL record before using it in a benchmark or demo.

## Output

Return JSONL-ready records plus a short validation summary.
