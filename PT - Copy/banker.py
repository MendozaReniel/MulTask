"""
Banker's Algorithm - core simulation logic (no console input/output).

PT 101 Final Project - Topic 5: Deadlock Avoidance (Banker's Algorithm)
Project title: MultiTask

Public API
----------
SystemState.from_vectors(...)  validated Total / Allocation / Max snapshot
SystemState.need               Max - Allocation
SystemState.available          Total - column sums of Allocation
SystemState.safety()           run the Banker's Safety Algorithm
SystemState.grant(...)         commit a request that already passed the safety check
request_resources(...)         Resource-Request Algorithm (checks + tentative state)
evaluate_safety(...)           safety algorithm on raw matrices (used for tentative states)

Terminology
-----------
n  number of processes
m  number of resource types
Allocation[i][j]  units of resource j currently held by process i
Max[i][j]         maximum units of resource j that process i may ever claim
Need[i][j]        Max[i][j] - Allocation[i][j]
Available[j]      Total[j] - sum of Allocation[i][j] over all processes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Union


class BankerError(ValueError):
    """Raised when a system state or a resource request is not valid."""


def default_resource_names(count: int) -> List[str]:
    """Return A, B, C, ... (then R27, R28, ...) for *count* resource types."""
    return [chr(ord("A") + index) if index < 26 else f"R{index + 1}" for index in range(count)]


def _fmt(values: Sequence[int]) -> str:
    """Format a resource vector as (x, y, z)."""
    return "(" + ", ".join(str(value) for value in values) + ")"


def _clean_vector(values: Sequence[int], length: int, label: str) -> List[int]:
    """Validate one vector of whole, non-negative numbers and return a copy."""
    cleaned = list(values)
    if len(cleaned) != length:
        raise BankerError(
            f"{label} must contain {length} value(s), one per resource type; "
            f"got {len(cleaned)}."
        )
    for value in cleaned:
        if isinstance(value, bool) or not isinstance(value, int):
            raise BankerError(f"{label} must contain whole numbers only; got {value!r}.")
        if value < 0:
            raise BankerError(f"{label} cannot contain negative values.")
    return cleaned


@dataclass
class NeedCheck:
    """One 'Need <= Work' comparison performed by the safety scan."""

    process: int
    need: List[int]
    work: List[int]
    fits: bool


@dataclass
class AllocationStep:
    """A process that fitted and was allowed to finish in the safety scan."""

    process: int
    work_before: List[int]
    allocation: List[int]
    work_after: List[int]
    finish: List[bool]


TraceEvent = Union[NeedCheck, AllocationStep]


@dataclass
class SafetyResult:
    """Outcome of one complete run of the Banker's Safety Algorithm."""

    safe: bool
    sequence: List[int]
    finish: List[bool]
    available: List[int]
    allocation: List[List[int]]
    need: List[List[int]]
    work_final: List[int]
    events: List[TraceEvent] = field(default_factory=list)


@dataclass
class RequestResult:
    """Outcome of the Resource-Request Algorithm for one process."""

    process: int
    request: List[int]
    status: str  # "GRANT" or "WAIT"
    reason: str
    available_before: List[int]
    need_before: List[int]
    tentative_available: Optional[List[int]] = None
    tentative_allocation: Optional[List[List[int]]] = None
    tentative_need: Optional[List[List[int]]] = None
    safety: Optional[SafetyResult] = None


