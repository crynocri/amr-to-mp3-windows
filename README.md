# AMR to MP3 Converter

面向普通用户的桌面版 AMR 转 MP3 工具，优先为 Windows 使用场景设计。

## 已实现的最小可用版本

- 桌面 GUI，默认启动图形界面
- 支持单文件转换
- 支持批量转换
- 输入 `.amr`，输出同名 `.mp3`
- 可选自定义输出目录
- 可选手动指定 `ffmpeg` 可执行文件路径
- 自动记录转换日志并汇总成功/失败数量

## 推荐分发方式

推荐使用 **PyInstaller one-folder** 打包为 Windows 桌面应用，并将 `ffmpeg.exe` 一起打包进分发目录。

这样普通用户只需要解压后双击 `AMRToMP3.exe`，不需要额外安装 Python，也不需要手动配置命令行环境。

## 运行方式

### 方式 1：直接运行已打包的 Windows 版本

前提：
- 使用 Windows 构建出的 `dist/AMRToMP3/` 分发目录
- 目录内包含 `AMRToMP3.exe`
- 若构建时已打包 `ffmpeg.exe`，用户无需额外安装 ffmpeg

运行：

1. 双击 `AMRToMP3.exe`
2. 点击 `Add Files` 选择一个或多个 `.amr` 文件
3. 或点击 `Add Folder` 导入某个目录下的 `.amr` 文件
4. 可选设置输出目录；不设置时默认输出到原文件所在目录
5. 点击 `Convert to MP3`

### 方式 2：开发模式运行

前提：
- Python 3.11+
- Python 发行版带 Tkinter
- 本机已安装 `ffmpeg`，或者设置环境变量 `AMR_TO_MP3_FFMPEG`

启动：

```bash
python3 -m amr_to_mp3
```

查看帮助：

```bash
python3 -m amr_to_mp3 --help
```

## 构建方式

Windows 上构建更稳妥，因为：

- 官方 Windows Python 通常自带 Tkinter
- PyInstaller 的最终产物应当在目标平台构建
- 需要一起验证 `ffmpeg.exe` 的捆绑行为

### 1. 准备依赖

必需项：
- Windows
- Python 3.11 或更高版本，建议使用官方安装包
- `pip`
- `PyInstaller`
- `ffmpeg.exe`

安装 PyInstaller：

```powershell
py -m pip install pyinstaller
```

准备 ffmpeg：

1. 下载 Windows 版 `ffmpeg.exe`
2. 放到仓库路径 `vendor/ffmpeg/ffmpeg.exe`

### 2. 运行构建脚本

```powershell
powershell -ExecutionPolicy Bypass -File .\build\windows\build.ps1
```

### 3. 产物位置

默认输出目录：

```text
dist/AMRToMP3/
```

核心文件通常包括：

```text
dist/AMRToMP3/AMRToMP3.exe
dist/AMRToMP3/ffmpeg.exe
```

## 依赖说明

### 运行时依赖

对最终 Windows 用户：

- 推荐使用已打包好的桌面版
- 不需要单独安装 Python
- 如果 `ffmpeg.exe` 已经随应用一起打包，则不需要额外安装 ffmpeg

对开发者：

- Python 3.11+
- Tkinter
- ffmpeg

### 构建时依赖

- PyInstaller
- Windows 版 `ffmpeg.exe`

## ffmpeg 查找顺序

程序按下面顺序寻找 ffmpeg：

1. 环境变量 `AMR_TO_MP3_FFMPEG`
2. 打包后的应用目录中的 `ffmpeg.exe`
3. PyInstaller 解包目录中的 `ffmpeg.exe`
4. 系统 `PATH` 中的 `ffmpeg`

## 自测方式

运行自动化测试：

```bash
python3 -m unittest discover -s tests -v
```

单独执行真实 ffmpeg 冒烟测试：

```bash
python3 -m unittest tests.test_converter.ConverterSmokeTests.test_real_ffmpeg_smoke_conversion -v
```

## 当前限制

- 当前仓库中的 GUI 使用 Tkinter。若开发机 Python 缺少 Tk 支持，`python3 -m amr_to_mp3` 会给出明确错误提示。
- 本次交付已在当前机器完成核心转换和入口层自动化验证，但 **Windows GUI 实际点选流程** 仍需在带 Tk 的 Windows 环境做一次人工确认。
- 批量导入目录当前为非递归模式，只导入所选目录下的 `.amr` 文件。
