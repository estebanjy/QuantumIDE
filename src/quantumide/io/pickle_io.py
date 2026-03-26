"""Pickle serialization for QuantumCircuit."""

import pickle
from pathlib import Path

from quantumide.core.circuit import QuantumCircuit


def save_pickle(circuit: QuantumCircuit, path: Path) -> None:
    path.write_bytes(pickle.dumps(circuit))


def load_pickle(path: Path) -> QuantumCircuit:
    obj = pickle.loads(path.read_bytes())
    if not isinstance(obj, QuantumCircuit):
        raise TypeError(f"Expected QuantumCircuit, got {type(obj).__name__}")
    return obj
