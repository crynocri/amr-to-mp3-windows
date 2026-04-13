package tests_go

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func readFileForTest(t *testing.T, relPath string) string {
	t.Helper()

	_, thisFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatalf("resolve caller path failed")
	}
	repoRoot := filepath.Dir(filepath.Dir(thisFile))
	path := filepath.Join(repoRoot, filepath.FromSlash(relPath))

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v", path, err)
	}
	return string(data)
}

func assertScriptParamBlockFirst(t *testing.T, scriptPath string) {
	t.Helper()
	content := readFileForTest(t, scriptPath)
	lines := strings.Split(content, "\n")
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" {
			continue
		}
		if strings.HasPrefix(trimmed, "#") {
			continue
		}
		if !strings.HasPrefix(trimmed, "param(") {
			t.Fatalf("%s should start with param(...) before any executable statements; first statement was %q", scriptPath, trimmed)
		}
		return
	}
	t.Fatalf("%s should contain a param(...) block", scriptPath)
}

func TestInstallerOutputsSetupExe(t *testing.T) {
	installer := readFileForTest(t, "build/windows/installer.iss")

	if !strings.Contains(installer, "OutputBaseFilename=AMRToMP3-Setup") {
		t.Fatalf("installer should output AMRToMP3-Setup.exe")
	}
	if strings.Contains(installer, "DefaultLanguage=") {
		t.Fatalf("installer should not use unsupported DefaultLanguage directive")
	}
	if !strings.Contains(installer, "LanguageDetectionMethod=none") {
		t.Fatalf("installer should disable auto language detection to default to first language entry")
	}
	if !strings.Contains(installer, "ShowLanguageDialog=no") {
		t.Fatalf("installer should suppress language dialog")
	}
	if !strings.Contains(installer, "Name: \"chinesesimplified\"; MessagesFile: \"languages\\ChineseSimplified.isl\"") {
		t.Fatalf("installer should list Chinese language entry")
	}
	if !strings.Contains(installer, "Name: \"english\"; MessagesFile: \"compiler:Default.isl\"") {
		t.Fatalf("installer should list English language entry")
	}
	chineseIdx := strings.Index(installer, "Name: \"chinesesimplified\"; MessagesFile: \"languages\\ChineseSimplified.isl\"")
	englishIdx := strings.Index(installer, "Name: \"english\"; MessagesFile: \"compiler:Default.isl\"")
	if chineseIdx == -1 || englishIdx == -1 || chineseIdx > englishIdx {
		t.Fatalf("installer should place Chinese language before English to make Chinese the default")
	}
	if !strings.Contains(installer, `MessagesFile: "languages\ChineseSimplified.isl"`) {
		t.Fatalf("installer should load Chinese language file from project")
	}
	for _, token := range []string{
		"#ifndef TargetArch",
		"#define TargetArch \"amd64\"",
		"InstallerArchitecturesAllowed",
		"InstallerArchitecturesInstallMode",
		"ArchitecturesAllowed={#InstallerArchitecturesAllowed}",
		"ArchitecturesInstallIn64BitMode={#InstallerArchitecturesInstallMode}",
	} {
		if !strings.Contains(installer, token) {
			t.Fatalf("installer should contain %q", token)
		}
	}
	if !strings.Contains(installer, `Parameters: "install-shell"`) {
		t.Fatalf("installer should call install-shell on install")
	}
	if !strings.Contains(installer, `Parameters: "uninstall-shell"`) {
		t.Fatalf("installer should call uninstall-shell on uninstall")
	}
}

func TestWorkflowRunsGoBuildPipeline(t *testing.T) {
	workflow := readFileForTest(t, ".github/workflows/windows-package.yml")

	for _, token := range []string{
		"matrix:",
		"goarch: amd64",
		"goarch: arm64",
		"actions/setup-go",
		"go test ./...",
		`build\windows\build.ps1`,
		"-TargetArch",
		`scripts\windows\assert-context-menu.ps1`,
		`scripts\windows\smoke-convert.ps1`,
		"install-shell",
		"uninstall-shell",
		"AMRToMP3-Setup.exe",
		"AMRToMP3-windows-x64",
		"AMRToMP3-windows-arm64",
	} {
		if !strings.Contains(workflow, token) {
			t.Fatalf("workflow should contain %q", token)
		}
	}
}

func TestWorkflowUsesRealChocolateyFfmpegBinary(t *testing.T) {
	workflow := readFileForTest(t, ".github/workflows/windows-package.yml")

	if strings.Contains(workflow, `C:\ProgramData\chocolatey\bin\ffmpeg.exe`) {
		t.Fatalf("workflow should not use chocolatey shim path")
	}
	if !strings.Contains(workflow, `C:\ProgramData\chocolatey\lib\ffmpeg`) {
		t.Fatalf("workflow should use real ffmpeg binary under chocolatey lib directory")
	}
}

func TestBuildScriptUsesGoAndInnoSetup(t *testing.T) {
	buildScript := readFileForTest(t, "build/windows/build.ps1")

	for _, token := range []string{
		"[ValidateSet(\"amd64\", \"arm64\")]",
		"$TargetArch",
		"$env:GOARCH = $TargetArch",
		"\"/DTargetArch=$TargetArch\"",
		"$bundledFfmpeg",
		"-version",
		"$versionOutput = & $bundledFfmpeg -version 2>&1",
		"go build",
		"iscc",
	} {
		if !strings.Contains(buildScript, token) {
			t.Fatalf("build script should contain %q", token)
		}
	}
}

func TestPackageLocalPassesTargetArchToBuildScript(t *testing.T) {
	packageScript := readFileForTest(t, "build/windows/package-local.ps1")

	for _, token := range []string{
		"[ValidateSet(\"amd64\", \"arm64\")]",
		"$TargetArch",
		"-TargetArch",
		"-File $buildScript",
	} {
		if !strings.Contains(packageScript, token) {
			t.Fatalf("package-local script should contain %q", token)
		}
	}
}

func TestWindowsHelperScriptsDeclareParamBlockFirst(t *testing.T) {
	assertScriptParamBlockFirst(t, "scripts/windows/smoke-convert.ps1")
	assertScriptParamBlockFirst(t, "scripts/windows/assert-context-menu.ps1")
}
