"""SVG circuit renderer."""

from __future__ import annotations

from pathlib import Path

from quantumide.core.circuit import QuantumCircuit
from quantumide.core.gates import GATES

# Layout constants
QUBIT_SPACING = 50       # px between qubit lines
GATE_WIDTH = 40
GATE_HEIGHT = 36
COL_WIDTH = 60           # px between gate columns
LEFT_MARGIN = 60         # space for qubit labels
TOP_MARGIN = 40
WIRE_COLOR = "#555"
GATE_FILL = "#4C9BE8"
CTRL_COLOR = "#333"
TEXT_COLOR = "white"


def _column_positions(circuit: QuantumCircuit) -> list[list[int]]:
    """Assign each gate to the earliest column where its qubits are free."""
    occupied: dict[int, int] = {}  # qubit -> next free column
    columns: list[list[int]] = []

    for idx, spec in enumerate(circuit.gates):
        qubits = spec.all_qubits
        col = max((occupied.get(q, 0) for q in qubits), default=0)
        while len(columns) <= col:
            columns.append([])
        columns[col].append(idx)
        for q in qubits:
            occupied[q] = col + 1

    return columns


def render_svg(circuit: QuantumCircuit, output: Path | None = None) -> str:
    """Render circuit as SVG. Returns SVG string; saves to file if output given."""
    columns = _column_positions(circuit)
    n_cols = len(columns)
    n_qubits = circuit.num_qubits

    width = LEFT_MARGIN + n_cols * COL_WIDTH + COL_WIDTH
    height = TOP_MARGIN + n_qubits * QUBIT_SPACING + TOP_MARGIN

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: monospace; }</style>',
    ]

    # Qubit wires + labels
    for q in range(n_qubits):
        y = TOP_MARGIN + q * QUBIT_SPACING
        lines.append(
            f'<line x1="{LEFT_MARGIN - 10}" y1="{y}" '
            f'x2="{width - 10}" y2="{y}" '
            f'stroke="{WIRE_COLOR}" stroke-width="1.5"/>'
        )
        lines.append(
            f'<text x="{LEFT_MARGIN - 15}" y="{y + 5}" '
            f'text-anchor="end" fill="#333" font-size="13">q{q}</text>'
        )

    # Gates
    for col_idx, gate_indices in enumerate(columns):
        x_center = LEFT_MARGIN + col_idx * COL_WIDTH + COL_WIDTH // 2

        for gate_idx in gate_indices:
            spec = circuit.gates[gate_idx]
            gate_def = GATES[spec.name.upper()]

            targets = spec.targets
            controls = spec.controls

            # Draw control dots and vertical line for multi-qubit gates
            if controls:
                all_q = controls + targets
                y_min = TOP_MARGIN + min(all_q) * QUBIT_SPACING
                y_max = TOP_MARGIN + max(all_q) * QUBIT_SPACING
                lines.append(
                    f'<line x1="{x_center}" y1="{y_min}" '
                    f'x2="{x_center}" y2="{y_max}" '
                    f'stroke="{CTRL_COLOR}" stroke-width="1.5"/>'
                )
                for cq in controls:
                    cy = TOP_MARGIN + cq * QUBIT_SPACING
                    lines.append(
                        f'<circle cx="{x_center}" cy="{cy}" r="6" '
                        f'fill="{CTRL_COLOR}"/>'
                    )

            # SWAP: draw ✕ on both target qubits
            if spec.name.upper() == "SWAP":
                for tq in targets:
                    ty = TOP_MARGIN + tq * QUBIT_SPACING
                    d = 8
                    lines.append(
                        f'<line x1="{x_center - d}" y1="{ty - d}" '
                        f'x2="{x_center + d}" y2="{ty + d}" '
                        f'stroke="{CTRL_COLOR}" stroke-width="2"/>'
                    )
                    lines.append(
                        f'<line x1="{x_center + d}" y1="{ty - d}" '
                        f'x2="{x_center - d}" y2="{ty + d}" '
                        f'stroke="{CTRL_COLOR}" stroke-width="2"/>'
                    )
                if len(targets) == 2:
                    y1 = TOP_MARGIN + targets[0] * QUBIT_SPACING
                    y2 = TOP_MARGIN + targets[1] * QUBIT_SPACING
                    lines.append(
                        f'<line x1="{x_center}" y1="{y1}" '
                        f'x2="{x_center}" y2="{y2}" '
                        f'stroke="{CTRL_COLOR}" stroke-width="1.5"/>'
                    )
                continue

            # Standard gate box on each target qubit
            for tq in targets:
                ty = TOP_MARGIN + tq * QUBIT_SPACING
                rx = x_center - GATE_WIDTH // 2
                ry = ty - GATE_HEIGHT // 2
                lines.append(
                    f'<rect x="{rx}" y="{ry}" width="{GATE_WIDTH}" '
                    f'height="{GATE_HEIGHT}" rx="4" ry="4" '
                    f'fill="{GATE_FILL}" stroke="white" stroke-width="1"/>'
                )
                label = spec.name if len(spec.name) <= 3 else spec.name[:3]
                lines.append(
                    f'<text x="{x_center}" y="{ty + 5}" '
                    f'text-anchor="middle" fill="{TEXT_COLOR}" '
                    f'font-size="12" font-weight="bold">{label}</text>'
                )

    lines.append("</svg>")
    svg = "\n".join(lines)

    if output:
        output.write_text(svg)

    return svg
