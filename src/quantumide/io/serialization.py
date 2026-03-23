"""Circuit serialization and session management."""

import json
from pathlib import Path

from quantumide.core.circuit import QuantumCircuit

SESSION_FILE = Path(".qide_session.json")


def save_circuit(circuit: QuantumCircuit, path: Path) -> None:
    path.write_text(circuit.model_dump_json(indent=2))


def load_circuit(path: Path) -> QuantumCircuit:
    return QuantumCircuit.model_validate(json.loads(path.read_text()))


def save_session(circuit: QuantumCircuit) -> None:
    save_circuit(circuit, SESSION_FILE)


def load_session() -> QuantumCircuit:
    if not SESSION_FILE.exists():
        raise FileNotFoundError("No active session. Run 'qide create' first.")
    return load_circuit(SESSION_FILE)


def clear_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
