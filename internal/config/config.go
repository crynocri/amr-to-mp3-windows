package config

const (
	ExitCodeOK        = 0
	ExitCodeParam     = 2
	ExitCodeFFmpeg    = 3
	ExitCodeConvert   = 4
	ExitCodeAllFailed = 10
	ExitCodePartial   = 11
)

const (
	AppName           = "AMRToMP3"
	EnvFFmpegOverride = "AMR_TO_MP3_FFMPEG"
)
