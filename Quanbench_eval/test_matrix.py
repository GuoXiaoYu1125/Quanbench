from math import log2
import cmath
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from qiskit import QuantumCircuit


def _qiskit_imports():
    from qiskit import transpile
    from qiskit.quantum_info import Operator, Statevector
    from qiskit_aer import Aer

    return transpile, Operator, Statevector, Aer


def run_circuit(circuit: "QuantumCircuit", shots: int = 10000) -> dict:
    transpile, _, _, Aer = _qiskit_imports()
    simulator = Aer.get_backend("qasm_simulator")
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=shots).result()
    return result.get_counts()


def compute_KL(circuit1: "QuantumCircuit", circuit2: "QuantumCircuit", shots: int = 10000) -> float:
    counts1 = run_circuit(circuit1, shots)
    counts2 = run_circuit(circuit2, shots)
    return compute_KL_noexecute(counts1, counts2, shots=shots)


def compute_KL_noexecute(counts1: dict, counts2: dict, shots: int = 10000) -> float:
    all_keys = set(counts1.keys()).union(set(counts2.keys()))
    p = np.array([max(counts1.get(key, 0) / shots, 1e-10) for key in all_keys])
    q = np.array([max(counts2.get(key, 0) / shots, 1e-10) for key in all_keys])
    return kl_divergence(p, q)


def compare_depth_gatecount(circ1: "QuantumCircuit", circ2: "QuantumCircuit") -> dict:
    info1 = analyze_circuit(circ1)
    info2 = analyze_circuit(circ2)
    all_gate_keys = set(info1["gate_counts"].keys()).union(set(info2["gate_counts"].keys()))
    gate_counts_diff = {
        gate: info1["gate_counts"].get(gate, 0) - info2["gate_counts"].get(gate, 0)
        for gate in all_gate_keys
    }
    return {
        "depth_diff": info1["depth"] - info2["depth"],
        "total_gates_diff": info1["total_gates"] - info2["total_gates"],
        "gate_counts_diff": gate_counts_diff,
    }


def unitary_equivalent(circ1: "QuantumCircuit", circ2: "QuantumCircuit") -> bool:
    _, Operator, _, _ = _qiskit_imports()
    qc1 = circ1.copy()
    qc2 = circ2.copy()
    qc1.remove_final_measurements()
    qc2.remove_final_measurements()
    return Operator(qc1).equiv(Operator(qc2))


def compute_matrix_similarity(circ1: "QuantumCircuit", circ2: "QuantumCircuit") -> float:
    _, Operator, _, _ = _qiskit_imports()
    qc1 = circ1.copy()
    qc2 = circ2.copy()
    qc1.remove_final_measurements()
    qc2.remove_final_measurements()
    u1 = Operator(qc1).data
    u2 = Operator(qc2).data
    return np.linalg.norm(u1 - u2, "fro")


def check_phase(circuit: "QuantumCircuit", state: str) -> float:
    _, _, Statevector, _ = _qiskit_imports()
    qc = circuit.copy()
    qc.remove_final_measurements()
    index = int(state, 2)
    amp = Statevector.from_instruction(qc).data[index]
    return cmath.phase(amp)


def is_gate_count_subset(expected: dict, actual: dict) -> bool:
    return all(actual.get(gate, 0) >= count for gate, count in expected.items())


def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    return sum(p[idx] * log2(p[idx] / q[idx]) for idx in range(len(p)))


def analyze_circuit(circuit: "QuantumCircuit") -> dict:
    qc = circuit.copy()
    qc.remove_final_measurements()
    gate_counts = qc.count_ops()
    return {
        "depth": qc.depth(),
        "total_gates": sum(gate_counts.values()),
        "gate_counts": dict(gate_counts),
    }
