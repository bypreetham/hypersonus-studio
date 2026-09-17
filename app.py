import streamlit as st
import sys
import os
import shutil

st.set_page_config(
    page_title="Hypersonus Studio - Audio Processing Suite",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #00E5FF, #7C4DFF, #FF4081);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .feature-card {
        background: #1A1C23;
        border: 1px solid #2E3440;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s, border-color 0.2s;
    }
    .feature-card:hover {
        border-color: #00E5FF;
        transform: translateY(-2px);
    }
    .badge-ok {
        color: #00E676;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎛️ Hypersonus Studio</h1>', unsafe_allow_html=True)
st.write("A modular audio processing application featuring spatial 3D enhancement, binaural surround sound splitting, real-time vocal suppression, and neural stem extraction.")

st.markdown("---")

# Module Cards Grid
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🎵 1. 3D Ping-Pong Spatializer</h3>
        <p>Dynamic stereophonic panning engine. Sweeps backing instruments across left and right stereo channels in smooth timed cycles while keeping vocals locked in the center.</p>
        <p><i>Derived and enhanced from <code>3daudio.py</code></i></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h3>🎙️ 3. Fast Vocal Remover</h3>
        <p>Instant center-channel cancellation using stereo phase inversion. Features smart low-pass bass protection to preserve kick drums and sub-bass lines.</p>
        <p><i>Derived and enhanced from <code>vocal_remover.py</code></i></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🎧 2. Binaural Surround Splitter</h3>
        <p>Directional audio separation. Directs backing instruments into one ear and isolated vocals into the other with configurable crossfeed to eliminate headphone ear fatigue.</p>
        <p><i>Derived and enhanced from <code>surroundSound.py</code></i></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h3>🎼 4. AI BGM & Vocal Extractor</h3>
        <p>High-fidelity stem separation. Isolates clean Background Music (BGM/Accompaniment) and Acapella vocal tracks using neural networks and spectral harmonic-percussive decomposition.</p>
        <p><i>Derived and enhanced from <code>audionumpy.py</code></i></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# System Diagnostics / Environment Status
st.subheader("🖥️ System & Audio Engine Status")

col_sys1, col_sys2, col_sys3, col_sys4 = st.columns(4)

ffmpeg_path = shutil.which("ffmpeg")
with col_sys1:
    st.metric(
        "Python Runtime",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "Active"
    )

with col_sys2:
    st.metric(
        "FFmpeg Engine",
        "Found" if ffmpeg_path else "Missing",
        "Ready" if ffmpeg_path else "Install Required"
    )

with col_sys3:
    try:
        import torch
        cuda_status = f"CUDA ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else "CPU Mode"
    except Exception:
        cuda_status = "Not Installed"
    st.metric("PyTorch Acceleration", cuda_status)

with col_sys4:
    st.metric("Audio I/O Formats", "WAV, MP3, FLAC, OGG, M4A", "Multi-format")

st.markdown("---")
st.info("👈 **Use the sidebar on the left** to navigate to any audio module.", icon="🧭")
