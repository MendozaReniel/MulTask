#!/usr/bin/env python3
"""
Testing evidence for the MultiTask Banker's Algorithm simulator.

Every case states the result the program is expected to produce and prints the
result it actually produced. Run with:

    python test_banker.py

Exit status is 0 when every case passes, 1 otherwise.
"""

from __future__ import annotations

import sys
from typing import Callable, List, Sequence, Tuple

from banker import BankerError, SystemState, request_resources
from display import format_vector


def classic_state() -> SystemState:
    """The standard five-process, three-resource example used in the demo."""
    return SystemState.from_vectors(
        total=[10, 5, 7],
        allocation=[
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2],
        ],
        maximum=[
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3],
        ],
    )


def unsafe_state() -> SystemState:
    """A three-process state in which no process can finish."""
    return SystemState.from_vectors(
        total=[3, 3],
        allocation=[
            [2, 0],
            [1, 1],
            [0, 1],
        ],
        maximum=[
            [2, 2],
            [2, 2],
            [2, 2],
        ],
    )


def summarize_safety(result, state: SystemState) -> str:
    """Describe a SafetyResult in one line."""
    if not result.safe:
        return "UNSAFE, no safe sequence"
    sequence = " -> ".join(state.process_names[index] for index in result.sequence)
    return f"SAFE, sequence {sequence}"


# --------------------------------------------------------------------------- #
# Test cases
# --------------------------------------------------------------------------- #
def classic_safe_case() -> str:
    state = classic_state()
    return summarize_safety(state.safety(), state)


def unsafe_state_case() -> str:
    state = unsafe_state()
    return summarize_safety(state.safety(), state)


def request_grant_case() -> str:
    state = classic_state()
    result = request_resources(state, 1, [1, 0, 2])
    safe = result.safety is not None and result.safety.safe
    state.grant(1, [1, 0, 2])
    return f"{result.status}, safe={safe}, Available {format_vector(state.available)}"


def request_unsafe_case() -> str:
    state = classic_state()
    result = request_resources(state, 4, [3, 3, 0])
    if result.safety is None:
        tentative = "no safety check"
    else:
        tentative = "tentative safe" if result.safety.safe else "tentative unsafe"
    return f"{result.status}, {tentative}, Available {format_vector(state.available)}"


def request_exceeds_available_case() -> str:
    state = classic_state()
    result = request_resources(state, 0, [4, 0, 0])
    checked = "no safety check" if result.safety is None else "safety checked"
    return f"{result.status}, {checked}, Available {format_vector(state.available)}"


def request_exceeds_need_case() -> str:
    state = classic_state()
    try:
        request_resources(state, 1, [2, 2, 2])
    except BankerError as exc:
        return f"ERROR: {exc}"
    return "ERROR: no exception was raised"


def invalid_max_case() -> str:
    try:
        SystemState.from_vectors(
            total=[5, 5, 5],
            allocation=[[2, 0, 0]],
            maximum=[[1, 0, 0]],
        )
    except BankerError as exc:
        return f"ERROR: {exc}"
    return "ERROR: no exception was raised"


def invalid_total_case() -> str:
    try:
        SystemState.from_vectors(
            total=[1, 1, 1],
            allocation=[[2, 0, 0]],
            maximum=[[2, 0, 0]],
        )
    except BankerError as exc:
        return f"ERROR: {exc}"
    return "ERROR: no exception was raised"


Case = Tuple[str, str, Callable[[], str]]

CASES: List[Case] = [
    (
        "Case 1 - Classic 5-process state is safe",
        "SAFE, sequence P1 -> P3 -> P0 -> P2 -> P4",
        classic_safe_case,
    ),
    (
        "Case 2 - State with no safe sequence",
        "UNSAFE, no safe sequence",
        unsafe_state_case,
    ),
    (
        "Case 3 - P1 requests (1, 0, 2): request is granted",
        "GRANT, safe=True, Available (2, 3, 0)",
        request_grant_case,
    ),
    (
        "Case 4 - P4 requests (3, 3, 0): request must wait",
        "WAIT, tentative unsafe, Available (3, 3, 2)",
        request_unsafe_case,
    ),
    (
        "Case 5 - P0 requests (4, 0, 0): exceeds Available",
        "WAIT, no safety check, Available (3, 3, 2)",
        request_exceeds_available_case,
    ),
    (
        "Case 6 - P1 requests (2, 2, 2): exceeds maximum claim",
        "ERROR: Request exceeds the maximum claim of P1*",
        request_exceeds_need_case,
    ),
    (
        "Case 7 - Max below Allocation is rejected",
        "ERROR: Invalid state: Max for P0*",
        invalid_max_case,
    ),
    (
        "Case 8 - Total below allocated units is rejected",
        "ERROR: Invalid state: Total for resource A*",
        invalid_total_case,
    ),
]


def run_all() -> bool:
    """Run every case and print expected versus actual results."""
    print("MultiTask - Banker's Algorithm test cases")
    print("=" * 60)

    passed = 0
    for name, expected, action in CASES:
        print(f"\n{name}")
        try:
            actual = action()
        except Exception as exc:  # report unexpected failures as the actual result
            actual = f"UNEXPECTED ERROR: {exc.__class__.__name__}: {exc}"

        prefix_match = expected.endswith("*")
        target = expected[:-1] if prefix_match else expected
        ok = actual.startswith(target) if prefix_match else actual == expected

        print(f"  Expected: {expected.rstrip('*')}")
        print(f"  Actual:   {actual}")
        print(f"  Result:   {'PASS' if ok else 'FAIL'}")
        passed += 1 if ok else 0

    print("\n" + "=" * 60)
    print(f"Summary: {passed}/{len(CASES)} test cases passed.")
    return passed == len(CASES)


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
