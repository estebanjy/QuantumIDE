"""Matplotlib-based state vector bar charts and Bloch sphere."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from quantumide.simulation.simulator import SimulationResult


def plot_probabilities(
    result: SimulationResult,
    output: Optional[Path] = None,
    title: str = "State Probabilities",
) -> None:
    """Bar chart of state probabilities. Saves to file or shows interactively."""
    import matplotlib.pyplot as plt

    states = list(result.probabilities.keys())
    probs = list(result.probabilities.values())

    fig, ax = plt.subplots(figsize=(max(6, len(states) * 0.6), 4))
    bars = ax.bar(
        [f"|{s}⟩" for s in states],
        probs,
        color="#4C9BE8",
        edgecolor="white",
        linewidth=0.5,
    )
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Probability")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)

    for bar, prob in zip(bars, probs):
        if prob > 0.01:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"{prob:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    fig.tight_layout()
    if output:
        fig.savefig(output, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_counts(
    result: SimulationResult,
    output: Optional[Path] = None,
    title: str = "Measurement Counts",
) -> None:
    """Bar chart of measurement counts."""
    import matplotlib.pyplot as plt

    if not result.counts:
        raise ValueError("No counts available. Run simulation with shots > 0.")

    states = list(result.counts.keys())
    counts = list(result.counts.values())

    fig, ax = plt.subplots(figsize=(max(6, len(states) * 0.6), 4))
    ax.bar(
        [f"|{s}⟩" for s in states],
        counts,
        color="#7BC67E",
        edgecolor="white",
        linewidth=0.5,
    )
    ax.set_ylabel("Count")
    ax.set_title(f"{title} ({result.shots} shots)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    if output:
        fig.savefig(output, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_bloch_sphere(
    state_vector: list[complex],
    qubit: int = 0,
    output: Optional[Path] = None,
    title: str = "Bloch Sphere",
) -> None:
    """Plot the Bloch sphere for a single qubit reduced state."""
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    sv = np.array(state_vector, dtype=complex)
    n_qubits = int(np.log2(len(sv)))

    # Compute single-qubit reduced density matrix by tracing out other qubits
    dim = 2 ** n_qubits
    rho_full = np.outer(sv, sv.conj())
    rho_full = rho_full.reshape([2] * (2 * n_qubits))

    # Trace out all qubits except `qubit`
    axes_to_trace = list(range(n_qubits))
    axes_to_trace.remove(qubit)
    rho = rho_full
    offset = 0
    for ax_idx in sorted(axes_to_trace):
        rho = np.trace(rho, axis1=ax_idx - offset, axis2=ax_idx - offset + n_qubits - offset)
        offset += 1
    rho = rho.reshape(2, 2)

    # Bloch vector
    x = 2 * np.real(rho[0, 1])
    y = 2 * np.imag(rho[1, 0])
    z = float(np.real(rho[0, 0] - rho[1, 1]))

    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, projection="3d")

    # Draw sphere wireframe
    u, v = np.mgrid[0:2 * np.pi:30j, 0:np.pi:20j]
    xs = np.cos(u) * np.sin(v)
    ys = np.sin(u) * np.sin(v)
    zs = np.cos(v)
    ax.plot_wireframe(xs, ys, zs, color="lightgray", alpha=0.3, linewidth=0.4)

    # Axes
    for vec, label in [([1, 0, 0], "|+⟩"), ([-1, 0, 0], "|-⟩"),
                        ([0, 1, 0], "|+i⟩"), ([0, -1, 0], "|-i⟩"),
                        ([0, 0, 1], "|0⟩"), ([0, 0, -1], "|1⟩")]:
        ax.plot([0, vec[0] * 1.2], [0, vec[1] * 1.2], [0, vec[2] * 1.2],
                "k--", linewidth=0.5, alpha=0.5)
        ax.text(vec[0] * 1.3, vec[1] * 1.3, vec[2] * 1.3, label, fontsize=9, ha="center")

    # State vector arrow
    ax.quiver(0, 0, 0, x, y, z, color="#E84C4C", linewidth=2, arrow_length_ratio=0.15)

    ax.set_xlim([-1.5, 1.5])
    ax.set_ylim([-1.5, 1.5])
    ax.set_zlim([-1.5, 1.5])
    ax.set_title(f"{title} — qubit {qubit}")
    ax.set_box_aspect([1, 1, 1])
    ax.axis("off")

    fig.tight_layout()
    if output:
        fig.savefig(output, dpi=150)
        plt.close(fig)
    else:
        plt.show()
