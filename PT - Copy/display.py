"""Console presentation helpers for the MultiTask Banker's Algorithm simulator."""

from __future__ import annotations

from typing import List, Sequence

from banker import (
    AllocationStep,
    NeedCheck,
    RequestResult,
    SafetyResult,
    SystemState,
)


def banner() -> str:
    """Return the program banner."""
    return "\n".join(
        [
            "=" * 70,
            "  MULTITASK - Banker's Algorithm Simulator",
            "  PT 101 Final Project - Topic 5: Deadlock Avoidance",
            "=" * 70,
        ]
    )


def format_vector(values: Sequence[int]) -> str:
    """Format a resource vector as (x, y, z)."""
    return "(" + ", ".join(str(value) for value in values) + ")"


def format_finish(finish: Sequence[bool], process_names: Sequence[str]) -> str:
    """Format Finish flags as [P0=F, P1=T, ...]."""
    return "[" + ", ".join(
        f"{name}={'T' if done else 'F'}" for name, done in zip(process_names, finish)
    ) + "]"


def format_sequence(sequence: Sequence[int], process_names: Sequence[str]) -> str:
    """Format a safe sequence as P1 -> P3 -> ..."""
    if not sequence:
        return "(none)"
    return " -> ".join(process_names[index] for index in sequence)


def _table(header: Sequence[str], rows: Sequence[Sequence[str]], indent: str = "  ") -> List[str]:
    """Render a simple left-aligned text table."""
    widths = []
    for column, title in enumerate(header):
        widths.append(max([len(title)] + [len(row[column]) for row in rows]))

    lines = [
        indent + "  ".join(title.ljust(widths[i]) for i, title in enumerate(header)).rstrip()
    ]
    lines.append(indent + "  ".join("-" * width for width in widths))
    for row in rows:
        lines.append(
            indent + "  ".join(value.ljust(widths[i]) for i, value in enumerate(row)).rstrip()
        )
    return lines


def render_state(state: SystemState) -> str:
    """Render Total, Allocation, Max, Need, and Available for a state."""
    header = ["Process", "Allocation", "Max", "Need"]
    rows = [
        [
            state.process_names[i],
            format_vector(state.allocation[i]),
            format_vector(state.maximum[i]),
            format_vector(state.need[i]),
        ]
        for i in range(state.process_count)
    ]

    lines = [f"  Resource order: {', '.join(state.resource_names)}", ""]
    lines.extend(_table(header, rows))
    lines.append("")
    lines.append(f"  {'Total:':<11}{format_vector(state.total)}")
    lines.append(
        f"  {'Available:':<11}{format_vector(state.available)}"
        f"   (Total - sum of Allocation columns)"
    )
    lines.append(f"  {'Need:':<11}Max - Allocation for each process")
    return "\n".join(lines)


def render_safety(result: SafetyResult, process_names: Sequence[str]) -> str:
    """Render the full trace and the verdict of a safety run."""
    lines: List[str] = [
        "",
        f"  Initial Work = Available = {format_vector(result.available)}",
        f"  Initial Finish = {format_finish([False] * len(process_names), process_names)}",
        "",
    ]

    step = 0
    new_step = True
    for event in result.events:
        if isinstance(event, NeedCheck):
            if new_step:
                step += 1
                lines.append(f"  Step {step}:")
                new_step = False
            verdict = "YES" if event.fits else "NO"
            lines.append(
                f"    {process_names[event.process]}: Need {format_vector(event.need)}"
                f" <= Work {format_vector(event.work)}? {verdict}"
            )
        else:
            lines.append(
                f"    -> Work = {format_vector(event.work_before)} + "
                f"Allocation({process_names[event.process]}) "
                f"{format_vector(event.allocation)} = {format_vector(event.work_after)}"
            )
            lines.append(f"       Finish = {format_finish(event.finish, process_names)}")
            lines.append("")
            new_step = True

    if not result.safe:
        lines.append("  No unfinished process has Need <= Work, so the scan stops.")
        lines.append("")

    if result.safe:
        lines.append("  Safety result: SAFE STATE")
        lines.append(f"  Safe sequence: {format_sequence(result.sequence, process_names)}")
    else:
        lines.append("  Safety result: UNSAFE STATE")
        lines.append("  No safe sequence exists for this allocation.")
    return "\n".join(lines)


def render_request(result: RequestResult, state: SystemState) -> str:
    """Render the resource-request checks, tentative state, and verdict."""
    name = state.process_names[result.process]
    available_ok = all(
        request <= available
        for request, available in zip(result.request, result.available_before)
    )

    lines = ["", f"  Request from {name}: {format_vector(result.request)}", ""]
    lines.append(
        f"  Check 1 - Request <= Need:      {format_vector(result.request)}"
        f" <= {format_vector(result.need_before)}  -> YES"
    )
    lines.append(
        f"  Check 2 - Request <= Available: {format_vector(result.request)}"
        f" <= {format_vector(result.available_before)}"
        f"  -> {'YES' if available_ok else 'NO'}"
    )
    lines.append("")

    if not available_ok:
        lines.append(f"  Request result: WAIT - {result.reason}")
        lines.append("  The state is unchanged.")
        return "\n".join(lines)

    lines.append(f"  Check 3 - Tentative allocation for {name} (other rows unchanged):")
    allocation_label = f"Allocation({name})"
    need_label = f"Need({name})"
    lines.append(
        f"    {allocation_label:<16}= "
        f"{format_vector(result.tentative_allocation[result.process])}"
    )
    lines.append(
        f"    {need_label:<16}= {format_vector(result.tentative_need[result.process])}"
    )
    lines.append(f"    {'Available':<16}= {format_vector(result.tentative_available)}")
    lines.append("")
    lines.append("  Check 4 - Banker's Safety Algorithm on the tentative state:")
    lines.append(render_safety(result.safety, state.process_names))
    lines.append("")

    if result.status == "GRANT":
        lines.append(f"  Request result: GRANT - {result.reason}")
        lines.append(
            f"  {name} receives {format_vector(result.request)}; "
            f"Available becomes {format_vector(result.tentative_available)}."
        )
    else:
        lines.append(f"  Request result: WAIT - {result.reason}")
        lines.append("  The request is not granted and the state is unchanged.")
    return "\n".join(lines)
