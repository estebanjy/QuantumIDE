"""ASCII/Rich circuit renderer."""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from quantumide.core.circuit import QuantumCircuit
from quantumide.simulation.simulator import SimulationResult


def render_circuit(circuit: QuantumCircuit, console: Console | None = None) -> str:
    """Return a Rich-formatted ASCII diagram string and optionally print it."""
    diagram = circuit.diagram() if circuit.gates else "(empty circuit)"
    if console is not None:
        panel = Panel(
            Text(diagram, style="bold cyan"),
            title=f"[bold]{circuit.name}[/bold]",
            subtitle=(
                f"[dim]{circuit.num_qubits} qubit(s) · "
                f"{circuit.gate_count()} gate(s) · "
                f"depth {circuit.depth()}[/dim]"
            ),
            border_style="blue",
        )
        console.print(panel)
    return diagram


def render_probabilities(result: SimulationResult, console: Console, top: int = 8) -> None:
    """Print a Rich bar-chart of state probabilities."""
    from rich.table import Table

    table = Table(title="State Probabilities", show_header=True)
    table.add_column("State", style="cyan bold")
    table.add_column("Probability", justify="right")
    table.add_column("Bar")

    bar_width = 30
    for state, prob in sorted(result.probabilities.items(), key=lambda x: -x[1])[:top]:
        filled = int(prob * bar_width)
        bar = "[green]" + "█" * filled + "[/green]" + "░" * (bar_width - filled)
        table.add_row(f"|{state}⟩", f"{prob:.4f}", bar)

    console.print(table)


def render_counts(result: SimulationResult, console: Console) -> None:
    """Print a Rich bar-chart of measurement counts."""
    from rich.table import Table

    if not result.counts:
        console.print("[yellow]No counts available. Run with --shots.[/yellow]")
        return

    total = sum(result.counts.values())
    table = Table(title=f"Measurement Counts ({total} shots)", show_header=True)
    table.add_column("State", style="cyan bold")
    table.add_column("Count", justify="right")
    table.add_column("Frequency", justify="right")
    table.add_column("Bar")

    bar_width = 30
    for state, count in sorted(result.counts.items(), key=lambda x: -x[1]):
        freq = count / total
        filled = int(freq * bar_width)
        bar = "[magenta]" + "█" * filled + "[/magenta]" + "░" * (bar_width - filled)
        table.add_row(f"|{state}⟩", str(count), f"{freq:.3f}", bar)

    console.print(table)
