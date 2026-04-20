from __future__ import annotations

import argparse
import json
import sys
from multiprocessing import freeze_support

from .data import detect_problem_file, find_sample_file
from .evaluation import evaluate_functional_correctness
from .paths import DEFAULT_PROBLEM_FILE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate QuanBench model-generated solutions and report pass@k."
    )
    parser.add_argument("sample_file", help="Path or filename of the generated solutions jsonl.")
    parser.add_argument(
        "--k",
        default="1,5,10,30,50,100",
        help="Comma-separated pass@k values. Default: 1,5,10,30,50,100",
    )
    parser.add_argument("--n-workers", type=int, default=4, help="Number of worker threads.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=50.0,
        help="Per-sample timeout in seconds.",
    )
    parser.add_argument(
        "--problem-file",
        default=None,
        help=(
            "Problem-set jsonl path. If omitted, Quanbench_eval will auto-select "
            "the 44-task or 117-task problem file based on the sample location."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    sample_file = find_sample_file(args.sample_file)
    problem_file = detect_problem_file(sample_file, args.problem_file)
    k_values = [int(value) for value in args.k.split(",") if value.strip()]
    results = evaluate_functional_correctness(
        sample_file=sample_file,
        k=k_values,
        n_workers=args.n_workers,
        timeout=args.timeout,
        problem_file=problem_file,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    freeze_support()
    sys.exit(main())
