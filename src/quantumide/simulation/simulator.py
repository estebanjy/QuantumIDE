"""Quantum simulator wrapping cirq.Simulator and cirq.DensityMatrixSimulator."""

from __future__ import annotations

from typing import Dict, List, Optional

import cirq
import numpy as np
from pydantic import BaseModel

from quantumide.core.circuit import QuantumCircuit


class SimulationResult(BaseModel):
    """Result of a quantum circuit simulation."""

    model_config = {"arbitrary_types_allowed": True}

    num_qubits: int
    state_vector: List[complex]
    probabilities: Dict[str, float]
    counts: Optional[Dict[str, int]] = None
    shots: Optional[int] = None

    @classmethod
    def from_cirq(
        cls,
        result: cirq.StateVectorTrialResult | cirq.SimulatesSamples,
        num_qubits: int,
    ) -> "SimulationResult":
        sv = result.final_state_vector.flatten()
        probs = {
            format(i, f"0{num_qubits}b"): float(np.abs(amp) ** 2)
            for i, amp in enumerate(sv)
        }
        return cls(
            num_qubits=num_qubits,
            state_vector=sv.tolist(),
            probabilities=probs,
        )

    def top_states(self, n: int = 4) -> Dict[str, float]:
        """Return top-n states by probability."""
        return dict(
            sorted(self.probabilities.items(), key=lambda x: x[1], reverse=True)[:n]
        )

    def sample(self, shots: int = 1024) -> Dict[str, int]:
        """Sample from the probability distribution."""
        states = list(self.probabilities.keys())
        probs = np.array(list(self.probabilities.values()), dtype=float)
        probs /= probs.sum()  # normalise for floating point safety
        indices = np.random.choice(len(states), size=shots, p=probs)
        counts: Dict[str, int] = {}
        for idx in indices:
            key = states[idx]
            counts[key] = counts.get(key, 0) + 1
        self.counts = counts
        self.shots = shots
        return counts


class QuantumSimulator:
    """Wraps cirq simulators and returns SimulationResult."""

    def __init__(self, noisy: bool = False, noise: Optional[cirq.NoiseModel] = None):
        if noisy or noise is not None:
            self._sim = cirq.DensityMatrixSimulator(noise=noise or cirq.ConstantQubitNoiseModel(cirq.depolarize(p=0.01)))
        else:
            self._sim = cirq.Simulator()
        self._noisy = noisy or noise is not None

    def run(self, circuit: QuantumCircuit) -> SimulationResult:
        """Simulate a QuantumCircuit and return a SimulationResult."""
        cirq_circuit = circuit.to_cirq()

        if self._noisy:
            result = self._sim.simulate(cirq_circuit)
            sv = result.final_density_matrix
            # For noisy sim, derive probabilities from diagonal of density matrix
            probs = {
                format(i, f"0{circuit.num_qubits}b"): float(np.real(sv[i, i]))
                for i in range(2 ** circuit.num_qubits)
            }
            state_vector = [complex(sv[i, i]) for i in range(2 ** circuit.num_qubits)]
            return SimulationResult(
                num_qubits=circuit.num_qubits,
                state_vector=state_vector,
                probabilities=probs,
            )

        result = self._sim.simulate(cirq_circuit)
        return SimulationResult.from_cirq(result, circuit.num_qubits)
