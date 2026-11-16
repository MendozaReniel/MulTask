#!/usr/bin/env python3
"""
MultiTask - interactive Banker's Algorithm simulator.

PT 101 Final Project - Topic 5: Deadlock Avoidance (Banker's Algorithm)

Usage:
    python main.py           start the interactive menu
    python main.py --demo    run a scripted demonstration (no typing needed)
    python main.py --help    show the command-line options
"""

from __future__ import annotations

import sys
from typing import List, Sequence

import display
from banker import (
    BankerError,
    SystemState,
    default_resource_names,
    request_resources,
)
from sample_data import sample_state

MENU = """
Current scenario: {scenario}
----------------------------------------------------------------------
1. Load the sample scenario
2. Enter a system state manually
3. Display the current state
4. Run the Banker's Safety Algorithm
5. Request resources
6. Run the built-in test cases
7. Help / About
0. Exit
"""

ABOUT = """
ABOUT MULTITASK
  Project   : MultiTask - Deadlock Avoidance using the Banker's Algorithm
  Course    : PT 101 - Platform Technologies, Final Project (Topic 5)
  Language  : Python 3 (standard library only)

WHAT IT DOES
  Models several active processes that already hold some resources and may
  ask for more. Before a request is granted, the program applies the
  Banker's Safety Algorithm to check that the system stays in a safe state,
  meaning every process can still finish in some order.

INPUTS
  Total       total units of each resource type in the system
  Allocation  units currently held by each process
  Max         maximum units each process may ever claim
  Request     optional vector for one process

COMPUTED VALUES
  Need        Max - Allocation
  Available   Total - column sums of Allocation

HOW TO READ THE OUTPUT
  A state is SAFE when the safety scan can finish every process; the
  program then prints a safe sequence. Otherwise it reports UNSAFE STATE.
  For a resource request the program prints both checks
  (Request <= Need, Request <= Available), the tentative state, the safety
  trace, and GRANT or WAIT.

INPUT TIPS
  Enter vectors as numbers separated by spaces or commas, for example:
      10 5 7      or      10, 5, 7
  Type 'b' at any input prompt to cancel and return to the menu.
"""

USAGE = """Usage:
  python main.py           Start the interactive menu
  python main.py --demo    Run a scripted demonstration
  python main.py --help    Show this message
"""


class Cancelled(Exception):
    """The user typed 'b' to go back to the menu."""


class ExitRequested(Exception):
    """Input ended (for example, Ctrl+D)."""


# --------------------------------------------------------------------------- #
# Input helpers
# --------------------------------------------------------------------------- #
def ask(prompt: str) -> str:
    """Read one line of input; end-of-input exits the program."""
    try:
        return input(prompt)
    except EOFError:
        raise ExitRequested


def parse_values(text: str, length: int, label: str) -> List[int]:
    """Parse a space- or comma-separated list of whole numbers."""
    tokens = text.replace(",", " ").split()
    if len(tokens) != length:
        raise BankerError(f"{label} needs {length} value(s); got {len(tokens)}.")

    values = []
    for token in tokens:
        try:
            value = int(token)
        except ValueError:
            raise BankerError(f"'{token}' is not a whole number.")
        if value < 0:
            raise BankerError("Values cannot be negative.")
        values.append(value)
    return values


def prompt_vector(prompt: str, length: int, label: str) -> List[int]:
    """Prompt until a valid vector of *length* whole numbers is entered."""
    while True:
        text = ask(prompt).strip()
        if text.lower() in ("b", "back"):
            raise Cancelled
        try:
            return parse_values(text, length, label)
        except BankerError as exc:
            print(f"  Invalid input: {exc}")


def prompt_int(prompt: str, minimum: int) -> int:
    """Prompt until a whole number of at least *minimum* is entered."""
    while True:
        text = ask(prompt).strip()
        if text.lower() in ("b", "back"):
            raise Cancelled
        try:
            value = int(text)
        except ValueError:
            print(f"  Enter a whole number of at least {minimum}.")
            continue
        if value < minimum:
            print(f"  Enter a whole number of at least {minimum}.")
            continue
        return value


def prompt_matrix(
    label: str, process_names: Sequence[str], resource_count: int
) -> List[List[int]]:
    """Prompt for one row per process."""
    matrix = []
    for name in process_names:
        matrix.append(
            prompt_vector(
                f"  {label} for {name} ({resource_count} values): ",
                resource_count,
                f"{label} for {name}",
            )
        )
    return matrix


# --------------------------------------------------------------------------- #
# Program actions
# --------------------------------------------------------------------------- #
def enter_state() -> SystemState:
    """Interactively build a system state."""
    print("\nEnter a system state. Type 'b' at any prompt to cancel.\n")

    resource_count = prompt_int("Number of resource types: ", 1)
    defaults = default_resource_names(resource_count)
    names_text = ask(f"Resource names [{', '.join(defaults)}]: ").strip()
    if names_text.lower() in ("b", "back"):
        raise Cancelled

    if names_text:
        resource_names = [
            part.strip()
            for part in names_text.replace(";", ",").split(",")
            if part.strip()
        ]
        if len(resource_names) != resource_count:
            print(f"  Expected {resource_count} name(s); using the default names.")
            resource_names = defaults
    else:
        resource_names = defaults

    process_count = prompt_int("Number of processes: ", 1)
    process_names = [f"P{index}" for index in range(process_count)]

    total = prompt_vector(
        f"Total vector ({resource_count} values): ", resource_count, "Total vector"
    )
    allocation = prompt_matrix("Allocation", process_names, resource_count)
    maximum = prompt_matrix("Max", process_names, resource_count)

    return SystemState.from_vectors(
        total=total,
        allocation=allocation,
        maximum=maximum,
        process_names=process_names,
        resource_names=resource_names,
    )


