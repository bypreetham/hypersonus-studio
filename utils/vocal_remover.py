import numpy as np
from scipy.signal import butter, lfilter, stft, istft
from .dsp_filters import normalize_audio, bandpass_filter

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


def extract_vocals_phase(
    samples: np.ndarray,
    fs: int,
    lowcut_hz: float = 120.0,
    highcut_hz: float = 8000.0,
    sensitivity: float = 1.2,
    gain_boost: float = 1.2,
) -> np.ndarray:
    """
    Extract center-channel lead vocals using stereo spectral coherence masking & STFT.
    
    Isolates vocals by comparing Left and Right spectral channels:
    signal appearing equally with coherent phase in both channels (center pan)
    is isolated, while wide stereo instruments (panned guitars, synths, reverb)
    are attenuated.
    
    Args:
        samples (np.ndarray): 2D array of shape (N, 2) or 1D array.
        fs (int): Sample rate.
        lowcut_hz (float): Highpass cutoff to reject sub-bass, kick drum, rumble.
        highcut_hz (float): Lowpass cutoff to reject high cymbals and air hiss.
        sensitivity (float): Exponent controlling mask steepness (higher = cleaner vocals).
        gain_boost (float): Output amplification factor.
        
    Returns:
        np.ndarray: 2D stereo array of shape (N, 2) containing isolated vocal stem.
    """
    if samples.ndim < 2 or samples.shape[1] < 2:
        # For mono, apply vocal bandpass filter
        filtered = bandpass_filter(samples.flatten(), lowcut_hz, min(highcut_hz, 0.49 * fs), fs)
        norm = normalize_audio(filtered * gain_boost, 0.95)
        return np.stack((norm, norm), axis=-1)

    left = samples[:, 0].astype(np.float32)
    right = samples[:, 1].astype(np.float32)
    target_length = len(samples)

    # STFT parameters
    nperseg = 2048
    noverlap = 1536

    f, _, Z_left = stft(left, fs=fs, nperseg=nperseg, noverlap=noverlap)
    _, _, Z_right = stft(right, fs=fs, nperseg=nperseg, noverlap=noverlap)

    # Center Pan Coherence Mask
    diff_mag = np.abs(Z_left - Z_right)
    sum_mag = np.abs(Z_left) + np.abs(Z_right) + 1e-8
    center_mask = np.maximum(0.0, 1.0 - (diff_mag / sum_mag))
    
    if sensitivity != 1.0:
        center_mask = np.power(center_mask, max(0.5, float(sensitivity)))

    # Vocal frequency bandpass weighting
    nyquist = 0.5 * fs
    safe_low = max(50.0, float(lowcut_hz))
    safe_high = min(nyquist - 20.0, float(highcut_hz))
    
    freq_weights = np.ones_like(f, dtype=np.float32)
    low_idx = f < safe_low
    freq_weights[low_idx] = np.maximum(0.0, (f[low_idx] / safe_low) ** 2)
    high_idx = f > safe_high
    freq_weights[high_idx] = np.maximum(0.0, 1.0 - ((f[high_idx] - safe_high) / (nyquist - safe_high)) ** 2)

    center_mask = center_mask * freq_weights[:, np.newaxis]

    # Apply mask to mid (center) channel
    Z_mid = 0.5 * (Z_left + Z_right)
    Z_vocal = Z_mid * center_mask

    # Inverse STFT
    _, vocal_time = istft(Z_vocal, fs=fs, nperseg=nperseg, noverlap=noverlap)

    # Align length with input
    if len(vocal_time) > target_length:
        vocal_time = vocal_time[:target_length]
    elif len(vocal_time) < target_length:
        vocal_time = np.pad(vocal_time, (0, target_length - len(vocal_time)))

    vocal_time = vocal_time * gain_boost
    vocal_time = normalize_audio(vocal_time, target_peak=0.95)

    return np.stack((vocal_time, vocal_time), axis=-1)


