# MultiTask - Banker's Algorithm Simulator

**PT 101 - Platform Technologies | Final Project**
**Topic 5: Deadlock Avoidance - Banker's Algorithm**

A menu-driven Python program that simulates several active processes sharing
limited resource types. Before any request is granted, the program applies the
Banker's Safety Algorithm to confirm that the system remains in a safe state,
prints the complete comparison trace and safe sequence (or `UNSAFE STATE`), and
then reports `GRANT` or `WAIT` for the request.

---

## 1. Project title

Among the six sample titles for Topic 5, **MultiTask** is the best fit:

- Its description matches the required algorithm exactly: several active
  applications hold some resources and request more, and the simulator uses
  `Allocation`, `Max`, `Need`, and `Available` to find a safe sequence or
  report an unsafe state.
- The other titles are valid but narrower: `AppShield`, `DownloadSafe`,
  `UpdateGuard`, and `DataFlow` each frame the same algorithm around one
  specific workload, while `VirtualSafe` frames it around virtual machines.
  `MultiTask` keeps the general process/resource model that the guidelines
  require and is the easiest to explain during the oral defense.

---

## 2. Features

- Banker's Safety Algorithm with a step-by-step trace: every `Need <= Work`
  comparison, every `Work = Work + Allocation` update, and the `Finish` flags
  after each process finishes.
- Safe sequence when the state is safe; `UNSAFE STATE` otherwise.
- Resource-Request Algorithm: `Request <= Need`, `Request <= Available`,
  tentative allocation, safety check, and `GRANT` / `WAIT`.
- Input validation: negative values, wrong vector sizes, `Max < Allocation`,
  and `Total < allocated` are rejected with a clear message.
- Menu-driven interface, plus a scripted `--demo` mode for the presentation.
- Tkinter graphical interface with an editable state grid and the same trace
  output.
- Built-in testing evidence with expected and actual results.
- Standard library only - no installation step.

---

## 3. Requirements and execution

- Python 3.8 or newer (tested on Python 3.12).
- No third-party packages.

```
python main.py          # interactive console menu
python gui.py           # Tkinter graphical interface
python main.py --demo   # scripted demonstration, no typing needed
python main.py --help   # command-line options
```

On Windows, `py main.py` and `py gui.py` work the same way.

The GUI needs Tkinter, which is included with the standard Python installer on
Windows and macOS. On Linux, install `python3-tk` if `import tkinter` fails.

Run the testing evidence with:

```
python test_banker.py
```

Exit status is `0` when all cases pass, `1` otherwise.

---

## 4. Using the menu

| Option | Action |
|---|---|
| 1 | Load the sample scenario (5 processes, 3 resource types, safe state) |
| 2 | Enter a system state manually |
| 3 | Display the current state |
| 4 | Run the Banker's Safety Algorithm on the current state |
| 5 | Submit a resource request for one process |
| 6 | Run the built-in test cases |
| 7 | Help / About |
| 0 | Exit |

At any input prompt, type `b` to cancel and return to the menu.

### Manual entry

The program asks for, in order:

1. Number of resource types.
2. Resource names (press Enter to accept `A, B, C, ...`).
3. Number of processes (named `P0`, `P1`, ... automatically).
4. `Total` vector.
5. `Allocation` matrix, one row per process.
6. `Max` matrix, one row per process.

Vectors and rows accept spaces or commas, for example `10 5 7` or `10, 5, 7`.
The state is validated before it is accepted; if it is invalid, the previous
state is kept.

### Request entry

Choose the process by name (`P1`) or index (`1`), then enter the request
vector. The simulator prints the checks, the tentative state, the safety trace,
and the final `GRANT` or `WAIT`.

---

## 5. Inputs and computed values

| Quantity | Meaning |
|---|---|
| `Total[j]` | total units of resource `j` in the system |
| `Allocation[i][j]` | units of resource `j` currently held by process `i` |
| `Max[i][j]` | maximum units of resource `j` that process `i` may ever claim |
| `Need[i][j]` | `Max[i][j] - Allocation[i][j]` |
| `Available[j]` | `Total[j] - sum of Allocation[i][j]` over all processes |
| `Request[j]` | units of resource `j` requested by one process |

The program checks that every value is a non-negative whole number, that every
row has one value per resource type, that `Max >= Allocation` (otherwise
`Need` would be negative), and that `Total` is at least the sum of each
`Allocation` column (otherwise `Available` would be negative).

---

## 6. Reading the output

### State table

```
Resource order: A, B, C

Process  Allocation  Max        Need
-------  ----------  ---------  ---------
P0       (0, 1, 0)   (7, 5, 3)  (7, 4, 3)
...
Total:     (10, 5, 7)
Available: (3, 3, 2)
```

### Safety trace

