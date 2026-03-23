"""Core QuantumCircuit data model."""

from typing import List

import cirq
from pydantic import BaseModel, Field

from quantumide.core.gates import GATES


class GateSpec(BaseModel):
    """Serializable specification for a single gate operation."""

    name: str
    targets: List[int]
    controls: List[int] = Field(default_factory=list)

    @property
    def all_qubits(self) -> List[int]:
        return self.controls + self.targets


class QuantumCircuit(BaseModel):
    """Serializable quantum circuit wrapping cirq.Circuit."""

    num_qubits: int = Field(gt=0)
    name: str = "circuit"
    gates: List[GateSpec] = Field(default_factory=list)

    def add_gate(self, spec: GateSpec) -> None:
        all_q = spec.all_qubits
        if not all_q:
            raise ValueError("Gate must specify at least one qubit.")
        if max(all_q) >= self.num_qubits:
            raise ValueError(
                f"Qubit index {max(all_q)} out of range "
                f"(circuit has {self.num_qubits} qubits, indices 0–{self.num_qubits - 1})."
            )
        if len(set(all_q)) != len(all_q):
            raise ValueError("Duplicate qubit indices in gate specification.")
        if spec.name.upper() not in GATES:
            raise ValueError(
                f"Unknown gate '{spec.name}'. Available: {', '.join(GATES)}."
            )
        self.gates.append(spec)

    def remove_gate(self, index: int) -> GateSpec:
        if index < 0 or index >= len(self.gates):
            raise IndexError(
                f"Gate index {index} out of range (circuit has {len(self.gates)} gates)."
            )
        return self.gates.pop(index)

    def to_cirq(self) -> cirq.Circuit:
        qubits = cirq.LineQubit.range(self.num_qubits)
        circuit = cirq.Circuit()
        for spec in self.gates:
            gate_def = GATES[spec.name.upper()]
            all_qs = [qubits[i] for i in spec.controls] + [qubits[i] for i in spec.targets]
            circuit.append(gate_def.cirq_gate.on(*all_qs))
        return circuit

    def gate_count(self) -> int:
        return len(self.gates)

    def depth(self) -> int:
        return len(self.to_cirq()) if self.gates else 0

    def diagram(self) -> str:
        return str(self.to_cirq())
