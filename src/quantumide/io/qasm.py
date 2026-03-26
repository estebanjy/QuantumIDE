"""QASM 2.0 / 3.0 import and export."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from quantumide.core.circuit import GateSpec, QuantumCircuit

# ---------------------------------------------------------------------------
# QASM 2.0 export
# ---------------------------------------------------------------------------

# Map internal gate names → QASM 2.0 gate names
_TO_QASM2: dict[str, str] = {
    "H": "h",
    "X": "x",
    "Y": "y",
    "Z": "z",
    "S": "s",
    "T": "t",
    "CNOT": "cx",
    "CX": "cx",
    "CZ": "cz",
    "SWAP": "swap",
    "CCX": "ccx",
    "TOFFOLI": "ccx",
}

# Map QASM 2.0 gate names → internal names
_FROM_QASM2: dict[str, str] = {v: k for k, v in _TO_QASM2.items() if k not in ("CX", "TOFFOLI")}
_FROM_QASM2["cx"] = "CNOT"
_FROM_QASM2["ccx"] = "CCX"


def _spec_to_qasm2(spec: GateSpec) -> str:
    gate = _TO_QASM2.get(spec.name.upper(), spec.name.lower())
    qubits = [f"q[{q}]" for q in spec.controls + spec.targets]
    return f"{gate} {', '.join(qubits)};"


def export_qasm2(circuit: QuantumCircuit, output: Path | None = None) -> str:
    lines: List[str] = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"// {circuit.name}",
        f"qreg q[{circuit.num_qubits}];",
        f"creg c[{circuit.num_qubits}];",
    ]
    for spec in circuit.gates:
        lines.append(_spec_to_qasm2(spec))
    lines.append(f"measure q -> c;")
    qasm = "\n".join(lines) + "\n"
    if output:
        output.write_text(qasm)
    return qasm


# ---------------------------------------------------------------------------
# QASM 3.0 export
# ---------------------------------------------------------------------------

_TO_QASM3: dict[str, str] = {**_TO_QASM2}  # same gate names in 3.0


def _spec_to_qasm3(spec: GateSpec) -> str:
    gate = _TO_QASM3.get(spec.name.upper(), spec.name.lower())
    qubits = [f"q[{q}]" for q in spec.controls + spec.targets]
    return f"{gate} {', '.join(qubits)};"


def export_qasm3(circuit: QuantumCircuit, output: Path | None = None) -> str:
    lines: List[str] = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"// {circuit.name}",
        f"qubit[{circuit.num_qubits}] q;",
        f"bit[{circuit.num_qubits}] c;",
    ]
    for spec in circuit.gates:
        lines.append(_spec_to_qasm3(spec))
    lines.append(f"c = measure q;")
    qasm = "\n".join(lines) + "\n"
    if output:
        output.write_text(qasm)
    return qasm


# ---------------------------------------------------------------------------
# QASM 2.0 import
# ---------------------------------------------------------------------------

# Regex for gate lines: gate_name arg1, arg2, ...;
_GATE_LINE = re.compile(r"^\s*(\w+)\s+([\w\[\], ]+);")
_QUBIT_IDX = re.compile(r"\[(\d+)\]")
_QREG_LINE = re.compile(r"^\s*qreg\s+\w+\[(\d+)\]")


def import_qasm2(source: str | Path) -> QuantumCircuit:
    """Parse a QASM 2.0 string or file into a QuantumCircuit."""
    if isinstance(source, Path):
        text = source.read_text()
    else:
        text = source

    num_qubits = 1
    gates: List[GateSpec] = []

    # Single-qubit gate names (no controls)
    SINGLE = {"h", "x", "y", "z", "s", "t", "sdg", "tdg", "id"}
    # Two-qubit (1 control, 1 target)
    TWO_CTRL = {"cx", "cz", "cy"}
    # Three-qubit (2 controls, 1 target)
    THREE_CTRL = {"ccx", "cswap"}
    # Two-target (swap)
    TWO_TARGET = {"swap"}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("OPENQASM") or line.startswith("include"):
            continue

        qreg_m = _QREG_LINE.match(line)
        if qreg_m:
            num_qubits = int(qreg_m.group(1))
            continue

        if line.startswith("creg") or line.startswith("measure") or line.startswith("barrier"):
            continue

        m = _GATE_LINE.match(line)
        if not m:
            continue

        gate_token = m.group(1).lower()
        qubit_str = m.group(2)
        indices = [int(x) for x in _QUBIT_IDX.findall(qubit_str)]

        if not indices:
            continue

        internal_name = _FROM_QASM2.get(gate_token)
        if internal_name is None:
            # Best-effort: treat as single-qubit gate on first qubit
            internal_name = gate_token.upper()

        if gate_token in SINGLE:
            gates.append(GateSpec(name=internal_name, targets=indices[:1]))
        elif gate_token in TWO_CTRL:
            gates.append(GateSpec(name=internal_name, targets=[indices[1]], controls=[indices[0]]))
        elif gate_token in THREE_CTRL:
            gates.append(GateSpec(name=internal_name, targets=[indices[2]], controls=indices[:2]))
        elif gate_token in TWO_TARGET:
            gates.append(GateSpec(name=internal_name, targets=indices[:2]))
        else:
            gates.append(GateSpec(name=internal_name, targets=indices[:1]))

    circuit = QuantumCircuit(num_qubits=num_qubits)
    circuit.gates = gates
    return circuit
