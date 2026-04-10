from __future__ import annotations

import unittest
from pathlib import Path

from amr_to_mp3.gui import ConverterApp
from amr_to_mp3.converter import BatchConversionSummary, ConversionResult


class FakeVariable:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class FakeWidget:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.options = dict(kwargs)

    def pack(self, **kwargs: object) -> None:
        self.pack_options = kwargs

    def grid(self, **kwargs: object) -> None:
        self.grid_options = kwargs

    def configure(self, **kwargs: object) -> None:
        self.options.update(kwargs)

    def columnconfigure(self, index: int, weight: int) -> None:
        self.column_options = (index, weight)


class FakeScrollbar(FakeWidget):
    def set(self, *args: object) -> None:
        self.last_set = args


class FakeListbox(FakeWidget):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.items: list[str] = []

    def delete(self, start: object, end: object | None = None) -> None:
        self.items.clear()

    def insert(self, index: object, value: str) -> None:
        self.items.append(value)

    def yview(self, *args: object) -> None:
        self.last_yview = args


class FakeText(FakeWidget):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.content = ""

    def insert(self, index: object, value: str) -> None:
        self.content += value

    def see(self, index: object) -> None:
        self.last_seen = index

    def yview(self, *args: object) -> None:
        self.last_yview = args


class FakeRoot:
    def __init__(self) -> None:
        self.window_title = ""

    def title(self, value: str) -> None:
        self.window_title = value

    def geometry(self, value: str) -> None:
        self.window_geometry = value

    def minsize(self, width: int, height: int) -> None:
        self.minimum_size = (width, height)

    def after(self, delay: int, callback: object, *args: object) -> None:
        callback(*args)


class FakeTk:
    END = "end"
    StringVar = FakeVariable
    Listbox = FakeListbox
    Text = FakeText


class FakeFileDialog:
    def askopenfilenames(self, **kwargs: object) -> tuple[str, ...]:
        self.last_openfilenames = kwargs
        return ()

    def askdirectory(self, **kwargs: object) -> str:
        self.last_directory = kwargs
        return ""

    def askopenfilename(self, **kwargs: object) -> str:
        self.last_openfilename = kwargs
        return ""


class FakeMessageBox:
    def __init__(self) -> None:
        self.warning_calls: list[tuple[str, str]] = []
        self.error_calls: list[tuple[str, str]] = []
        self.info_calls: list[tuple[str, str]] = []

    def showwarning(self, title: str, message: str) -> None:
        self.warning_calls.append((title, message))

    def showerror(self, title: str, message: str) -> None:
        self.error_calls.append((title, message))

    def showinfo(self, title: str, message: str) -> None:
        self.info_calls.append((title, message))


class FakeTtk:
    def __init__(self) -> None:
        self.labels: list[FakeWidget] = []
        self.buttons: list[FakeWidget] = []
        self.label_frames: list[FakeWidget] = []

    def Frame(self, *args: object, **kwargs: object) -> FakeWidget:
        return FakeWidget(*args, **kwargs)

    def Label(self, *args: object, **kwargs: object) -> FakeWidget:
        widget = FakeWidget(*args, **kwargs)
        self.labels.append(widget)
        return widget

    def Button(self, *args: object, **kwargs: object) -> FakeWidget:
        widget = FakeWidget(*args, **kwargs)
        self.buttons.append(widget)
        return widget

    def LabelFrame(self, *args: object, **kwargs: object) -> FakeWidget:
        widget = FakeWidget(*args, **kwargs)
        self.label_frames.append(widget)
        return widget

    def Entry(self, *args: object, **kwargs: object) -> FakeWidget:
        return FakeWidget(*args, **kwargs)

    def Scrollbar(self, *args: object, **kwargs: object) -> FakeScrollbar:
        return FakeScrollbar(*args, **kwargs)

    def Progressbar(self, *args: object, **kwargs: object) -> FakeWidget:
        return FakeWidget(*args, **kwargs)


