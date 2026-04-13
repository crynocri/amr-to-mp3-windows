package tests_go

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/crynocri/amr-to-mp3-windows/internal/config"
	"github.com/crynocri/amr-to-mp3-windows/internal/converter"
	"github.com/crynocri/amr-to-mp3-windows/internal/ffmpeg"
)

func TestBuildConvertArgsForMP3(t *testing.T) {
	args, err := ffmpeg.BuildConvertArgs("in.amr", "out.mp3", "mp3")
	if err != nil {
		t.Fatalf("BuildConvertArgs returned error: %v", err)
	}

	joined := filepath.ToSlash(joinArgs(args))
	if !strings.Contains(joined, "-i in.amr") {
		t.Fatalf("args should include input, got: %v", args)
	}
	if !strings.Contains(joined, "libmp3lame") {
		t.Fatalf("args should include mp3 codec settings, got: %v", args)
	}
	if !strings.Contains(joined, "out.mp3") {
		t.Fatalf("args should include output, got: %v", args)
	}
}

func TestBuildConvertArgsRejectsUnsupportedFormat(t *testing.T) {
	_, err := ffmpeg.BuildConvertArgs("in.amr", "out.flac", "flac")
	if err == nil {
		t.Fatalf("expected unsupported format error")
	}
}

func TestNextAvailableOutputAppendsIncrementalSuffix(t *testing.T) {
	tempDir := t.TempDir()
	input := filepath.Join(tempDir, "sample.amr")
	if err := os.WriteFile(input, []byte("fake"), 0o644); err != nil {
		t.Fatalf("write input: %v", err)
	}

	first := filepath.Join(tempDir, "sample.mp3")
	second := filepath.Join(tempDir, "sample (1).mp3")
	if err := os.WriteFile(first, []byte("a"), 0o644); err != nil {
		t.Fatalf("write first output: %v", err)
	}
	if err := os.WriteFile(second, []byte("b"), 0o644); err != nil {
		t.Fatalf("write second output: %v", err)
	}

	got, err := converter.NextAvailableOutput(input, "mp3")
	if err != nil {
		t.Fatalf("NextAvailableOutput returned error: %v", err)
	}
	want := filepath.Join(tempDir, "sample (2).mp3")
	if got != want {
		t.Fatalf("unexpected output path, want=%s got=%s", want, got)
	}
}

func TestResolveExecutablePrefersBundledBinary(t *testing.T) {
	tempDir := t.TempDir()
	binDir := filepath.Join(tempDir, "bin")
	if err := os.MkdirAll(binDir, 0o755); err != nil {
		t.Fatalf("mkdir bin: %v", err)
	}
	bundled := filepath.Join(binDir, "ffmpeg.exe")
	if err := os.WriteFile(bundled, []byte("fake"), 0o755); err != nil {
		t.Fatalf("write bundled binary: %v", err)
	}

	override := filepath.Join(tempDir, "custom-ffmpeg.exe")
	if err := os.WriteFile(override, []byte("fake"), 0o755); err != nil {
		t.Fatalf("write env override binary: %v", err)
	}
	t.Setenv(config.EnvFFmpegOverride, override)

	got, err := ffmpeg.ResolveExecutable(tempDir)
	if err != nil {
		t.Fatalf("ResolveExecutable returned error: %v", err)
	}
	if got != bundled {
		t.Fatalf("expected bundled binary to win, want=%s got=%s", bundled, got)
	}
}

func joinArgs(args []string) string {
	if len(args) == 0 {
		return ""
	}
	out := args[0]
	for i := 1; i < len(args); i++ {
		out += " " + args[i]
	}
	return out
}
