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
# simulate
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("circuit_file", type=click.Path(exists=True), required=False)
@click.option("--shots", "-s", default=0, show_default=True, type=int, help="Sample circuit N times (0 = statevector only).")
@click.option("--noisy", is_flag=True, default=False, help="Run with depolarising noise model.")
@click.option("--top", default=4, show_default=True, type=int, help="Number of top states to display.")
def simulate(circuit_file: str | None, shots: int, noisy: bool, top: int) -> None:
    """Simulate the current session or CIRCUIT_FILE."""
    from quantumide.simulation import QuantumSimulator
    from rich.table import Table as RichTable

    try:
        circuit = load_circuit(Path(circuit_file)) if circuit_file else load_session()
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise SystemExit(1)

    sim = QuantumSimulator(noisy=noisy)
    result = sim.run(circuit)

    # State vector / probabilities
    table = RichTable(title=f"Simulation — [bold]{circuit.name}[/bold]" + (" (noisy)" if noisy else ""))
    table.add_column("State", style="cyan bold")
    table.add_column("Probability", justify="right")

    for state, prob in result.top_states(top).items():
        table.add_row(f"|{state}⟩", f"{prob:.4f}")

    console.print(table)

    from quantumide.visualization.ascii import render_probabilities, render_counts

    render_probabilities(result, console, top=top)

    if shots > 0:
        result.sample(shots)
        render_counts(result, console)


# ---------------------------------------------------------------------------
# interactive
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("circuit_file", type=click.Path(exists=True), required=False)
def interactive(circuit_file: str | None) -> None:
    """Launch the interactive TUI. Loads CIRCUIT_FILE or the active session."""
    from quantumide.tui.app import QuantumIDEApp

    circuit = None
    if circuit_file:
        try:
            circuit = load_circuit(Path(circuit_file))
        except Exception as exc:
            console.print(f"[red]Error loading file: {exc}[/red]")
            raise SystemExit(1)
    else:
        try:
            circuit = load_session()
        except FileNotFoundError:
            circuit = None  # start with blank circuit

    app = QuantumIDEApp(circuit=circuit)
    app.run()


# ---------------------------------------------------------------------------
# template
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("name", type=click.Choice(["bell", "ghz", "qft", "grover", "shor"], case_sensitive=False))
@click.option("--qubits", "-q", default=None, type=int, help="Override qubit count (for ghz, qft, grover).")
def template(name: str, qubits: int | None) -> None:
    """Load a built-in circuit template as the active session."""
    from quantumide.core.templates import TEMPLATES

    fn = TEMPLATES[name.lower()]
    try:
        circuit = fn(qubits) if qubits is not None and name.lower() in ("ghz", "qft", "grover") else fn()
    except (TypeError, ValueError) as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise SystemExit(1)

    save_session(circuit)
    _print_circuit(circuit)
    console.print(f"\n[green]Template '[bold]{name}[/bold]' loaded as active session.[/green]")


# ---------------------------------------------------------------------------
# optimize
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("circuit_file", type=click.Path(exists=True), required=False)
@click.option("--basis", "-b", default=None, show_default=True,
              type=click.Choice(["clifford_t", "ibm", "native"], case_sensitive=False),
              help="Transpile to target basis after optimization.")
@click.option("--save-session/--no-save-session", default=True, show_default=True,
              help="Replace the active session with the optimized circuit.")
def optimize(circuit_file: str | None, basis: str | None, save_session: bool) -> None:
    """Optimize the current session or CIRCUIT_FILE."""
    from quantumide.optimization import full_optimize

    try:
        circuit = load_circuit(Path(circuit_file)) if circuit_file else load_session()
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise SystemExit(1)

    before_gates = circuit.gate_count()
    before_depth = circuit.depth()

    optimized = full_optimize(circuit, basis=basis)

    after_gates = optimized.gate_count()
    after_depth = optimized.depth()

    console.print(
        f"[green]Optimized '[bold]{circuit.name}[/bold]': "
        f"gates {before_gates} → {after_gates} "
        f"([bold]{before_gates - after_gates:+d}[/bold]), "
        f"depth {before_depth} → {after_depth} "
        f"([bold]{before_depth - after_depth:+d}[/bold]).[/green]"
    )
    if basis:
        console.print(f"[dim]Transpiled to basis: {basis}[/dim]")

    if save_session:
        save_session_fn = save_session  # avoid name clash with click option
        from quantumide.io.serialization import save_session as _save_session
        _save_session(optimized)

    _print_circuit(optimized)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("output", type=click.Path())
@click.argument("circuit_file", type=click.Path(exists=True), required=False)
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["svg", "png", "prob", "counts", "qasm2", "qasm3", "pickle"], case_sensitive=False),
    default="svg", show_default=True,
    help="Export format.",
)
@click.option("--shots", "-s", default=1024, show_default=True, type=int, help="Shots for counts export.")
def export(output: str, circuit_file: str | None, fmt: str, shots: int) -> None:
    """Export the current session or CIRCUIT_FILE to OUTPUT."""
    from quantumide.visualization.svg import render_svg
    from quantumide.visualization.charts import plot_probabilities, plot_counts
    from quantumide.simulation import QuantumSimulator
    from quantumide.io.qasm import export_qasm2, export_qasm3
    from quantumide.io.pickle_io import save_pickle

    try:
        circuit = load_circuit(Path(circuit_file)) if circuit_file else load_session()
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise SystemExit(1)

    out_path = Path(output)
    fmt = fmt.lower()

    if fmt == "svg":
        render_svg(circuit, out_path)
        console.print(f"[green]SVG circuit diagram saved to [bold]{output}[/bold].[/green]")
    elif fmt in ("png", "prob"):
        result = QuantumSimulator().run(circuit)
        plot_probabilities(result, out_path, title=f"{circuit.name} — Probabilities")
        console.print(f"[green]Probability chart saved to [bold]{output}[/bold].[/green]")
    elif fmt == "counts":
        result = QuantumSimulator().run(circuit)
        result.sample(shots)
        plot_counts(result, out_path, title=f"{circuit.name} — Counts")
        console.print(f"[green]Counts chart saved to [bold]{output}[/bold].[/green]")
    elif fmt == "qasm2":
        export_qasm2(circuit, out_path)
        console.print(f"[green]QASM 2.0 saved to [bold]{output}[/bold].[/green]")
    elif fmt == "qasm3":
        export_qasm3(circuit, out_path)
        console.print(f"[green]QASM 3.0 saved to [bold]{output}[/bold].[/green]")
    elif fmt == "pickle":
        save_pickle(circuit, out_path)
        console.print(f"[green]Pickle saved to [bold]{output}[/bold].[/green]")


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