class GuiLocalizationTests(unittest.TestCase):
    def _make_app(self) -> tuple[ConverterApp, FakeRoot, FakeFileDialog, FakeMessageBox, FakeTtk]:
        root = FakeRoot()
        filedialog = FakeFileDialog()
        messagebox = FakeMessageBox()
        ttk = FakeTtk()
        app = ConverterApp(root, FakeTk, filedialog, messagebox, ttk)
        return app, root, filedialog, messagebox, ttk

    def test_converter_app_starts_tall_enough_to_show_log_area(self) -> None:
        _app, root, _filedialog, _messagebox, _ttk = self._make_app()

        self.assertEqual(root.window_geometry, "760x680")
        self.assertEqual(root.minimum_size, (680, 620))

    def test_converter_app_uses_chinese_layout_text(self) -> None:
        app, root, _filedialog, _messagebox, ttk = self._make_app()
        label_texts = [widget.options["text"] for widget in ttk.labels if "text" in widget.options]
        label_frame_texts = [widget.options["text"] for widget in ttk.label_frames if "text" in widget.options]

        self.assertEqual(root.window_title, "AMR 转 MP3 转换工具")
        self.assertEqual(app.status_var.get(), "就绪")
        self.assertEqual(
            [widget.options["text"] for widget in ttk.buttons],
            ["添加文件", "添加文件夹", "清空", "浏览", "浏览", "开始转换"],
        )
        self.assertIn("将 AMR 语音文件转换为 MP3", label_texts)
        self.assertIn("可选择单个 AMR 文件进行转换，也可选择多个文件或文件夹进行批量转换。", label_texts)
        self.assertIn("已选 AMR 文件", label_frame_texts)
        self.assertIn("输出设置", label_frame_texts)
        self.assertIn("日志", label_frame_texts)

    def test_start_conversion_without_files_shows_chinese_warning(self) -> None:
        app, _root, _filedialog, messagebox, _ttk = self._make_app()

        app.start_conversion()

        self.assertEqual(messagebox.warning_calls, [("未选择文件", "请先至少选择一个 AMR 文件。")])

    def test_handle_worker_complete_includes_failure_details_in_warning(self) -> None:
        app, _root, _filedialog, messagebox, _ttk = self._make_app()
        summary = BatchConversionSummary(
            results=[
                ConversionResult(
                    input_path=Path("ok.amr"),
                    output_path=Path("ok.mp3"),
                    succeeded=True,
                    command=("ffmpeg",),
                    return_code=0,
                    stdout="",
                    stderr="",
                ),
                ConversionResult(
                    input_path=Path("bad.amr"),
                    output_path=Path("bad.mp3"),
                    succeeded=False,
                    command=("ffmpeg",),
                    return_code=1,
                    stdout="",
                    stderr="invalid data found when processing input",
                ),
            ]
        )

        app._handle_worker_complete(summary)

        self.assertEqual(
            messagebox.warning_calls,
            [
                (
                    "转换完成，但有错误",
                    "成功 1 个，失败 1 个。\n\nbad.amr：invalid data found when processing input",
                )
            ],
        )

    def test_handle_worker_complete_falls_back_when_failure_has_no_stderr(self) -> None:
        app, _root, _filedialog, messagebox, _ttk = self._make_app()
        summary = BatchConversionSummary(
            results=[
                ConversionResult(
                    input_path=Path("silent.amr"),
                    output_path=Path("silent.mp3"),
                    succeeded=False,
                    command=("ffmpeg",),
                    return_code=7,
                    stdout="",
                    stderr="",
                )
            ]
        )

        app._handle_worker_complete(summary)

        self.assertEqual(
            messagebox.warning_calls,
            [
                (
                    "转换完成，但有错误",
                    "成功 0 个，失败 1 个。\n\nsilent.amr：转换失败（退出码 7）",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
