import os
from dataclasses import dataclass
from typing import Optional
import numpy as np
from .audio_io import load_audio, get_audio_info

@dataclass
class SongItem:
    filepath: str
    filename: str
    samples: np.ndarray
    fs: int
    duration_seconds: float
    channels: int
    start_pos: float = 0.0
    end_pos: float = 0.0

    def __post_init__(self):
        if self.end_pos <= 0.0 or self.end_pos > self.duration_seconds:
            self.end_pos = float(self.duration_seconds)
        self.start_pos = max(0.0, float(self.start_pos))

    @classmethod
    def from_file(cls, filepath: str) -> "SongItem":
        """Load an audio file and create a SongItem instance."""
        samples, fs = load_audio(filepath)
        info = get_audio_info(samples, fs)
        duration = float(info["duration_seconds"])
        channels = int(info["channels"])
        filename = os.path.basename(filepath)
        return cls(
            filepath=filepath,
            filename=filename,
            samples=samples,
            fs=fs,
            duration_seconds=duration,
            channels=channels,
            start_pos=0.0,
            end_pos=duration,
        )

    def set_range(self, start_pos: float, end_pos: float):
        """Safely set start and end trimming positions."""
        safe_start = max(0.0, min(float(start_pos), self.duration_seconds))
        safe_end = max(safe_start, min(float(end_pos), self.duration_seconds))
        self.start_pos = safe_start
        self.end_pos = safe_end

    def get_trimmed_samples(self) -> np.ndarray:
        """Returns the slice of audio samples between start_pos and end_pos."""
        start_frame = max(0, int(self.start_pos * self.fs))
        end_frame = min(len(self.samples), int(self.end_pos * self.fs))
        if start_frame >= end_frame:
            return self.samples
        return self.samples[start_frame:end_frame]

    @property
    def range_duration(self) -> float:
        """Duration of the selected range in seconds."""
        return max(0.0, self.end_pos - self.start_pos)

    @staticmethod
    def format_time(seconds: float) -> str:
        """Formats seconds into MM:SS.S string."""
        s = max(0.0, float(seconds))
        mins = int(s // 60)
        secs = int(s % 60)
        tenths = int((s - int(s)) * 10)
        return f"{mins:02d}:{secs:02d}.{tenths}"
