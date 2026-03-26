"""Textual TUI for QuantumIDE."""

from __future__ import annotations

from typing import ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.core.gates import GATES
from quantumide.simulation import QuantumSimulator

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
Screen {
    background: $surface;
}

#layout {
    height: 1fr;
}

/* ── Sidebar ─────────────────────────────────────────── */
#sidebar {
    width: 22;
    border: solid $primary;
    padding: 0 1;
}

#sidebar-title {
    text-style: bold;
    color: $accent;
    padding: 1 0 0 0;
}

#gate-list {
    height: 1fr;
}

/* ── Main area ───────────────────────────────────────── */
#main {
    width: 1fr;
}

/* ── Circuit canvas ──────────────────────────────────── */
#canvas-pane {
    height: 1fr;
    border: solid $primary;
    padding: 0 1;
}

#canvas-title {
    text-style: bold;
    color: $accent;
    padding: 1 0 0 0;
}

#circuit-diagram {
    height: 1fr;
    color: $text;
}

/* ── Simulation panel ────────────────────────────────── */
#sim-pane {
    height: 14;
    border: solid $success;
    padding: 0 1;
}

#sim-title {
    text-style: bold;
    color: $success;
    padding: 1 0 0 0;
}

#sim-table {
    height: 1fr;
}

/* ── Status bar ──────────────────────────────────────── */
#status {
    height: 1;
    background: $panel;
    color: $text-muted;
    padding: 0 1;
}

/* ── Modal ───────────────────────────────────────────── */
AddGateScreen {
    align: center middle;
}

#modal-box {
    width: 50;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#modal-title {
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

.modal-label {
    margin-top: 1;
    color: $text-muted;
}

