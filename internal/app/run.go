package app

import (
	"flag"
	"fmt"
	"io"
	"strings"

	"github.com/crynocri/amr-to-mp3-windows/internal/config"
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

	if err := fs.Parse(args); err != nil {
		return config.ExitCodeParam
	}
	if strings.TrimSpace(*target) == "" {
		fmt.Fprintln(streams.Stderr, "missing required flag: --to")
		return config.ExitCodeParam
	}
	if strings.TrimSpace(*files) == "" {
		fmt.Fprintln(streams.Stderr, "missing required flag: --files")
		return config.ExitCodeParam
	}

	fmt.Fprintln(streams.Stderr, "convert is not implemented yet")
	return config.ExitCodeConvert
}

func runInstallShell(streams IOStreams) int {
	fmt.Fprintln(streams.Stderr, "install-shell is not implemented yet")
	return config.ExitCodeConvert
}

func runUninstallShell(streams IOStreams) int {
	fmt.Fprintln(streams.Stderr, "uninstall-shell is not implemented yet")
	return config.ExitCodeConvert
}

func runProbe(streams IOStreams) int {
	fmt.Fprintln(streams.Stderr, "probe is not implemented yet")
	return config.ExitCodeFFmpeg
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
