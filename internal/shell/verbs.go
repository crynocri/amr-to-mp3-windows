package shell

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const (
	parentMenuLabel          = "格式转换"
	parentMenuKey            = "AMRToMP3.Convert"
	contextMenuIconFileName  = "context-menu-logo.ico"
	contextMenuIconDirectory = "assets"
	parentRegistryHK         = `HKCU\Software\Classes\SystemFileAssociations\.amr\shell\` + parentMenuKey
)

type Verb struct {
	KeyName      string
	MenuLabel    string
	TargetFormat string
}

func defaultVerbs() []Verb {
	return []Verb{
		{KeyName: "to_mp3", MenuLabel: "转换为 MP3", TargetFormat: "mp3"},
		{KeyName: "to_wav", MenuLabel: "转换为 WAV", TargetFormat: "wav"},
		{KeyName: "to_aac", MenuLabel: "转换为 AAC", TargetFormat: "aac"},
		{KeyName: "to_m4a", MenuLabel: "转换为 M4A", TargetFormat: "m4a"},
	}
}

func ParentRegistryKey() string {
	return parentRegistryHK
}

func ParentMenuLabel() string {
	return parentMenuLabel
}

func ContextMenuIconPath(executablePath string) string {
	if strings.TrimSpace(executablePath) == "" {
		return ""
	}

	iconPath := filepath.Join(filepath.Dir(executablePath), contextMenuIconDirectory, contextMenuIconFileName)
	if _, err := os.Stat(iconPath); err == nil {
		return iconPath
	}
	return executablePath
}

func BuildCommand(executablePath, targetFormat string) string {
	return fmt.Sprintf(`"%s" convert --to %s --files "%%1"`, executablePath, targetFormat)
}
