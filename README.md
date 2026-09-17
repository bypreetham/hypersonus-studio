# Hypersonus Studio — Multiplatform Audio Processing Suite

Hypersonus Studio is a modular, cross-platform audio engineering application that consolidates 3D spatialization, binaural channel splitting, phase-inversion vocal suppression, and neural stem extraction into a single, unified studio application.

Available both as a **Native Desktop App (Windows, macOS, Linux)** powered by Flet, and an interactive **Browser Studio** powered by Streamlit.

---

## Key Modules

| Module | Derived From | Key Capabilities |
| :--- | :--- | :--- |
| **1. 3D Ping-Pong Spatializer** | `3daudio.py` | Butterworth bandpass vocal isolation, dynamic stereo ping-pong panning cycles (0.5s–5.0s), center vocal lock, stereo width control. |
| **2. Binaural Surround Splitter** | `surroundSound.py` | Frequency-based channel splitting (vocals to one ear, instruments to the other), adjustable crossfeed blend (to prevent ear fatigue), and ear-swap toggle. |
| **3. Fast Vocal Remover** | `vocal_remover.py` | Instant center-channel phase inversion (`L - R`), intelligent lowpass bass preservation (keeps kick & bassline intact), and output gain compensation. |
| **4. AI BGM & Vocal Extractor** | `audionumpy.py` | High-fidelity stem separation into isolated Vocals and Background Music (BGM), supporting Spleeter neural networks and high-speed Spectral DSP decomposition. |

---

##  Architecture

```
Hypersonus-studio/
│
├── desktop/                       # Native Desktop Application (Flet / Flutter)
│   ├── main.py                    # Desktop entry point (1220x840 window, NavigationRail)
│   ├── theme.py                   # Dark theme color tokens & container cards
│   ├── components/                # Reusable desktop widgets (audio player, DSP sliders)
│   └── views/                     # Native views (Home, 3D Ping-Pong, Surround, Vocal Remover, BGM)
│
├── utils/                         # Core Audio DSP Engine (100% Shared & UI-Agnostic)
│   ├── audio_io.py                # Multi-format loader, normalizer, and exporter
│   ├── dsp_filters.py             # Butterworth bandpass filters & Nyquist bounds validation
│   ├── spatializer.py             # 3D ping-pong panning & surround sound channel splitter
│   ├── vocal_remover.py           # Phase-inversion center-channel vocal remover with bass protection
│   └── stem_separator.py          # AI & Spectral DSP stem separator for BGM & Acapella
│
├── pages/                         # Alternative Browser Studio (Streamlit)
├── app.py                         # Browser Studio entry point
├── tests/                         # Automated Unit Tests (Pytest)
│   └── test_dsp.py                # DSP mathematical validation
│
├── run.bat                        # Single launcher (Double-click, CMD, or PowerShell)
├── main.py                        # Root application entry point
│
├── .github/workflows/             # GitHub Actions Automation
│   └── release.yml                # Automatic build of Windows .exe, Mac .dmg, and Linux .AppImage
│
├── requirements.txt               # Pinned dependencies
└── README.md                      # Documentation
```

---

## Quick Start

### Windows
Double-click **`run.bat`** or run in PowerShell / CMD:
```powershell
.\run.bat
```

### Direct Python Command
```powershell
python main.py          # Native Desktop App (Default)
python main.py --web    # Browser Studio (Streamlit)
```

### macOS & Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 📦 Building Standalone Executables (.exe / .dmg / .AppImage)

To build standalone binary installers with zero Python requirement for end-users:

- **Windows (.exe)**:
  ```bash
  flet build windows
  ```
- **macOS (.dmg / .app)**:
  ```bash
  flet build macos
  ```
- **Linux (Executable / AppImage)**:
  ```bash
  flet build linux
  ```

### Automated GitHub Releases
Whenever you push a version tag (e.g. `git tag v1.0.0 && git push origin v1.0.0`), the included **GitHub Actions workflow** (`.github/workflows/release.yml`) will automatically compile the Windows, Mac, and Linux binaries and publish them directly to your repository's Releases page for users to download.

---

## Testing
Run automated DSP test suite:
```powershell
pytest tests/test_dsp.py -v
```

---

## License & Acknowledgments

This project is licensed under the [BSD 3-Clause License](LICENSE) — Copyright (c) 2026 Hari Preetham Lanka.

### Third-Party Libraries
Hypersonus Studio stands on the shoulders of these open-source projects:
- **[Flet](https://flet.dev)** — Apache 2.0
- **[NumPy](https://numpy.org)** & **[SciPy](https://scipy.org)** — BSD 3-Clause
- **[SoundFile](https://python-soundfile.readthedocs.io)** — BSD 3-Clause
- **[SoundDevice](https://python-sounddevice.readthedocs.io)** — MIT
- **[PyDub](https://github.com/jiaaro/pydub)** — MIT
- **[Librosa](https://librosa.org)** — ISC
- **[Streamlit](https://streamlit.io)** — Apache 2.0
- **[FFmpeg](https://ffmpeg.org)** — LGPL / GPL

