from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from amr_to_mp3.converter import (
    ConversionError,
    convert_batch,
    convert_file,
    plan_batch,
    plan_conversion,
    resolve_ffmpeg_binary,
)
from tests.test_helpers import write_fake_ffmpeg, write_minimal_amr


class ConversionPlanningTests(unittest.TestCase):
    def test_plan_single_file_defaults_to_source_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = write_minimal_amr(Path(temp_dir) / "voice.amr")

            task = plan_conversion(source, None)

            self.assertEqual(task.input_path, source)
            self.assertEqual(task.output_path, source.with_suffix(".mp3"))

    def test_plan_single_file_uses_selected_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = write_minimal_amr(root / "voice.amr")
            output_dir = root / "exports"

            task = plan_conversion(source, output_dir)

            self.assertEqual(task.output_path, output_dir / "voice.mp3")

    def test_plan_conversion_rejects_non_amr_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "notes.txt"
            source.write_text("not audio", encoding="utf-8")

            with self.assertRaises(ConversionError):
                plan_conversion(source, None)

    def test_plan_batch_filters_non_amr_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            amr_file = write_minimal_amr(root / "keep.amr")
            text_file = root / "skip.txt"
            text_file.write_text("skip", encoding="utf-8")

            tasks = plan_batch([amr_file, text_file], root / "out")

            self.assertEqual([task.input_path for task in tasks], [amr_file])
            self.assertEqual(tasks[0].output_path, root / "out" / "keep.mp3")


class ConversionExecutionTests(unittest.TestCase):
    def test_convert_file_uses_devnull_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = write_minimal_amr(root / "voice.amr")
            task = plan_conversion(source, root / "out")

            def fake_run(command, **kwargs):
                task.output_path.parent.mkdir(parents=True, exist_ok=True)
                task.output_path.write_bytes(b"ID3")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with patch("amr_to_mp3.converter.subprocess.run", side_effect=fake_run) as run:
                result = convert_file(task, ffmpeg_path=Path("ffmpeg.exe"))

            self.assertTrue(result.succeeded)
            self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_convert_file_runs_ffmpeg_and_creates_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = write_minimal_amr(root / "voice.amr")
            ffmpeg_path = write_fake_ffmpeg(root / "fake_ffmpeg.py")
            task = plan_conversion(source, root / "out")

            result = convert_file(task, ffmpeg_path=ffmpeg_path)

            self.assertTrue(result.succeeded)
            self.assertEqual(result.input_path, source)
            self.assertTrue(task.output_path.exists())
            self.assertEqual(task.output_path.read_bytes()[:3], b"ID3")

    def test_convert_batch_collects_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            success_file = write_minimal_amr(root / "ok.amr")
            failed_file = write_minimal_amr(root / "fail.amr")
            ffmpeg_path = write_fake_ffmpeg(root / "fake_ffmpeg.py", fail_names=("fail.amr",))
            tasks = plan_batch([success_file, failed_file], root / "out")

            summary = convert_batch(tasks, ffmpeg_path=ffmpeg_path)

            self.assertEqual(summary.total_count, 2)
            self.assertEqual(summary.succeeded_count, 1)
            self.assertEqual(summary.failed_count, 1)
            self.assertFalse(summary.results[1].succeeded)
            self.assertIn("failed for fail.amr", summary.results[1].stderr)


class FfmpegResolutionTests(unittest.TestCase):
    def test_resolve_ffmpeg_uses_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ffmpeg_path = write_fake_ffmpeg(Path(temp_dir) / "custom_ffmpeg.py")

            with patch.dict(os.environ, {"AMR_TO_MP3_FFMPEG": str(ffmpeg_path)}, clear=False):
                resolved = resolve_ffmpeg_binary()

            self.assertEqual(resolved, ffmpeg_path)


class ConverterSmokeTests(unittest.TestCase):
    def test_real_ffmpeg_smoke_conversion(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg is not installed")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = write_minimal_amr(root / "smoke.amr")
            task = plan_conversion(source, root / "out")

            result = convert_file(task)

            self.assertTrue(result.succeeded, msg=result.stderr)
            self.assertTrue(task.output_path.exists())
            self.assertGreater(task.output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
