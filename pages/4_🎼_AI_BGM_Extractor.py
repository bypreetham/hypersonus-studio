import streamlit as st
import os
from utils.stem_separator import separate_stems, is_spleeter_available
from components.file_uploader import render_file_uploader
from components.audio_player import render_download_button
from components.visualizer import render_waveform_comparison
from utils.audio_io import audio_to_bytes

st.set_page_config(page_title="AI BGM & Vocal Extractor", page_icon="🎼", layout="wide")

st.title("🎼 AI BGM & Vocal Extractor")
st.caption("Isolates clean Background Music (BGM/Accompaniment) and Acapella Vocals into individual studio stems.")

# Show engine status
spleeter_ready = is_spleeter_available()
if spleeter_ready:
    st.info("🤖 Spleeter Deep Learning Engine detected and ready.", icon="✨")
else:
    st.info("⚡ High-Speed Harmonic-Percussive Spectral DSP Engine active.", icon="🚀")

uploaded = render_file_uploader(key="bgm_upload")

if uploaded is not None:
    samples, fs, filename = uploaded
    st.divider()

    st.markdown("### ⚙️ Separation Engine")
    engine_options = ["Spectral DSP (Instant)"]
    if spleeter_ready:
        engine_options.insert(0, "Spleeter (Neural Network)")

    selected_engine = st.selectbox("Select Engine", options=engine_options)
    engine_key = "spleeter" if "Spleeter" in selected_engine else "dsp"

    if st.button("🚀 Extract BGM & Vocals", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def on_progress(percent: float, message: str):
            progress_bar.progress(percent)
            status_text.text(f"⏳ {message}")

        vocals, bgm, engine_used = separate_stems(
            samples=samples,
            fs=fs,
            engine=engine_key,
            progress_callback=on_progress
        )

        st.success(f"✅ Stem separation complete using {engine_used}!")

        # Stem comparison
        tab1, tab2 = st.tabs(["🎵 Isolated BGM (Accompaniment)", "🎤 Isolated Vocals (Acapella)"])

        base_name, _ = os.path.splitext(filename)

        with tab1:
            st.markdown("#### 🎼 Background Music (BGM / Instruments)")
            bgm_bytes = audio_to_bytes(bgm, fs)
            st.audio(bgm_bytes, format="audio/wav")
            render_download_button(bgm, fs, f"{base_name}_BGM.wav", "Download BGM Track (.WAV)", key="dl_bgm")
            render_waveform_comparison(samples, bgm, fs, label_a="Original", label_b="Extracted BGM")

        with tab2:
            st.markdown("#### 🎙️ Isolated Vocals (Acapella)")
            voc_bytes = audio_to_bytes(vocals, fs)
            st.audio(voc_bytes, format="audio/wav")
            render_download_button(vocals, fs, f"{base_name}_Vocals.wav", "Download Vocal Track (.WAV)", key="dl_voc")
            render_waveform_comparison(samples, vocals, fs, label_a="Original", label_b="Isolated Vocals")
