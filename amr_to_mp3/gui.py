from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Any

from .converter import (
    ConversionError,
    ConversionResult,
    convert_batch,
    plan_batch,
)


def _load_tk_modules() -> tuple[Any, Any, Any, Any]:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tkinter is unavailable. Use the packaged Windows build or install a Python build with Tk support."
        ) from exc

    return tk, filedialog, messagebox, ttk


class ConverterApp:
    def __init__(self, root: Any, tk: Any, filedialog: Any, messagebox: Any, ttk: Any) -> None:
        self.root = root
        self.tk = tk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.ttk = ttk

        self.selected_files: list[Path] = []
        self.is_running = False

        self.output_dir_var = tk.StringVar(value="")
        self.ffmpeg_path_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")

        self.root.title("AMR to MP3 Converter")
        self.root.geometry("760x520")
        self.root.minsize(680, 480)

        self._build_layout()

    def _build_layout(self) -> None:
        container = self.ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        header = self.ttk.Label(
            container,
            text="Convert AMR voice files to MP3",
            font=("Segoe UI", 15, "bold"),
        )
        header.pack(anchor="w")

        subheader = self.ttk.Label(
            container,
            text="Select one AMR file for single conversion or choose multiple files/folders for batch conversion.",
        )
        subheader.pack(anchor="w", pady=(4, 12))

        actions = self.ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 12))

        self.add_files_button = self.ttk.Button(actions, text="Add Files", command=self.add_files)
        self.add_files_button.pack(side="left")

        self.add_folder_button = self.ttk.Button(actions, text="Add Folder", command=self.add_folder)
        self.add_folder_button.pack(side="left", padx=(8, 0))

        self.clear_button = self.ttk.Button(actions, text="Clear", command=self.clear_files)
        self.clear_button.pack(side="left", padx=(8, 0))

        list_frame = self.ttk.LabelFrame(container, text="Selected AMR Files", padding=8)
        list_frame.pack(fill="both", expand=True)

        self.file_list = self.tk.Listbox(list_frame, selectmode="extended", height=10)
        self.file_list.pack(side="left", fill="both", expand=True)

        scrollbar = self.ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        output_frame = self.ttk.LabelFrame(container, text="Output Settings", padding=8)
        output_frame.pack(fill="x", pady=(12, 12))

        self.ttk.Label(output_frame, text="Output folder (optional)").grid(row=0, column=0, sticky="w")
        output_entry = self.ttk.Entry(output_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.ttk.Button(output_frame, text="Browse", command=self.choose_output_dir).grid(
            row=1, column=1, sticky="ew"
        )

        self.ttk.Label(output_frame, text="ffmpeg path (optional)").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        ffmpeg_entry = self.ttk.Entry(output_frame, textvariable=self.ffmpeg_path_var)
        ffmpeg_entry.grid(row=3, column=0, sticky="ew", padx=(0, 8))
        self.ttk.Button(output_frame, text="Browse", command=self.choose_ffmpeg).grid(
            row=3, column=1, sticky="ew"
        )
        output_frame.columnconfigure(0, weight=1)

        footer = self.ttk.Frame(container)
        footer.pack(fill="x", pady=(0, 12))

        self.progress = self.ttk.Progressbar(footer, mode="determinate")
        self.progress.pack(fill="x", expand=True, side="left")

        self.convert_button = self.ttk.Button(
            footer,
            text="Convert to MP3",
            command=self.start_conversion,
        )
        self.convert_button.pack(side="left", padx=(12, 0))

        status_label = self.ttk.Label(container, textvariable=self.status_var)
        status_label.pack(anchor="w", pady=(0, 8))

        log_frame = self.ttk.LabelFrame(container, text="Log", padding=8)
        log_frame.pack(fill="both", expand=True)

        self.log_text = self.tk.Text(log_frame, height=8, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scroll = self.ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def add_files(self) -> None:
        file_names = self.filedialog.askopenfilenames(
            title="Choose AMR files",
            filetypes=[("AMR files", "*.amr"), ("All files", "*.*")],
        )
        self._append_files(Path(name) for name in file_names)

    def add_folder(self) -> None:
        folder_name = self.filedialog.askdirectory(title="Choose a folder containing AMR files")
        if not folder_name:
            return
        folder = Path(folder_name)
        self._append_files(sorted(folder.glob("*.amr")))

    def clear_files(self) -> None:
        if self.is_running:
            return
        self.selected_files.clear()
        self.file_list.delete(0, self.tk.END)
        self.status_var.set("Ready")
        self.progress.configure(value=0, maximum=100)
        self._append_log("Cleared selected files.")

    def choose_output_dir(self) -> None:
        folder_name = self.filedialog.askdirectory(title="Choose output folder")
        if folder_name:
            self.output_dir_var.set(folder_name)

    def choose_ffmpeg(self) -> None:
        file_name = self.filedialog.askopenfilename(
            title="Choose ffmpeg executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if file_name:
            self.ffmpeg_path_var.set(file_name)

    def start_conversion(self) -> None:
        if self.is_running:
            return
        if not self.selected_files:
            self.messagebox.showwarning("No files selected", "Choose at least one AMR file first.")
            return

        output_dir = Path(self.output_dir_var.get()).expanduser() if self.output_dir_var.get().strip() else None

        try:
            tasks = plan_batch(self.selected_files, output_dir)
        except ConversionError as exc:
            self.messagebox.showerror("Cannot start conversion", str(exc))
            return

        if not tasks:
            self.messagebox.showwarning("No AMR files", "The current selection does not contain any .amr files.")
            return

        ffmpeg_path = self.ffmpeg_path_var.get().strip() or None
        self._set_running(True, len(tasks))
        self._append_log(f"Starting conversion for {len(tasks)} file(s).")

        worker = Thread(
            target=self._convert_worker,
            args=(tasks, ffmpeg_path),
            daemon=True,
        )
        worker.start()

    def _convert_worker(self, tasks: list[Any], ffmpeg_path: str | None) -> None:
        try:
            summary = convert_batch(
                tasks,
                ffmpeg_path=ffmpeg_path,
                progress_callback=self._schedule_progress_update,
            )
        except Exception as exc:  # pragma: no cover - GUI fallback path
            self.root.after(0, self._handle_worker_failure, str(exc))
            return

        self.root.after(0, self._handle_worker_complete, summary)

    def _schedule_progress_update(self, result: ConversionResult, index: int, total: int) -> None:
        self.root.after(0, self._handle_progress_update, result, index, total)

    def _handle_progress_update(self, result: ConversionResult, index: int, total: int) -> None:
        self.progress.configure(value=index, maximum=max(total, 1))
        state = "OK" if result.succeeded else "FAILED"
        self.status_var.set(f"Converted {index}/{total}")
        self._append_log(f"[{state}] {result.input_path.name} -> {result.output_path.name}")
        if result.stderr:
            self._append_log(result.stderr)

    def _handle_worker_failure(self, message: str) -> None:
        self._set_running(False, 100)
        self.status_var.set("Conversion failed")
        self._append_log(message)
        self.messagebox.showerror("Conversion failed", message)

    def _handle_worker_complete(self, summary: Any) -> None:
        self._set_running(False, summary.total_count or 100)
        self.status_var.set(
            f"Finished: {summary.succeeded_count} succeeded, {summary.failed_count} failed"
        )
        self._append_log(
            f"Finished conversion. Succeeded: {summary.succeeded_count}, Failed: {summary.failed_count}"
        )
        if summary.failed_count:
            self.messagebox.showwarning(
                "Conversion finished with errors",
                f"{summary.succeeded_count} succeeded and {summary.failed_count} failed.",
            )
        else:
            self.messagebox.showinfo(
                "Conversion finished",
                f"Converted {summary.succeeded_count} file(s) successfully.",
            )

    def _set_running(self, running: bool, total_items: int) -> None:
        self.is_running = running
        state = "disabled" if running else "normal"
        self.add_files_button.configure(state=state)
        self.add_folder_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.convert_button.configure(state=state)
        self.progress.configure(value=0 if not running else 0, maximum=max(total_items, 1))

    def _append_files(self, paths: Any) -> None:
        changed = False
        existing = {path.resolve() for path in self.selected_files}
        for path in paths:
            file_path = Path(path).expanduser()
            if not file_path.exists() or file_path.suffix.lower() != ".amr":
                continue
            resolved = file_path.resolve()
            if resolved in existing:
                continue
            existing.add(resolved)
            self.selected_files.append(resolved)
            self.file_list.insert(self.tk.END, str(resolved))
            changed = True

        if changed:
            self.status_var.set(f"Selected {len(self.selected_files)} AMR file(s)")
        else:
            self._append_log("No new AMR files were added.")

    def _append_log(self, message: str) -> None:
        self.log_text.insert(self.tk.END, f"{message}\n")
        self.log_text.see(self.tk.END)


def launch_gui() -> None:
    tk, filedialog, messagebox, ttk = _load_tk_modules()
    root = tk.Tk()
    ConverterApp(root, tk, filedialog, messagebox, ttk)
    root.mainloop()
