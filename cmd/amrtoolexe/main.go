package main

import (
	"os"

	"github.com/crynocri/amr-to-mp3-windows/internal/app"
)

func main() {
	exitCode := app.Run(os.Args[1:], app.IOStreams{
		Stdout: os.Stdout,
		Stderr: os.Stderr,
	})
	os.Exit(exitCode)
}
