import io
import os
from typing import Tuple, Dict, Any, Union
import numpy as np
import soundfile as sf
from pydub import AudioSegment

def load_audio(
    file_source: Union[str, io.BytesIO, bytes], 
    target_fs: int = None, 
    to_mono: bool = False
) -> Tuple[np.ndarray, int]:
    """
    Loads audio from a file path, BytesIO, or raw bytes.
    Returns:
        samples (np.ndarray): float32 array normalized to [-1.0, 1.0].
                              Shape is (N,) for mono or (N, channels) for stereo.
        fs (int): Sample rate in Hz.
    """
    try:
        # Try soundfile first (fastest for wav, flac, ogg)
        if isinstance(file_source, bytes):
            file_source = io.BytesIO(file_source)
        
        samples, fs = sf.read(file_source, dtype="float32")
    except Exception:
        # Fallback to pydub (handles mp3, m4a, aac via ffmpeg)
        if isinstance(file_source, io.BytesIO):
            file_source.seek(0)
            audio = AudioSegment.from_file(file_source)
        elif isinstance(file_source, bytes):
            audio = AudioSegment.from_file(io.BytesIO(file_source))
        else:
            audio = AudioSegment.from_file(file_source)
            
        fs = audio.frame_rate
        raw_samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        
        if audio.channels == 2:
            samples = raw_samples.reshape((-1, 2))
        else:
            samples = raw_samples
            
        # Normalize to [-1.0, 1.0]
        max_possible = float(1 << (8 * audio.sample_width - 1))
        samples = samples / max_possible

    # Convert to mono if requested
    if to_mono and samples.ndim > 1 and samples.shape[1] > 1:
        samples = np.mean(samples, axis=1)

    return samples.astype(np.float32), int(fs)

def save_audio(output_path: str, samples: np.ndarray, fs: int, format: str = "WAV") -> str:
    """Save audio array to file path."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    # Clip to prevent overflow
    samples = np.clip(samples, -1.0, 1.0)
    sf.write(output_path, samples, fs, format=format)
    return output_path

def audio_to_bytes(samples: np.ndarray, fs: int, format: str = "WAV") -> bytes:
    """
    Encode audio array into an in-memory byte buffer.
    Ideal for Streamlit st.audio playback and file download buttons.
    """
    buffer = io.BytesIO()
    samples = np.clip(samples, -1.0, 1.0)
    sf.write(buffer, samples, fs, format=format)
    buffer.seek(0)
    return buffer.read()

def get_audio_info(samples: np.ndarray, fs: int) -> Dict[str, Any]:
    """Calculate duration, channel count, sample rate, and peak amplitude."""
    total_frames = samples.shape[0]
    duration_sec = total_frames / fs if fs > 0 else 0
    channels = 1 if samples.ndim == 1 else samples.shape[1]
    peak = float(np.max(np.abs(samples))) if total_frames > 0 else 0.0
    peak_db = 20 * np.log10(peak) if peak > 1e-6 else -100.0

    return {
        "duration_seconds": round(duration_sec, 2),
        "duration_formatted": f"{int(duration_sec // 60):02d}:{int(duration_sec % 60):02d}",
        "sample_rate": fs,
        "channels": channels,
        "channel_str": "Stereo (2ch)" if channels == 2 else ("Mono (1ch)" if channels == 1 else f"{channels} channels"),
        "peak_db": round(peak_db, 1)
    }
