from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


class ConversionError(Exception):
    """Raised when a conversion request cannot be planned or executed."""


@dataclass(slots=True)
class ConversionTask:
    input_path: Path
    output_path: Path


@dataclass(slots=True)
class ConversionResult:
    input_path: Path
    output_path: Path
    succeeded: bool
    command: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str


@dataclass(slots=True)
class BatchConversionSummary:
    results: list[ConversionResult]

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def succeeded_count(self) -> int:
        return sum(1 for item in self.results if item.succeeded)

    @property
    def failed_count(self) -> int:
        return self.total_count - self.succeeded_count


def plan_conversion(input_path: Path | str, output_dir: Path | str | None) -> ConversionTask:
    source = Path(input_path).expanduser()
    if not source.exists() or not source.is_file():
        raise ConversionError(f"Input file does not exist: {source}")
    if source.suffix.lower() != ".amr":
        raise ConversionError(f"Input file must end with .amr: {source.name}")

    target_dir = Path(output_dir).expanduser() if output_dir else source.parent
    return ConversionTask(input_path=source, output_path=target_dir / f"{source.stem}.mp3")


def plan_batch(
    input_paths: Iterable[Path | str], output_dir: Path | str | None
) -> list[ConversionTask]:
    tasks: list[ConversionTask] = []
    for input_path in input_paths:
        source = Path(input_path).expanduser()
        if source.suffix.lower() != ".amr":
            continue
        tasks.append(plan_conversion(source, output_dir))
    return tasks


def resolve_ffmpeg_binary() -> Path:
    env_override = os.environ.get("AMR_TO_MP3_FFMPEG")
    if env_override:
        override_path = Path(env_override).expanduser()
        if override_path.exists():
            return override_path
        raise ConversionError(f"Configured ffmpeg binary does not exist: {override_path}")

    packaged_candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        packaged_candidates.extend(
            [
                executable_dir / "ffmpeg.exe",
                executable_dir / "ffmpeg",
            ]
        )
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            packaged_candidates.extend(
                [
                    Path(meipass) / "ffmpeg.exe",
                    Path(meipass) / "ffmpeg",
                ]
            )

    for candidate in packaged_candidates:
        if candidate.exists():
            return candidate

    command = shutil.which("ffmpeg")
    if command:
        return Path(command)

    raise ConversionError(
        "Unable to find ffmpeg. Install ffmpeg or set AMR_TO_MP3_FFMPEG."
    )


def build_ffmpeg_command(ffmpeg_path: Path | str, task: ConversionTask) -> tuple[str, ...]:
    binary = Path(ffmpeg_path)
    executable: list[str]
    if binary.suffix.lower() == ".py":
        executable = [sys.executable, str(binary)]
    else:
        executable = [str(binary)]

    return tuple(
        executable
        + [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(task.input_path),
            "-vn",
            str(task.output_path),
        ]
    )


def convert_file(task: ConversionTask, ffmpeg_path: Path | str | None = None) -> ConversionResult:
    binary = Path(ffmpeg_path) if ffmpeg_path else resolve_ffmpeg_binary()
    task.output_path.parent.mkdir(parents=True, exist_ok=True)

    command = build_ffmpeg_command(binary, task)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    succeeded = completed.returncode == 0 and task.output_path.exists()
    stderr = completed.stderr.strip()
    if completed.returncode == 0 and not task.output_path.exists():
        stderr = (stderr + "\n" if stderr else "") + "ffmpeg finished without creating the output file."

    return ConversionResult(
        input_path=task.input_path,
        output_path=task.output_path,
        succeeded=succeeded,
        command=command,
        return_code=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=stderr,
    )


def convert_batch(
    tasks: Iterable[ConversionTask],
    ffmpeg_path: Path | str | None = None,
    progress_callback: Callable[[ConversionResult, int, int], None] | None = None,
) -> BatchConversionSummary:
    planned_tasks = list(tasks)
    binary = Path(ffmpeg_path) if ffmpeg_path else resolve_ffmpeg_binary()
    results: list[ConversionResult] = []

    total = len(planned_tasks)
    for index, task in enumerate(planned_tasks, start=1):
        result = convert_file(task, ffmpeg_path=binary)
        results.append(result)
        if progress_callback is not None:
            progress_callback(result, index, total)

    return BatchConversionSummary(results=results)
