import os
import flet as ft
import numpy as np
from desktop.theme import (
    create_card, create_badge, AMBER_ACCENT, CYAN_ACCENT,
    TEXT_PRIMARY, TEXT_MUTED
)
from desktop.components.dsp_slider import DSPSlider
from desktop.components.audio_player import DesktopAudioPlayer
from utils.song_item import SongItem
from utils.vocal_remover import extract_vocals_phase, extract_vocals_multistage_dsp
from utils.stem_separator import separate_stems, is_spleeter_available

class VocalExtractorView(ft.Column):
    """
    Dedicated Acapella & Lead Vocal Extractor View.
    Isolates clean vocals using STFT spectral center coherence masking,
    harmonic-percussive decomposition, or deep learning neural networks.
    """
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

        self.song_item: SongItem = None

        # Native File Picker
        self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.page.overlay.append(self.file_picker)

        self.file_status = ft.Text("No audio file selected", size=13, color=TEXT_MUTED)
        self.select_btn = ft.ElevatedButton(
            "Select Audio File",
            icon=ft.Icons.AUDIO_FILE_ROUNDED,
            on_click=lambda _: self.file_picker.pick_files(
                allowed_extensions=["wav", "mp3", "flac", "ogg", "m4a"],
                allow_multiple=False,
            ),
        )

        file_card = create_card(
            ft.Row(
                controls=[
                    ft.Column([
                        ft.Text("Input Song for Vocal Extraction", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        self.file_status,
                    ], spacing=4),
                    self.select_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Region Selection Controls (Start Pos & End Pos)
        self.range_info_badge = create_badge("Full Track (00:00.0 - 00:00.0)", AMBER_ACCENT)

        self.start_pos_slider = DSPSlider("Start Position", 0.0, 100.0, 0.0, step=0.5, unit="s", on_change=self._on_range_slider_changed)
        self.end_pos_slider = DSPSlider("End Position", 0.0, 100.0, 100.0, step=0.5, unit="s", on_change=self._on_range_slider_changed)

        self.set_start_btn = ft.OutlinedButton(
            "Set Start to Playhead",
            icon=ft.Icons.START_ROUNDED,
            disabled=True,
            on_click=self._set_start_from_playhead,
        )
        self.set_end_btn = ft.OutlinedButton(
            "Set End to Playhead",
            icon=ft.Icons.FLAG_ROUNDED,
            disabled=True,
            on_click=self._set_end_from_playhead,
        )
        self.reset_range_btn = ft.TextButton(
            "Reset to Full Track",
            icon=ft.Icons.RESTART_ALT_ROUNDED,
            disabled=True,
            on_click=self._reset_full_range,
        )

        region_card = create_card(
            ft.Column([
                ft.Row(
                    controls=[
                        ft.Text("✂️ Vocal Segment & Region Selection", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        self.range_info_badge,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row([
                    ft.Column([self.start_pos_slider], expand=True),
                    ft.Column([self.end_pos_slider], expand=True),
                ], spacing=20),
                ft.Row(
                    controls=[
                        ft.Row([self.set_start_btn, self.set_end_btn], spacing=8),
                        self.reset_range_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ], spacing=10)
        )

        # Extraction Engine Selection
        spleeter_ok = is_spleeter_available()
        engine_options = [
            ft.dropdown.Option("multistage", "🚀 Multi-Stage Spectral Isolator (HPSS + Side Subtraction + VAD Gate) [Recommended]"),
            ft.dropdown.Option("phase", "⚡ Fast Center Coherence (Legacy Phase Mask)"),
            ft.dropdown.Option("spectral", "🎼 Spectral Harmonic Extraction (Harmonic-Percussive Separation)"),
        ]
        if spleeter_ok:
            engine_options.append(ft.dropdown.Option("spleeter", "🧠 Spleeter Neural Network (Deep Learning Acapella Model)"))

        self.engine_dropdown = ft.Dropdown(
            label="Vocal Extraction Engine",
            options=engine_options,
            value="multistage",
            width=560,
            on_change=self._on_engine_change,
        )

        # Vocal Tuning Controls
        self.music_suppression = DSPSlider("Music Suppression Strength (Side Cancellation)", 0.5, 3.0, 1.6, step=0.1, unit="x")
        self.gate_threshold = DSPSlider("Vocal Activity Gate (Silence Intro/Breaks)", 0.0, 0.8, 0.40, step=0.05, unit="")
        self.harmonic_margin = DSPSlider("Harmonic Vocal Focus (Guitar Pluck / Transient Rejection)", 1.0, 3.0, 1.5, step=0.1, unit="x")
        self.vocal_lowcut = DSPSlider("Vocal Highpass Cutoff (Bass Reject)", 60, 300, 120, step=10, unit=" Hz")
        self.vocal_highcut = DSPSlider("Vocal Lowpass Cutoff (Cymbal Reject)", 4000, 12000, 7500, step=500, unit=" Hz")
        self.gain_slider = DSPSlider("Vocal Output Gain", 0.8, 2.5, 1.2, step=0.1, unit="x")

        self.dsp_tuning_col = ft.Column([
            ft.Text("🎤 Spectral Vocal Filters & Music Suppression Tuning", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Row([
                ft.Column([self.music_suppression], expand=True),
                ft.Column([self.gate_threshold], expand=True),
            ], spacing=20),
            ft.Row([
                ft.Column([self.harmonic_margin], expand=True),
                ft.Column([self.gain_slider], expand=True),
            ], spacing=20),
            ft.Row([
                ft.Column([self.vocal_lowcut], expand=True),
                ft.Column([self.vocal_highcut], expand=True),
            ], spacing=20),
        ], spacing=10, visible=True)

        self.engine_hint_text = ft.Text(
            "Multi-Stage Isolator: Side-channel spectral subtraction removes stereo instruments, HPSS strips guitar plucks, and dynamic VAD gates out non-vocal sections.",
            size=12,
            color=TEXT_MUTED,
        )

        engine_card = create_card(
            ft.Column([
                ft.Text("⚙️ Engine & Vocal Filter Controls", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                self.engine_dropdown,
                self.engine_hint_text,
                self.dsp_tuning_col,
            ], spacing=12)
        )

        # Process Action
        self.progress_ring = ft.ProgressRing(visible=False, width=22, height=22, stroke_width=3, color=AMBER_ACCENT)
        self.extract_btn = ft.FilledButton(
            "Extract Acapella Vocals",
            icon=ft.Icons.MIC_ROUNDED,
            disabled=True,
            style=ft.ButtonStyle(bgcolor=AMBER_ACCENT, color="#0A0E17"),
            on_click=self._process_audio,
        )

        action_row = ft.Row([self.extract_btn, self.progress_ring], alignment=ft.MainAxisAlignment.START, spacing=12)

        # Audio Players: Original & Extracted Vocals
        self.orig_player = DesktopAudioPlayer("Original Track (SongItem)", CYAN_ACCENT)
        self.voc_player = DesktopAudioPlayer("Isolated Acapella Vocals", AMBER_ACCENT)

        orig_row = ft.Row([
            ft.Container(self.orig_player, expand=True),
        ])

        output_row = ft.Row([
            ft.Container(self.voc_player, expand=True),
        ])

        self.controls = [
            ft.Text("🎤 Acapella Vocal Extractor", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Extracts clean lead vocals and speech from songs by stripping away background music and stereo instrumentation.", size=13, color=TEXT_MUTED),
            file_card,
            orig_row,
            region_card,
            engine_card,
            action_row,
            output_row,
        ]

    def _on_engine_change(self, e):
        val = self.engine_dropdown.value
        if val == "multistage":
            self.dsp_tuning_col.visible = True
            self.engine_hint_text.value = "Multi-Stage Isolator: Side spectral subtraction strips stereo guitars/music, HPSS separates plucks, and dynamic VAD gates non-singing sections."
        elif val == "phase":
            self.dsp_tuning_col.visible = True
            self.engine_hint_text.value = "STFT Center Coherence analyzes spectral phase agreement to isolate lead vocals from stereo backing."
        elif val == "spectral":
            self.dsp_tuning_col.visible = False
            self.engine_hint_text.value = "Spectral Harmonic Separation isolates continuous vocal formants from percussive and transient instrument sounds."
        elif val == "spleeter":
            self.dsp_tuning_col.visible = False
            self.engine_hint_text.value = "Spleeter uses deep learning neural networks to isolate high-fidelity vocals."
        self.update()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files or len(e.files) == 0:
            return
        path = e.files[0].path
        try:
            self.song_item = SongItem.from_file(path)

            dur = self.song_item.duration_seconds
            status_text = f"Loaded: {self.song_item.filename} ({self.song_item.format_time(dur)})"
            if self.song_item.channels < 2:
                status_text += " [Mono - Spectral harmonic mode recommended]"

            self.file_status.value = status_text
            self.file_status.color = AMBER_ACCENT
            self.extract_btn.disabled = False

            # Configure Region Sliders
            self.start_pos_slider.slider.min = 0.0
            self.start_pos_slider.slider.max = dur
            self.start_pos_slider.slider.value = 0.0
            self.start_pos_slider.slider.divisions = max(10, int(dur * 2))
            self.start_pos_slider.value_label.value = f"0.0s ({SongItem.format_time(0.0)})"

            self.end_pos_slider.slider.min = 0.0
            self.end_pos_slider.slider.max = dur
            self.end_pos_slider.slider.value = dur
            self.end_pos_slider.slider.divisions = max(10, int(dur * 2))
            self.end_pos_slider.value_label.value = f"{dur:.1f}s ({SongItem.format_time(dur)})"

            self.set_start_btn.disabled = False
            self.set_end_btn.disabled = False
            self.reset_range_btn.disabled = False

            self._update_range_badge()
            self.orig_player.load_samples(self.song_item.samples, self.song_item.fs, self.song_item.filename)
            self.update()
        except Exception as ex:
            self.file_status.value = f"Error: {ex}"
            self.update()

    def _on_range_slider_changed(self, val):
        if not self.song_item:
            return
        start_val = self.start_pos_slider.get_value()
        end_val = self.end_pos_slider.get_value()

        if start_val > end_val:
            end_val = start_val
            self.end_pos_slider.slider.value = end_val
            self.end_pos_slider.value_label.value = f"{end_val:.1f}s ({SongItem.format_time(end_val)})"

        self.song_item.set_range(start_val, end_val)
        self._update_range_badge()

    def _update_range_badge(self):
        if not self.song_item:
            return
        s_str = SongItem.format_time(self.song_item.start_pos)
        e_str = SongItem.format_time(self.song_item.end_pos)
        dur_str = SongItem.format_time(self.song_item.range_duration)
        self.range_info_badge.content.value = f"Selected Range: {s_str} - {e_str} (Duration: {dur_str})"
        self.range_info_badge.update()

    def _set_start_from_playhead(self, e):
        if not self.song_item:
            return
        cur_pos = self.orig_player.get_current_position()
        self.start_pos_slider.slider.value = cur_pos
        self.start_pos_slider.value_label.value = f"{cur_pos:.1f}s ({SongItem.format_time(cur_pos)})"
        self.start_pos_slider.update()
        self._on_range_slider_changed(cur_pos)

    def _set_end_from_playhead(self, e):
        if not self.song_item:
            return
        cur_pos = self.orig_player.get_current_position()
        self.end_pos_slider.slider.value = cur_pos
        self.end_pos_slider.value_label.value = f"{cur_pos:.1f}s ({SongItem.format_time(cur_pos)})"
        self.end_pos_slider.update()
        self._on_range_slider_changed(cur_pos)

    def _reset_full_range(self, e):
        if not self.song_item:
            return
        dur = self.song_item.duration_seconds
        self.start_pos_slider.slider.value = 0.0
        self.start_pos_slider.value_label.value = f"0.0s ({SongItem.format_time(0.0)})"
        self.start_pos_slider.update()

        self.end_pos_slider.slider.value = dur
        self.end_pos_slider.value_label.value = f"{dur:.1f}s ({SongItem.format_time(dur)})"
        self.end_pos_slider.update()

        self.song_item.set_range(0.0, dur)
        self._update_range_badge()

    def _process_audio(self, e):
        if self.song_item is None:
            return

        self.extract_btn.disabled = True
        self.progress_ring.visible = True
        self.update()

        try:
            trimmed_samples = self.song_item.get_trimmed_samples()
            fs = self.song_item.fs
            engine_choice = self.engine_dropdown.value or "phase"

            base_name, _ = os.path.splitext(self.song_item.filename)
            range_tag = f"_{int(self.song_item.start_pos)}s-{int(self.song_item.end_pos)}s" if self.song_item.range_duration < self.song_item.duration_seconds else ""

            if engine_choice == "multistage":
                vocals = extract_vocals_multistage_dsp(
                    samples=trimmed_samples,
                    fs=fs,
                    music_suppression=self.music_suppression.get_value(),
                    gate_threshold=self.gate_threshold.get_value(),
                    harmonic_margin=self.harmonic_margin.get_value(),
                    lowcut_hz=self.vocal_lowcut.get_value(),
                    highcut_hz=self.vocal_highcut.get_value(),
                    gain_boost=self.gain_slider.get_value(),
                )
                engine_label = "Multi-Stage Spectral Isolator"
            elif engine_choice == "phase":
                vocals = extract_vocals_phase(
                    samples=trimmed_samples,
                    fs=fs,
                    lowcut_hz=self.vocal_lowcut.get_value(),
                    highcut_hz=self.vocal_highcut.get_value(),
                    sensitivity=self.music_suppression.get_value(),
                    gain_boost=self.gain_slider.get_value(),
                )
                engine_label = "Fast Stereo DSP"
            else:
                vocals, _, engine_label = separate_stems(
                    samples=trimmed_samples,
                    fs=fs,
                    engine=engine_choice,
                )

            self.voc_player.load_samples(vocals, fs, f"{base_name}{range_tag}_Vocals.wav")
            self.file_status.value = f"Vocal extraction complete via {engine_label}!"
        except Exception as ex:
            self.file_status.value = f"Error: {ex}"
        finally:
            self.extract_btn.disabled = False
            self.progress_ring.visible = False
            self.update()
