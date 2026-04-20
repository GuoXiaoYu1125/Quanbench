from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
DATA_DIR = REPO_ROOT / "data"
TASKS_DIR = REPO_ROOT / "Quanbench"
PROBLEM_SETS_DIR = PACKAGE_ROOT / "problem_sets"
PROBLEM_SET_44_DIR = PROBLEM_SETS_DIR / "quanbench44"
PROBLEM_SET_117_DIR = PROBLEM_SETS_DIR / "quanbench117"
DEFAULT_PROBLEM_FILE = PROBLEM_SET_44_DIR / "Quanbench.jsonl"
GENERATED_DIR = PACKAGE_ROOT / "generated"
GENERATED_44_DIR = GENERATED_DIR / "quanbench44"
GENERATED_117_DIR = GENERATED_DIR / "quanbench117"
PROBLEM_FILE_117 = PROBLEM_SET_117_DIR / "Quanbench.jsonl"


def has_reference_solutions() -> bool:
    return TASKS_DIR.exists()
