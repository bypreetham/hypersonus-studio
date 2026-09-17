import numpy as np
from scipy.signal import butter, lfilter

def butter_bandpass(lowcut: float, highcut: float, fs: int, order: int = 5):
    """
    Design a Butterworth bandpass filter.
    Clamps frequencies to ensure stability with respect to the Nyquist frequency.
    """
    nyquist = 0.5 * fs
    # Ensure safe frequency bounds
    safe_low = max(10.0, float(lowcut))
    safe_high = min(nyquist - 10.0, float(highcut))
    
    if safe_low >= safe_high:
        safe_low = 100.0
        safe_high = min(nyquist - 10.0, 5000.0)
        
    low = safe_low / nyquist
    high = safe_high / nyquist
    b, a = butter(order, [low, high], btype="band")
    return b, a

def bandpass_filter(data: np.ndarray, lowcut: float, highcut: float, fs: int, order: int = 5) -> np.ndarray:
    """
    Apply a Butterworth bandpass filter to 1D audio sample array.
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return np.asarray(y, dtype=np.float32)

def normalize_audio(samples: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """
    Peak-normalize audio data to prevent digital clipping.
    Works for 1D (mono) or 2D (stereo, shape (N, 2)) float32 arrays.
    """
    max_val = np.max(np.abs(samples))
    if max_val > 1e-6:
        return (samples / max_val * target_peak).astype(np.float32)
    return samples.astype(np.float32)

def to_int16(samples: np.ndarray) -> np.ndarray:
    """Convert float32 samples in range [-1.0, 1.0] to int16 PCM."""
    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767.0).astype(np.int16)