@dataclass
class SystemState:
    """A validated snapshot of Total, Allocation, and Max."""

    process_names: List[str]
    resource_names: List[str]
    total: List[int]
    allocation: List[List[int]]
    maximum: List[List[int]]

    def __post_init__(self) -> None:
        self.process_names = [str(name) for name in self.process_names]
        self.resource_names = [str(name) for name in self.resource_names]
        self._validate()

    # -- construction ------------------------------------------------------ #
    @classmethod
    def from_vectors(
        cls,
        total: Sequence[int],
        allocation: Sequence[Sequence[int]],
        maximum: Sequence[Sequence[int]],
        process_names: Optional[Sequence[str]] = None,
        resource_names: Optional[Sequence[str]] = None,
    ) -> "SystemState":
        """Build and validate a state from plain vectors and matrices."""
        allocation_rows = [list(row) for row in allocation]
        maximum_rows = [list(row) for row in maximum]
        total_values = list(total)
        if process_names is None:
            process_names = [f"P{index}" for index in range(len(allocation_rows))]
        if resource_names is None:
            resource_names = default_resource_names(len(total_values))
        return cls(
            list(process_names),
            list(resource_names),
            total_values,
            allocation_rows,
            maximum_rows,
        )

    # -- validation -------------------------------------------------------- #
    def _validate(self) -> None:
        if not self.process_names:
            raise BankerError("At least one process is required.")
        if not self.resource_names:
            raise BankerError("At least one resource type is required.")

        n = self.process_count
        m = self.resource_count

        if len(self.total) != m:
            raise BankerError(
                f"Total vector must contain {m} value(s), one per resource type; "
                f"got {len(self.total)}."
            )
        self.total = _clean_vector(self.total, m, "Total vector")

        if len(self.allocation) != n:
            raise BankerError(
                f"Allocation must have {n} row(s), one per process; "
                f"got {len(self.allocation)}."
            )
        if len(self.maximum) != n:
            raise BankerError(
                f"Max must have {n} row(s), one per process; got {len(self.maximum)}."
            )

        self.allocation = [
            _clean_vector(self.allocation[i], m, f"Allocation for {self.process_names[i]}")
            for i in range(n)
        ]
        self.maximum = [
            _clean_vector(self.maximum[i], m, f"Max for {self.process_names[i]}")
            for i in range(n)
        ]

        for i in range(n):
            for j in range(m):
                if self.maximum[i][j] < self.allocation[i][j]:
                    raise BankerError(
                        f"Invalid state: Max for {self.process_names[i]} in resource "
                        f"{self.resource_names[j]} ({self.maximum[i][j]}) is less than "
                        f"its Allocation ({self.allocation[i][j]}), so Need would be "
                        f"negative."
                    )

        for j in range(m):
            allocated = sum(self.allocation[i][j] for i in range(n))
            if self.total[j] < allocated:
                raise BankerError(
                    f"Invalid state: Total for resource {self.resource_names[j]} "
                    f"({self.total[j]}) is less than the total already allocated "
                    f"({allocated}), so Available would be negative."
                )

    # -- derived values ---------------------------------------------------- #
    @property
    def process_count(self) -> int:
        return len(self.process_names)

    @property
    def resource_count(self) -> int:
        return len(self.resource_names)

    @property
    def need(self) -> List[List[int]]:
        """Remaining claim of every process: Max - Allocation."""
        return [
            [self.maximum[i][j] - self.allocation[i][j] for j in range(self.resource_count)]
            for i in range(self.process_count)
        ]

    @property
    def available(self) -> List[int]:
        """Units still unallocated: Total - column sums of Allocation."""
        return [
            self.total[j] - sum(self.allocation[i][j] for i in range(self.process_count))
            for j in range(self.resource_count)
        ]

    # -- algorithm --------------------------------------------------------- #
    def safety(self) -> SafetyResult:
        """Run the Banker's Safety Algorithm on this state."""
        return evaluate_safety(self.available, self.allocation, self.need)

    def grant(self, process: int, request: Sequence[int]) -> None:
        """
        Commit an allocation for *process*.

        The caller is expected to have obtained a GRANT from
        request_resources(); the guards below only protect against misuse.
        """
        if (
            isinstance(process, bool)
            or not isinstance(process, int)
            or not 0 <= process < self.process_count
        ):
            raise BankerError(f"Process must be an index from 0 to {self.process_count - 1}.")

        request = _clean_vector(request, self.resource_count, "Request vector")
        need = self.need[process]
        available = self.available

        if any(request[j] > need[j] for j in range(self.resource_count)):
            raise BankerError("Cannot grant: the request exceeds the process's remaining Need.")
        if any(request[j] > available[j] for j in range(self.resource_count)):
            raise BankerError("Cannot grant: the request exceeds the Available resources.")

        for j in range(self.resource_count):
            self.allocation[process][j] += request[j]


