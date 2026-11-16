#!/usr/bin/env python3
"""
MultiTask - Tkinter graphical interface for the Banker's Algorithm simulator.

PT 101 Final Project - Topic 5: Deadlock Avoidance (Banker's Algorithm)

Run:
    python gui.py

The window uses banker.py for every computation and display.py for the trace
text, so its results are identical to the console version in main.py.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk
from typing import List, Sequence

import display
from banker import (
    BankerError,
    SystemState,
    default_resource_names,
    request_resources,
)
from sample_data import sample_state

APP_TITLE = "MultiTask - Banker's Algorithm Simulator"


def parse_vector(text: str, length: int, label: str) -> List[int]:
    """Parse a space- or comma-separated list of whole numbers."""
    tokens = text.replace(",", " ").split()
    if len(tokens) != length:
        raise BankerError(f"{label} needs {length} value(s); got {len(tokens)}.")

    values = []
    for token in tokens:
        try:
            value = int(token)
        except ValueError:
            raise BankerError(f"'{token}' in the {label} is not a whole number.")
        if value < 0:
            raise BankerError(f"{label} cannot contain negative values.")
        values.append(value)
    return values


class BankerApp:
    """Main window: editable state grid, actions, and trace output."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1120x800")
        root.minsize(920, 680)

        self.process_count = tk.IntVar(value=5)
        self.resource_count = tk.IntVar(value=3)
        self.total_var = tk.StringVar(value="")
        self.process_var = tk.StringVar(value="")
        self.request_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready.")

        self.allocation_entries: List[List[tk.Entry]] = []
        self.max_entries: List[List[tk.Entry]] = []

        self._build_menu()
        self._build_layout()
        self.load_sample()

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load sample scenario", command=self.load_sample)
        file_menu.add_command(label="Clear output", command=self.clear_output)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = ttk.Frame(self.root, padding=10)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(
            header, text="MultiTask", font=("Segoe UI", 18, "bold")
        ).pack(side="left")
        ttk.Label(
            header,
            text="Banker's Algorithm - Deadlock Avoidance",
            foreground="#555555",
        ).pack(side="left", padx=(12, 0))

        paned = ttk.Panedwindow(outer, orient=tk.VERTICAL)
        paned.grid(row=1, column=0, sticky="nsew")

        top = ttk.Frame(paned, padding=(0, 0, 0, 6))
        bottom = ttk.Frame(paned)
        paned.add(top, weight=3)
        paned.add(bottom, weight=2)

        self._build_inputs(top)
        self._build_actions(top)
        self._build_output(bottom)

        self.status_label = tk.Label(
            outer,
            textvariable=self.status_var,
            anchor="w",
            font=("Segoe UI", 10),
            foreground="#333333",
        )
        self.status_label.grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _build_inputs(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="System state", padding=8)
        box.pack(fill="x")
        box.columnconfigure(0, weight=1)

        dims = ttk.Frame(box)
        dims.grid(row=0, column=0, sticky="ew")

        ttk.Label(dims, text="Processes:").pack(side="left")
        ttk.Spinbox(
            dims, from_=1, to=10, width=4, textvariable=self.process_count
        ).pack(side="left", padx=(4, 14))

        ttk.Label(dims, text="Resource types:").pack(side="left")
        ttk.Spinbox(
            dims, from_=1, to=8, width=4, textvariable=self.resource_count
        ).pack(side="left", padx=(4, 14))

        ttk.Button(dims, text="Build table", command=self.build_table).pack(side="left")
        ttk.Label(
            dims,
            text="Build table starts a new grid of zeros.",
            foreground="#777777",
        ).pack(side="left", padx=(10, 0))

        total_row = ttk.Frame(box)
        total_row.grid(row=1, column=0, sticky="ew", pady=(8, 6))
        ttk.Label(total_row, text="Total vector:").pack(side="left")
        ttk.Entry(total_row, textvariable=self.total_var, width=30).pack(
            side="left", padx=(6, 8)
        )
        ttk.Label(
            total_row,
            text="Numbers separated by spaces or commas, e.g. 10 5 7",
            foreground="#777777",
        ).pack(side="left")

        self.matrix_holder = ttk.Frame(box)
        self.matrix_holder.grid(row=2, column=0, sticky="w")

    def _build_actions(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="Actions", padding=8)
        box.pack(fill="x", pady=(8, 0))

        buttons = ttk.Frame(box)
        buttons.pack(fill="x")
        ttk.Button(
            buttons, text="Run Safety Check", command=self.run_safety
        ).pack(side="left")
        ttk.Button(
            buttons, text="Request Resources", command=self.submit_request
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            buttons, text="Load Sample", command=self.load_sample
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            buttons, text="Clear Output", command=self.clear_output
        ).pack(side="left", padx=(8, 0))

        request_row = ttk.Frame(box)
        request_row.pack(fill="x", pady=(8, 0))
        ttk.Label(request_row, text="Requesting process:").pack(side="left")
        self.process_combo = ttk.Combobox(
            request_row, textvariable=self.process_var, state="readonly", width=6
        )
        self.process_combo.pack(side="left", padx=(6, 16))

        ttk.Label(request_row, text="Request vector:").pack(side="left")
        self.request_entry = ttk.Entry(
            request_row, textvariable=self.request_var, width=24
        )
        self.request_entry.pack(side="left", padx=(6, 8))
        self.request_entry.bind("<Return>", lambda event: self.submit_request())
        ttk.Label(
            request_row, text="e.g. 1 0 2", foreground="#777777"
        ).pack(side="left")

    def _build_output(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="Output", padding=8)
        box.pack(fill="both", expand=True)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(box)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(
            toolbar, text="Safety trace, request checks, and verdicts"
        ).pack(side="left")
        ttk.Button(
            toolbar, text="Clear output", command=self.clear_output
        ).pack(side="right")

        text_frame = ttk.Frame(box)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        fixed_font = tkfont.nametofont("TkFixedFont").copy()
        fixed_font.configure(size=10)

        self.output = tk.Text(
            text_frame,
            wrap="none",
            font=fixed_font,
            background="#111827",
            foreground="#e5e7eb",
            insertbackground="#e5e7eb",
            relief="flat",
            padx=10,
            pady=8,
        )
        self.output.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.output.yview
        )
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(
            text_frame, orient="horizontal", command=self.output.xview
        )
        xscroll.grid(row=1, column=0, sticky="ew")
        self.output.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.output.configure(state="disabled")

    # ------------------------------------------------------------------ #
    # Editable grid
    # ------------------------------------------------------------------ #
    def build_table(self) -> None:
        """Create a fresh grid of zeros for the selected dimensions."""
        try:
            n = int(self.process_count.get())
            m = int(self.resource_count.get())
        except (tk.TclError, ValueError):
            self.show_error("Process and resource counts must be whole numbers.")
            return

        if not 1 <= n <= 10 or not 1 <= m <= 8:
            self.show_error("Use 1 to 10 processes and 1 to 8 resource types.")
            return

        for child in self.matrix_holder.winfo_children():
            child.destroy()

        self.allocation_entries = []
        self.max_entries = []
        resource_names = default_resource_names(m)

        tk.Label(
            self.matrix_holder,
            text="Process",
            width=8,
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, rowspan=2, sticky="w")
        tk.Label(
            self.matrix_holder,
            text="Allocation",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=1, columnspan=m, sticky="w")
        tk.Label(
            self.matrix_holder,
            text="Max",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=1 + m, columnspan=m, sticky="w")

        for j, resource in enumerate(resource_names):
            tk.Label(self.matrix_holder, text=resource, width=5).grid(
                row=1, column=1 + j
            )
            tk.Label(self.matrix_holder, text=resource, width=5).grid(
                row=1, column=1 + m + j
            )

        for i in range(n):
            tk.Label(
                self.matrix_holder, text=f"P{i}", width=8, anchor="w"
            ).grid(row=2 + i, column=0, sticky="w")

            allocation_row = []
            maximum_row = []
            for j in range(m):
                allocation_entry = tk.Entry(
                    self.matrix_holder, width=5, justify="center"
                )
                allocation_entry.grid(row=2 + i, column=1 + j, padx=1, pady=1)
                allocation_entry.insert(0, "0")
                allocation_row.append(allocation_entry)

                maximum_entry = tk.Entry(
                    self.matrix_holder, width=5, justify="center"
                )
                maximum_entry.grid(row=2 + i, column=1 + m + j, padx=1, pady=1)
                maximum_entry.insert(0, "0")
                maximum_row.append(maximum_entry)

            self.allocation_entries.append(allocation_row)
            self.max_entries.append(maximum_row)

        self.process_combo["values"] = [f"P{i}" for i in range(n)]
        self.process_combo.current(0)
        self.process_var.set("P0")
        self.request_var.set("")
        self.set_status(
            f"Table built: {n} process(es), {m} resource type(s). "
            "Enter values or load the sample."
        )

    def _read_matrix(
        self, entries: Sequence[Sequence[tk.Entry]], label: str
    ) -> List[List[int]]:
        matrix = []
        for i, row in enumerate(entries):
            values = []
            for j, entry in enumerate(row):
                text = entry.get().strip()
                if not text:
                    raise BankerError(f"{label} for P{i}, resource {j + 1} is empty.")
                try:
                    value = int(text)
                except ValueError:
                    raise BankerError(
                        f"{label} for P{i}, resource {j + 1} must be a whole number."
                    )
                if value < 0:
                    raise BankerError(
                        f"{label} for P{i}, resource {j + 1} cannot be negative."
                    )
                values.append(value)
            matrix.append(values)
        return matrix

    def _current_state(self) -> SystemState:
        """Read the grid and build a validated SystemState."""
        if not self.allocation_entries:
            raise BankerError("Build the table first, or load the sample scenario.")

        n = len(self.allocation_entries)
        m = len(self.allocation_entries[0])
        total = parse_vector(self.total_var.get(), m, "Total vector")
        allocation = self._read_matrix(self.allocation_entries, "Allocation")
        maximum = self._read_matrix(self.max_entries, "Max")

        return SystemState.from_vectors(
            total=total,
            allocation=allocation,
            maximum=maximum,
            process_names=[f"P{i}" for i in range(n)],
            resource_names=default_resource_names(m),
        )

    @staticmethod
    def _populate(entries: Sequence[Sequence[tk.Entry]], values: Sequence[Sequence[int]]) -> None:
        for row_entries, row_values in zip(entries, values):
            for entry, value in zip(row_entries, row_values):
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def load_sample(self) -> None:
        """Load the classic safe state into the grid."""
        state = sample_state()
        self.process_count.set(state.process_count)
        self.resource_count.set(state.resource_count)
        self.build_table()

        self.total_var.set(" ".join(str(value) for value in state.total))
        self._populate(self.allocation_entries, state.allocation)
        self._populate(self.max_entries, state.maximum)

        if state.process_count > 1:
            self.process_combo.current(1)
            self.process_var.set(state.process_names[1])
        self.request_var.set("1 0 2")

        self.set_status(
            "Sample scenario loaded: 5 processes, 3 resource types."
        )
        self.write("Sample scenario loaded.")
        self.write(display.render_state(state))

    def run_safety(self) -> None:
        """Run the Banker's Safety Algorithm on the values in the grid."""
        try:
            state = self._current_state()
            result = state.safety()
        except (BankerError, ValueError) as exc:
            self.show_error(exc)
            return

        self.write("=" * 72)
        self.write("BANKER'S SAFETY ALGORITHM")
        self.write(display.render_state(state))
        self.write(display.render_safety(result, state.process_names))

        if result.safe:
            sequence = display.format_sequence(result.sequence, state.process_names)
            self.set_status(f"SAFE STATE - safe sequence: {sequence}", ok=True)
        else:
            self.set_status("UNSAFE STATE - no safe sequence exists.", ok=False)

    def submit_request(self) -> None:
        """Apply the Resource-Request Algorithm to the selected process."""
        try:
            state = self._current_state()
            selected = self.process_var.get().strip()
            if selected not in state.process_names:
                raise BankerError("Choose the requesting process from the list.")
            process = state.process_names.index(selected)
            request = parse_vector(
                self.request_var.get(), state.resource_count, "Request vector"
            )
            result = request_resources(state, process, request)
        except (BankerError, ValueError) as exc:
            self.show_error(exc)
            return

        self.write("=" * 72)
        self.write("RESOURCE REQUEST")
        self.write(display.render_request(result, state))

        if result.status == "GRANT":
            state.grant(process, request)

            # Keep the editable grid in sync with the committed state.
            for j in range(state.resource_count):
                entry = self.allocation_entries[process][j]
                entry.delete(0, tk.END)
                entry.insert(0, str(state.allocation[process][j]))

            self.write("")
            self.write("Committed state after the granted request:")
            self.write(display.render_state(state))
            self.set_status(
                f"GRANT - {state.process_names[process]} received "
                f"{display.format_vector(request)}; Available is now "
                f"{display.format_vector(state.available)}.",
                ok=True,
            )
        else:
            self.set_status(
                "WAIT - the request was not granted; the state is unchanged.",
                ok=False,
            )

    # ------------------------------------------------------------------ #
    # Small helpers
    # ------------------------------------------------------------------ #
    def write(self, text: str) -> None:
        """Append one block of text to the output pane."""
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self) -> None:
        """Empty the output pane."""
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.configure(state="disabled")

    def set_status(self, text: str, ok: bool | None = None) -> None:
        """Update the status bar; green for success, red for problems."""
        self.status_var.set(text)
        if ok is True:
            color = "#1b5e20"
        elif ok is False:
            color = "#b71c1c"
        else:
            color = "#333333"
        self.status_label.configure(foreground=color)

    def show_error(self, error: Exception | str) -> None:
        """Show a validation error in the status bar and a dialog."""
        message = str(error)
        self.set_status("Error: " + message, ok=False)
        messagebox.showerror("Invalid input", message, parent=self.root)

    def show_about(self) -> None:
        """Show a short description of the project."""
        messagebox.showinfo(
            "About MultiTask",
            "MultiTask - Banker's Algorithm Simulator\n\n"
            "PT 101 Final Project - Topic 5: Deadlock Avoidance\n\n"
            "Need = Max - Allocation\n"
            "Available = Total - column sums of Allocation\n\n"
            "Before a request is granted, the tentative allocation is checked "
            "with the Banker's Safety Algorithm.",
            parent=self.root,
        )


def main() -> None:
    """Start the Tkinter application."""
    root = tk.Tk()
    BankerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
