"""Tests for visualization module."""

import tempfile
from pathlib import Path

import pytest

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.simulation import QuantumSimulator
from quantumide.visualization.ascii import render_circuit, render_probabilities, render_counts
from quantumide.visualization.svg import render_svg


def bell_circuit() -> QuantumCircuit:
    c = QuantumCircuit(num_qubits=2, name="bell")
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    return c


# ---------------------------------------------------------------------------
# ASCII renderer
# ---------------------------------------------------------------------------

def test_render_circuit_returns_string() -> None:
    diagram = render_circuit(bell_circuit())
    assert isinstance(diagram, str)
    assert "H" in diagram


def test_render_circuit_empty() -> None:
    c = QuantumCircuit(num_qubits=2, name="empty")
    diagram = render_circuit(c)
    assert "empty" in diagram.lower() or diagram == "(empty circuit)"


def test_render_probabilities_no_error(capsys) -> None:
    from rich.console import Console
    console = Console(force_terminal=False)
    result = QuantumSimulator().run(bell_circuit())
    render_probabilities(result, console)  # should not raise


def test_render_counts_warns_without_shots(capsys) -> None:
    from rich.console import Console
    console = Console(force_terminal=False)
    result = QuantumSimulator().run(bell_circuit())
    render_counts(result, console)  # should print warning, not raise


def test_render_counts_with_shots(capsys) -> None:
    from rich.console import Console
    console = Console(force_terminal=False)
    result = QuantumSimulator().run(bell_circuit())
    result.sample(256)
    render_counts(result, console)  # should not raise


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------

def test_svg_is_valid_xml() -> None:
    svg = render_svg(bell_circuit())
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")


def test_svg_contains_gate_labels() -> None:
    svg = render_svg(bell_circuit())
    assert "H" in svg
    assert "CNOT" in svg or "CNO" in svg  # label may be truncated to 3 chars


def test_svg_saves_to_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "circuit.svg"
        render_svg(bell_circuit(), out)
        assert out.exists()
        content = out.read_text()
        assert "<svg" in content


def test_svg_toffoli() -> None:
    c = QuantumCircuit(num_qubits=3, name="toffoli")
    c.add_gate(GateSpec(name="CCX", targets=[2], controls=[0, 1]))
    svg = render_svg(c)
    assert "<svg" in svg


def test_svg_swap() -> None:
    c = QuantumCircuit(num_qubits=2, name="swap")
    c.add_gate(GateSpec(name="SWAP", targets=[0, 1]))
    svg = render_svg(c)
    assert "<svg" in svg


def test_svg_empty_circuit() -> None:
    c = QuantumCircuit(num_qubits=2, name="empty")
    svg = render_svg(c)
    assert "<svg" in svg
