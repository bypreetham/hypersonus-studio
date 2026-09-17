import numpy as np
from typing import Tuple
from .dsp_filters import bandpass_filter, normalize_audio

def create_ping_pong_effect(
    samples: np.ndarray, 
    fs: int, 
    chunk_duration: float = 2.0,
    pan_depth: float = 1.0
) -> np.ndarray:
    """
    Apply smooth ping-pong panning across stereo channels.
    
    Args:
        samples (np.ndarray): 1D mono audio array.
        fs (int): Sample rate.
        chunk_duration (float): Seconds per pan cycle.
        pan_depth (float): Stereo spread [0.0 to 1.0]. 1.0 is full ping-pong.
        
    Returns:
        stereo_audio (np.ndarray): 2D array of shape (N, 2)
    """
    chunk_size = max(int(fs * chunk_duration), 100)
    left_channel = []
    right_channel = []

    for i in range(0, len(samples), chunk_size):
        chunk = samples[i : i + chunk_size]
        n_chunk = len(chunk)
        if n_chunk == 0:
            continue
            
        fade = np.linspace(0, 1, n_chunk, dtype=np.float32)

        # Scale fade by pan depth: full depth is 0..1, lesser depth centers the sound
        left_fade = 0.5 * (1.0 - pan_depth) + pan_depth * fade
        right_fade = 0.5 * (1.0 - pan_depth) + pan_depth * (1.0 - fade)

        if (i // chunk_size) % 2 == 0:
            # Left fades in, right fades out
            left_channel.append(chunk * left_fade)
            right_channel.append(chunk * right_fade)
        else:
            # Right fades in, left fades out
            left_channel.append(chunk * right_fade)
            right_channel.append(chunk * left_fade)

    left_arr = np.concatenate(left_channel) if left_channel else np.zeros_like(samples)
    right_arr = np.concatenate(right_channel) if right_channel else np.zeros_like(samples)

    min_len = min(len(left_arr), len(right_arr), len(samples))
    stereo_audio = np.stack((left_arr[:min_len], right_arr[:min_len]), axis=-1)
    return stereo_audio

def apply_ping_pong_3d(
    samples: np.ndarray,
    fs: int,
    chunk_duration: float = 2.0,
    lowcut: float = 250.0,
    highcut: float = 6000.0,
    pan_depth: float = 1.0,
    vocal_center_mix: float = 1.0,
) -> np.ndarray:
    """
    Full 3D Ping-Pong Spatializer pipeline (from 3daudio.py).
    Separates vocals via bandpass filter to keep vocal presence centered,
    while rotating/panning instruments across left and right stereo field.
    """
    # If stereo, average to mono first
    if samples.ndim > 1 and samples.shape[1] > 1:
        mono = np.mean(samples, axis=1)
    else:
        mono = samples.flatten()

    # Normalize input
    mono = normalize_audio(mono, target_peak=0.95)

    # Extract vocal frequencies and non-vocal frequencies
    vocals = bandpass_filter(mono, lowcut, highcut, fs)
    non_vocals = mono - vocals

    # Apply ping-pong panning to the non-vocal audio
    stereo_non_vocals = create_ping_pong_effect(non_vocals, fs, chunk_duration, pan_depth)

    # Center vocals equally across both channels
    v_len = min(len(vocals), len(stereo_non_vocals))
    stereo_vocals = np.stack((vocals[:v_len] * vocal_center_mix, vocals[:v_len] * vocal_center_mix), axis=-1)

    # Combine non-vocals and centered vocals
    stereo_output = stereo_non_vocals[:v_len] + stereo_vocals

    # Final normalization
    return normalize_audio(stereo_output, target_peak=0.95)

def apply_surround_split(
    samples: np.ndarray,
    fs: int,
    lowcut: float = 250.0,
    highcut: float = 6000.0,
    swap_channels: bool = False,
    crossfeed: float = 0.15,
) -> np.ndarray:
    """
    Binaural Surround Channel Splitter pipeline (from surroundSound.py).
    Separates vocals (bandpass) and instruments (residual).
    Assigns instruments to one ear and vocals to the other ear,
    with an adjustable crossfeed blend to eliminate headphone fatigue.
    """
    if samples.ndim > 1 and samples.shape[1] > 1:
        mono = np.mean(samples, axis=1)
    else:
        mono = samples.flatten()

    mono = normalize_audio(mono, target_peak=0.95)

    # Frequency band separation
    vocals = bandpass_filter(mono, lowcut, highcut, fs)
    instruments = mono - vocals

    # Crossfeed mixing to produce pleasant spatial separation without harsh isolation
    # ch_a: primary instruments + small bleed of vocals
    # ch_b: primary vocals + small bleed of instruments
    ch_a = (1.0 - crossfeed) * instruments + crossfeed * vocals
    ch_b = (1.0 - crossfeed) * vocals + crossfeed * instruments

    if not swap_channels:
        stereo_output = np.stack((ch_a, ch_b), axis=-1)  # Left: Instruments, Right: Vocals
    else:
        stereo_output = np.stack((ch_b, ch_a), axis=-1)  # Left: Vocals, Right: Instruments

    return normalize_audio(stereo_output, target_peak=0.95)
