import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def set_plot_style():
    plt.style.use("dark_background")
    plt.rcParams["figure.facecolor"] = "#0E1117"
    plt.rcParams["axes.facecolor"] = "#1A1C23"
    plt.rcParams["axes.edgecolor"] = "#2E3440"
    plt.rcParams["axes.labelcolor"] = "#E5E9F0"
    plt.rcParams["xtick.color"] = "#8892B0"
    plt.rcParams["ytick.color"] = "#8892B0"
    plt.rcParams["grid.color"] = "#2E3440"

def render_waveform_comparison(
    samples_a: np.ndarray,
    samples_b: np.ndarray,
    fs: int,
    label_a: str = "Original",
    label_b: str = "Processed",
    max_display_seconds: float = 30.0
):
    """
    Renders comparative dual waveforms using high-contrast sleek styling.
    """
    set_plot_style()
    
    # Downsample for snappy rendering
    max_pts = int(fs * max_display_seconds)
    sig_a = samples_a[:max_pts]
    sig_b = samples_b[:max_pts]
    
    # Downsample if still very large
    stride = max(1, len(sig_a) // 4000)
    sig_a = sig_a[::stride]
    sig_b = sig_b[::stride]
    
    time_axis = np.linspace(0, min(len(samples_a) / fs, max_display_seconds), len(sig_a))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 3.5), sharex=True)
    
    # Track A
    if sig_a.ndim > 1 and sig_a.shape[1] > 1:
        ax1.plot(time_axis, sig_a[:, 0], color="#00E5FF", alpha=0.8, label="Left / Mono")
        ax1.plot(time_axis, sig_a[:, 1], color="#7C4DFF", alpha=0.6, label="Right")
    else:
        ax1.plot(time_axis, sig_a, color="#00E5FF", alpha=0.9, label=label_a)
    ax1.set_title(f"Waveform: {label_a}", fontsize=11, color="#00E5FF", loc="left")
    ax1.set_ylim(-1.05, 1.05)
    ax1.grid(True, alpha=0.3)

    # Track B
    min_b_pts = min(len(time_axis), len(sig_b))
    if sig_b.ndim > 1 and sig_b.shape[1] > 1:
        ax2.plot(time_axis[:min_b_pts], sig_b[:min_b_pts, 0], color="#FF4081", alpha=0.8, label="Left")
        ax2.plot(time_axis[:min_b_pts], sig_b[:min_b_pts, 1], color="#FFD700", alpha=0.6, label="Right")
    else:
        ax2.plot(time_axis[:min_b_pts], sig_b[:min_b_pts], color="#FF4081", alpha=0.9, label=label_b)
    ax2.set_title(f"Waveform: {label_b}", fontsize=11, color="#FF4081", loc="left")
    ax2.set_xlabel("Time (seconds)", fontsize=9)
    ax2.set_ylim(-1.05, 1.05)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

def render_spectrogram(samples: np.ndarray, fs: int, title: str = "Spectrogram"):
    """Renders a frequency spectrogram for frequency analysis."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 2.5))
    
    sig = samples[:, 0] if samples.ndim > 1 else samples
    # Max 10 seconds for fast calculation
    sig = sig[:fs * 10]
    
    ax.specgram(sig, Fs=fs, NFFT=1024, noverlap=512, cmap="magma")
    ax.set_title(title, fontsize=10, color="#FF9100", loc="left")
    ax.set_ylabel("Frequency (Hz)", fontsize=8)
    ax.set_xlabel("Time (s)", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
