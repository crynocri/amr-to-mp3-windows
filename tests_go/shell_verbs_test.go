package tests_go

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/crynocri/amr-to-mp3-windows/internal/shell"
)

func TestParentRegistryKeyUsesHKCU(t *testing.T) {
	key := shell.ParentRegistryKey()
	if !strings.HasPrefix(key, `HKCU\Software\Classes\`) {
		t.Fatalf("context menu key should stay under HKCU for non-admin install, got: %s", key)
	}
	if !strings.Contains(key, `SystemFileAssociations\.amr\shell\`) {
		t.Fatalf("context menu key should target .amr system file associations, got: %s", key)
	}
}

func TestBuildCommandUsesSingleFilePlaceholder(t *testing.T) {
	cmd := shell.BuildCommand(`C:\Program Files\AMRToMP3\AMRToMP3.exe`, "mp3")
	if !strings.Contains(cmd, `convert --to mp3`) {
		t.Fatalf("command should include target format, got: %s", cmd)
	}
	if !strings.Contains(cmd, `--files "%1"`) {
		t.Fatalf("command should include %%1 file placeholder, got: %s", cmd)
	}
}

func TestContextMenuIconPathUsesBundledIconWhenPresent(t *testing.T) {
	tempDir := t.TempDir()
	exePath := filepath.Join(tempDir, "AMRToMP3.exe")
	iconDir := filepath.Join(tempDir, "assets")
	iconPath := filepath.Join(iconDir, "context-menu-logo.ico")

	if err := os.MkdirAll(iconDir, 0o755); err != nil {
		t.Fatalf("create icon dir: %v", err)
	}
	if err := os.WriteFile(iconPath, []byte("ico"), 0o644); err != nil {
		t.Fatalf("create icon file: %v", err)
	}

	resolved := shell.ContextMenuIconPath(exePath)
	if resolved != iconPath {
		t.Fatalf("icon path should prefer bundled icon, got: %s", resolved)
	}
}

func TestContextMenuIconPathFallsBackToExecutable(t *testing.T) {
	tempDir := t.TempDir()
	exePath := filepath.Join(tempDir, "AMRToMP3.exe")

	resolved := shell.ContextMenuIconPath(exePath)
	if resolved != exePath {
		t.Fatalf("icon path should fall back to executable when bundled icon is missing, got: %s", resolved)
	}
}