```
Initial Work = Available = (3, 3, 2)
Initial Finish = [P0=F, P1=F, P2=F, P3=F, P4=F]

Step 1:
  P0: Need (7, 4, 3) <= Work (3, 3, 2)? NO
  P1: Need (1, 2, 2) <= Work (3, 3, 2)? YES
  -> Work = (3, 3, 2) + Allocation(P1) (2, 0, 0) = (5, 3, 2)
     Finish = [P0=F, P1=T, P2=F, P3=F, P4=F]
```

- Each `Step` is one pass of the scan.
- `YES` means every resource in that process's `Need` fits in the current
  `Work`; `NO` means at least one resource is short.
- When a process fits, its `Allocation` is returned to `Work` and its
  `Finish` flag becomes `T`.
- If the scan finishes every process, the program prints `SAFE STATE` and a
  safe sequence. Otherwise it prints `UNSAFE STATE` and explains that no safe
  sequence exists.

### Resource-request result

```
Check 1 - Request <= Need:      (1, 0, 2) <= (1, 2, 2)  -> YES
Check 2 - Request <= Available: (1, 0, 2) <= (3, 3, 2)  -> YES
...
Request result: GRANT - The tentative state is safe, so the request can be granted.
```

- `WAIT` means the request is not granted; the state is unchanged.
- `GRANT` commits the request: `Allocation` increases, `Need` decreases, and
  `Available` is recomputed.
- A request larger than the process's `Need` is rejected as an error because
  the process has exceeded its maximum claim.

---

## 7. Algorithm

### Banker's Safety Algorithm

```
Need[i][j]    = Max[i][j] - Allocation[i][j]
Available[j]  = Total[j] - sum_i Allocation[i][j]

Work          = Available
Finish[i]     = False for every process
safe_sequence = []

while True:
    find the first unfinished process i (in index order) such that
        Need[i][j] <= Work[j] for every resource j
    if no such process exists:
        stop
    Work[j] = Work[j] + Allocation[i][j] for every resource j
    Finish[i] = True
    append i to safe_sequence
    restart the scan from the first process

if every Finish[i] is True:
    SAFE STATE; safe_sequence is a valid completion order
else:
    UNSAFE STATE; no safe sequence exists
```

### Resource-Request Algorithm

```
if Request > Need:
    reject: the process exceeded its maximum claim
if Request > Available:
    WAIT: the resources are not available yet

Available'  = Available - Request
Allocation' = Allocation with Allocation'[i] += Request
Need'       = Need with Need'[i] -= Request

if safety(Allocation', Need', Available') is safe:
    GRANT and keep the tentative state
else:
    WAIT and keep the old state
```

The implementation restarts the scan after each process finishes, which is
equivalent to the textbook version because `Work` only grows. Any valid safe
sequence proves the state is safe; a different scan order may produce a
different (also valid) sequence.

---

## 8. Sample run

`python main.py --demo` runs this scenario without input:

```
SCENARIO - Sample - classic 5-process, 3-resource safe state
  Resource order: A, B, C

  Process  Allocation  Max        Need
  -------  ----------  ---------  ---------
  P0       (0, 1, 0)   (7, 5, 3)  (7, 4, 3)
  P1       (2, 0, 0)   (3, 2, 2)  (1, 2, 2)
  P2       (3, 0, 2)   (9, 0, 2)  (6, 0, 0)
  P3       (2, 1, 1)   (2, 2, 2)  (0, 1, 1)
  P4       (0, 0, 2)   (4, 3, 3)  (4, 3, 1)

  Total:     (10, 5, 7)
  Available: (3, 3, 2)   (Total - sum of Allocation columns)

  Step 1:
    P0: Need (7, 4, 3) <= Work (3, 3, 2)? NO
    P1: Need (1, 2, 2) <= Work (3, 3, 2)? YES
    -> Work = (3, 3, 2) + Allocation(P1) (2, 0, 0) = (5, 3, 2)
       Finish = [P0=F, P1=T, P2=F, P3=F, P4=F]
  ...
  Safety result: SAFE STATE
  Safe sequence: P1 -> P3 -> P0 -> P2 -> P4

STEP 2 - P4 requests (3, 3, 0)
  Check 1 - Request <= Need:      (3, 3, 0) <= (4, 3, 1)  -> YES
  Check 2 - Request <= Available: (3, 3, 0) <= (3, 3, 2)  -> YES
  ...
  Safety result: UNSAFE STATE
  Request result: WAIT - Granting the request would leave the system in an UNSAFE state.

STEP 3 - P1 requests (1, 0, 2)
  Check 1 - Request <= Need:      (1, 0, 2) <= (1, 2, 2)  -> YES
  Check 2 - Request <= Available: (1, 0, 2) <= (3, 3, 2)  -> YES
  ...
  Safety result: SAFE STATE
  Safe sequence: P1 -> P3 -> P0 -> P2 -> P4
  Request result: GRANT - The tentative state is safe, so the request can be granted.
  P1 receives (1, 0, 2); Available becomes (2, 3, 0).
```

The demo then shows the updated state and runs one final safety check, which is
still safe.

