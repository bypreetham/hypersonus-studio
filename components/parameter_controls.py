import streamlit as st
from typing import Dict, Any

def render_dsp_controls(module_type: str) -> Dict[str, Any]:
    """
    Renders modular tuning parameters based on the selected DSP module.
    """
    params = {}

    if module_type == "3d_ping_pong":
        st.markdown("### 🎛️ Spatial & Filter Parameters")
        c1, c2 = st.columns(2)
        with c1:
            params["chunk_duration"] = st.slider(
                "Cycle Duration (Seconds per Pan)",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.25,
                help="Shorter values cause faster left-right alternation. Longer values yield smooth cinematic panning."
            )
            params["pan_depth"] = st.slider(
                "Panning Depth (Stereo Width)",
                min_value=0.2,
                max_value=1.0,
                value=1.0,
                step=0.05,
                help="1.0 is full left-to-right sweep. Lower values keep more sound centered."
            )
        with c2:
            freq_range = st.slider(
                "Vocal Isolation Frequency Band (Hz)",
                min_value=100,
                max_value=10000,
                value=(250, 6000),
                step=50,
                help="Frequencies kept centered as vocal presence."
            )
            params["lowcut"] = freq_range[0]
            params["highcut"] = freq_range[1]
            params["vocal_center_mix"] = st.slider(
                "Center Vocal Mix Volume",
                min_value=0.0,
                max_value=1.5,
                value=1.0,
                step=0.1
            )

    elif module_type == "surround_sound":
        st.markdown("### 🎛️ Channel Splitting Controls")
        c1, c2 = st.columns(2)
        with c1:
            params["swap_channels"] = st.checkbox(
                "Swap Ears (Left: Vocals, Right: Instruments)",
                value=False,
                help="Default is Left: Instruments, Right: Vocals."
            )
            params["crossfeed"] = st.slider(
                "Crossfeed Blend (Reduces Ear Fatigue)",
                min_value=0.0,
                max_value=0.35,
                value=0.12,
                step=0.01,
                help="Blends a small percentage between channels so full silence isn't felt in either ear."
            )
        with c2:
            freq_range = st.slider(
                "Vocal Filter Range (Hz)",
                min_value=100,
                max_value=8000,
                value=(250, 6000),
                step=50
            )
            params["lowcut"] = freq_range[0]
            params["highcut"] = freq_range[1]

    elif module_type == "vocal_remover":
        st.markdown("### 🎛️ Phase Inversion Settings")
        c1, c2 = st.columns(2)
        with c1:
            params["preserve_bass"] = st.checkbox(
                "Preserve Bass & Sub-frequencies",
                value=True,
                help="Protects center-panned kick drums and sub-bass lines from cancellation."
            )
            params["bass_cutoff_hz"] = st.slider(
                "Bass Retention Cutoff (Hz)",
                min_value=60,
                max_value=250,
                value=140,
                step=10,
                disabled=not params.get("preserve_bass", True)
            )
        with c2:
            params["gain_boost"] = st.slider(
                "Output Gain Compensation",
                min_value=0.8,
                max_value=2.0,
                value=1.2,
                step=0.1,
                help="Compensates for volume drop caused by channel subtraction."
            )

    return params
