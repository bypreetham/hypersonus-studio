import os
import sys
import numpy as np
import pytest

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.dsp_filters import butter_bandpass, bandpass_filter, normalize_audio, to_int16
from utils.spatializer import apply_ping_pong_3d, apply_surround_split, create_ping_pong_effect
from utils.vocal_remover import remove_vocals_phase, extract_vocals_phase, extract_vocals_multistage_dsp
from utils.stem_separator import separate_stems
from utils.audio_io import audio_to_bytes, get_audio_info
from utils.song_item import SongItem

@pytest.fixture
def synthetic_stereo_audio():
    """Generates 3 seconds of a stereo sine wave (440Hz Left, 880Hz Right)."""
    fs = 44100
    duration = 3.0
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    left = 0.5 * np.sin(2 * np.pi * 440 * t)
    right = 0.5 * np.sin(2 * np.pi * 880 * t)
    stereo = np.stack((left, right), axis=-1).astype(np.float32)
    return stereo, fs

def test_bandpass_filter(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    mono = stereo[:, 0]
    filtered = bandpass_filter(mono, 300, 3000, fs, order=4)
    assert filtered.shape == mono.shape
    assert not np.isnan(filtered).any()

def test_normalize_audio(synthetic_stereo_audio):
    stereo, _ = synthetic_stereo_audio
    boosted = stereo * 10.0
    norm = normalize_audio(boosted, target_peak=0.9)
    assert np.max(np.abs(norm)) <= 0.9001

def test_3d_ping_pong(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    processed = apply_ping_pong_3d(stereo, fs, chunk_duration=1.0, pan_depth=0.8)
    assert processed.ndim == 2
    assert processed.shape[1] == 2
    assert len(processed) > 0
    assert not np.isnan(processed).any()

def test_surround_split(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    processed = apply_surround_split(stereo, fs, lowcut=250, highcut=4000, swap_channels=False)
    assert processed.ndim == 2
    assert processed.shape[1] == 2
    assert not np.isnan(processed).any()

def test_vocal_remover_phase(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    processed = remove_vocals_phase(stereo, fs, preserve_bass=True, bass_cutoff_hz=140)
    assert processed.ndim == 2
    assert processed.shape[1] == 2
    assert not np.isnan(processed).any()

def test_vocal_extractor_phase(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    vocals = extract_vocals_phase(stereo, fs, lowcut_hz=120, highcut_hz=8000, sensitivity=1.2)
    assert vocals.ndim == 2
    assert vocals.shape[1] == 2
    assert len(vocals) == len(stereo)
    assert not np.isnan(vocals).any()

def test_vocal_extractor_multistage_dsp(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    vocals = extract_vocals_multistage_dsp(
        stereo, fs, music_suppression=1.6, gate_threshold=0.3, harmonic_margin=1.5
    )
    assert vocals.ndim == 2
    assert vocals.shape[1] == 2
    assert len(vocals) == len(stereo)
    assert not np.isnan(vocals).any()


def test_stem_separator_dsp(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    vocals, bgm, engine = separate_stems(stereo, fs, engine="dsp")
    assert vocals.shape[0] > 0
    assert bgm.shape[0] > 0
    assert engine is not None

def test_audio_io_bytes(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    raw_bytes = audio_to_bytes(stereo, fs, format="WAV")
    assert len(raw_bytes) > 100
    info = get_audio_info(stereo, fs)
    assert info["channels"] == 2
    assert info["sample_rate"] == 44100
    assert info["duration_seconds"] == 3.0

def test_song_item(synthetic_stereo_audio):
    stereo, fs = synthetic_stereo_audio
    item = SongItem(
        filepath="dummy.wav",
        filename="dummy.wav",
        samples=stereo,
        fs=fs,
        duration_seconds=3.0,
        channels=2,
        start_pos=0.0,
        end_pos=3.0,
    )
    assert item.duration_seconds == 3.0
    assert item.range_duration == 3.0
    assert len(item.get_trimmed_samples()) == len(stereo)

    # Test range setting & trimming
    item.set_range(1.0, 2.5)
    assert item.start_pos == 1.0
    assert item.end_pos == 2.5
    assert item.range_duration == 1.5
    trimmed = item.get_trimmed_samples()
    expected_len = int(1.5 * fs)
    assert abs(len(trimmed) - expected_len) <= 1

    # Test time formatting
    assert SongItem.format_time(65.4) == "01:05.4"
    assert SongItem.format_time(0.0) == "00:00.0"