def resolve_process(state: SystemState, raw: str) -> int:
    """Accept a process name (P1) or an index (1)."""
    token = raw.strip().upper()
    for index, name in enumerate(state.process_names):
        if name.upper() == token:
            return index
    try:
        index = int(token)
    except ValueError:
        index = -1
    if 0 <= index < state.process_count:
        return index
    raise BankerError(
        f"Unknown process '{raw}'. Use one of: {', '.join(state.process_names)}."
    )


def run_safety(state: SystemState) -> None:
    """Run and print the Banker's Safety Algorithm."""
    result = state.safety()
    print(display.render_safety(result, state.process_names))


def run_request(state: SystemState) -> None:
    """Ask for one process and request vector, then apply the request algorithm."""
    print("\nProcesses: " + ", ".join(state.process_names))
    process = resolve_process(
        state, ask("Process making the request (name or index): ")
    )
    request = prompt_vector(
        f"Request vector ({state.resource_count} values): ",
        state.resource_count,
        "Request vector",
    )

    try:
        result = request_resources(state, process, request)
    except BankerError as exc:
        print(f"\n  REJECTED - {exc}")
        print("  The state is unchanged.")
        return

    print(display.render_request(result, state))

    if result.status == "GRANT":
        state.grant(process, request)
        print("\n  Updated state:")
        print(display.render_state(state))


def run_tests() -> None:
    """Run the built-in testing evidence."""
    import test_banker

    test_banker.run_all()


def demo_request(state: SystemState, process: int, request: List[int]) -> None:
    """Run one request and commit it when it is granted."""
    result = request_resources(state, process, request)
    print(display.render_request(result, state))
    if result.status == "GRANT":
        state.grant(process, request)
        print("\n  Updated state:")
        print(display.render_state(state))


def run_demo() -> None:
    """Run a scripted demonstration suitable for the face-to-face defense."""
    print(display.banner())
    state = sample_state()
    scenario = "Sample - classic 5-process, 3-resource safe state"

    print(f"\nSCENARIO - {scenario}")
    print(display.render_state(state))

    print("\n" + "=" * 70)
    print("STEP 1 - Banker's Safety Algorithm on the initial state")
    print("=" * 70)
    run_safety(state)

    print("\n" + "=" * 70)
    print("STEP 2 - P4 requests (3, 3, 0)")
    print("=" * 70)
    demo_request(state, 4, [3, 3, 0])

    print("\n" + "=" * 70)
    print("STEP 3 - P1 requests (1, 0, 2)")
    print("=" * 70)
    demo_request(state, 1, [1, 0, 2])

    print("\n" + "=" * 70)
    print("STEP 4 - Safety check on the updated state")
    print("=" * 70)
    run_safety(state)
    print("\nDemo finished.")


def interactive() -> None:
    """Run the menu until the user exits."""
    state = None
    scenario = "none loaded"
    print(display.banner())

    while True:
        print(MENU.format(scenario=scenario))
        try:
            choice = ask("Select an option: ").strip()

            if choice == "1":
                state = sample_state()
                scenario = "Sample - classic 5-process, 3-resource safe state"
                print(f"\nLoaded: {scenario}\n")
                print(display.render_state(state))

            elif choice == "2":
                state = enter_state()
                scenario = "Manual entry"
                print("\nState loaded.\n")
                print(display.render_state(state))

            elif choice == "3":
                if state is None:
                    print("\n  No state loaded yet - use option 1 or 2 first.\n")
                    continue
                print(f"\nCurrent scenario: {scenario}\n")
                print(display.render_state(state))

            elif choice == "4":
                if state is None:
                    print("\n  No state loaded yet - use option 1 or 2 first.\n")
                    continue
                print(f"\nBanker's Safety Algorithm - {scenario}\n")
                run_safety(state)
                print()

            elif choice == "5":
                if state is None:
                    print("\n  No state loaded yet - use option 1 or 2 first.\n")
                    continue
                run_request(state)
                print()

            elif choice == "6":
                print()
                run_tests()
                print()

            elif choice == "7":
                print(ABOUT)

            elif choice == "0":
                print("\nGoodbye.")
                return

            else:
                print("\n  Please choose an option from 0 to 7.\n")

        except Cancelled:
            print("\n  Cancelled. The current state is unchanged.\n")
        except BankerError as exc:
            print(f"\n  Invalid input: {exc}\n")
        except (ExitRequested, KeyboardInterrupt):
            print("\nGoodbye.")
            return


def main(argv: Sequence[str]) -> int:
    """Program entry point."""
    if len(argv) > 1:
        option = argv[1].lower()
        if option in ("--demo", "-d"):
            run_demo()
            return 0
        if option in ("--help", "-h"):
            print(USAGE)
            return 0
        print(f"Unknown option: {argv[1]}\n")
        print(USAGE)
        return 2

    interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
