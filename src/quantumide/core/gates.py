"""Gate definitions and metadata."""

from dataclasses import dataclass
from typing import Any, Dict

import cirq


@dataclass
class GateDef:
    name: str
    cirq_gate: Any
    n_targets: int
    n_controls: int = 0
    description: str = ""


# Try both CCX aliases across Cirq versions
try:
    _toffoli: Any = cirq.CCX
except AttributeError:
    _toffoli = cirq.CCNOT  # type: ignore[attr-defined]

GATES: Dict[str, GateDef] = {
    "H": GateDef("H", cirq.H, 1, 0, "Hadamard"),
    "X": GateDef("X", cirq.X, 1, 0, "Pauli-X (NOT)"),
    "Y": GateDef("Y", cirq.Y, 1, 0, "Pauli-Y"),
    "Z": GateDef("Z", cirq.Z, 1, 0, "Pauli-Z"),
    "T": GateDef("T", cirq.T, 1, 0, "T gate (π/8)"),
    "S": GateDef("S", cirq.S, 1, 0, "S gate (π/4)"),
    "CNOT": GateDef("CNOT", cirq.CNOT, 1, 1, "Controlled-NOT"),
    "CX": GateDef("CX", cirq.CNOT, 1, 1, "Controlled-X (alias for CNOT)"),
    "CZ": GateDef("CZ", cirq.CZ, 1, 1, "Controlled-Z"),
    "SWAP": GateDef("SWAP", cirq.SWAP, 2, 0, "SWAP"),
    "CCX": GateDef("CCX", _toffoli, 1, 2, "Toffoli (Controlled-Controlled-X)"),
    "TOFFOLI": GateDef("TOFFOLI", _toffoli, 1, 2, "Toffoli"),
}
