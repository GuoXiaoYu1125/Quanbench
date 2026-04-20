from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

from .paths import (
    DATA_DIR,
    DEFAULT_PROBLEM_FILE,
    GENERATED_117_DIR,
    GENERATED_44_DIR,
    PROBLEM_FILE_117,
    PROBLEM_SET_117_DIR,
    PROBLEM_SET_44_DIR,
    REPO_ROOT,
)


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate

    direct = (REPO_ROOT / candidate).resolve()
    if direct.exists():
        return direct

    data_candidate = (DATA_DIR / candidate).resolve()
    if data_candidate.exists():
        return data_candidate

    return direct


def default_problem_file() -> Path:
    return DEFAULT_PROBLEM_FILE.resolve()


def read_problems(evalset_file: str | Path | None = None) -> Dict[str, Dict]:
    problem_file = resolve_path(evalset_file or default_problem_file())
    return {task["task_id"]: task for task in stream_jsonl(problem_file)}


def stream_jsonl(filename: str | Path) -> Iterator[Dict]:
    path = resolve_path(filename)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8-sig") as fp:
            for line in fp:
                if line.strip():
                    yield json.loads(line)
    else:
        with path.open("r", encoding="utf-8-sig") as fp:
            for line in fp:
                if line.strip():
                    yield json.loads(line)


def write_jsonl(filename: str | Path, data: Iterable[Dict], append: bool = False) -> Path:
    path = resolve_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix == ".gz":
        mode = "ab" if append else "wb"
        with path.open(mode) as raw_fp:
            with gzip.GzipFile(fileobj=raw_fp, mode="wb") as gz_fp:
                for item in data:
                    gz_fp.write((json.dumps(item, ensure_ascii=False) + "\n").encode("utf-8"))
    else:
        mode = "a" if append else "w"
        with path.open(mode, encoding="utf-8") as fp:
            for item in data:
                fp.write(json.dumps(item, ensure_ascii=False) + "\n")

    return path


def find_sample_file(name: str | Path, search_dir: Optional[str | Path] = None) -> Path:
    candidate = Path(name)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    search_roots = []
    if search_dir is not None:
        search_roots.append(resolve_path(search_dir))
    search_roots.extend(
        [
            PROBLEM_SET_44_DIR,
            PROBLEM_SET_117_DIR,
            GENERATED_44_DIR,
            GENERATED_117_DIR,
            REPO_ROOT / "LLM_gen_Quanbench1",
            DATA_DIR,
            REPO_ROOT,
        ]
    )

    for root in search_roots:
        path = (root / candidate).resolve()
        if path.exists():
            return path

    return resolve_path(candidate)


def detect_problem_file(sample_file: str | Path, requested_problem_file: str | Path | None = None) -> Path:
    if requested_problem_file is not None:
        return resolve_path(requested_problem_file)

    sample_path = resolve_path(sample_file)
    sample_text = str(sample_path)

    if GENERATED_117_DIR.resolve() in sample_path.parents:
        return resolve_path(PROBLEM_FILE_117)

    if GENERATED_44_DIR.resolve() in sample_path.parents:
        return resolve_path(DEFAULT_PROBLEM_FILE)

    if "LLM_gen_Quanbench1" in sample_text:
        return resolve_path(PROBLEM_FILE_117)

    return resolve_path(DEFAULT_PROBLEM_FILE)
