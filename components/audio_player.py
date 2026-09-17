import streamlit as st
import numpy as np
import os
from utils.audio_io import audio_to_bytes

def render_audio_comparison(
    original_samples: np.ndarray,
    processed_samples: np.ndarray,
    fs: int,
    original_label: str = "Original Audio",
    processed_label: str = "Enhanced / Processed Audio"
):
    """
    Renders side-by-side comparison players with direct audio stream playback.
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### 📻 {original_label}")
        orig_bytes = audio_to_bytes(original_samples, fs)
        st.audio(orig_bytes, format="audio/wav")

    with col2:
        st.markdown(f"#### 🎧 {processed_label}")
        proc_bytes = audio_to_bytes(processed_samples, fs)
        st.audio(proc_bytes, format="audio/wav")

def render_download_button(
    samples: np.ndarray,
    fs: int,
    suggested_filename: str,
    button_label: str = "Download Processed Audio (.WAV)",
    key: str = "download_btn"
):
    """Renders a one-click download button for processed audio."""
    wav_bytes = audio_to_bytes(samples, fs, format="WAV")
    st.download_button(
        label=f"💾 {button_label}",
        data=wav_bytes,
        file_name=suggested_filename,
        mime="audio/wav",
        key=key,
        use_container_width=True
    )
