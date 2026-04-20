# QuanBench

QuanBench is a benchmark suite for evaluating Large Language Models (LLMs) on quantum program generation.

This repository currently contains:

- `Quanbench_eval/`: a functional evaluation pipeline for QuanBench-generated solutions
- `Quanbench_eval/problem_sets/quanbench44/Quanbench.jsonl`: the 44-task problem set
- `Quanbench_eval/problem_sets/quanbench117/Quanbench.jsonl`: the 117-task problem set
- `Quanbench_eval/generated/`: example model outputs and evaluation inputs
- `QuanBench44.jsonl` and `Quanbench117.jsonl`: top-level dataset copies kept for compatibility with earlier layouts

## Repository Status

The evaluation pipeline in `Quanbench_eval/` is self-contained for the included problem sets.

Reference implementations are loaded from the `canonical_solution` field inside the problem-set JSONL files. If an external `Quanbench/sXX/solution.py` directory is present, it can still be used as a compatibility fallback for tasks that do not embed a canonical solution.

## Installation

Create and activate the Conda environment:

```powershell
conda env create -f environment.yml
conda activate Quanbench
```

If you already have a Conda environment named `Quanbench`, you can activate it directly:

```powershell
conda activate Quanbench
```

If needed, you can also install the same dependencies into the active environment with:

```powershell
python -m pip install -r requirements.txt
```

Core runtime dependencies in the `Quanbench` environment:

- `numpy`
- `qiskit>=1.0`
- `qiskit-aer`
- `tqdm`

## Evaluation Usage

Run from the repository root.

Example for the 44-task set:

```powershell
python -m Quanbench_eval.evaluate_functional_correctness Quanbench_eval/generated/quanbench44/results_gpt-4.1_T0.8.jsonl
```

Example for the 117-task set:

```powershell
python -m Quanbench_eval.evaluate_functional_correctness Quanbench_eval/generated/quanbench117/results_gpt-4o.jsonl
```

You can also override the default evaluation parameters:

```powershell
python -m Quanbench_eval.evaluate_functional_correctness Quanbench_eval/generated/quanbench44/<your_file>.jsonl --k 1,5,10 --n-workers 4 --timeout 50
```

By default, the evaluator writes:

```text
<sample_file>_results.jsonl
```

next to the input sample file.

## Layout Notes

- `Quanbench_eval/generated/quanbench44` maps to the 44-task problem set
- `Quanbench_eval/generated/quanbench117` maps to the 117-task problem set
- `Quanbench_eval/problem_sets/` is the preferred source for benchmark JSONL files
- historical paths such as `data/` and `LLM_gen_Quanbench1/` are still referenced only for compatibility

## Before Publishing

These remaining items should be decided manually before making the repository public:

1. Decide whether the top-level JSONL copies should remain, or whether `Quanbench_eval/problem_sets/` should become the only canonical dataset location.

## License

This repository is released under the MIT License. See [LICENSE](LICENSE) for details.
