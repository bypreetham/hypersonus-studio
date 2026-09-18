"""
Demucs Multi-Stem Neural Splitter Engine Adapter.
Directly integrates F:\\Hypersonus\\surround-decoder\\.h3da-codec\\Demucs-audio-splitter
into Hypersonus Studio with support for 4-stem and 6-stem separation.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple, Union

import numpy as np

# Suppress NumPy 2.x C-API warnings if present
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.transformer")

# Ensure the local Demucs repository is in sys.path
_DEMUCS_REPO_PATH = Path(r"F:\Hypersonus\surround-decoder\.h3da-codec\Demucs-audio-splitter")
if _DEMUCS_REPO_PATH.exists() and str(_DEMUCS_REPO_PATH) not in sys.path:
    sys.path.insert(0, str(_DEMUCS_REPO_PATH))


def is_demucs_available() -> Tuple[bool, str]:
    """Check if Demucs and Torch can be imported."""
    try:
        import torch
        import demucs.api
        import demucs.pretrained
        device_name = "CUDA" if torch.cuda.is_available() else "CPU"
        return True, f"Demucs Ready ({device_name})"
    except ImportError as e:
        return False, f"Demucs not available: {e}"
    except Exception as e:
        return False, f"Demucs error: {e}"


def get_demucs_info() -> Dict[str, Union[bool, str, list]]:
    """Get system runtime and model diagnostics for Demucs."""
    ready, status_msg = is_demucs_available()
    cuda_available = False
    cuda_device = "N/A"
    
    if ready:
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_device = torch.cuda.get_device_name(0)
        except Exception:
            pass

    return {
        "ready": ready,
        "status": status_msg,
        "cuda_available": cuda_available,
        "cuda_device": cuda_device,
        "available_models": [
            {
                "id": "htdemucs",
                "name": "HT Demucs (4-Stem Standard)",
                "stems": ["drums", "bass", "other", "vocals"],
                "stem_count": 4,
                "desc": "Fast & robust Hybrid Transformer model (Vocals, Drums, Bass, Other).",
            },
            {
                "id": "htdemucs_6s",
                "name": "HT Demucs 6S (6-Stem Full Studio)",
                "stems": ["drums", "bass", "other", "vocals", "guitar", "piano"],
                "stem_count": 6,
                "desc": "Isolates Guitar and Piano in addition to Drums, Bass, Vocals & Other.",
            },
            {
                "id": "htdemucs_ft",
                "name": "HT Demucs Fine-Tuned (4-Stem Studio Master)",
                "stems": ["drums", "bass", "other", "vocals"],
                "stem_count": 4,
                "desc": "Fine-tuned high-fidelity 4-stem model with enhanced SDR.",
            },
            {
                "id": "hdemucs_mmi",
                "name": "HDemucs MMI (4-Stem Classic)",
                "stems": ["drums", "bass", "other", "vocals"],
                "stem_count": 4,
                "desc": "Hybrid Demucs v3 music separation architecture.",
            },
        ],
    }


def separate_stems_demucs(
    samples: np.ndarray,
    fs: int,
    model_name: str = "htdemucs",
    device: str = "auto",
    shifts: int = 1,
    overlap: float = 0.25,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Tuple[Dict[str, np.ndarray], int]:
    """
    Separate audio into 4 or 6 stems using Demucs.

    Args:
        samples (np.ndarray): 2D array of shape (N, 2) or 1D array of shape (N,).
        fs (int): Sample rate of the audio.
        model_name (str): Model name, e.g. 'htdemucs' (4 stems) or 'htdemucs_6s' (6 stems).
        device (str): 'auto', 'cuda', or 'cpu'.
        shifts (int): Shift equivariance count (1 = standard fast, 2 = higher SDR).
        overlap (float): Overlap between chunk splits (default 0.25).
        progress_callback (Callable): Callback taking (progress_fraction: float, status_msg: str).

    Returns:
        Tuple[Dict[str, np.ndarray], int]:
            stems dict with stem name -> stereo (N, 2) float32 numpy array,
            sample rate fs.
    """
    import torch
    from demucs.api import Separator

    if progress_callback:
        progress_callback(0.05, f"Initializing Demucs ({model_name})...")

    # Select execution device
    if device == "auto":
        target_device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        target_device = device

    # Prepare input tensor: Demucs expects (channels, samples)
    if samples.ndim == 1:
        stereo_samples = np.stack((samples, samples), axis=0)
    elif samples.ndim == 2:
        if samples.shape[1] == 1:
            stereo_samples = np.repeat(samples.T, 2, axis=0)
        elif samples.shape[1] >= 2:
            stereo_samples = samples[:, :2].T
        else:
            stereo_samples = samples
    else:
        raise ValueError(f"Unsupported audio samples shape: {samples.shape}")

    try:
        wav_tensor = torch.from_numpy(stereo_samples.astype(np.float32))
    except Exception:
        wav_tensor = torch.tensor(stereo_samples.tolist(), dtype=torch.float32)

    # Initialize callback wrapper
    def _api_callback(info: dict):
        if not progress_callback:
            return
        audio_length = info.get("audio_length", 1)
        segment_offset = info.get("segment_offset", 0)
        models_count = info.get("models", 1)
        model_idx = info.get("model_idx_in_bag", 0)
        shift_idx = info.get("shift_idx", 0)
        shifts_total = max(1, shifts)

        # Approximate overall progress
        seg_ratio = min(1.0, float(segment_offset) / max(1.0, float(audio_length)))
        sub_progress = (float(model_idx) + (float(shift_idx) + seg_ratio) / shifts_total) / max(1.0, float(models_count))
        pct = 0.10 + 0.85 * min(1.0, max(0.0, sub_progress))
        pct_display = int(pct * 100)
        progress_callback(pct, f"Separating audio with Demucs {model_name} ({pct_display}%)...")

    if progress_callback:
        progress_callback(0.10, f"Loading neural model {model_name} on {target_device.upper()}...")

    separator = Separator(
        model=model_name,
        device=target_device,
        shifts=shifts,
        overlap=overlap,
        callback=_api_callback,
    )

    if progress_callback:
        progress_callback(0.15, "Performing neural inference across audio tracks...")

    # Run separation
    _, separated_dict = separator.separate_tensor(wav_tensor, sr=fs)

    if progress_callback:
        progress_callback(0.95, "Normalizing stems and assembling stereo output...")

    # Convert torch outputs to numpy arrays formatted as (samples, channels)
    out_stems: Dict[str, np.ndarray] = {}
    target_sr = separator.samplerate

    for stem_name, stem_tensor in separated_dict.items():
        # stem_tensor shape is (channels, samples)
        try:
            stem_np = stem_tensor.cpu().numpy().T  # Shape: (samples, channels)
        except Exception:
            stem_np = np.array(stem_tensor.cpu().tolist(), dtype=np.float32).T
        
        # Ensure 2-channel stereo
        if stem_np.ndim == 1:
            stem_np = np.stack((stem_np, stem_np), axis=-1)
        elif stem_np.shape[1] == 1:
            stem_np = np.repeat(stem_np, 2, axis=-1)

        # Soft peak normalization to prevent clipping (0.95 peak limit)
        peak = float(np.max(np.abs(stem_np))) if stem_np.size else 0.0
        if peak > 0.95:
            stem_np = (stem_np / peak) * 0.95
        elif peak > 0.0:
            # Gentle headroom scaling
            stem_np = stem_np * 0.98

        out_stems[stem_name] = stem_np.astype(np.float32)

    if progress_callback:
        progress_callback(1.0, f"Demucs separation complete! ({len(out_stems)} stems extracted)")

    return out_stems, target_sr


def create_instrumental_mix(stems: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Sum all non-vocal stems to create a complete instrumental / backing track.
    """
    instrumental = None
    for name, data in stems.items():
        if name.lower() == "vocals":
            continue
        if instrumental is None:
            instrumental = data.copy()
        else:
            instrumental = instrumental + data

    if instrumental is None:
        return np.zeros((100, 2), dtype=np.float32)

    peak = float(np.max(np.abs(instrumental))) if instrumental.size else 0.0
    if peak > 0.95:
        instrumental = (instrumental / peak) * 0.95
    return instrumental.astype(np.float32)
