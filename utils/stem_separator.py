import os
import io
import tempfile
import numpy as np
import soundfile as sf
from typing import Tuple, Dict, Optional, Callable
from .dsp_filters import normalize_audio

def is_demucs_available() -> bool:
    try:
        import demucs.api
        return True
    except ImportError:
        return False

def is_spleeter_available() -> bool:
    try:
        from spleeter.separator import Separator
        return True
    except ImportError:
        return False

def separate_stems_dsp(
    samples: np.ndarray, 
    fs: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    High-speed DSP Harmonic-Percussive / Center-Cancellation BGM Extractor.
    Extracts accompaniment (BGM) and isolated vocal component without requiring AI models.
    """
    if samples.ndim > 1 and samples.shape[1] > 1:
        left = samples[:, 0]
        right = samples[:, 1]
        mono = 0.5 * (left + right)
        instrumental_diff = left - right
    else:
        mono = samples.flatten()
        instrumental_diff = mono

    # Try librosa harmonic-percussive separation if available
    try:
        import librosa
        stft = librosa.stft(mono)
        harmonic, percussive = librosa.decompose.hpss(stft, margin=(1.2, 1.2))
        vocal_est = librosa.istft(harmonic, length=len(mono))
        bgm_est = librosa.istft(percussive, length=len(mono))
    except (ImportError, Exception):
        # High quality Scipy-based spectral band extraction
        from scipy.signal import butter, lfilter
        nyquist = 0.5 * fs
        # Vocals typically concentrated in 300Hz - 4000Hz
        low_v = max(50.0, 300.0) / nyquist
        high_v = min(nyquist - 20.0, 4000.0) / nyquist
        b_v, a_v = butter(4, [low_v, high_v], btype="band")
        vocal_est = lfilter(b_v, a_v, mono)
        bgm_est = mono - vocal_est

    # If stereo original, blend with phase difference for rich stereo BGM
    if samples.ndim > 1 and samples.shape[1] > 1:
        bgm_left = 0.6 * bgm_est + 0.4 * instrumental_diff
        bgm_right = 0.6 * bgm_est - 0.4 * instrumental_diff
        bgm_stereo = np.stack((bgm_left, bgm_right), axis=-1)
        vocals_stereo = np.stack((vocal_est, vocal_est), axis=-1)
    else:
        bgm_stereo = np.stack((bgm_est, bgm_est), axis=-1)
        vocals_stereo = np.stack((vocal_est, vocal_est), axis=-1)
        
    return normalize_audio(vocals_stereo, 0.95), normalize_audio(bgm_stereo, 0.95)

def separate_stems_spleeter(
    audio_path: str,
    output_dir: str
) -> Tuple[str, str]:
    """
    Separate vocals and accompaniment using Spleeter (from audionumpy.py).
    Returns (vocals_file_path, accompaniment_file_path).
    """
    from spleeter.separator import Separator
    separator = Separator("spleeter:2stems")
    separator.separate_to_file(audio_path, output_dir)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    stem_dir = os.path.join(output_dir, base_name)
    vocals_path = os.path.join(stem_dir, "vocals.wav")
    accompaniment_path = os.path.join(stem_dir, "accompaniment.wav")
    return vocals_path, accompaniment_path

def separate_stems(
    samples: np.ndarray,
    fs: int,
    engine: str = "auto",
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Unified stem separation dispatcher.
    Returns:
        vocals (np.ndarray), accompaniment (np.ndarray), engine_used (str)
    """
    if progress_callback:
        progress_callback(0.1, "Initializing separation engine...")

    if engine == "spleeter" and is_spleeter_available():
        if progress_callback:
            progress_callback(0.3, "Running Spleeter 2-stem neural network...")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            sf.write(tf.name, samples, fs)
            temp_in = tf.name

        temp_out = tempfile.mkdtemp()
        try:
            v_path, a_path = separate_stems_spleeter(temp_in, temp_out)
            vocals, _ = sf.read(v_path, dtype="float32")
            accompaniment, _ = sf.read(a_path, dtype="float32")
            if progress_callback:
                progress_callback(1.0, "Separation complete!")
            return vocals, accompaniment, "Spleeter (AI)"
        finally:
            if os.path.exists(temp_in):
                try: os.remove(temp_in)
                except Exception: pass
    
    # Fast Spectral / DSP Separation
    if progress_callback:
        progress_callback(0.4, "Executing Harmonic-Percussive / Spectral DSP separation...")
    vocals, accompaniment = separate_stems_dsp(samples, fs)
    if progress_callback:
        progress_callback(1.0, "Separation complete!")
    return vocals, accompaniment, "Spectral DSP"
