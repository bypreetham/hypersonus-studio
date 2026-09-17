import streamlit as st
import os
from utils.vocal_remover import remove_vocals_phase
from components.file_uploader import render_file_uploader
from components.parameter_controls import render_dsp_controls
from components.audio_player import render_audio_comparison, render_download_button
from components.visualizer import render_waveform_comparison

st.set_page_config(page_title="Fast Vocal Remover", page_icon="🎙️", layout="wide")

st.title("🎙️ Fast Center-Channel Vocal Remover")
st.caption("Instantly eliminates center-panned lead vocals using stereo phase inversion with intelligent bass preservation.")

uploaded = render_file_uploader(key="vocal_remover_upload")

if uploaded is not None:
    samples, fs, filename = uploaded
    st.divider()

    if samples.ndim < 2 or samples.shape[1] < 2:
        st.warning("⚠️ The uploaded audio is Mono (single channel). Phase-inversion vocal removal requires a Stereo track with center-panned vocals. For mono tracks, please use the AI BGM Extractor page instead.")
    else:
        params = render_dsp_controls("vocal_remover")

        if st.button("🚀 Remove Lead Vocals", type="primary", use_container_width=True):
            with st.spinner("Cancelling center-channel vocals..."):
                instrumental = remove_vocals_phase(
                    samples=samples,
                    fs=fs,
                    preserve_bass=params["preserve_bass"],
                    bass_cutoff_hz=params["bass_cutoff_hz"],
                    gain_boost=params["gain_boost"]
                )

            st.success("✅ Lead vocals removed! Play the instrumental below:")

            render_audio_comparison(
                original_samples=samples,
                processed_samples=instrumental,
                fs=fs,
                original_label="Original Song",
                processed_label="Instrumental (Karaoke Backing)"
            )

            st.markdown("---")
            st.subheader("📊 Waveform Comparison (Original vs Instrumental)")
            render_waveform_comparison(
                samples_a=samples,
                samples_b=instrumental,
                fs=fs,
                label_a="Original",
                label_b="Instrumental (Vocals Suppressed)"
            )

            base_name, _ = os.path.splitext(filename)
            output_name = f"{base_name}_Instrumental.wav"
            render_download_button(instrumental, fs, output_name, "Download Instrumental (.WAV)")
