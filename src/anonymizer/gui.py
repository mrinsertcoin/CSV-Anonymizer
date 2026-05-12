from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from .keymgmt import load_keyfile
from .pipeline import run_pipeline
from .profile import load_profile
from .audit import make_audit_record, write_audit
import time


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Anonymizer")
        self.geometry("650x260")
        self.entries = {}
        for i, label in enumerate(["Input CSV", "Output CSV", "Profile YAML", "Keyfile", "Audit JSONL"]):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=6)
            entry = tk.Entry(self, width=65)
            entry.grid(row=i, column=1, padx=10, pady=6)
            self.entries[label] = entry
            tk.Button(self, text="...", command=lambda e=entry, l=label: self.pick(e, l)).grid(row=i, column=2, padx=5)
        self.entries["Audit JSONL"].insert(0, "audit/audit-log.jsonl")
        tk.Button(self, text="Start anonymization", command=self.run).grid(row=6, column=1, pady=20)

    def pick(self, entry: tk.Entry, label: str) -> None:
        if "Output" in label or "Audit" in label:
            path = filedialog.asksaveasfilename()
        else:
            path = filedialog.askopenfilename()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def run(self) -> None:
        started_at = time.time()
        try:
            input_path = Path(self.entries["Input CSV"].get())
            output_path = Path(self.entries["Output CSV"].get())
            profile = load_profile(self.entries["Profile YAML"].get())
            keymat = load_keyfile(self.entries["Keyfile"].get())
            if keymat.version != profile.key_version:
                raise ValueError(f"key version mismatch: profile expects {profile.key_version}, keyfile has {keymat.version}")
            stats = run_pipeline(input_path, output_path, profile, keymat.key)
            audit_path = Path(self.entries["Audit JSONL"].get() or "audit/audit-log.jsonl")
            write_audit(
                make_audit_record(
                    input_file=input_path,
                    output_file=output_path,
                    profile=profile,
                    key_version=keymat.version,
                    rows_in=stats.rows_in,
                    rows_out=stats.rows_out,
                    operations=stats.operations,
                    exit_code=0,
                    started_at=started_at,
                ),
                audit_path,
            )
            messagebox.showinfo("Done", f"Anonymized CSV written to:\n{output_path}\n\nAudit:\n{audit_path}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
