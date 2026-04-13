package app

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/crynocri/amr-to-mp3-windows/internal/config"
	"github.com/crynocri/amr-to-mp3-windows/internal/converter"
	"github.com/crynocri/amr-to-mp3-windows/internal/ffmpeg"
	"github.com/crynocri/amr-to-mp3-windows/internal/shell"
)

type IOStreams struct {
	Stdout io.Writer
	Stderr io.Writer
}

func Run(args []string, streams IOStreams) int {
	if streams.Stdout == nil {
		streams.Stdout = io.Discard
	}
	if streams.Stderr == nil {
		streams.Stderr = io.Discard
	}

	if len(args) == 0 {
		printUsage(streams.Stderr)
		return config.ExitCodeParam
	}

	switch args[0] {
	case "-h", "--help", "help":
		printUsage(streams.Stdout)
		return config.ExitCodeOK
	case "convert":
		return runConvert(args[1:], streams)
	case "install-shell":
		return runInstallShell(streams)
	case "uninstall-shell":
		return runUninstallShell(streams)
	case "probe":
		return runProbe(streams)
	default:
		fmt.Fprintf(streams.Stderr, "unknown subcommand: %s\n\n", args[0])
		printUsage(streams.Stderr)
		return config.ExitCodeParam
	}
}

func runConvert(args []string, streams IOStreams) int {
	fs := flag.NewFlagSet("convert", flag.ContinueOnError)
	fs.SetOutput(streams.Stderr)
	target := fs.String("to", "", "Target format. Example: mp3")
	files := fs.String("files", "", "Input files. Use ';' as separator.")
	workers := fs.Int("workers", 0, "Worker count for batch conversion. Default: auto (2-4).")

	if err := fs.Parse(args); err != nil {
		return config.ExitCodeParam
	}
	if strings.TrimSpace(*target) == "" {
		fmt.Fprintln(streams.Stderr, "missing required flag: --to")
		return config.ExitCodeParam
	}
	fileInputs := parseFileInputs(*files, fs.Args())
	if len(fileInputs) == 0 {
		fmt.Fprintln(streams.Stderr, "missing input files: pass --files or trailing file paths")
		return config.ExitCodeParam
	}

	executableDir := executableDirectory()
	ffmpegPath, err := ffmpeg.ResolveExecutable(executableDir)
	if err != nil {
		fmt.Fprintf(streams.Stderr, "ffmpeg not available: %v\n", err)
		return config.ExitCodeFFmpeg
	}

	runner, err := ffmpeg.NewRunner(ffmpegPath)
	if err != nil {
		fmt.Fprintf(streams.Stderr, "failed to initialize ffmpeg runner: %v\n", err)
		return config.ExitCodeFFmpeg
	}
	service, err := converter.NewService(runner, *workers)
	if err != nil {
		fmt.Fprintf(streams.Stderr, "failed to initialize converter service: %v\n", err)
		return config.ExitCodeConvert
	}

	result := service.ConvertBatch(context.Background(), fileInputs, *target)
	fmt.Fprintf(streams.Stdout, "conversion summary: success=%d failed=%d\n", result.SuccessCount(), result.FailureCount())
	for i, failure := range result.Failures {
		if i >= 3 {
			break
		}
		fmt.Fprintf(streams.Stderr, "failed: %s (%v)\n", failure.Input, failure.Err)
	}

	if result.FailureCount() == 0 {
		return config.ExitCodeOK
	}
	if result.SuccessCount() == 0 {
		return config.ExitCodeAllFailed
	}
	return config.ExitCodePartial
}

func runInstallShell(streams IOStreams) int {
	selfPath, err := os.Executable()
	if err != nil {
		fmt.Fprintf(streams.Stderr, "failed to resolve executable path: %v\n", err)
		return config.ExitCodeConvert
	}
	if err := shell.InstallContextMenu(selfPath, streams.Stdout); err != nil {
		fmt.Fprintf(streams.Stderr, "install-shell failed: %v\n", err)
		return config.ExitCodeConvert
	}
	return config.ExitCodeOK
}

func runUninstallShell(streams IOStreams) int {
	if err := shell.UninstallContextMenu(streams.Stdout); err != nil {
		fmt.Fprintf(streams.Stderr, "uninstall-shell failed: %v\n", err)
		return config.ExitCodeConvert
	}
	return config.ExitCodeOK
}

func runProbe(streams IOStreams) int {
	executableDir := executableDirectory()
	ffmpegPath, err := ffmpeg.ResolveExecutable(executableDir)
	if err != nil {
		fmt.Fprintf(streams.Stderr, "ffmpeg not available: %v\n", err)
		return config.ExitCodeFFmpeg
	}
	runner, err := ffmpeg.NewRunner(ffmpegPath)
	if err != nil {
		fmt.Fprintf(streams.Stderr, "failed to initialize ffmpeg runner: %v\n", err)
		return config.ExitCodeFFmpeg
	}
	if err := runner.Probe(context.Background()); err != nil {
		fmt.Fprintf(streams.Stderr, "ffmpeg probe failed: %v\n", err)
		return config.ExitCodeFFmpeg
	}
	fmt.Fprintf(streams.Stdout, "ffmpeg ok: %s\n", ffmpegPath)
	return config.ExitCodeOK
}

func printUsage(w io.Writer) {
	fmt.Fprintf(w, `%s

Usage:
  AMRToMP3 <subcommand> [flags]

Subcommands:
  convert          Convert .amr files to another format
  install-shell    Install Windows shell context menu
  uninstall-shell  Remove Windows shell context menu
  probe            Check ffmpeg availability
`, config.AppName)
}

func parseFileInputs(filesFlag string, trailing []string) []string {
	if strings.TrimSpace(filesFlag) == "" {
		return compactInputs(trailing)
	}
	parts := strings.Split(filesFlag, ";")
	return compactInputs(parts)
}

func compactInputs(inputs []string) []string {
	out := make([]string, 0, len(inputs))
	for _, input := range inputs {
		trimmed := strings.TrimSpace(strings.Trim(input, `"`))
		if trimmed == "" {
			continue
		}
		out = append(out, trimmed)
	}
	return out
}

func executableDirectory() string {
	selfPath, err := os.Executable()
	if err != nil {
		return ""
	}
	return filepath.Dir(selfPath)
}
