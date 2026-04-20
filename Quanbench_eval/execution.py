from __future__ import annotations

import builtins
import cmath
import contextlib
import faulthandler
import io
import multiprocessing
import os
from pathlib import Path
import platform
import signal
import sys
import tempfile
import time
import traceback
import types
import unittest
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict, Optional

import numpy as np

from .paths import REPO_ROOT
from .paths import TASKS_DIR
from .test_matrix import (
    check_phase,
    compare_depth_gatecount,
    compute_KL,
    compute_KL_noexecute,
    compute_matrix_similarity,
    is_gate_count_subset,
    run_circuit,
    unitary_equivalent,
)


def build_check_program(problem: Dict, completion: str) -> str:
    if problem.get("canonical_solution"):
        solution_import = "\n".join(
            [
                problem["canonical_solution"],
                f"cir_solution = {problem['entry_point']}",
            ]
        )
    elif TASKS_DIR.exists():
        solution_import = (
            f"from Quanbench.s{problem['task_id']}.solution "
            f"import {problem['entry_point']} as cir_solution"
        )
    else:
        raise FileNotFoundError(
            "Missing reference solution for task "
            f"{problem['task_id']}. Neither `canonical_solution` in the "
            "problem set nor `Quanbench/sXX/solution.py` is available."
        )
    generated_alias = f"cir_generated = {problem['entry_point']}"
    return "\n".join([solution_import, completion, generated_alias, problem["test"]])


def unsafe_execute(problem: Dict, completion: str, timeout: float, result) -> None:
    with create_tempdir():
        import shutil

        original_rmtree = shutil.rmtree
        original_rmdir = os.rmdir
        original_chdir = os.chdir

        module_name = "__quanbench_eval__"
        mod = types.ModuleType(module_name)
        mod.__dict__.update(
            {
                "__builtins__": builtins,
                "__file__": f"{module_name}.py",
                "__package__": None,
                "__doc__": None,
                "sys": sys,
                "os": os,
                "np": np,
                "cmath": cmath,
                "environ": os.environ,
                "run_circuit": run_circuit,
                "compute_KL": compute_KL,
                "compare_depth_gatecount": compare_depth_gatecount,
                "unitary_equivalent": unitary_equivalent,
                "compute_matrix_similarity": compute_matrix_similarity,
                "compute_KL_noexecute": compute_KL_noexecute,
                "check_phase": check_phase,
                "is_gate_count_subset": is_gate_count_subset,
            }
        )

        repo_root = str(REPO_ROOT)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        details = {}
        try:
            check_program = build_check_program(problem, completion)
            with swallow_io():
                exec(check_program, mod.__dict__)
                suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
                test_result = unittest.TestResult()
                with time_limit(timeout):
                    suite.run(test_result)
            issues = test_result.failures + test_result.errors
            for test, trace in issues:
                details[test.id().split(".")[-1]] = trace
            if issues:
                raise AssertionError(issues)
        except BaseException:
            if not details:
                details["All"] = traceback.format_exc()

        if details:
            result.append(details)
        else:
            result.append("passed")

        shutil.rmtree = original_rmtree
        os.rmdir = original_rmdir
        os.chdir = original_chdir


def check_correctness(
    problem: Dict, completion: str, timeout: float, completion_id: Optional[int] = None
) -> Dict:
    manager = multiprocessing.Manager()
    result = manager.list()

    process = multiprocessing.Process(
        target=unsafe_execute, args=(problem, completion, timeout, result)
    )
    process.start()
    process.join(timeout=timeout + 1)
    if process.is_alive():
        process.kill()

    if not result:
        result.append("timed out")

    return {
        "task_id": problem["task_id"],
        "passed": result[0] == "passed",
        "result": result[0],
        "completion_id": completion_id,
    }


class TimeoutException(Exception):
    pass


@contextlib.contextmanager
def time_limit(seconds: float):
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        yield lambda fn, *args, **kwargs: executor.submit(fn, *args, **kwargs).result(
            timeout=seconds
        )
    except TimeoutError as exc:
        raise TimeoutException("Timed out!") from exc
    finally:
        executor.shutdown(wait=False)


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname


class WriteOnlyStringIO(io.StringIO):
    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore[attr-defined]
    _stream = "stdin"


@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(cwd)


def reliability_guard(maximum_memory_bytes: Optional[int] = None):
    if maximum_memory_bytes is not None:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if platform.uname().system != "Darwin":
            resource.setrlimit(
                resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes)
            )

    faulthandler.disable()
    builtins.exit = None
    builtins.quit = None

    os.environ["OMP_NUM_THREADS"] = "1"
    os.kill = None
    os.system = None
    os.putenv = None
    os.remove = None
    os.removedirs = None
    os.rmdir = None
    os.fchdir = None
    os.setuid = None
    os.fork = None
    os.forkpty = None
    os.killpg = None
    os.rename = None
    os.renames = None
    os.truncate = None
    os.replace = None
    os.unlink = None
    os.fchmod = None
    os.fchown = None
    os.chmod = None
    os.chown = None
    os.chroot = None
    os.getcwd = None
    os.chdir = None

    import shutil
    import subprocess

    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None
    subprocess.Popen = None  # type: ignore[assignment]

    __builtins__["help"] = None
    sys.modules["ipdb"] = None
    sys.modules["joblib"] = None
    sys.modules["resource"] = None
    sys.modules["psutil"] = None
    sys.modules["tkinter"] = None
