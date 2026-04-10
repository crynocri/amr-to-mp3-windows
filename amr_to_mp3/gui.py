from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Any

from .converter import (
    BatchConversionSummary,
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


def _build_failure_details(summary: BatchConversionSummary, max_items: int = 3) -> str:
    failed_results = [result for result in summary.results if not result.succeeded]
    if not failed_results:
        return ""

    details: list[str] = []
    for result in failed_results[:max_items]:
        reason = result.stderr or result.stdout or f"转换失败（退出码 {result.return_code}）"
        details.append(f"{result.input_path.name}：{reason}")

    remaining_count = len(failed_results) - len(details)
    if remaining_count > 0:
        details.append(f"另有 {remaining_count} 个文件转换失败，请查看下方日志。")

    return "\n".join(details)


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
        self.status_var = tk.StringVar(value="就绪")

        self.root.title("AMR 转 MP3 转换工具")
        self.root.geometry("760x680")
        self.root.minsize(680, 620)

        self._build_layout()

    def _build_layout(self) -> None:
        container = self.ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        header = self.ttk.Label(
            container,
            text="将 AMR 语音文件转换为 MP3",
            font=("Segoe UI", 15, "bold"),
        )
        header.pack(anchor="w")

        subheader = self.ttk.Label(
            container,
            text="可选择单个 AMR 文件进行转换，也可选择多个文件或文件夹进行批量转换。",
        )
        subheader.pack(anchor="w", pady=(4, 12))

        actions = self.ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 12))

        self.add_files_button = self.ttk.Button(actions, text="添加文件", command=self.add_files)
        self.add_files_button.pack(side="left")

        self.add_folder_button = self.ttk.Button(actions, text="添加文件夹", command=self.add_folder)
        self.add_folder_button.pack(side="left", padx=(8, 0))

        self.clear_button = self.ttk.Button(actions, text="清空", command=self.clear_files)
        self.clear_button.pack(side="left", padx=(8, 0))

        list_frame = self.ttk.LabelFrame(container, text="已选 AMR 文件", padding=8)
        list_frame.pack(fill="both", expand=True)

        self.file_list = self.tk.Listbox(list_frame, selectmode="extended", height=10)
        self.file_list.pack(side="left", fill="both", expand=True)

        scrollbar = self.ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        output_frame = self.ttk.LabelFrame(container, text="输出设置", padding=8)
        output_frame.pack(fill="x", pady=(12, 12))

        self.ttk.Label(output_frame, text="输出文件夹（可选）").grid(row=0, column=0, sticky="w")
        output_entry = self.ttk.Entry(output_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.ttk.Button(output_frame, text="浏览", command=self.choose_output_dir).grid(
            row=1, column=1, sticky="ew"
        )

        self.ttk.Label(output_frame, text="ffmpeg 路径（可选）").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        ffmpeg_entry = self.ttk.Entry(output_frame, textvariable=self.ffmpeg_path_var)
        ffmpeg_entry.grid(row=3, column=0, sticky="ew", padx=(0, 8))
        self.ttk.Button(output_frame, text="浏览", command=self.choose_ffmpeg).grid(
            row=3, column=1, sticky="ew"
        )
        output_frame.columnconfigure(0, weight=1)

        footer = self.ttk.Frame(container)
        footer.pack(fill="x", pady=(0, 12))

        self.progress = self.ttk.Progressbar(footer, mode="determinate")
        self.progress.pack(fill="x", expand=True, side="left")

        self.convert_button = self.ttk.Button(
            footer,
            text="开始转换",
            command=self.start_conversion,
        )
        self.convert_button.pack(side="left", padx=(12, 0))

        status_label = self.ttk.Label(container, textvariable=self.status_var)
        status_label.pack(anchor="w", pady=(0, 8))

        log_frame = self.ttk.LabelFrame(container, text="日志", padding=8)
        log_frame.pack(fill="both", expand=True)

        self.log_text = self.tk.Text(log_frame, height=8, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scroll = self.ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def add_files(self) -> None:
        file_names = self.filedialog.askopenfilenames(
            title="选择 AMR 文件",
            filetypes=[("AMR 文件", "*.amr"), ("所有文件", "*.*")],
        )
        self._append_files(Path(name) for name in file_names)

    def add_folder(self) -> None:
        folder_name = self.filedialog.askdirectory(title="选择包含 AMR 文件的文件夹")
        if not folder_name:
            return
        folder = Path(folder_name)
        self._append_files(sorted(folder.glob("*.amr")))

    def clear_files(self) -> None:
        if self.is_running:
            return
        self.selected_files.clear()
        self.file_list.delete(0, self.tk.END)
        self.status_var.set("就绪")
        self.progress.configure(value=0, maximum=100)
        self._append_log("已清空已选文件。")

    def choose_output_dir(self) -> None:
        folder_name = self.filedialog.askdirectory(title="选择输出文件夹")
        if folder_name:
            self.output_dir_var.set(folder_name)

    def choose_ffmpeg(self) -> None:
        file_name = self.filedialog.askopenfilename(
            title="选择 ffmpeg 可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
        )
        if file_name:
            self.ffmpeg_path_var.set(file_name)

    def start_conversion(self) -> None:
        if self.is_running:
            return
        if not self.selected_files:
            self.messagebox.showwarning("未选择文件", "请先至少选择一个 AMR 文件。")
            return

        output_dir = Path(self.output_dir_var.get()).expanduser() if self.output_dir_var.get().strip() else None

        try:
            tasks = plan_batch(self.selected_files, output_dir)
        except ConversionError as exc:
            self.messagebox.showerror("无法开始转换", str(exc))
            return

        if not tasks:
            self.messagebox.showwarning("没有 AMR 文件", "当前选择中不包含 .amr 文件。")
            return

        ffmpeg_path = self.ffmpeg_path_var.get().strip() or None
        self._set_running(True, len(tasks))
        self._append_log(f"开始转换，共 {len(tasks)} 个文件。")

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
        state = "成功" if result.succeeded else "失败"
        self.status_var.set(f"已转换 {index}/{total}")
        self._append_log(f"[{state}] {result.input_path.name} -> {result.output_path.name}")
        if result.stderr:
            self._append_log(result.stderr)

    def _handle_worker_failure(self, message: str) -> None:
        self._set_running(False, 100)
        self.status_var.set("转换失败")
        self._append_log(message)
        self.messagebox.showerror("转换失败", message)

    def _handle_worker_complete(self, summary: Any) -> None:
        self._set_running(False, summary.total_count or 100)
        self.status_var.set(
            f"转换完成：成功 {summary.succeeded_count} 个，失败 {summary.failed_count} 个"
        )
        self._append_log(
            f"转换完成。成功：{summary.succeeded_count}，失败：{summary.failed_count}"
        )
        if summary.failed_count:
            warning_message = f"成功 {summary.succeeded_count} 个，失败 {summary.failed_count} 个。"
            failure_details = _build_failure_details(summary)
            if failure_details:
                warning_message = f"{warning_message}\n\n{failure_details}"
            self.messagebox.showwarning(
                "转换完成，但有错误",
                warning_message,
            )
        else:
            self.messagebox.showinfo(
                "转换完成",
                f"已成功转换 {summary.succeeded_count} 个文件。",
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
            self.status_var.set(f"已选择 {len(self.selected_files)} 个 AMR 文件")
        else:
            self._append_log("没有新增 AMR 文件。")

    def _append_log(self, message: str) -> None:
        self.log_text.insert(self.tk.END, f"{message}\n")
        self.log_text.see(self.tk.END)


def launch_gui() -> None:
    tk, filedialog, messagebox, ttk = _load_tk_modules()
    root = tk.Tk()
    ConverterApp(root, tk, filedialog, messagebox, ttk)
    root.mainloop()