.modal-btn {
    margin-top: 1;
}
"""

# ---------------------------------------------------------------------------
# Add-gate modal
# ---------------------------------------------------------------------------

class AddGateScreen(ModalScreen[GateSpec | None]):
    """Modal dialog to specify a gate to add."""

    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]

    def __init__(self, gate_name: str) -> None:
        super().__init__()
        self._gate_name = gate_name.upper()
        self._gate_def = GATES[self._gate_name]

    def compose(self) -> ComposeResult:
        gdef = self._gate_def
        hint_targets = f"e.g. 0" if gdef.n_targets == 1 else f"e.g. 0,1"
        hint_controls = f"e.g. 1" if gdef.n_controls == 1 else (
            f"e.g. 0,1" if gdef.n_controls > 1 else ""
        )

        with Vertical(id="modal-box"):
            yield Label(f"Add gate: {self._gate_name}", id="modal-title")
            yield Label(f"{gdef.description}", classes="modal-label")

            yield Label(f"Target qubit(s)  ({hint_targets}):", classes="modal-label")
            yield Input(placeholder=hint_targets, id="targets-input")

            if gdef.n_controls > 0:
                yield Label(f"Control qubit(s)  ({hint_controls}):", classes="modal-label")
                yield Input(placeholder=hint_controls, id="controls-input")

            yield Button("Add", variant="primary", id="btn-add", classes="modal-btn")
            yield Button("Cancel", variant="default", id="btn-cancel", classes="modal-btn")

    def _parse_indices(self, widget_id: str) -> list[int]:
        try:
            widget = self.query_one(f"#{widget_id}", Input)
            raw = widget.value.strip()
            if not raw:
                return []
            return [int(x.strip()) for x in raw.split(",")]
        except Exception:
            return []

    @on(Button.Pressed, "#btn-add")
    def submit(self) -> None:
        targets = self._parse_indices("targets-input")
        controls = self._parse_indices("controls-input") if self._gate_def.n_controls > 0 else []
        if not targets:
            self.notify("Enter at least one target qubit.", severity="warning")
            return
        self.dismiss(GateSpec(name=self._gate_name, targets=targets, controls=controls))

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class QuantumIDEApp(App[None]):
    """QuantumIDE interactive TUI."""

    TITLE = "QuantumIDE"
    CSS = CSS
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit"),
        Binding("a", "add_gate", "Add gate"),
        Binding("d", "remove_last", "Remove last gate"),
        Binding("s", "save_session", "Save session"),
        Binding("r", "simulate", "Simulate"),
        Binding("ctrl+n", "new_circuit", "New circuit"),
    ]

    circuit: reactive[QuantumCircuit] = reactive(
        lambda: QuantumCircuit(num_qubits=2, name="untitled"), recompose=False
    )

    def __init__(self, circuit: QuantumCircuit | None = None) -> None:
        super().__init__()
        if circuit is not None:
            self._initial_circuit = circuit
        else:
            self._initial_circuit = QuantumCircuit(num_qubits=2, name="untitled")

    def on_mount(self) -> None:
        self.circuit = self._initial_circuit
        self._refresh_all()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout"):
            # Sidebar — gate palette
            with Vertical(id="sidebar"):
                yield Label("Gate Palette", id="sidebar-title")
                items = [ListItem(Label(f"{n}  {GATES[n].description[:18]}"), id=f"gate-{n}") for n in sorted(GATES)]
                yield ListView(*items, id="gate-list")

            # Main area
            with Vertical(id="main"):
                # Circuit canvas
                with ScrollableContainer(id="canvas-pane"):
                    yield Label("Circuit", id="canvas-title")
                    yield Static("", id="circuit-diagram")

                # Simulation panel
                with Vertical(id="sim-pane"):
                    yield Label("Simulation", id="sim-title")
                    yield DataTable(id="sim-table")

        yield Static("", id="status")
        yield Footer()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _refresh_diagram(self) -> None:
        c = self.circuit
        if c.gates:
            text = c.diagram()
        else:
            text = "(empty — press [a] to add gates)"
        self.query_one("#circuit-diagram", Static).update(text)
        self.query_one("#canvas-title", Label).update(
            f"Circuit: [bold]{c.name}[/bold]  "
            f"[dim]{c.num_qubits}q · {c.gate_count()} gates · depth {c.depth()}[/dim]"
        )

    def _refresh_sim(self) -> None:
        table = self.query_one("#sim-table", DataTable)
        table.clear(columns=True)
        table.add_columns("State", "Probability", "Bar")

        c = self.circuit
        if not c.gates:
            return

        try:
            result = QuantumSimulator().run(c)
            bar_width = 20
            for state, prob in sorted(result.probabilities.items(), key=lambda x: -x[1])[:8]:
                filled = int(prob * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                table.add_row(f"|{state}⟩", f"{prob:.4f}", bar)
        except Exception as exc:
            table.add_row("error", str(exc), "")

    def _refresh_status(self, msg: str = "") -> None:
        self.query_one("#status", Static).update(
            msg or f"[dim]{self.circuit.name}  |  "
                   f"{self.circuit.num_qubits} qubits  |  "
                   f"{self.circuit.gate_count()} gates  |  "
                   f"[a] add  [d] remove last  [r] simulate  [s] save  [q] quit[/dim]"
        )

    def _refresh_all(self) -> None:
        self._refresh_diagram()
        self._refresh_sim()
        self._refresh_status()

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------

    def action_simulate(self) -> None:
        self._refresh_sim()
        self._refresh_status("[green]Simulation updated.[/green]")

    def action_remove_last(self) -> None:
        if not self.circuit.gates:
            self._refresh_status("[yellow]No gates to remove.[/yellow]")
            return
        removed = self.circuit.remove_gate(len(self.circuit.gates) - 1)
        self._refresh_all()
        self._refresh_status(f"[green]Removed gate: {removed.name}[/green]")

    def action_save_session(self) -> None:
        try:
            from quantumide.io.serialization import save_session
            save_session(self.circuit)
            self._refresh_status("[green]Session saved.[/green]")
        except Exception as exc:
            self._refresh_status(f"[red]Save failed: {exc}[/red]")

    def action_new_circuit(self) -> None:
        self.circuit = QuantumCircuit(num_qubits=2, name="untitled")
        self._refresh_all()
        self._refresh_status("[green]New circuit created.[/green]")

    def action_add_gate(self) -> None:
        # Default to H — user can also double-click from list
        self._open_add_gate("H")

    def _open_add_gate(self, gate_name: str) -> None:
        def handle(result: GateSpec | None) -> None:
            if result is None:
                return
            try:
                self.circuit.add_gate(result)
                self._refresh_all()
                self._refresh_status(f"[green]Added {result.name} on targets={result.targets}[/green]")
            except (ValueError, IndexError) as exc:
                self._refresh_status(f"[red]{exc}[/red]")

        self.push_screen(AddGateScreen(gate_name), handle)

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    @on(ListView.Selected, "#gate-list")
    def gate_selected(self, event: ListView.Selected) -> None:
        item_id: str = event.item.id or ""
        if item_id.startswith("gate-"):
            gate_name = item_id[len("gate-"):]
            self._open_add_gate(gate_name)
