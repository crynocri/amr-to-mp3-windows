package ffmpeg

import (
	"fmt"
	"strings"
)

type FormatSpec struct {
	Name string
	Ext  string
	Args []string
}

var formatSpecs = map[string]FormatSpec{
	"mp3": {
		Name: "mp3",
		Ext:  "mp3",
		Args: []string{"-vn", "-codec:a", "libmp3lame", "-q:a", "2"},
	},
	"wav": {
		Name: "wav",
		Ext:  "wav",
		Args: []string{"-vn", "-codec:a", "pcm_s16le"},
	},
	"aac": {
		Name: "aac",
		Ext:  "aac",
		Args: []string{"-vn", "-codec:a", "aac", "-b:a", "192k"},
	},
	"m4a": {
		Name: "m4a",
		Ext:  "m4a",
		Args: []string{"-vn", "-codec:a", "aac", "-b:a", "192k"},
	},
}

func NormalizeTarget(raw string) (FormatSpec, error) {
	target := strings.ToLower(strings.TrimSpace(raw))
	spec, ok := formatSpecs[target]
	if !ok {
		return FormatSpec{}, fmt.Errorf("unsupported target format: %q", raw)
	}
	return spec, nil
}

func BuildConvertArgs(inputFile, outputFile, targetFormat string) ([]string, error) {
	spec, err := NormalizeTarget(targetFormat)
	if err != nil {
		return nil, err
	}

	args := []string{
		"-hide_banner",
		"-loglevel", "error",
		"-nostdin",
		"-i", inputFile,
	}
	args = append(args, spec.Args...)
	args = append(args, outputFile)
	return args, nil
}
