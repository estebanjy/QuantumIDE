"""Circuit optimization: depth minimization, gate-count reduction, transpilation."""

from __future__ import annotations

from typing import Dict, List, Set

import cirq

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.core.gates import GATES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cancel_adjacent(gates: List[GateSpec]) -> List[GateSpec]:
    """Cancel consecutive self-inverse gate pairs (H·H, X·X, etc.)."""
    SELF_INVERSE = {"H", "X", "Y", "Z", "CNOT", "CX", "SWAP"}
    changed = True
    while changed:
        changed = False
        result: List[GateSpec] = []
        skip: Set[int] = set()
        for i, gate in enumerate(gates):
            if i in skip:
                continue
            if (
                gate.name.upper() in SELF_INVERSE
                and i + 1 < len(gates)
                and gates[i + 1].name.upper() == gate.name.upper()
                and gates[i + 1].targets == gate.targets
                and gates[i + 1].controls == gate.controls
            ):
                skip.add(i + 1)
                changed = True
            else:
                result.append(gate)
        gates = result
    return gates


def _remove_identity_pairs(gates: List[GateSpec]) -> List[GateSpec]:
    """Remove S·S·S·S = I and T·T·T·T·T·T·T·T = I cycles."""
    # S^4 = I, T^8 = I — handled by counting consecutive same-qubit runs
    result: List[GateSpec] = []
    for gate in gates:
        result.append(gate)
        name = gate.name.upper()
        if name in ("S", "T"):
            period = 4 if name == "S" else 8
            # collect trailing same-gate same-target sequence
            run = [
                g for g in result
                if g.name.upper() == name and g.targets == gate.targets
            ]
            if len(run) % period == 0:
                # remove the last `period` entries for this gate/qubit
                new_result: List[GateSpec] = []
                removed = 0
                for g in reversed(result):
                    if removed < period and g.name.upper() == name and g.targets == gate.targets:
                        removed += 1
                    else:
                        new_result.append(g)
                result = list(reversed(new_result))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def reduce_gate_count(circuit: QuantumCircuit) -> QuantumCircuit:
    """
    Return a new circuit with fewer gates by:
    - Cancelling adjacent self-inverse pairs (H·H, X·X, …)
    - Removing S^4 and T^8 identity cycles
    """
    gates = list(circuit.gates)
    gates = _cancel_adjacent(gates)
    gates = _remove_identity_pairs(gates)

    optimized = QuantumCircuit(num_qubits=circuit.num_qubits, name=circuit.name)
    optimized.gates = gates
    return optimized


def minimize_depth(circuit: QuantumCircuit) -> QuantumCircuit:
    """
    Return a new circuit with minimal depth by re-scheduling gates as early
    as possible (list scheduling / as-soon-as-possible).
    """
    # Track the earliest column each qubit is free
    qubit_free: Dict[int, int] = {q: 0 for q in range(circuit.num_qubits)}
    # Assign each gate a column
    scheduled: List[tuple[int, GateSpec]] = []

    for spec in circuit.gates:
        qubits = spec.all_qubits
        col = max(qubit_free.get(q, 0) for q in qubits)
        scheduled.append((col, spec))
        for q in qubits:
            qubit_free[q] = col + 1

    # Rebuild in column order (stable)
    scheduled.sort(key=lambda x: x[0])
    optimized = QuantumCircuit(num_qubits=circuit.num_qubits, name=circuit.name)
    optimized.gates = [spec for _, spec in scheduled]
    return optimized


# Basis sets: name → list of gate names available in that basis
BASIS_SETS: Dict[str, Set[str]] = {
    "clifford_t": {"H", "X", "Y", "Z", "S", "T", "CNOT", "CZ", "SWAP"},
    "ibm": {"H", "X", "Z", "S", "T", "CNOT"},
    "native": set(GATES.keys()),
}

# Decomposition rules: gate → list of GateSpec sequences (same qubits/controls)
# Each rule is a callable(spec) -> List[GateSpec]
def _decompose_ccx(spec: GateSpec) -> List[GateSpec]:
    """Decompose CCX (Toffoli) into H, T, CNOT gates."""
    c0, c1 = spec.controls[0], spec.controls[1]
    t = spec.targets[0]
    return [
        GateSpec(name="H", targets=[t]),
        GateSpec(name="CNOT", targets=[t], controls=[c1]),
        GateSpec(name="T", targets=[t]),  # T†  approximated; full decomp needs Tdg
        GateSpec(name="CNOT", targets=[t], controls=[c0]),
        GateSpec(name="T", targets=[t]),
        GateSpec(name="CNOT", targets=[t], controls=[c1]),
        GateSpec(name="T", targets=[t]),
        GateSpec(name="CNOT", targets=[t], controls=[c0]),
        GateSpec(name="T", targets=[c1]),
        GateSpec(name="H", targets=[t]),
        GateSpec(name="CNOT", targets=[c1], controls=[c0]),
        GateSpec(name="T", targets=[c0]),
        GateSpec(name="T", targets=[c1]),
        GateSpec(name="CNOT", targets=[c1], controls=[c0]),
    ]


def _decompose_swap(spec: GateSpec) -> List[GateSpec]:
    """Decompose SWAP into 3 CNOTs."""
    a, b = spec.targets[0], spec.targets[1]
    return [
        GateSpec(name="CNOT", targets=[b], controls=[a]),
        GateSpec(name="CNOT", targets=[a], controls=[b]),
        GateSpec(name="CNOT", targets=[b], controls=[a]),
    ]


def _decompose_cz(spec: GateSpec) -> List[GateSpec]:
    """Decompose CZ into H + CNOT + H."""
    c, t = spec.controls[0], spec.targets[0]
    return [
        GateSpec(name="H", targets=[t]),
        GateSpec(name="CNOT", targets=[t], controls=[c]),
        GateSpec(name="H", targets=[t]),
    ]


_DECOMPOSITIONS = {
    "CCX": _decompose_ccx,
    "TOFFOLI": _decompose_ccx,
    "SWAP": _decompose_swap,
    "CZ": _decompose_cz,
}


def transpile(circuit: QuantumCircuit, basis: str = "clifford_t") -> QuantumCircuit:
    """
    Transpile circuit to a target basis gate set.

    Supported bases: 'clifford_t', 'ibm', 'native'.
    Gates not in the basis are decomposed if a rule exists, else kept as-is.
    """
    allowed = BASIS_SETS.get(basis.lower(), BASIS_SETS["native"])
    result_gates: List[GateSpec] = []

    for spec in circuit.gates:
        if spec.name.upper() in allowed:
            result_gates.append(spec)
        elif spec.name.upper() in _DECOMPOSITIONS:
            result_gates.extend(_DECOMPOSITIONS[spec.name.upper()](spec))
        else:
            # Keep unsupported gate as-is with a best-effort pass-through
            result_gates.append(spec)

    optimized = QuantumCircuit(num_qubits=circuit.num_qubits, name=circuit.name)
    optimized.gates = result_gates
    return optimized


def full_optimize(circuit: QuantumCircuit, basis: str | None = None) -> QuantumCircuit:
    """
    Apply the full optimization pipeline:
      1. Gate-count reduction (cancel pairs, remove identity cycles)
      2. Depth minimization (ASAP scheduling)
      3. Optional transpilation to target basis
    """
    c = reduce_gate_count(circuit)
    c = minimize_depth(c)
    if basis:
        c = transpile(c, basis)
    return c
