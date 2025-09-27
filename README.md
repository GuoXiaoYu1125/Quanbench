# Quanbench
QuanBench is a benchmark suite for evaluating Large Language Models (LLMs) on quantum program generation.

We currently provide two released versions:
- QuanBench-44: Initial release with 44 tasks.
- QuanBench-117: Extended version with 117 tasks.

An automated testing framework based on HumanEval will be released in the future, enabling consistent and reproducible evaluation of LLMs.

Notes on QuanBench-117
- QuanBench-117 is designed for Qiskit 1.0.
- When evaluating LLMs, a common issue arises:
Many LLMs automatically import outdated Qiskit modules during code generation, which leads to runtime errors.
This problem cannot be resolved by prompt engineering alone (e.g., instructing the model not to add extra imports).

