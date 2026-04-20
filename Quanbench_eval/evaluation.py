from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
from pathlib import Path
from typing import Dict, Iterable, List, Union

import numpy as np
import tqdm

from .data import read_problems, stream_jsonl, write_jsonl
from .execution import check_correctness
from .paths import DEFAULT_PROBLEM_FILE


def estimate_pass_at_k(
    num_samples: Union[int, List[int], np.ndarray],
    num_correct: Union[List[int], np.ndarray],
    k: int,
) -> np.ndarray:
    def estimator(n: int, c: int, k_value: int) -> float:
        if n - c < k_value:
            return 1.0
        return 1.0 - np.prod(1.0 - k_value / np.arange(n - c + 1, n + 1))

    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    return np.array(
        [estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)]
    )


def evaluate_functional_correctness(
    sample_file: str | Path,
    k: List[int] | None = None,
    n_workers: int = 4,
    timeout: float = 50.0,
    problem_file: str | Path = DEFAULT_PROBLEM_FILE,
) -> Dict[str, float]:
    ks = k or [1, 5, 10, 30, 50, 100]
    problems = read_problems(problem_file)

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        completion_id = Counter()
        n_samples = 0
        results = defaultdict(list)

        print("Reading samples...")
        for sample in tqdm.tqdm(stream_jsonl(sample_file)):
            task_id = sample["task_id"]
            completion = sample["solution"]
            args = (problems[task_id], completion, timeout, completion_id[task_id])
            futures.append(executor.submit(check_correctness, *args))
            completion_id[task_id] += 1
            n_samples += 1

        assert len(completion_id) == len(problems), "Some problems are not attempted."

        print("Running test suites...")
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            results[result["task_id"]].append((result["completion_id"], result))

    total, correct = [], []
    for result in results.values():
        result.sort()
        passed = [item[1]["passed"] for item in result]
        total.append(len(passed))
        correct.append(sum(passed))

    total_array = np.array(total)
    correct_array = np.array(correct)

    pass_at_k = {
        f"pass@{k_value}": estimate_pass_at_k(total_array, correct_array, k_value).mean()
        for k_value in ks
        if (total_array >= k_value).all()
    }

    def combine_results():
        ordered = {task_id: list(task_results) for task_id, task_results in results.items()}
        for sample in stream_jsonl(sample_file):
            task_id = sample["task_id"]
            result = ordered[task_id].pop(0)
            sample["result"] = result[1]["result"]
            sample["passed"] = result[1]["passed"]
            yield sample

    output_path = Path(str(sample_file) + "_results.jsonl")
    print(f"Writing results to {output_path}...")
    write_jsonl(output_path, tqdm.tqdm(combine_results(), total=n_samples))
    return pass_at_k