def extract_vocals_multistage_dsp(
    samples: np.ndarray,
    fs: int,
    music_suppression: float = 1.6,
    gate_threshold: float = 0.40,
    harmonic_margin: float = 1.5,
    lowcut_hz: float = 120.0,
    highcut_hz: float = 7500.0,
    gain_boost: float = 1.2,
) -> np.ndarray:
    """
    Advanced Multi-Stage CPU Spectral Vocal Isolator & Music Suppressor.
    
    Combines:
    1. Stereo Side-Channel Spectral Subtraction (Wiener-style cancellation of panned guitars/music).
    2. Harmonic-Percussive Separation (HPSS) to strip acoustic guitar plucks & percussion transients.
    3. Vocal Formant Bandpass Shaping (rejects sub-bass rumble and high cymbal sizzle).
    4. Dynamic Vocal Activity Gating (VAD) to smoothly mute non-vocal sections (e.g. intro/interludes).
    
    Args:
        samples (np.ndarray): 2D array of shape (N, 2) or 1D array.
        fs (int): Sample rate.
        music_suppression (float): Side spectral subtraction factor (higher = more music removed).
        gate_threshold (float): Vocal presence percentile threshold (0.0 to 1.0; 0.40 gates quiet intro/breaks).
        harmonic_margin (float): HPSS harmonic margin (higher = sharper rejection of guitar plucks/drums).
        lowcut_hz (float): Low cut frequency for vocal formants (Hz).
        highcut_hz (float): High cut frequency for vocal formants (Hz).
        gain_boost (float): Vocal amplification gain multiplier.
        
    Returns:
        np.ndarray: Stereo array (N, 2) of cleanly isolated acapella vocals.
    """
    try:
        import librosa
        has_librosa = True
    except ImportError:
        has_librosa = False

    if not has_librosa:
        # Fall back to phase coherence mask if librosa is not installed
        return extract_vocals_phase(
            samples, fs, lowcut_hz=lowcut_hz, highcut_hz=highcut_hz,
            sensitivity=music_suppression, gain_boost=gain_boost
        )

    target_length = len(samples)
    if samples.ndim < 2 or samples.shape[1] < 2:
        mid = samples.flatten().astype(np.float32)
        side = np.zeros_like(mid)
    else:
        left = samples[:, 0].astype(np.float32)
        right = samples[:, 1].astype(np.float32)
        mid = 0.5 * (left + right)
        side = left - right

    # Overlap-add chunking for fast CPU performance & low RAM usage
    chunk_sec = 15.0
    overlap_sec = 1.5
    chunk_samples = int(chunk_sec * fs)
    overlap_samples = int(overlap_sec * fs)
    step_samples = max(1024, chunk_samples - overlap_samples)

    n_fft = 2048
    hop_length = 512

    out_vocal = np.zeros(target_length, dtype=np.float32)
    out_weight = np.zeros(target_length, dtype=np.float32)
    hann_window = np.hanning(chunk_samples).astype(np.float32)

    freqs = librosa.fft_frequencies(sr=fs, n_fft=n_fft)

    # Precompute vocal bandpass curve
    f_weight = np.ones_like(freqs, dtype=np.float32)
    low_cutoff = max(60.0, float(lowcut_hz))
    high_cutoff = min(fs * 0.49, float(highcut_hz))
    low_idx = freqs < low_cutoff
    f_weight[low_idx] = np.maximum(0.0, (freqs[low_idx] / low_cutoff) ** 2)
    high_idx = freqs > high_cutoff
    f_weight[high_idx] = np.maximum(0.0, 1.0 - ((freqs[high_idx] - high_cutoff) / (fs * 0.5 - high_cutoff + 1e-6)) ** 2)

    v_band = (freqs >= 300.0) & (freqs <= 3400.0)

    # Lightweight global pre-scan to estimate true vocal energy ceiling across track
    prescan_hop = max(1024, int(fs * 0.25))
    prescan_stft = np.abs(librosa.stft(mid, n_fft=1024, hop_length=prescan_hop))
    prescan_f = librosa.fft_frequencies(sr=fs, n_fft=1024)
    prescan_v_idx = (prescan_f >= 300.0) & (prescan_f <= 3400.0)
    global_vocal_max = float(np.max(np.mean(prescan_stft[prescan_v_idx, :], axis=0))) + 1e-6

    for start in range(0, target_length, step_samples):
        end = min(start + chunk_samples, target_length)
        chunk_m = mid[start:end]
        chunk_s = side[start:end]
        cur_len = len(chunk_m)
        if cur_len < n_fft:
            break

        # STFT
        Sm, pm = librosa.magphase(librosa.stft(chunk_m, n_fft=n_fft, hop_length=hop_length))
        Ss, _ = librosa.magphase(librosa.stft(chunk_s, n_fft=n_fft, hop_length=hop_length))

        # 1. Stereo Side Spectral Subtraction
        alpha = max(0.5, float(music_suppression))
        Sm_sub = np.maximum(Sm - alpha * Ss, 0.02 * Sm)

        # 2. Harmonic-Percussive Separation (HPSS) to strip plucking / drum transients
        h_margin = max(1.0, float(harmonic_margin))
        H, _ = librosa.decompose.hpss(Sm_sub, margin=(h_margin, 2.0))

        # 3. Vocal Formant Bandpass Shaping
        H_shaped = H * f_weight[:, np.newaxis]

        # 4. Dynamic Vocal Activity Gate (VAD)
        if gate_threshold > 0.02:
            band_energy = np.mean(H_shaped[v_band, :], axis=0)
            win_len = min(15, len(band_energy))
            if win_len > 3:
                kernel = np.hanning(win_len)
                kernel /= np.sum(kernel)
                smooth_e = np.convolve(band_energy, kernel, mode='same')
            else:
                smooth_e = band_energy

            p_val = min(90.0, max(5.0, float(gate_threshold) * 100.0))
            local_thresh = np.percentile(smooth_e, p_val)
            global_thresh = float(gate_threshold) * global_vocal_max * 0.5
            thresh = max(local_thresh, global_thresh)
            max_ref = max(float(np.max(smooth_e)), global_vocal_max)
            # Sigmoid soft gate
            vad_gain = 1.0 / (1.0 + np.exp(-18.0 * (smooth_e - thresh) / (0.35 * max_ref + 1e-6)))
            H_shaped = H_shaped * vad_gain[np.newaxis, :]

        # Inverse STFT
        chunk_rec = librosa.istft(H_shaped * pm, hop_length=hop_length, length=cur_len)

        # Overlap-add
        w = hann_window[:cur_len] if cur_len == chunk_samples else np.hanning(cur_len).astype(np.float32)
        out_vocal[start:end] += chunk_rec * w
        out_weight[start:end] += w

    # Normalize window overlap
    valid = out_weight > 1e-5
    out_vocal[valid] /= out_weight[valid]

    # If any remaining zero frames at tail
    if not np.all(valid):
        out_vocal[~valid] = 0.0

    out_vocal = out_vocal * gain_boost
    out_vocal = normalize_audio(out_vocal, target_peak=0.95)

    return np.stack((out_vocal, out_vocal), axis=-1)

