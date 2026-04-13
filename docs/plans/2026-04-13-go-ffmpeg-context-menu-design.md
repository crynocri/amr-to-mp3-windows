# Go + FFmpeg Windows Context Menu Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将当前 Python + Tkinter 版本重构为 Go 版本，并在 Windows 安装后支持“右键 -> 格式转换 -> 目标格式”二级菜单，完成 AMR 文件格式转换；以右键菜单为主产品形态，不保留旧 GUI。

**Architecture:** 采用“Go 主程序 + FFmpeg 子进程封装 + Windows 注册表右键菜单 + Setup 安装器”的组合。转换能力全部集中在 Go CLI/Service 层，GUI 不作为 Phase 1 必选项。上下文菜单通过安装器写入与清理，确保可卸载和可回滚。

**Tech Stack:** Go 1.23+, FFmpeg (vendored), Inno Setup (推荐), GitHub Actions Windows runner, PowerShell test scripts

## 1. 目标产品形态（与你描述对齐）

- 用户安装 `AMRToMP3-Setup.exe`
- 安装后在资源管理器中选中 `.amr` 文件，右键出现 `格式转换`
- 悬停/点击 `格式转换` 显示二级菜单（如 `转换为 MP3`、`转换为 WAV`）
- 点击目标格式后执行转换，默认输出到源文件同目录
- 支持多选文件批量转换
- 卸载时清理右键菜单注册项

## 2. 已确认技术路线

### 路线 A（已确认）: 静态右键级联菜单（Registry Verb）

- 实现：通过注册表写入静态 verb 与子命令
- 优点：实现快、稳定、纯 Go 即可落地、维护成本低
- 限制：在 Windows 11 上通常出现在“显示更多选项”中（传统菜单层）

### 明确不做（Phase 1）

- 不做 Win11 一级新菜单 COM 扩展（`IExplorerCommand`）
- 不保留 Python/Tkinter GUI 形态

## 3. 建议目录重构

### Task 1: 建立 Go 工程骨架

**Files:**
- Create: `go.mod`
- Create: `cmd/amrtoolexe/main.go`
- Create: `internal/app/run.go`
- Create: `internal/config/config.go`
- Create: `README.md`（迁移说明段落）

**Step 1:** 初始化 Go 模块与基础 CLI 入口
- 子命令：`convert`, `install-shell`, `uninstall-shell`, `probe`

**Step 2:** 定义统一错误码
- 例如：`0` 成功，`2` 参数错误，`3` ffmpeg 不可用，`4` 转换失败

**Step 3:** 提交最小可运行版本

### Task 2: FFmpeg 封装层（核心能力）

**Files:**
- Create: `internal/ffmpeg/runner.go`
- Create: `internal/ffmpeg/args.go`
- Create: `internal/converter/service.go`
- Create: `internal/converter/output.go`
- Create: `tests_go/ffmpeg_args_test.go`

**Step 1:** 统一 ffmpeg 查找顺序
- 安装目录 `bin/ffmpeg.exe`
- 环境变量 `AMR_TO_MP3_FFMPEG`
- PATH

**Step 2:** 实现格式映射
- `amr -> mp3/wav/aac/m4a`
- 输出命名冲突策略：自动递增，不覆盖（如 `name.mp3`, `name (1).mp3`, `name (2).mp3`）

**Step 3:** 支持批量转换
- Worker pool（默认并发 2-4）
- 汇总成功/失败结果

### Task 3: Windows 右键菜单（二级菜单）

**Files:**
- Create: `internal/shell/windows_registry.go`
- Create: `internal/shell/verbs.go`
- Create: `scripts/windows/assert-context-menu.ps1`

**Step 1:** 为 `.amr` 注册父级菜单
- 建议菜单文案：`格式转换`

**Step 2:** 注册子命令
- `转换为 MP3`
- `转换为 WAV`
- `转换为 AAC`
- `转换为 M4A`

**Step 3:** 子命令调用方式
- 命令模板：`"<InstallDir>\\AMRToMP3.exe" convert --to mp3 --files "%1"`
- 多选行为通过集成测试确认 `%1/%*` 策略

**Step 4:** 实现 uninstall 清理
- 仅删除本产品写入的 key，避免误删
- 安装范围限定为当前用户（`HKCU\Software\Classes`），无需管理员权限

### Task 4: Setup 安装器与卸载逻辑

