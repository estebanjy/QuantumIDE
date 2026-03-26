"""Tests for the simulation module."""

import numpy as np
import pytest

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.simulation import QuantumSimulator, SimulationResult


def bell_circuit() -> QuantumCircuit:
    c = QuantumCircuit(num_qubits=2, name="bell")
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    return c


# ---------------------------------------------------------------------------
# SimulationResult
# ---------------------------------------------------------------------------

def test_result_probabilities_sum_to_one() -> None:
    sim = QuantumSimulator()
    result = sim.run(bell_circuit())
    total = sum(result.probabilities.values())
    assert abs(total - 1.0) < 1e-6


def test_bell_state_probabilities() -> None:
    sim = QuantumSimulator()
    result = sim.run(bell_circuit())
    # |00⟩ and |11⟩ should each be ~0.5
    assert abs(result.probabilities["00"] - 0.5) < 1e-5
    assert abs(result.probabilities["11"] - 0.5) < 1e-5
    assert result.probabilities["01"] < 1e-10
    assert result.probabilities["10"] < 1e-10


def test_state_vector_length() -> None:
    sim = QuantumSimulator()
    result = sim.run(bell_circuit())
    assert len(result.state_vector) == 2 ** 2


def test_top_states() -> None:
    sim = QuantumSimulator()
    result = sim.run(bell_circuit())
    top = result.top_states(2)
    assert len(top) == 2
    assert set(top.keys()) == {"00", "11"}


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def test_sample_counts_sum_to_shots() -> None:
    sim = QuantumSimulator()
    result = sim.run(bell_circuit())
    counts = result.sample(shots=512)
    assert sum(counts.values()) == 512


def test_sample_only_valid_states() -> None:
    sim = QuantumSimulator()
    result = sim.run(bell_circuit())
    counts = result.sample(shots=256)
    for state in counts:
        assert state in {"00", "11"}


# ---------------------------------------------------------------------------
# Single qubit
# ---------------------------------------------------------------------------

def test_hadamard_superposition() -> None:
    c = QuantumCircuit(num_qubits=1)
    c.add_gate(GateSpec(name="H", targets=[0]))
    result = QuantumSimulator().run(c)
    assert abs(result.probabilities["0"] - 0.5) < 1e-5
    assert abs(result.probabilities["1"] - 0.5) < 1e-5


def test_x_gate_flips_qubit() -> None:
    c = QuantumCircuit(num_qubits=1)
    c.add_gate(GateSpec(name="X", targets=[0]))
    result = QuantumSimulator().run(c)
    assert abs(result.probabilities["1"] - 1.0) < 1e-5


# ---------------------------------------------------------------------------
# Noisy simulator
# ---------------------------------------------------------------------------

def test_noisy_simulator_runs() -> None:
    sim = QuantumSimulator(noisy=True)
    result = sim.run(bell_circuit())
    total = sum(result.probabilities.values())
    assert abs(total - 1.0) < 1e-4
