package ffmpeg

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/crynocri/amr-to-mp3-windows/internal/config"
)

var ErrNotFound = errors.New("ffmpeg executable not found")

type Runner struct {
	Executable string
}

func NewRunner(executable string) (*Runner, error) {
	if executable == "" {
		return nil, fmt.Errorf("ffmpeg executable is empty")
	}
	return &Runner{Executable: executable}, nil
}

func ResolveExecutable(executableDir string) (string, error) {
	if executableDir != "" {
		bundled := filepath.Join(executableDir, "bin", "ffmpeg.exe")
		if fileExists(bundled) {
			return bundled, nil
		}
	}

	override := os.Getenv(config.EnvFFmpegOverride)
	if override != "" {
		if fileExists(override) {
			return override, nil
		}
		if resolved, err := exec.LookPath(override); err == nil {
			return resolved, nil
		}
	}

	if resolved, err := exec.LookPath("ffmpeg.exe"); err == nil {
		return resolved, nil
	}
	if resolved, err := exec.LookPath("ffmpeg"); err == nil {
		return resolved, nil
	}
	return "", ErrNotFound
}

func (r *Runner) Probe(ctx context.Context) error {
	cmd := exec.CommandContext(ctx, r.Executable, "-version")
	cmd.Stdout = io.Discard
	cmd.Stderr = io.Discard
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ffmpeg probe failed: %w", err)
	}
	return nil
}

func (r *Runner) Convert(ctx context.Context, inputFile, outputFile, targetFormat string) (string, error) {
	args, err := BuildConvertArgs(inputFile, outputFile, targetFormat)
	if err != nil {
		return "", err
	}

	cmd := exec.CommandContext(ctx, r.Executable, args...)
	cmd.Stdout = io.Discard
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return stderr.String(), fmt.Errorf("ffmpeg convert failed: %w", err)
	}
	return stderr.String(), nil
}

func fileExists(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	return !info.IsDir()
}
