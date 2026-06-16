"""Command line interface for synthetic multimodal eval datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .forge import DOMAINS, generate_dataset
from .io import read_jsonl, write_jsonl
from .report import render_validation
from .validator import validate_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and validate multimodal evaluation JSONL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate synthetic records.")
    generate.add_argument("--domain", choices=DOMAINS + ("mixed",), default="mixed")
    generate.add_argument("--count", type=int, default=6)
    generate.add_argument("--seed", type=int, default=17)
    generate.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="Validate a JSONL dataset.")
    validate.add_argument("path", type=Path)
    validate.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        records = generate_dataset(args.domain, args.count, args.seed)
        if args.output:
            write_jsonl(args.output, records)
            print(f"Wrote {len(records)} records to {args.output}")
        else:
            for record in records:
                print(json.dumps(record, sort_keys=True))
        return 0

    if args.command == "validate":
        report = validate_records(read_jsonl(args.path))
        if args.format == "json":
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(render_validation(report))
        return 0 if report.status == "pass" else 1

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
