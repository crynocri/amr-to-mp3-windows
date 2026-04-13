//go:build windows

package tests_go

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/crynocri/amr-to-mp3-windows/internal/converter"
	"github.com/crynocri/amr-to-mp3-windows/internal/ffmpeg"
)

func TestRealFFmpegSmokeConversion(t *testing.T) {
	ffmpegPath, err := ffmpeg.ResolveExecutable("")
	if err != nil {
		t.Skipf("ffmpeg is not available: %v", err)
	}

	runner, err := ffmpeg.NewRunner(ffmpegPath)
	if err != nil {
		t.Fatalf("create ffmpeg runner: %v", err)
	}
	service, err := converter.NewService(runner, 2)
	if err != nil {
		t.Fatalf("create converter service: %v", err)
	}

	input := filepath.Join(t.TempDir(), "smoke.amr")
	minimalAMR := []byte{35, 33, 65, 77, 82, 10, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
	if err := os.WriteFile(input, minimalAMR, 0o644); err != nil {
		t.Fatalf("write smoke amr: %v", err)
	}

	result := service.ConvertFile(context.Background(), input, "mp3")
	if result.Err != nil {
		t.Fatalf("convert file failed: %v (stderr=%s)", result.Err, result.Stderr)
	}
	info, err := os.Stat(result.Output)
	if err != nil {
		t.Fatalf("expected output not found: %v", err)
	}
	if info.Size() <= 0 {
		t.Fatalf("output file is empty: %s", result.Output)
	}
}
