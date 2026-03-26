"""Tests for io: QASM export/import and pickle serialization."""

import tempfile
from pathlib import Path

import pytest

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.io.qasm import export_qasm2, export_qasm3, import_qasm2
from quantumide.io.pickle_io import save_pickle, load_pickle


def bell() -> QuantumCircuit:
    c = QuantumCircuit(num_qubits=2, name="bell")
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    return c


# ---------------------------------------------------------------------------
# QASM 2.0 export
# ---------------------------------------------------------------------------

def test_qasm2_header() -> None:
    qasm = export_qasm2(bell())
    assert "OPENQASM 2.0" in qasm
    assert 'include "qelib1.inc"' in qasm


def test_qasm2_qreg() -> None:
    qasm = export_qasm2(bell())
    assert "qreg q[2]" in qasm


def test_qasm2_gates() -> None:
    qasm = export_qasm2(bell())
    assert "h q[0]" in qasm
    assert "cx q[0], q[1]" in qasm


def test_qasm2_measure() -> None:
    qasm = export_qasm2(bell())
    assert "measure q -> c" in qasm


def test_qasm2_saves_to_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bell.qasm"
        export_qasm2(bell(), out)
        assert out.exists()
        assert "OPENQASM 2.0" in out.read_text()


# ---------------------------------------------------------------------------
# QASM 3.0 export
# ---------------------------------------------------------------------------

def test_qasm3_header() -> None:
    qasm = export_qasm3(bell())
    assert "OPENQASM 3.0" in qasm
    assert 'include "stdgates.inc"' in qasm


def test_qasm3_qubit_declaration() -> None:
    qasm = export_qasm3(bell())
    assert "qubit[2] q" in qasm


def test_qasm3_measure_syntax() -> None:
    qasm = export_qasm3(bell())
    assert "c = measure q" in qasm


def test_qasm3_saves_to_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bell.qasm3"
        export_qasm3(bell(), out)
        assert out.exists()


# ---------------------------------------------------------------------------
# QASM 2.0 import
# ---------------------------------------------------------------------------

def test_import_qasm2_roundtrip() -> None:
    qasm = export_qasm2(bell())
    loaded = import_qasm2(qasm)
    assert loaded.num_qubits == 2
    assert loaded.gate_count() == 2
    assert loaded.gates[0].name == "H"
    assert loaded.gates[1].name == "CNOT"


def test_import_qasm2_from_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bell.qasm"
        export_qasm2(bell(), out)
        loaded = import_qasm2(out)
        assert loaded.num_qubits == 2


def test_import_qasm2_single_qubit_gates() -> None:
    qasm = "OPENQASM 2.0;\nqreg q[3];\nh q[0];\nx q[1];\nz q[2];\n"
    loaded = import_qasm2(qasm)
    assert loaded.gate_count() == 3
    assert loaded.gates[0].name == "H"
    assert loaded.gates[1].name == "X"
    assert loaded.gates[2].name == "Z"


def test_import_qasm2_swap() -> None:
    qasm = "OPENQASM 2.0;\nqreg q[2];\nswap q[0], q[1];\n"
    loaded = import_qasm2(qasm)
    assert loaded.gates[0].name == "SWAP"
    assert loaded.gates[0].targets == [0, 1]


def test_import_qasm2_ccx() -> None:
    qasm = "OPENQASM 2.0;\nqreg q[3];\nccx q[0], q[1], q[2];\n"
    loaded = import_qasm2(qasm)
    assert loaded.gates[0].name == "CCX"
    assert loaded.gates[0].controls == [0, 1]
    assert loaded.gates[0].targets == [2]


# ---------------------------------------------------------------------------
# Pickle
# ---------------------------------------------------------------------------

def test_pickle_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bell.pkl"
        save_pickle(bell(), out)
        loaded = load_pickle(out)
        assert loaded.num_qubits == 2
        assert loaded.gate_count() == 2
        assert loaded.gates[0].name == "H"


def test_pickle_rejects_wrong_type() -> None:
    import pickle
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bad.pkl"
        out.write_bytes(pickle.dumps({"not": "a circuit"}))
        with pytest.raises(TypeError):
            load_pickle(out)
