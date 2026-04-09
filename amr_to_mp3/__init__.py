"""AMR to MP3 desktop converter package."""

from .converter import (
    BatchConversionSummary,
    ConversionError,
    ConversionResult,
    ConversionTask,
    convert_batch,
    convert_file,
    plan_batch,
    plan_conversion,
    resolve_ffmpeg_binary,
)

__all__ = [
    "BatchConversionSummary",
    "ConversionError",
    "ConversionResult",
    "ConversionTask",
    "convert_batch",
    "convert_file",
    "plan_batch",
    "plan_conversion",
    "resolve_ffmpeg_binary",
]
