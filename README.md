# AMR to MP3 Converter (Windows)

面向 Windows 的 AMR 音频格式转换工具。当前主线实现为 **Go CLI + FFmpeg + 资源管理器右键菜单 + Inno Setup 安装器**。

## 当前实现状态

- 主入口：`cmd/amrtoolexe/main.go`
- 已支持子命令：`convert`、`probe`、`install-shell`、`uninstall-shell`
- Windows 右键菜单安装范围：`HKCU\Software\Classes`（当前用户，无需管理员）
- 打包产物：`dist/AMRToMP3.exe` 与 `dist/AMRToMP3-Setup.exe`
- GitHub Actions artifact 名称保持为：`AMRToMP3-windows`

## 功能说明（Go 主线）

### 转换能力

- 输入格式：`.amr`
- 目标格式：`mp3`、`wav`、`aac`、`m4a`
- 批量转换：支持（`--files` 使用 `;` 分隔，或传入多个尾随文件参数）
- 并发：默认自动 2-4 个 worker（可通过 `--workers` 指定）
- 输出冲突策略：自动递增命名，不覆盖已有文件（例如 `name.mp3`、`name (1).mp3`）

### 右键菜单

- 父菜单：`格式转换`
- 子菜单：`转换为 MP3/WAV/AAC/M4A`
- 当前命令模板使用 `"%1"` 占位符（单次调用单文件）
- 安装器会在安装时执行 `install-shell`，卸载时执行 `uninstall-shell`
- Setup 安装界面默认中文（`chinesesimplified`）

## 快速使用（开发态）

```bash
# 查看帮助
go run ./cmd/amrtoolexe --help

# 检测 ffmpeg 可用性
go run ./cmd/amrtoolexe probe

# 转换单文件
go run ./cmd/amrtoolexe convert --to mp3 --files "C:\path\voice.amr"

# 转换多文件（; 分隔）
go run ./cmd/amrtoolexe convert --to wav --files "C:\a.amr;C:\b.amr"
```

在非 Windows 系统上，`install-shell` / `uninstall-shell` 会返回不支持错误，这是预期行为。

## FFmpeg 查找顺序

程序按以下顺序查找 ffmpeg：

1. 可执行文件目录下的 `bin/ffmpeg.exe`
2. 环境变量 `AMR_TO_MP3_FFMPEG`
3. 系统 `PATH` 中的 `ffmpeg.exe` / `ffmpeg`

## Windows 打包

### 构建依赖

- Go（`go.mod` 当前声明 `go 1.23`）
- Inno Setup（`iscc` 可执行）
- `vendor/ffmpeg/ffmpeg.exe`（可运行的真实二进制）

### 构建命令

```powershell
powershell -ExecutionPolicy Bypass -File .\build\windows\build.ps1
```

说明：

- 默认目标架构：`amd64`（对应客户常见 x64 Windows 环境）
- 可选 `-TargetArch arm64` 构建 ARM64 Windows 包
- 即使构建机是 ARM，也可以交叉编译产出 `amd64` 可执行文件

### 一键本地打包（Windows）

```powershell
powershell -ExecutionPolicy Bypass -File .\build\windows\package-local.ps1 -InstallTools
```

可选参数：

- `-SkipTests`：跳过 Go 测试后直接打包
- `-InstallTools`：自动安装缺失的 Go / Inno Setup / ffmpeg
- `-TargetArch amd64|arm64`：指定目标 Windows 架构（默认 `amd64`）

示例（ARM 构建机为客户打 x64 包）：

```powershell
powershell -ExecutionPolicy Bypass -File .\build\windows\package-local.ps1 -InstallTools -TargetArch amd64
```

### 产物

```text
dist/AMRToMP3.exe
dist/AMRToMP3-Setup.exe
```

## CI/CD

工作流：`.github/workflows/windows-package.yml`

主要步骤：

- 使用 matrix 构建 `amd64(x64)` 与 `arm64` 两套包
- Windows runner 安装 Go、Inno Setup、ffmpeg
- 执行 `go test ./...`
- 执行 `build/windows/build.ps1 -TargetArch <arch>`
- 仅在 `amd64` 上执行 `scripts/windows/assert-context-menu.ps1`（右键菜单冒烟）
- 仅在 `amd64` 上执行 `scripts/windows/smoke-convert.ps1`
- 上传 artifact：
  - `AMRToMP3-windows-x64`
  - `AMRToMP3-windows-arm64`

## 测试与验证

```bash
# Go 测试（含 tests_go）
go test ./...
```

## 当前状态

- Python 版本代码已下线
- 当前发布主线为 Go + Inno Setup

## 回滚策略

- 发布前保留回滚标签（例如 `pre-go-migration-2026-04-13`）
- 若新版本出现关键问题，优先回切到最近稳定标签
- 回滚后继续保持 artifact 名称 `AMRToMP3-windows`，减少分发链路变化