def evaluate_safety(
    available: Sequence[int],
    allocation: Sequence[Sequence[int]],
    need: Sequence[Sequence[int]],
) -> SafetyResult:
    """
    Run the Banker's Safety Algorithm and record every comparison.

    Work starts as Available. While an unfinished process exists whose Need is
    less than or equal to Work in every resource, that process is marked
    finished and its Allocation is returned to Work. The state is safe when
    every process can finish; the order in which they finish is the safe
    sequence.
    """
    available_values = list(available)
    allocation_rows = [list(row) for row in allocation]
    need_rows = [list(row) for row in need]

    if not available_values:
        raise BankerError("At least one resource type is required for the safety check.")
    if not allocation_rows:
        raise BankerError("At least one process is required for the safety check.")
    if len(need_rows) != len(allocation_rows):
        raise BankerError("Allocation and Need must have the same number of rows.")

    m = len(available_values)
    available_values = _clean_vector(available_values, m, "Available vector")
    allocation_rows = [
        _clean_vector(row, m, f"Allocation row {index + 1}")
        for index, row in enumerate(allocation_rows)
    ]
    need_rows = [
        _clean_vector(row, m, f"Need row {index + 1}") for index, row in enumerate(need_rows)
    ]

    work = list(available_values)
    finish = [False] * len(allocation_rows)
    sequence: List[int] = []
    events: List[TraceEvent] = []

    while True:
        selected: Optional[int] = None
        for i in range(len(allocation_rows)):
            if finish[i]:
                continue
            fits = all(need_rows[i][j] <= work[j] for j in range(m))
            events.append(
                NeedCheck(process=i, need=list(need_rows[i]), work=list(work), fits=fits)
            )
            if fits:
                selected = i
                break

        if selected is None:
            break

        work_before = list(work)
        work = [work_before[j] + allocation_rows[selected][j] for j in range(m)]
        finish[selected] = True
        sequence.append(selected)
        events.append(
            AllocationStep(
                process=selected,
                work_before=work_before,
                allocation=list(allocation_rows[selected]),
                work_after=list(work),
                finish=list(finish),
            )
        )

    return SafetyResult(
        safe=len(sequence) == len(allocation_rows),
        sequence=sequence,
        finish=finish,
        available=available_values,
        allocation=allocation_rows,
        need=need_rows,
        work_final=work,
        events=events,
    )


def request_resources(
    state: SystemState,
    process: int,
    request: Sequence[int],
) -> RequestResult:
    """
    Apply the Resource-Request Algorithm to one request.

    The checks are:
      1. Request <= Need, otherwise the process has exceeded its maximum claim
         and a BankerError is raised.
      2. Request <= Available, otherwise the process must wait.
      3. Pretend to allocate, run the safety check, and grant only if the
         resulting state is safe; otherwise the process must wait.

    This function does not modify *state*. Call state.grant() only after a
    GRANT result, as the menu and demo do.
    """
    if (
        isinstance(process, bool)
        or not isinstance(process, int)
        or not 0 <= process < state.process_count
    ):
        raise BankerError(f"Process must be an index from 0 to {state.process_count - 1}.")

    request = _clean_vector(request, state.resource_count, "Request vector")
    need = list(state.need[process])
    available = list(state.available)

    if any(request[j] > need[j] for j in range(state.resource_count)):
        raise BankerError(
            f"Request exceeds the maximum claim of {state.process_names[process]}: "
            f"Request {_fmt(request)} > Need {_fmt(need)}. The request cannot be granted."
        )

    if any(request[j] > available[j] for j in range(state.resource_count)):
        return RequestResult(
            process=process,
            request=request,
            status="WAIT",
            reason="The request exceeds Available, so the process must wait.",
            available_before=available,
            need_before=need,
        )

    tentative_available = [
        available[j] - request[j] for j in range(state.resource_count)
    ]
    tentative_allocation = [list(row) for row in state.allocation]
    tentative_need = [list(row) for row in state.need]
    for j in range(state.resource_count):
        tentative_allocation[process][j] += request[j]
        tentative_need[process][j] -= request[j]

    safety = evaluate_safety(tentative_available, tentative_allocation, tentative_need)

    if safety.safe:
        status = "GRANT"
        reason = "The tentative state is safe, so the request can be granted."
    else:
        status = "WAIT"
        reason = "Granting the request would leave the system in an UNSAFE state."

    return RequestResult(
        process=process,
        request=request,
        status=status,
        reason=reason,
        available_before=available,
        need_before=need,
        tentative_available=tentative_available,
        tentative_allocation=tentative_allocation,
        tentative_need=tentative_need,
        safety=safety,
    )
