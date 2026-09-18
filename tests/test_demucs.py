import os
import sys
import numpy as np
import pytest

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.demucs_splitter import (
    is_demucs_available,
    get_demucs_info,
    create_instrumental_mix,
    separate_stems_demucs,
)
from desktop.views import DemucsSplitterView

def test_demucs_availability():
    ready, status = is_demucs_available()
    assert ready, f"Demucs should be available: {status}"

def test_demucs_diagnostics():
    info = get_demucs_info()
    assert info["ready"] is True
    models = info["available_models"]
    model_ids = [m["id"] for m in models]
    assert "htdemucs" in model_ids
    assert "htdemucs_6s" in model_ids

    # Verify 4-stem and 6-stem definitions
    htdemucs_model = next(m for m in models if m["id"] == "htdemucs")
    assert htdemucs_model["stem_count"] == 4
    assert set(htdemucs_model["stems"]) == {"drums", "bass", "other", "vocals"}

    htdemucs_6s_model = next(m for m in models if m["id"] == "htdemucs_6s")
    assert htdemucs_6s_model["stem_count"] == 6
    assert set(htdemucs_6s_model["stems"]) == {"drums", "bass", "other", "vocals", "guitar", "piano"}

def test_create_instrumental_mix():
    n_samples = 1000
    stems = {
        "vocals": np.ones((n_samples, 2), dtype=np.float32) * 0.5,
        "drums": np.ones((n_samples, 2), dtype=np.float32) * 0.2,
        "bass": np.ones((n_samples, 2), dtype=np.float32) * 0.3,
        "other": np.ones((n_samples, 2), dtype=np.float32) * 0.1,
    }
    mix = create_instrumental_mix(stems)
    assert mix.shape == (n_samples, 2)
    # Expected sum of drums + bass + other = 0.2 + 0.3 + 0.1 = 0.6
    np.testing.assert_allclose(mix[0, 0], 0.6, atol=1e-4)

def test_demucs_view_class():
    # Verify the view class is imported and has expected attributes
    assert hasattr(DemucsSplitterView, "_on_model_change")
    assert hasattr(DemucsSplitterView, "_start_separation")
    assert hasattr(DemucsSplitterView, "_render_stems_ui")

@pytest.mark.skipif(not is_demucs_available()[0], reason="Demucs not available")
def test_demucs_separation_synthetic():
    # 0.5 seconds of synthetic audio
    fs = 44100
    duration = 0.5
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    sig = 0.3 * np.sin(2 * np.pi * 440 * t)
    stereo = np.stack((sig, sig), axis=-1).astype(np.float32)

    progress_records = []
    def _cb(fraction, msg):
        progress_records.append((fraction, msg))

    stems, out_sr = separate_stems_demucs(
        samples=stereo,
        fs=fs,
        model_name="htdemucs",
        device="cpu",
        shifts=1,
        progress_callback=_cb,
    )

    assert isinstance(stems, dict)
    assert "vocals" in stems
    assert "drums" in stems
    assert "bass" in stems
    assert "other" in stems
    assert out_sr > 0
    assert len(progress_records) > 0
    # Check shape of stems
    for name, data in stems.items():
        assert data.ndim == 2
        assert data.shape[1] == 2
        assert not np.isnan(data).any()
