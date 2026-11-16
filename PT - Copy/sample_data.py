"""Sample system state shared by the console demo and the Tkinter GUI."""

from banker import SystemState

SAMPLE_TOTAL = [10, 5, 7]
SAMPLE_ALLOCATION = [
    [0, 1, 0],
    [2, 0, 0],
    [3, 0, 2],
    [2, 1, 1],
    [0, 0, 2],
]
SAMPLE_MAX = [
    [7, 5, 3],
    [3, 2, 2],
    [9, 0, 2],
    [2, 2, 2],
    [4, 3, 3],
]
SAMPLE_PROCESSES = ["P0", "P1", "P2", "P3", "P4"]
SAMPLE_RESOURCES = ["A", "B", "C"]


def sample_state() -> SystemState:
    """Return the classic five-process, three-resource textbook state."""
    return SystemState.from_vectors(
        total=SAMPLE_TOTAL,
        allocation=SAMPLE_ALLOCATION,
        maximum=SAMPLE_MAX,
        process_names=SAMPLE_PROCESSES,
        resource_names=SAMPLE_RESOURCES,
    )
