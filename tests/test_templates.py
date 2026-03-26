"""Tests for built-in circuit templates."""

import pytest

from quantumide.core.circuit import QuantumCircuit
from quantumide.core.templates import bell, ghz, qft, grover, shor, TEMPLATES


# ---------------------------------------------------------------------------
# Bell
# ---------------------------------------------------------------------------

def test_bell_shape() -> None:
    c = bell()
    assert c.num_qubits == 2
    assert c.gate_count() == 2
    assert c.gates[0].name == "H"
    assert c.gates[1].name == "CNOT"


# ---------------------------------------------------------------------------
# GHZ
# ---------------------------------------------------------------------------

def test_ghz_default() -> None:
    c = ghz()
    assert c.num_qubits == 3
    assert c.gate_count() == 3  # H + 2 CNOTs


def test_ghz_custom_qubits() -> None:
    c = ghz(5)
    assert c.num_qubits == 5
    assert c.gate_count() == 5  # H + 4 CNOTs


def test_ghz_requires_two_qubits() -> None:
    with pytest.raises(ValueError):
        ghz(1)


# ---------------------------------------------------------------------------
# QFT
# ---------------------------------------------------------------------------

def test_qft_default() -> None:
    c = qft()
    assert c.num_qubits == 3
    assert c.gate_count() > 0


def test_qft_single_qubit() -> None:
    c = qft(1)
    assert c.num_qubits == 1
    assert c.gate_count() == 1  # just H


def test_qft_even_qubits() -> None:
    c = qft(4)
    assert c.num_qubits == 4


# ---------------------------------------------------------------------------
# Grover
# ---------------------------------------------------------------------------

def test_grover_default() -> None:
    c = grover()
    assert c.num_qubits == 2
    assert c.gate_count() > 0


def test_grover_three_qubits() -> None:
    c = grover(3)
    assert c.num_qubits == 3


def test_grover_requires_two_qubits() -> None:
    with pytest.raises(ValueError):
        grover(1)


# ---------------------------------------------------------------------------
# Shor
# ---------------------------------------------------------------------------

def test_shor_shape() -> None:
    c = shor()
    assert c.num_qubits == 4
    assert c.gate_count() > 0


# ---------------------------------------------------------------------------
# TEMPLATES registry
# ---------------------------------------------------------------------------

def test_templates_registry_complete() -> None:
    assert set(TEMPLATES.keys()) == {"bell", "ghz", "qft", "grover", "shor"}


def test_all_templates_produce_valid_circuits() -> None:
    for name, fn in TEMPLATES.items():
        try:
            c = fn()
        except TypeError:
            c = fn(3)
        assert isinstance(c, QuantumCircuit)
        assert c.num_qubits >= 1
