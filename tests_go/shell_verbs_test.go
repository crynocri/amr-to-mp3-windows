package tests_go

import (
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
