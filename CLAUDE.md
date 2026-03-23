# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**QuantumIDE** (`qide`) is a CLI/TUI tool for designing, visualizing, simulating, and optimizing quantum circuits using Google Cirq. The entry point command is `qide`.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_circuit.py::test_bell_state

# Run with coverage
pytest --cov=quantumide

# Lint
ruff check src/

# Type check
mypy src/

# Format
black src/ tests/
```

## Architecture

The package lives under `src/quantumide/` and is organized into these layers:

- **`core/`** — `QuantumCircuit` (Pydantic model wrapping `cirq.Circuit`) and `GateSpec`. The `to_cirq()` / `from_cirq()` methods are the bridge between the serializable data model and the Cirq runtime.
- **`cli/`** — Click command group (`main.py`) with sub-commands: `create`, `edit`, `simulate`, `optimize`, `export`. Each command lives in its own file and is registered in `main.py`.
- **`tui/`** — Textual app (`app.py`) with a circuit canvas, gate palette sidebar, and live simulation panel. Launched via `qide interactive`.
- **`visualization/`** — ASCII renderer (wraps `cirq`'s text diagram + Rich), SVG renderer, Bloch sphere, and state vector bar charts.
- **`simulation/`** — `QuantumSimulator` wraps `cirq.Simulator` / `cirq.DensityMatrixSimulator`. Returns `SimulationResult` (counts, state vector, probabilities).
- **`optimization/`** — Depth minimizer, gate-count reducer, transpiler to arbitrary basis gate sets.
- **`io/`** — JSON/pickle serialization, QASM 2.0/3.0 import-export, and an optional Qiskit bridge.

### Data flow

```
CLI/TUI command
  → load/create QuantumCircuit (Pydantic)
    → .to_cirq() → cirq.Circuit
      → simulation/visualization/optimization
        → SimulationResult / rendered output
          → Rich/Textual display or file export
```

## Tech Stack

| Concern | Library |
|---|---|
| Quantum framework | `cirq >= 1.3.0` |
| CLI | `click >= 8.1.7` |
| TUI | `textual >= 0.47.0` |
| Terminal output | `rich >= 13.7.0` |
| Data validation | `pydantic >= 2.5.0` |
| Numerics | `numpy >= 1.26.2` |
| Plotting/export | `matplotlib >= 3.8.2` |
| Optional cross-platform | `qiskit >= 0.45.0` |

## Circuit Templates

Built-in templates (created with `qide template NAME`): `bell`, `ghz`, `qft`, `grover`, `shor`. Example circuits live in `examples/` as JSON files.

## Key Design Decisions

- Circuits are stored as `QuantumCircuit` (Pydantic) JSON, **not** as serialized Cirq objects — this ensures format stability and cross-framework portability.
- Noise models are passed at simulator construction time, not baked into the circuit.
- The optional `qiskit` extra is kept separate to avoid a heavy default install.
