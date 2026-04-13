# AMR to MP3 Converter

面向普通用户的桌面版 AMR 转 MP3 工具，优先为 Windows 使用场景设计。

## Go 重构迁移状态（进行中）

- 已新增 Go CLI 工程骨架，入口位于 `cmd/amrtoolexe/main.go`
- 当前已定义子命令：`convert`、`install-shell`、`uninstall-shell`、`probe`
- 统一退出码已定义在 `internal/config/config.go`
- 现阶段仍以 Python 版本为可用版本，Go 版本将在后续任务中补齐 FFmpeg 转换与 Windows 右键集成能力

快速体验 Go 入口（开发中）：

```bash
go run ./cmd/amrtoolexe --help
```

## 当前发布策略（双轨）

- **Go + FFmpeg + 右键菜单** 是新主线（Phase 1 目标形态）
- **Python GUI 版本** 暂时保留，作为迁移期间回归对照与紧急回退路径
- 计划在 1-2 个迭代内并行验证后，再执行 Python 代码下线

## 已实现的最小可用版本

- 桌面 GUI，默认启动图形界面
- 支持单文件转换
- 支持批量转换
- 输入 `.amr`，输出同名 `.mp3`
- 可选自定义输出目录
- 可选手动指定 `ffmpeg` 可执行文件路径
- 自动记录转换日志并汇总成功/失败数量

## 推荐分发方式

当前推荐使用 **Go 二进制 + Inno Setup 安装器** 发布 Windows 版本，并将 `ffmpeg.exe` 放入安装目录 `bin\ffmpeg.exe`。

这样普通用户只需要安装 `AMRToMP3-Setup.exe`，安装后可通过资源管理器右键菜单执行转换。安装器会负责注册/卸载右键菜单。

说明：旧的 PyInstaller onefile 流程仍保留在仓库历史中，便于双轨阶段回归验证。

## Go 版本核心命令

```bash
# 检测 ffmpeg 可用性
go run ./cmd/amrtoolexe probe

# 单文件转换（输出到源文件同目录）
go run ./cmd/amrtoolexe convert --to mp3 --files "C:\path\voice.amr"

# 安装/卸载右键菜单（Windows）
go run ./cmd/amrtoolexe install-shell
go run ./cmd/amrtoolexe uninstall-shell
```

## 运行方式

### 方式 1：直接运行已打包的 Windows 版本

前提：
- 使用 Windows 构建出的 `dist/AMRToMP3.exe`
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
dist/AMRToMP3.exe
```

核心产物通常包括：

```text
dist/AMRToMP3.exe
```

## 依赖说明

### 运行时依赖

对最终 Windows 用户：

- 推荐使用已打包好的桌面版
- 不需要单独安装 Python
- 如果 `ffmpeg.exe` 已经随应用一起打包，则不需要额外安装 ffmpeg。单文件模式下，程序会在运行时临时解包该依赖。

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
go test ./...
python3 -m unittest discover -s tests -v
```

单独执行 Go 的 FFmpeg 参数与转换相关测试：

```bash
go test ./tests_go -v
```

单独执行 Python 旧版回归测试：

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

## 回滚策略（发布级）

- 在 Go 主线发布前，保留可回退标签（示例：`pre-go-migration-2026-04-13`）
- 若线上发现关键问题，可先回切到最近稳定标签，再继续修复 Go 分支
- 回滚后仍保持 artifact 名称 `AMRToMP3-windows`，降低分发链路变更风险
