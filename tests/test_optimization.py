"""Tests for the optimization module."""

import pytest

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.optimization import (
    reduce_gate_count,
    minimize_depth,
    transpile,
    full_optimize,
    BASIS_SETS,
)


def _circuit(*specs: tuple) -> QuantumCircuit:
    """Helper: build a circuit from (name, targets, controls) tuples."""
    c = QuantumCircuit(num_qubits=4, name="test")
    for item in specs:
        name, targets = item[0], item[1]
        controls = item[2] if len(item) > 2 else []
        c.add_gate(GateSpec(name=name, targets=targets, controls=controls))
    return c


# ---------------------------------------------------------------------------
# Gate-count reduction
# ---------------------------------------------------------------------------

def test_cancel_hh() -> None:
    c = _circuit(("H", [0]), ("H", [0]))
    result = reduce_gate_count(c)
    assert result.gate_count() == 0


def test_cancel_xx() -> None:
    c = _circuit(("X", [0]), ("X", [0]))
    assert reduce_gate_count(c).gate_count() == 0


def test_cancel_cnot_pair() -> None:
    c = _circuit(("CNOT", [1], [0]), ("CNOT", [1], [0]))
    assert reduce_gate_count(c).gate_count() == 0


def test_no_cancel_different_qubits() -> None:
    c = _circuit(("H", [0]), ("H", [1]))
    assert reduce_gate_count(c).gate_count() == 2


def test_no_cancel_different_gates() -> None:
    c = _circuit(("H", [0]), ("X", [0]))
    assert reduce_gate_count(c).gate_count() == 2


def test_cancel_swap_pair() -> None:
    c = _circuit(("SWAP", [0, 1]), ("SWAP", [0, 1]))
    assert reduce_gate_count(c).gate_count() == 0


def test_s4_identity_removed() -> None:
    c = _circuit(("S", [0]), ("S", [0]), ("S", [0]), ("S", [0]))
    assert reduce_gate_count(c).gate_count() == 0


def test_t8_identity_removed() -> None:
    c = QuantumCircuit(num_qubits=1, name="t8")
    for _ in range(8):
        c.add_gate(GateSpec(name="T", targets=[0]))
    assert reduce_gate_count(c).gate_count() == 0


def test_partial_cancel_keeps_remainder() -> None:
    # H·H·H → H (one pair cancels, one remains)
    c = _circuit(("H", [0]), ("H", [0]), ("H", [0]))
    assert reduce_gate_count(c).gate_count() == 1


# ---------------------------------------------------------------------------
# Depth minimization
# ---------------------------------------------------------------------------

def test_depth_not_increased() -> None:
    c = _circuit(("H", [0]), ("H", [1]), ("H", [2]))
    original_depth = c.depth()
    optimized = minimize_depth(c)
    assert optimized.depth() <= original_depth


def test_independent_gates_parallelized() -> None:
    # Three independent H gates should collapse to depth 1
    c = _circuit(("H", [0]), ("H", [1]), ("H", [2]))
    assert minimize_depth(c).depth() == 1


def test_dependent_gates_preserve_order() -> None:
    c = _circuit(("H", [0]), ("CNOT", [1], [0]))
    opt = minimize_depth(c)
    assert opt.gate_count() == 2
    assert opt.gates[0].name == "H"
    assert opt.gates[1].name == "CNOT"


# ---------------------------------------------------------------------------
# Transpilation
# ---------------------------------------------------------------------------

def test_transpile_native_unchanged() -> None:
    c = _circuit(("H", [0]), ("CNOT", [1], [0]))
    result = transpile(c, "native")
    assert result.gate_count() == c.gate_count()


def test_transpile_ccx_decomposes() -> None:
    c = QuantumCircuit(num_qubits=3, name="tof")
    c.add_gate(GateSpec(name="CCX", targets=[2], controls=[0, 1]))
    result = transpile(c, "clifford_t")
    # CCX decomposes into multiple gates
    assert result.gate_count() > 1


def test_transpile_swap_decomposes() -> None:
    c = _circuit(("SWAP", [0, 1]))
    result = transpile(c, "ibm")
    # SWAP not in ibm basis → decomposes to 3 CNOTs
    assert result.gate_count() == 3
    assert all(g.name == "CNOT" for g in result.gates)


def test_transpile_cz_decomposes() -> None:
    c = _circuit(("CZ", [1], [0]))
    result = transpile(c, "ibm")
    assert result.gate_count() == 3


def test_transpile_valid_basis_gates_unchanged() -> None:
    c = _circuit(("H", [0]), ("X", [1]))
    result = transpile(c, "ibm")
    assert result.gate_count() == 2


def test_invalid_basis_falls_back_to_native() -> None:
    c = _circuit(("H", [0]))
    result = transpile(c, "unknown_basis")
    # Unknown basis → uses native (all gates allowed)
    assert result.gate_count() == 1


# ---------------------------------------------------------------------------
# Full optimize pipeline
# ---------------------------------------------------------------------------

def test_full_optimize_bell() -> None:
    c = QuantumCircuit(num_qubits=2, name="bell")
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    result = full_optimize(c)
    assert result.gate_count() == 2  # nothing to cancel


def test_full_optimize_cancels_and_schedules() -> None:
    c = _circuit(("H", [0]), ("H", [0]), ("H", [1]), ("H", [2]))
    result = full_optimize(c)
    # H·H cancelled → 2 independent H gates left, depth 1
    assert result.gate_count() == 2
    assert result.depth() == 1


def test_full_optimize_with_basis() -> None:
    c = QuantumCircuit(num_qubits=3, name="tof")
    c.add_gate(GateSpec(name="CCX", targets=[2], controls=[0, 1]))
    result = full_optimize(c, basis="clifford_t")
    assert result.gate_count() > 1
    for g in result.gates:
        assert g.name.upper() in BASIS_SETS["clifford_t"]
