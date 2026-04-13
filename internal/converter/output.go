package converter

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/crynocri/amr-to-mp3-windows/internal/ffmpeg"
)

func NextAvailableOutput(inputFile, targetFormat string) (string, error) {
	spec, err := ffmpeg.NormalizeTarget(targetFormat)
	if err != nil {
		return "", err
	}

	dir := filepath.Dir(inputFile)
	stem := strings.TrimSuffix(filepath.Base(inputFile), filepath.Ext(inputFile))
	ext := "." + spec.Ext

	for i := 0; ; i++ {
		name := stem
		if i > 0 {
			name = fmt.Sprintf("%s (%d)", stem, i)
		}

		out := filepath.Join(dir, name+ext)
		_, statErr := os.Stat(out)
		if errors.Is(statErr, os.ErrNotExist) {
			return out, nil
		}
		if statErr != nil {
			return "", fmt.Errorf("check output conflict: %w", statErr)
		}
	}
}
