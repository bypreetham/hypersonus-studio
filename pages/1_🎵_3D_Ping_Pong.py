import streamlit as st
import os
from utils.spatializer import apply_ping_pong_3d
from components.file_uploader import render_file_uploader
from components.parameter_controls import render_dsp_controls
from components.audio_player import render_audio_comparison, render_download_button
from components.visualizer import render_waveform_comparison

st.set_page_config(page_title="3D Ping Pong Audio", page_icon="🎵", layout="wide")

st.title("🎵 3D Ping-Pong Spatializer")
st.caption("Creates an immersive binaural 3D effect alternating instruments left-to-right while keeping vocals centered.")

# File uploader
uploaded = render_file_uploader(key="ping_pong_upload")

if uploaded is not None:
    samples, fs, filename = uploaded
    st.divider()

    # Parameter Controls
    params = render_dsp_controls("3d_ping_pong")

    if st.button("🚀 Process 3D Ping-Pong Audio", type="primary", use_container_width=True):
        with st.spinner("Synthesizing 3D Ping-Pong audio..."):
            processed = apply_ping_pong_3d(
                samples=samples,
                fs=fs,
                chunk_duration=params["chunk_duration"],
                lowcut=params["lowcut"],
                highcut=params["highcut"],
                pan_depth=params["pan_depth"],
                vocal_center_mix=params["vocal_center_mix"],
            )

        st.success("✅ 3D Audio Processing Complete! Put on headphones 🎧 for the best spatial experience.")
        
        # Audio Comparison
        render_audio_comparison(
            original_samples=samples,
            processed_samples=processed,
            fs=fs,
            original_label="Original Track",
            processed_label=f"3D Ping-Pong ({params['chunk_duration']}s Cycle)"
        )

        st.markdown("---")
        # Waveform Visualizer
        st.subheader("📊 Stereo Spatial Waveforms")
        render_waveform_comparison(
            samples_a=samples,
            samples_b=processed,
            fs=fs,
            label_a="Original",
            label_b="3D Ping-Pong Stereo"
        )

        # Download Button
        base_name, _ = os.path.splitext(filename)
        output_name = f"{base_name}_3D_PingPong.wav"
        render_download_button(processed, fs, output_name, "Download 3D Spatial Audio (.WAV)")
