"""Built-in circuit templates: bell, ghz, qft, grover, shor."""

from __future__ import annotations

import math
from typing import Callable, Dict

from quantumide.core.circuit import GateSpec, QuantumCircuit


def bell() -> QuantumCircuit:
    """Bell state |Φ+⟩ on 2 qubits."""
    c = QuantumCircuit(num_qubits=2, name="bell")
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    return c


def ghz(n: int = 3) -> QuantumCircuit:
    """GHZ state on n qubits (n ≥ 2)."""
    if n < 2:
        raise ValueError("GHZ requires at least 2 qubits.")
    c = QuantumCircuit(num_qubits=n, name=f"ghz_{n}")
    c.add_gate(GateSpec(name="H", targets=[0]))
    for i in range(1, n):
        c.add_gate(GateSpec(name="CNOT", targets=[i], controls=[0]))
    return c


def qft(n: int = 3) -> QuantumCircuit:
    """Quantum Fourier Transform on n qubits using H and CZ approximation.

    Note: A full QFT uses controlled-Rk gates. Since our gate set doesn't
    include arbitrary rotations, we build a Clifford-approximate QFT using
    H, S (R2), T (R3-ish), and CZ — suitable for structural demonstration.
    """
    if n < 1:
        raise ValueError("QFT requires at least 1 qubit.")
    c = QuantumCircuit(num_qubits=n, name=f"qft_{n}")
    for i in range(n):
        c.add_gate(GateSpec(name="H", targets=[i]))
        if i + 1 < n:
            c.add_gate(GateSpec(name="CZ", targets=[i + 1], controls=[i]))
        if i + 2 < n:
            c.add_gate(GateSpec(name="CZ", targets=[i + 2], controls=[i]))
    # Bit-reversal swaps
    for i in range(n // 2):
        c.add_gate(GateSpec(name="SWAP", targets=[i, n - 1 - i]))
    return c


def grover(n: int = 2) -> QuantumCircuit:
    """Grover diffusion operator skeleton on n qubits.

    Builds the standard equal-superposition + diffusion structure.
    Oracle is left as identity (H-layer placeholder).
    """
    if n < 2:
        raise ValueError("Grover requires at least 2 qubits.")
    c = QuantumCircuit(num_qubits=n, name=f"grover_{n}")

    # Initialise superposition
    for i in range(n):
        c.add_gate(GateSpec(name="H", targets=[i]))

    # Oracle placeholder (X on all, multi-controlled Z, X on all)
    for i in range(n):
        c.add_gate(GateSpec(name="X", targets=[i]))
    # Multi-controlled Z approximated with H + CCX (for n==3) or CZ (for n==2)
    if n == 2:
        c.add_gate(GateSpec(name="CZ", targets=[1], controls=[0]))
    elif n >= 3:
        c.add_gate(GateSpec(name="H", targets=[n - 1]))
        c.add_gate(GateSpec(name="CCX", targets=[n - 1], controls=[n - 3, n - 2]))
        c.add_gate(GateSpec(name="H", targets=[n - 1]))
    for i in range(n):
        c.add_gate(GateSpec(name="X", targets=[i]))

    # Diffusion operator
    for i in range(n):
        c.add_gate(GateSpec(name="H", targets=[i]))
    for i in range(n):
        c.add_gate(GateSpec(name="X", targets=[i]))
    if n == 2:
        c.add_gate(GateSpec(name="CZ", targets=[1], controls=[0]))
    elif n >= 3:
        c.add_gate(GateSpec(name="H", targets=[n - 1]))
        c.add_gate(GateSpec(name="CCX", targets=[n - 1], controls=[n - 3, n - 2]))
        c.add_gate(GateSpec(name="H", targets=[n - 1]))
    for i in range(n):
        c.add_gate(GateSpec(name="X", targets=[i]))
    for i in range(n):
        c.add_gate(GateSpec(name="H", targets=[i]))

    return c


def shor() -> QuantumCircuit:
    """Simplified Shor's algorithm structure (modular exponentiation skeleton).

    Uses 4 qubits: 2 for the period-finding register, 2 for the work register.
    This is a structural/educational skeleton, not a full factoring circuit.
    """
    c = QuantumCircuit(num_qubits=4, name="shor")
    # Hadamard on input register
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="H", targets=[1]))
    # Modular exponentiation placeholder (CNOT cascade)
    c.add_gate(GateSpec(name="CNOT", targets=[2], controls=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[3], controls=[1]))
    c.add_gate(GateSpec(name="CNOT", targets=[2], controls=[1]))
    # Inverse QFT on input register (H + CZ)
    c.add_gate(GateSpec(name="CZ", targets=[1], controls=[0]))
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="H", targets=[1]))
    c.add_gate(GateSpec(name="SWAP", targets=[0, 1]))
    return c


TEMPLATES: Dict[str, Callable[..., QuantumCircuit]] = {
    "bell": bell,
    "ghz": ghz,
    "qft": qft,
    "grover": grover,
    "shor": shor,
}