**Files:**
- Create: `build/windows/installer.iss`
- Modify: `build/windows/build.ps1`
- Create: `build/windows/post-install.ps1`

**Step 1:** 生成 Setup 包
- 产物建议：`dist/AMRToMP3-Setup.exe`

**Step 2:** 安装时动作
- 安装 `AMRToMP3.exe`
- 安装 `ffmpeg.exe`
- 执行 `install-shell`

**Step 3:** 卸载时动作
- 执行 `uninstall-shell`
- 删除程序文件

### Task 5: CI/CD（保持你的 artifact 约定）

**Files:**
- Modify: `.github/workflows/windows-package.yml`
- Create: `tests_go/smoke_windows_test.go`
- Create: `scripts/windows/smoke-convert.ps1`

**Step 1:** 在 `windows-latest` 上构建 Go 二进制

**Step 2:** 运行自动化验证
- 单元测试（参数拼装/路径处理）
- 冒烟测试（真实 ffmpeg + 样例 amr）

**Step 3:** 上传 artifact
- 保持 artifact 名称：`AMRToMP3-windows`
- 打包内容建议：`AMRToMP3-Setup.exe` + `AMRToMP3.exe`（如你需要）

### Task 6: 迁移切换与回滚策略

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Keep (phase-out): `amr_to_mp3/**`（先保留，待并行验证后删除）

**Step 1:** 双轨期
- Python 版本与 Go 版本并行 1-2 个迭代

**Step 2:** 发布验证通过后再移除 Python 代码

**Step 3:** 保留回滚标签
- 若新版本问题可快速回切

## 4. 测试与验收标准

- 安装后右键 `.amr` 可见 `格式转换` 一级菜单
- 二级菜单可见目标格式项
- 单文件转换成功
- 多文件转换成功（至少 10 个样本）
- 异常文件给出可读错误信息
- 卸载后菜单项消失
- GitHub Actions 产物稳定可下载（`AMRToMP3-windows`）

## 5. 错误处理规范（待最终确认）

### 5.1 错误分层

- `E_PARAM`：命令参数错误（目标格式非法、未传文件）
- `E_INPUT_NOT_FOUND`：输入文件不存在/不可访问
- `E_INPUT_INVALID`：不是合法 AMR，或内容损坏
- `E_FFMPEG_NOT_FOUND`：找不到 `ffmpeg.exe`
- `E_FFMPEG_EXEC`：ffmpeg 运行失败（返回码非 0）
- `E_OUTPUT_IO`：输出目录无写权限或磁盘空间不足
- `E_PARTIAL`：批量任务部分成功部分失败

### 5.2 用户可见反馈（右键主形态）

- 单文件成功：静默成功，不弹窗
- 单文件失败：对话框显示“失败原因 + 输入文件名 + 错误码”
- 批量任务：结束后给汇总（成功 X，失败 Y）
- 若失败文件 > 3，弹窗仅显示前 3 条，完整明细写入日志

### 5.3 日志策略

- 默认日志目录：`%LOCALAPPDATA%\\AMRToMP3\\logs\\`
- 文件名：`convert-YYYYMMDD-HHMMSS.log`
- 记录字段：时间、输入文件、输出文件、ffmpeg 命令、退出码、stderr 摘要、错误码
- 日志保留：最近 30 天（安装后每次运行做轻量清理）

### 5.4 退出码约定（给 shell/CI 用）

- `0`：全部成功
- `10`：全部失败
- `11`：部分成功（仅批量）
- `2/3/4`：保留给参数与运行时基础错误（兼容前文约定）

## 6. 风险清单

1. Windows 11 一级右键菜单限制
- 若你要求“必须出现在一级新菜单”，需进入 COM 路线（复杂度提高）

2. FFmpeg 分发合规
- 需在安装包中附带 LICENSE 与来源说明

3. 多选参数传递差异
- `%1/%L/%*` 行为需在 Win10/Win11 实机验证

4. 杀软误报
- 建议后续加入签名（Code Signing）

## 7. 推荐里程碑（可执行）

- M1（2-3 天）: Go CLI + ffmpeg 封装可转换
- M2（2 天）: 右键菜单 + 子菜单 + 卸载清理
- M3（1-2 天）: Setup 打包与安装后联调
- M4（1-2 天）: CI 改造 + 冒烟测试 + 首次发布
