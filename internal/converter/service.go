package converter

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"

	"github.com/crynocri/amr-to-mp3-windows/internal/ffmpeg"
)

var (
	ErrInputNotFound = errors.New("input file does not exist")
	ErrInputInvalid  = errors.New("input file is not an amr audio")
)

type FileResult struct {
	Input  string
	Output string
	Err    error
	Stderr string
}

type BatchResult struct {
	Successes []FileResult
	Failures  []FileResult
}

func (r BatchResult) SuccessCount() int {
	return len(r.Successes)
}

func (r BatchResult) FailureCount() int {
	return len(r.Failures)
}

type Service struct {
	runner  *ffmpeg.Runner
	workers int
}

func NewService(runner *ffmpeg.Runner, workers int) (*Service, error) {
	if runner == nil {
		return nil, errors.New("runner is required")
	}

	if workers <= 0 {
		workers = defaultWorkers()
	}
	if workers < 1 {
		workers = 1
	}
	if workers > 8 {
		workers = 8
	}

	return &Service{runner: runner, workers: workers}, nil
}

func (s *Service) ConvertFile(ctx context.Context, inputFile, targetFormat string) FileResult {
	result := FileResult{Input: inputFile}

	normalizedInput := strings.TrimSpace(inputFile)
	if normalizedInput == "" {
		result.Err = ErrInputNotFound
		return result
	}

	if strings.ToLower(filepath.Ext(normalizedInput)) != ".amr" {
		result.Err = ErrInputInvalid
		return result
	}

	if _, err := os.Stat(normalizedInput); err != nil {
		if errors.Is(err, os.ErrNotExist) {
			result.Err = ErrInputNotFound
			return result
		}
		result.Err = fmt.Errorf("access input file: %w", err)
		return result
	}

	outputFile, err := NextAvailableOutput(normalizedInput, targetFormat)
	if err != nil {
		result.Err = err
		return result
	}

	stderr, err := s.runner.Convert(ctx, normalizedInput, outputFile, targetFormat)
	result.Stderr = stderr
	result.Output = outputFile
	if err != nil {
		result.Err = err
	}
	return result
}

func (s *Service) ConvertBatch(ctx context.Context, inputFiles []string, targetFormat string) BatchResult {
	type job struct {
		index int
		input string
	}
	type indexedResult struct {
		index  int
		result FileResult
	}

	if len(inputFiles) == 0 {
		return BatchResult{}
	}

	jobCh := make(chan job)
	resultCh := make(chan indexedResult, len(inputFiles))

	workerCount := s.workers
	if workerCount > len(inputFiles) {
		workerCount = len(inputFiles)
	}

	var wg sync.WaitGroup
	for i := 0; i < workerCount; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobCh {
				resultCh <- indexedResult{
					index:  j.index,
					result: s.ConvertFile(ctx, j.input, targetFormat),
				}
			}
		}()
	}

	for i, input := range inputFiles {
		jobCh <- job{index: i, input: input}
	}
	close(jobCh)

	wg.Wait()
	close(resultCh)

	ordered := make([]indexedResult, 0, len(inputFiles))
	for r := range resultCh {
		ordered = append(ordered, r)
	}
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].index < ordered[j].index
	})

	batch := BatchResult{
		Successes: make([]FileResult, 0, len(inputFiles)),
		Failures:  make([]FileResult, 0),
	}
	for _, item := range ordered {
		if item.result.Err != nil {
			batch.Failures = append(batch.Failures, item.result)
			continue
		}
		batch.Successes = append(batch.Successes, item.result)
	}

	return batch
}

func defaultWorkers() int {
	candidates := runtime.NumCPU() / 2
	if candidates < 2 {
		return 2
	}
	if candidates > 4 {
		return 4
	}
	return candidates
}
