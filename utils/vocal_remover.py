import numpy as np
from scipy.signal import butter, lfilter
from .dsp_filters import normalize_audio

def remove_vocals_phase(
    samples: np.ndarray,
    fs: int,
    preserve_bass: bool = True,
    bass_cutoff_hz: float = 140.0,
    gain_boost: float = 1.2
) -> np.ndarray:
    """
    Remove center-panned vocals using stereo phase inversion (from vocal_remover.py).
    
    If the track is stereo, subtracting the left channel from the right channel cancels out
    any signal mixed in the exact center (typically lead vocals).
    
    Args:
        samples (np.ndarray): 2D array of shape (N, 2) or 1D array.
        fs (int): Sample rate.
        preserve_bass (bool): If True, preserves low frequencies (kick drum, bassline)
                              which would otherwise also be cancelled out.
        bass_cutoff_hz (float): Frequency below which bass is retained.
        gain_boost (float): Gain multiplier after cancellation.
        
    Returns:
        np.ndarray: Processed instrumental audio (stereo or mono).
    """
    if samples.ndim < 2 or samples.shape[1] < 2:
        # Cannot perform phase cancellation on mono input
        return samples

    left = samples[:, 0]
    right = samples[:, 1]

    # Center cancellation: L - R
    instrumental = left - right

    if preserve_bass:
        nyquist = 0.5 * fs
        safe_cutoff = min(bass_cutoff_hz, nyquist - 10.0) / nyquist
        # 4th order lowpass filter for bass
        b, a = butter(4, safe_cutoff, btype="low")
        mono_original = 0.5 * (left + right)
        bass = lfilter(b, a, mono_original)
        
        # Add preserved center bass back
        instrumental = instrumental + bass

    instrumental = instrumental * gain_boost
    instrumental = normalize_audio(instrumental, target_peak=0.95)

    # Return as 2-channel stereo for uniform playback
    stereo_instrumental = np.stack((instrumental, instrumental), axis=-1)
    return stereo_instrumental
