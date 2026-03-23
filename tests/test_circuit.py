"""Unit tests for core circuit functionality."""

import json

import cirq
import numpy as np
import pytest

from quantumide.core.circuit import GateSpec, QuantumCircuit


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_circuit_creation() -> None:
    circuit = QuantumCircuit(num_qubits=2, name="test")
    assert circuit.num_qubits == 2
    assert circuit.name == "test"
    assert circuit.gates == []


def test_circuit_default_name() -> None:
    circuit = QuantumCircuit(num_qubits=1)
    assert circuit.name == "circuit"


# ---------------------------------------------------------------------------
# add_gate validation
# ---------------------------------------------------------------------------

def test_add_single_qubit_gate() -> None:
    circuit = QuantumCircuit(num_qubits=1)
    circuit.add_gate(GateSpec(name="H", targets=[0]))
    assert len(circuit.gates) == 1


def test_add_cnot() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    circuit.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    assert circuit.gates[0].name == "CNOT"


def test_qubit_out_of_range() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    with pytest.raises(ValueError, match="out of range"):
        circuit.add_gate(GateSpec(name="H", targets=[5]))


def test_duplicate_qubit_indices() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    with pytest.raises(ValueError, match="Duplicate"):
        circuit.add_gate(GateSpec(name="CNOT", targets=[0], controls=[0]))


def test_unknown_gate() -> None:
    circuit = QuantumCircuit(num_qubits=1)
    with pytest.raises(ValueError, match="Unknown gate"):
        circuit.add_gate(GateSpec(name="FOOBAR", targets=[0]))


# ---------------------------------------------------------------------------
# remove_gate
# ---------------------------------------------------------------------------

def test_remove_gate() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    circuit.add_gate(GateSpec(name="H", targets=[0]))
    circuit.add_gate(GateSpec(name="X", targets=[1]))
    removed = circuit.remove_gate(0)
    assert removed.name == "H"
    assert len(circuit.gates) == 1
    assert circuit.gates[0].name == "X"


def test_remove_gate_out_of_range() -> None:
    circuit = QuantumCircuit(num_qubits=1)
    with pytest.raises(IndexError):
        circuit.remove_gate(0)


# ---------------------------------------------------------------------------
# to_cirq / diagram
# ---------------------------------------------------------------------------

def test_to_cirq_hadamard() -> None:
    circuit = QuantumCircuit(num_qubits=1)
    circuit.add_gate(GateSpec(name="H", targets=[0]))
    assert len(circuit.to_cirq()) == 1


def test_bell_state_simulation() -> None:
    circuit = QuantumCircuit(num_qubits=2, name="bell")
    circuit.add_gate(GateSpec(name="H", targets=[0]))
    circuit.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))

    result = cirq.Simulator().simulate(circuit.to_cirq())
    state = result.final_state_vector
    expected = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    assert np.allclose(np.abs(state), np.abs(expected), atol=1e-6)


def test_all_single_qubit_gates() -> None:
    for name in ["H", "X", "Y", "Z", "T", "S"]:
        circuit = QuantumCircuit(num_qubits=1)
        circuit.add_gate(GateSpec(name=name, targets=[0]))
        assert len(circuit.to_cirq()) == 1, f"Failed for {name}"


def test_swap_gate() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    circuit.add_gate(GateSpec(name="SWAP", targets=[0, 1]))
    assert len(circuit.to_cirq()) == 1


def test_toffoli_gate() -> None:
    circuit = QuantumCircuit(num_qubits=3)
    circuit.add_gate(GateSpec(name="CCX", targets=[2], controls=[0, 1]))
    assert len(circuit.to_cirq()) == 1


def test_diagram_contains_gate() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    circuit.add_gate(GateSpec(name="H", targets=[0]))
    assert "H" in circuit.diagram()


def test_empty_depth() -> None:
    circuit = QuantumCircuit(num_qubits=2)
    assert circuit.depth() == 0


def test_gate_count() -> None:
    circuit = QuantumCircuit(num_qubits=3)
    for i in range(3):
        circuit.add_gate(GateSpec(name="H", targets=[i]))
    assert circuit.gate_count() == 3


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

def test_serialization_roundtrip() -> None:
    circuit = QuantumCircuit(num_qubits=2, name="roundtrip")
    circuit.add_gate(GateSpec(name="H", targets=[0]))
    circuit.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))

    loaded = QuantumCircuit.model_validate_json(circuit.model_dump_json())

    assert loaded.num_qubits == circuit.num_qubits
    assert loaded.name == circuit.name
    assert len(loaded.gates) == 2
    assert loaded.gates[0].name == "H"
    assert loaded.gates[1].name == "CNOT"
    assert loaded.gates[1].controls == [0]
    assert loaded.gates[1].targets == [1]
