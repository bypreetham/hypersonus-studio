import streamlit as st
import numpy as np
from typing import Optional, Tuple
from utils.audio_io import load_audio, get_audio_info

def render_file_uploader(key: str = "audio_uploader") -> Optional[Tuple[np.ndarray, int, str]]:
    """
    Renders a file uploader widget with audio file validation and metadata metrics.
    Returns:
        (samples, fs, filename) or None if no file is uploaded.
    """
    uploaded_file = st.file_uploader(
        "Choose an audio track (MP3, WAV, FLAC, OGG, M4A)",
        type=["wav", "mp3", "flac", "ogg", "m4a"],
        key=key,
        help="Upload an audio file to process."
    )

    if uploaded_file is None:
        st.info("👆 Upload an audio file to get started.", icon="💡")
        return None

    try:
        with st.spinner("Decoding audio track..."):
            file_bytes = uploaded_file.read()
            samples, fs = load_audio(file_bytes)
            info = get_audio_info(samples, fs)

        # Display track details in a clean metric row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", info["duration_formatted"])
        with col2:
            st.metric("Sample Rate", f"{info['sample_rate']} Hz")
        with col3:
            st.metric("Channels", info["channel_str"])
        with col4:
            st.metric("Peak Level", f"{info['peak_db']} dB")

        return samples, fs, uploaded_file.name

    except Exception as e:
        st.error(f"Error reading audio file: {e}")
        return None
