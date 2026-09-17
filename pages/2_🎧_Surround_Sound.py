import streamlit as st
import os
from utils.spatializer import apply_surround_split
from components.file_uploader import render_file_uploader
from components.parameter_controls import render_dsp_controls
from components.audio_player import render_audio_comparison, render_download_button
from components.visualizer import render_waveform_comparison

st.set_page_config(page_title="Binaural Surround Splitter", page_icon="🎧", layout="wide")

st.title("🎧 Binaural Surround Sound Splitter")
st.caption("Splits vocals and instrumental backing tracks into separate left/right audio channels for distinct spatial clarity.")

# File uploader
uploaded = render_file_uploader(key="surround_upload")

if uploaded is not None:
    samples, fs, filename = uploaded
    st.divider()

    # Parameter Controls
    params = render_dsp_controls("surround_sound")

    if st.button("🚀 Process Surround Audio", type="primary", use_container_width=True):
        with st.spinner("Splitting stereo channels..."):
            processed = apply_surround_split(
                samples=samples,
                fs=fs,
                lowcut=params["lowcut"],
                highcut=params["highcut"],
                swap_channels=params["swap_channels"],
                crossfeed=params["crossfeed"]
            )

        st.success("✅ Surround Processing Complete! Best experienced with headphones 🎧.")

        ear_config = "Left: Vocals | Right: Instruments" if params["swap_channels"] else "Left: Instruments | Right: Vocals"
        render_audio_comparison(
            original_samples=samples,
            processed_samples=processed,
            fs=fs,
            original_label="Original Track",
            processed_label=f"Surround Sound ({ear_config})"
        )

        st.markdown("---")
        st.subheader("📊 Left vs Right Channel Separation")
        render_waveform_comparison(
            samples_a=samples,
            samples_b=processed,
            fs=fs,
            label_a="Original",
            label_b="Surround Split (L: Cyan / R: Gold)"
        )

        base_name, _ = os.path.splitext(filename)
        output_name = f"{base_name}_Surround_Split.wav"
        render_download_button(processed, fs, output_name, "Download Surround Split Audio (.WAV)")