---

## 9. Testing evidence

Run `python test_banker.py`. The program prints the expected result, the actual
result, and PASS/FAIL for each case, and exits with status 1 if any case fails.

| # | Case | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Classic 5-process state | Safe, sequence `P1 -> P3 -> P0 -> P2 -> P4` | Same | PASS |
| 2 | State where no process can finish | `UNSAFE, no safe sequence` | Same | PASS |
| 3 | `P1` requests `(1, 0, 2)` | `GRANT`, `Available (2, 3, 0)` | Same | PASS |
| 4 | `P4` requests `(3, 3, 0)` | `WAIT`, tentative state unsafe, `Available (3, 3, 2)` | Same | PASS |
| 5 | `P0` requests `(4, 0, 0)` | `WAIT` because it exceeds `Available`, no safety check | Same | PASS |
| 6 | `P1` requests `(2, 2, 2)` | Error: exceeds the maximum claim | Same | PASS |
| 7 | `Max` below `Allocation` | Error: `Need` would be negative | Same | PASS |
| 8 | `Total` below allocated units | Error: `Available` would be negative | Same | PASS |

Actual summary from the last run:

```
MultiTask - Banker's Algorithm test cases
============================================================

Case 1 - Classic 5-process state is safe
  Expected: SAFE, sequence P1 -> P3 -> P0 -> P2 -> P4
  Actual:   SAFE, sequence P1 -> P3 -> P0 -> P2 -> P4
  Result:   PASS
...
============================================================
Summary: 8/8 test cases passed.
```

The guidelines require at least three test cases; this project ships eight
covering a safe state, an unsafe state, a granted request, a request denied by
the safety check, a request denied by availability, an invalid claim, and two
invalid-state checks.

---

## 10. Tkinter GUI

`python gui.py` opens the graphical version of the same simulator.

Layout:

- **Header** - program name and topic.
- **System state** - process and resource-type spin boxes (1-10 processes,
  1-8 resource types), a `Build table` button, the `Total` vector entry, and a
  grid with one row per process and editable `Allocation` and `Max` cells.
- **Actions** - `Run Safety Check`, `Request Resources`, `Load Sample`, and
  `Clear Output`, plus a process dropdown and the request vector entry.
- **Output** - the same state table, safety trace, request checks, and
  verdicts as the console version, with vertical and horizontal scrolling.
- **Status bar** - green for a safe state or granted request, red for an
  unsafe state, a waiting request, or invalid input.
- **Menus** - `File` (load sample, clear output, exit) and `Help` (about).

The GUI calls the same `banker.py` functions and `display.py` formatters as
`main.py`, so both versions produce identical results. After a request is
granted, the Allocation cells are updated to the committed values so the next
safety check or request starts from the new state. Invalid entries are
reported in a dialog and in the status bar instead of closing the window.

---

## 11. Project structure

| File | Purpose |
|---|---|
| `banker.py` | core algorithm: validation, `Need`/`Available`, safety trace, request algorithm |
| `sample_data.py` | sample scenario shared by the console and GUI versions |
| `display.py` | console formatting: state table, safety trace, request output |
| `gui.py` | Tkinter window: editable state grid, request controls, trace output |
| `main.py` | menu, manual entry, scripted demo |
| `test_banker.py` | eight test cases with expected versus actual results |
| `README.md` | this user guide |

---

## 12. Deliverables checklist

| Guideline deliverable | Where it is |
|---|---|
| Complete, organized source code (GitHub repository) | `banker.py`, `display.py`, `main.py`, `test_banker.py` - upload this folder to the group repository |
| User guide | this `README.md` |
| Optional graphical interface | `gui.py` (same algorithm and output as the console version) |
| Testing evidence with at least three test cases | `test_banker.py`; table in section 9 |
| Contribution record | instructor-provided Google Spreadsheet (each member fills in their assigned tasks) |
| Demo/presentation materials | `python main.py --demo` and the interactive menu; sample run in section 8 |

---

## 13. Notes and limitations

- Resource instances are modelled as whole numbers, so each resource type may
  have multiple instances - the setting the Banker's Algorithm is defined for.
- State is kept in memory only; closing the program discards manual entries.
  The sample scenario can be reloaded at any time.
- A granted request is committed immediately; there is no undo option. Reload
  the sample or re-enter the state to start over.
- The safe sequence printed depends on the fixed scan order (`P0` first).
  Another implementation may print another valid sequence for the same state.
- Very long process or resource names make the text tables wider.

Per the course guidelines, disclose any assistance or tools used during
development in the group's submission, following the instructor's policy.

---

## 14. References

- Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating System
  Concepts* (10th ed.). Wiley. Chapter 8: Deadlocks.
- Stallings, W. (2018). *Operating Systems: Internals and Design Principles*
  (9th ed.). Pearson.
- Python Software Foundation. *The Python Tutorial*.
  https://docs.python.org/3/tutorial/
