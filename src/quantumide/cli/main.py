"""CLI entry point and commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from quantumide.core.circuit import GateSpec, QuantumCircuit
from quantumide.core.gates import GATES
from quantumide.io.serialization import (
    clear_session,
    load_circuit,
    load_session,
    save_circuit,
    save_session,
)

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """QuantumIDE — Interactive Quantum Circuit Builder."""


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--qubits", "-q", required=True, type=int, help="Number of qubits.")
@click.option("--name", "-n", default="circuit", show_default=True, help="Circuit name.")
def create(qubits: int, name: str) -> None:
    """Create a new quantum circuit and start a session."""
    circuit = QuantumCircuit(num_qubits=qubits, name=name)
    save_session(circuit)
    console.print(f"[green]Created circuit '[bold]{name}[/bold]' with {qubits} qubit(s).[/green]")
    console.print("[dim]Use 'qide add-gate' to add gates, 'qide save <file>' to save.[/dim]")


# ---------------------------------------------------------------------------
# add-gate
# ---------------------------------------------------------------------------

@cli.command(name="add-gate")
@click.option("--gate", "-g", required=True, help="Gate name (H, X, Y, Z, T, S, CNOT, CZ, SWAP, CCX).")
@click.option("--qubit", "-q", "qubits", multiple=True, type=int, help="Target qubit index (repeatable).")
@click.option("--target", "-t", multiple=True, type=int, help="Target qubit index, alias for --qubit.")
@click.option("--control", "-c", multiple=True, type=int, help="Control qubit index (repeatable).")
def add_gate(gate: str, qubits: tuple, target: tuple, control: tuple) -> None:
    """Add a gate to the current session circuit."""
    targets = list(qubits) + list(target)
    controls = list(control)

    gate_name = gate.upper()
    if gate_name not in GATES:
        console.print(
            f"[red]Unknown gate '[bold]{gate}[/bold]'. "
            f"Available: {', '.join(sorted(GATES))}[/red]"
        )
        raise SystemExit(1)

    if not targets:
        console.print("[red]Specify at least one target with --qubit or --target.[/red]")
        raise SystemExit(1)

    try:
        circuit = load_session()
        spec = GateSpec(name=gate_name, targets=targets, controls=controls)
        circuit.add_gate(spec)
        save_session(circuit)

        qubit_desc = f"qubit(s) {targets}"
        if controls:
            qubit_desc = f"control(s) {controls} → target(s) {targets}"
        console.print(f"[green]Added [bold]{gate_name}[/bold] on {qubit_desc}.[/green]")
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# remove-gate
# ---------------------------------------------------------------------------

@cli.command(name="remove-gate")
@click.argument("index", type=int)
def remove_gate(index: int) -> None:
    """Remove the gate at INDEX from the current session circuit."""
    try:
        circuit = load_session()
        removed = circuit.remove_gate(index)
        save_session(circuit)
        console.print(f"[green]Removed gate #{index} ([bold]{removed.name}[/bold]).[/green]")
    except (FileNotFoundError, IndexError) as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("output", type=click.Path())
def save(output: str) -> None:
    """Save the current session circuit to OUTPUT file."""
    try:
        circuit = load_session()
        save_circuit(circuit, Path(output))
        console.print(f"[green]Saved '[bold]{circuit.name}[/bold]' to {output}.[/green]")
    except FileNotFoundError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("circuit_file", type=click.Path(exists=True))
def load(circuit_file: str) -> None:
    """Load a circuit file into the current session."""
    try:
        circuit = load_circuit(Path(circuit_file))
        save_session(circuit)
        _print_circuit(circuit)
        console.print(f"\n[green]Loaded '[bold]{circuit_file}[/bold]' as active session.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

@cli.command()
def show() -> None:
    """Show the current session circuit."""
    try:
        circuit = load_session()
        _print_circuit(circuit)
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# list-gates
# ---------------------------------------------------------------------------

@cli.command(name="list-gates")
@click.argument("circuit_file", type=click.Path(exists=True), required=False)
def list_gates(circuit_file: str | None) -> None:
    """List all gates in the current session or CIRCUIT_FILE."""
    try:
        circuit = load_circuit(Path(circuit_file)) if circuit_file else load_session()
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise SystemExit(1)

    if not circuit.gates:
        console.print("[yellow]Circuit has no gates.[/yellow]")
        return

    table = Table(title=f"Gates in '[bold]{circuit.name}[/bold]'")
    table.add_column("#", style="dim", width=4)
    table.add_column("Gate", style="cyan bold")
    table.add_column("Controls", style="yellow")
    table.add_column("Targets", style="green")

    for i, g in enumerate(circuit.gates):
        table.add_row(
            str(i),
            g.name,
            ", ".join(map(str, g.controls)) if g.controls else "—",
            ", ".join(map(str, g.targets)),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("circuit_file", type=click.Path(exists=True), required=False)
def info(circuit_file: str | None) -> None:
    """Show diagram and statistics for the current session or CIRCUIT_FILE."""
    try:
        circuit = load_circuit(Path(circuit_file)) if circuit_file else load_session()
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise SystemExit(1)

    _print_circuit(circuit)


# ---------------------------------------------------------------------------
# gates (list available gate types)
# ---------------------------------------------------------------------------

@cli.command(name="gates")
def list_available_gates() -> None:
    """List all supported gate types."""
    table = Table(title="Supported Gates")
    table.add_column("Name", style="cyan bold")
    table.add_column("Controls", justify="center")
    table.add_column("Targets", justify="center")
    table.add_column("Description")

    seen = set()
    for name, gdef in sorted(GATES.items()):
        if gdef.description in seen:
            continue
        seen.add(gdef.description)
        table.add_row(
            name,
            str(gdef.n_controls) if gdef.n_controls else "—",
            str(gdef.n_targets),
            gdef.description,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _print_circuit(circuit: QuantumCircuit) -> None:
    if circuit.gates:
        body = Text(circuit.diagram(), style="bold cyan")
    else:
        body = Text("(empty circuit)", style="dim")

    panel = Panel(
        body,
        title=f"[bold]{circuit.name}[/bold]",
        subtitle=(
            f"[dim]{circuit.num_qubits} qubit(s) · "
            f"{circuit.gate_count()} gate(s) · "
            f"depth {circuit.depth()}[/dim]"
        ),
        border_style="blue",
    )
    console.print(panel)
