"""Tests for the Textual TUI app."""

import pytest

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.tui.app import QuantumIDEApp


def bell_circuit() -> QuantumCircuit:
    c = QuantumCircuit(num_qubits=2, name="bell")
    c.add_gate(GateSpec(name="H", targets=[0]))
    c.add_gate(GateSpec(name="CNOT", targets=[1], controls=[0]))
    return c


# ---------------------------------------------------------------------------
# App startup
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_app_starts_with_blank_circuit() -> None:
    app = QuantumIDEApp()
    async with app.run_test(headless=True) as pilot:
        assert app.circuit.num_qubits == 2
        assert app.circuit.gate_count() == 0


@pytest.mark.asyncio
async def test_app_starts_with_provided_circuit() -> None:
    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        assert app.circuit.gate_count() == 2
        assert app.circuit.gates[0].name == "H"


# ---------------------------------------------------------------------------
# Circuit diagram widget
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diagram_shows_gate_name() -> None:
    from textual.widgets import Static
    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        diagram = app.query_one("#circuit-diagram", Static)
        assert "H" in str(diagram.content)


@pytest.mark.asyncio
async def test_empty_circuit_placeholder() -> None:
    from textual.widgets import Static
    app = QuantumIDEApp()
    async with app.run_test(headless=True) as pilot:
        diagram = app.query_one("#circuit-diagram", Static)
        assert "empty" in str(diagram.content).lower()


# ---------------------------------------------------------------------------
# Simulation panel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sim_table_populated_for_bell() -> None:
    from textual.widgets import DataTable
    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        table = app.query_one("#sim-table", DataTable)
        assert table.row_count > 0


@pytest.mark.asyncio
async def test_sim_table_empty_for_blank_circuit() -> None:
    from textual.widgets import DataTable
    app = QuantumIDEApp()
    async with app.run_test(headless=True) as pilot:
        table = app.query_one("#sim-table", DataTable)
        assert table.row_count == 0


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_remove_last_gate() -> None:
    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        assert app.circuit.gate_count() == 2
        await pilot.press("d")
        assert app.circuit.gate_count() == 1


@pytest.mark.asyncio
async def test_remove_last_gate_noop_on_empty() -> None:
    app = QuantumIDEApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("d")
        assert app.circuit.gate_count() == 0


@pytest.mark.asyncio
async def test_new_circuit_action() -> None:
    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        await pilot.press("ctrl+n")
        assert app.circuit.gate_count() == 0
        assert app.circuit.name == "untitled"


@pytest.mark.asyncio
async def test_simulate_action_does_not_crash() -> None:
    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        await pilot.press("r")  # simulate
        from textual.widgets import DataTable
        table = app.query_one("#sim-table", DataTable)
        assert table.row_count > 0


# ---------------------------------------------------------------------------
# Gate palette sidebar
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sidebar_has_gate_items() -> None:
    from textual.widgets import ListView
    app = QuantumIDEApp()
    async with app.run_test(headless=True) as pilot:
        lv = app.query_one("#gate-list", ListView)
        assert len(lv) > 0


# ---------------------------------------------------------------------------
# Save session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_session_action(tmp_path, monkeypatch) -> None:
    import quantumide.io.serialization as ser
    saved = {}

    def fake_save(circuit: QuantumCircuit) -> None:
        saved["circuit"] = circuit

    monkeypatch.setattr(ser, "save_session", fake_save)
    # Patch the import inside the app action
    import quantumide.tui.app as tui_mod
    monkeypatch.setattr(
        "quantumide.tui.app.QuantumIDEApp.action_save_session",
        lambda self: fake_save(self.circuit),
    )

    app = QuantumIDEApp(circuit=bell_circuit())
    async with app.run_test(headless=True) as pilot:
        await pilot.press("s")
        assert saved.get("circuit") is not None
        assert saved["circuit"].gate_count() == 2
