import os
import time
import threading
import flet as ft
import numpy as np

from desktop.theme import (
    create_card, create_badge, CYAN_ACCENT, PURPLE_ACCENT, PINK_ACCENT,
    AMBER_ACCENT, GREEN_ACCENT, TEXT_PRIMARY, TEXT_MUTED
)
from desktop.components.dsp_slider import DSPSlider
from desktop.components.audio_player import DesktopAudioPlayer
from utils.song_item import SongItem
from utils.audio_io import save_audio
from utils.demucs_splitter import (
    get_demucs_info, separate_stems_demucs, create_instrumental_mix
)

# Colors and icons for different stems
STEM_CONFIG = {
    "vocals": {"title": "🎤 Lead Vocals", "color": PINK_ACCENT, "desc": "Isolated singing and vocal speech"},
    "drums": {"title": "🥁 Drums & Percussion", "color": CYAN_ACCENT, "desc": "Snare, kick, cymbals, hi-hats, percussive transients"},
    "bass": {"title": "🎸 Bassline", "color": PURPLE_ACCENT, "desc": "Sub-bass, 808s, bass guitar, and low-end groove"},
    "guitar": {"title": "🎸 Guitar", "color": AMBER_ACCENT, "desc": "Acoustic and electric guitar leads and rhythm tracks"},
    "piano": {"title": "🎹 Piano & Keys", "color": "#00B4D8", "desc": "Acoustic piano, grand piano, Rhodes, and electric keys"},
    "other": {"title": "🎼 Other (Synths & Backing)", "color": GREEN_ACCENT, "desc": "Synths, strings, brass, orchestral layers, and sound FX"},
}


class DemucsSplitterView(ft.Column):
    """
    Dedicated Demucs Multi-Stem AI Splitter View.
    Supports 4-Stem (Vocals, Drums, Bass, Other) and 6-Stem (including Guitar & Piano)
    powered by Meta AI Demucs v4.
    """
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

        self.song_item: SongItem = None
        self.extracted_stems = {}
        self.extracted_sr = 44100
        self.is_processing = False

        # File Pickers
        self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.folder_picker = ft.FilePicker(on_result=self._on_folder_selected_for_export)
        self.instrumental_save_picker = ft.FilePicker(on_result=self._on_instrumental_save_selected)
        
        self.page.overlay.extend([self.file_picker, self.folder_picker, self.instrumental_save_picker])

        # Hardware & Model Info
        demucs_info = get_demucs_info()
        self.cuda_available = demucs_info.get("cuda_available", False)
        cuda_name = demucs_info.get("cuda_device", "CPU Mode")

        # --- Header Card ---
        header_card = create_card(
            ft.Row(
                controls=[
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CALL_SPLIT_ROUNDED, color=CYAN_ACCENT, size=24),
                            ft.Text("Demucs Neural Audio Splitter", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ], spacing=8),
                        ft.Text(
                            "Separate audio into 4 or 6 discrete studio stems using Meta AI Hybrid Transformer Demucs.",
                            size=13, color=TEXT_MUTED
                        ),
                    ], spacing=4, expand=True),
                    ft.Row([
                        create_badge("Demucs v4", CYAN_ACCENT),
                        create_badge(f"Device: {cuda_name}", GREEN_ACCENT if self.cuda_available else PURPLE_ACCENT),
                    ], spacing=6),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # --- File Selection Card ---
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
                        ft.Text("Source Track for Neural Stem Separation", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        self.file_status,
                    ], spacing=4),
                    self.select_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # --- Range Selection Card ---
        self.range_info_badge = create_badge("Full Track (00:00.0 - 00:00.0)", PINK_ACCENT)
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
                        ft.Text("✂️ Song Region & Range Selection", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
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

        # --- Model & Hardware Controls Card ---
        self.model_dropdown = ft.Dropdown(
            label="Demucs Neural Model & Stem Mode",
            options=[
                ft.dropdown.Option("htdemucs", "HT Demucs — 4 Stems (Vocals, Drums, Bass, Other) [Recommended]"),
                ft.dropdown.Option("htdemucs_6s", "HT Demucs 6S — 6 Stems (Vocals, Drums, Bass, Guitar, Piano, Other)"),
                ft.dropdown.Option("htdemucs_ft", "HT Demucs Fine-Tuned — 4 Stems (Highest Fidelity)"),
                ft.dropdown.Option("hdemucs_mmi", "HDemucs MMI — 4 Stems (v3 Architecture)"),
            ],
            value="htdemucs",
            width=580,
            on_change=self._on_model_change,
        )

        self.device_dropdown = ft.Dropdown(
            label="Execution Device",
            options=[
                ft.dropdown.Option("auto", "Auto (Use CUDA if available)"),
                ft.dropdown.Option("cuda", "CUDA GPU"),
                ft.dropdown.Option("cpu", "CPU Mode"),
            ],
            value="auto",
            width=260,
        )

        self.shifts_dropdown = ft.Dropdown(
            label="Shifts Equivariance",
            options=[
                ft.dropdown.Option("1", "1 Shift (Fastest)"),
                ft.dropdown.Option("2", "2 Shifts (Higher SDR / Quality)"),
            ],
            value="1",
            width=220,
        )

        self.model_info_text = ft.Text(
            "Selected: 4 Stems (Vocals, Drums, Bass, Other). Hybrid Transformer model optimized for standard tracks.",
            size=12, color=TEXT_MUTED
        )

        config_card = create_card(
            ft.Column([
                ft.Text("⚙️ Neural Splitter Configuration", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Row([
                    self.model_dropdown,
                    self.device_dropdown,
                    self.shifts_dropdown,
                ], spacing=16, wrap=True),
                self.model_info_text,
            ], spacing=12)
        )

        # --- Execution & Progress Card ---
        self.separate_btn = ft.ElevatedButton(
            "Separate Stems with Demucs",
            icon=ft.Icons.BOLT_ROUNDED,
            style=ft.ButtonStyle(
                color=TEXT_PRIMARY,
                bgcolor=CYAN_ACCENT,
                padding=ft.padding.symmetric(horizontal=24, vertical=16),
            ),
            disabled=True,
            on_click=self._start_separation,
        )

        self.progress_bar = ft.ProgressBar(value=0.0, color=CYAN_ACCENT, bgcolor="#21262D", visible=False)
        self.progress_label = ft.Text("", size=13, color=TEXT_MUTED, visible=False)
        self.progress_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, color=CYAN_ACCENT, visible=False)

        action_card = create_card(
            ft.Column([
                ft.Row([
                    self.separate_btn,
                    self.progress_spinner,
                    self.progress_label,
                ], spacing=16, alignment=ft.MainAxisAlignment.START),
                self.progress_bar,
            ], spacing=12)
        )

        # --- Input Player Preview ---
        self.input_player = DesktopAudioPlayer(title="Original Track Preview", color_accent=CYAN_ACCENT)

        # --- Stems Player Section ---
        self.stems_title = ft.Text("Separated Audio Stems", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        self.stems_badge = create_badge("Awaiting Separation", TEXT_MUTED)

        # Batch Export Buttons
        self.export_all_btn = ft.ElevatedButton(
            "Export All Stems to Folder",
            icon=ft.Icons.FOLDER_ZIP_ROUNDED,
            disabled=True,
            on_click=lambda _: self.folder_picker.get_directory_path(dialog_title="Select Destination Folder for Stems"),
        )
        self.export_instrumental_btn = ft.OutlinedButton(
            "Export Instrumental Mix (WAV)",
            icon=ft.Icons.MUSIC_NOTE_ROUNDED,
            disabled=True,
            on_click=lambda _: self.instrumental_save_picker.save_file(
                dialog_title="Save Instrumental Mix",
                file_name="instrumental_mix.wav",
                allowed_extensions=["wav"],
            ),
        )

        # Container holding individual stem audio players
        self.stems_deck = ft.Column(spacing=16)

        stems_header = ft.Row(
            controls=[
                ft.Row([self.stems_title, self.stems_badge], spacing=12),
                ft.Row([self.export_instrumental_btn, self.export_all_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Layout Assembly
        self.controls = [
            header_card,
            file_card,
            self.input_player,
            region_card,
            config_card,
            action_card,
            ft.Divider(color="#21262D", height=10),
            stems_header,
            self.stems_deck,
        ]

    def _on_model_change(self, e):
        model_id = self.model_dropdown.value
        if model_id == "htdemucs_6s":
            self.model_info_text.value = "Selected: 6 Stems (Vocals, Drums, Bass, Guitar, Piano, Other). Full band isolation with dedicated guitar and keyboard extraction."
        elif model_id == "htdemucs_ft":
            self.model_info_text.value = "Selected: 4 Stems Fine-Tuned (Vocals, Drums, Bass, Other). Highest fidelity separation trained with extended dataset."
        elif model_id == "hdemucs_mmi":
            self.model_info_text.value = "Selected: 4 Stems Classic (Vocals, Drums, Bass, Other). Demucs v3 Hybrid MMI architecture."
        else:
            self.model_info_text.value = "Selected: 4 Stems (Vocals, Drums, Bass, Other). Fast Hybrid Transformer model."
        self.page.update()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        file_path = e.files[0].path
        try:
            self.song_item = SongItem(file_path)
            self.file_status.value = f"{self.song_item.title} ({self.song_item.duration_formatted}, {self.song_item.sample_rate}Hz)"
            self.file_status.color = CYAN_ACCENT

            # Load into Input Player
            self.input_player.load_audio(
                self.song_item.samples,
                self.song_item.sample_rate,
                filename_prefix=f"{self.song_item.title}_orig",
            )

            # Update Region Sliders
            dur = self.song_item.duration_seconds
            self.start_pos_slider.slider.max = dur
            self.start_pos_slider.set_value(0.0)
            self.end_pos_slider.slider.max = dur
            self.end_pos_slider.set_value(dur)

            self.set_start_btn.disabled = False
            self.set_end_btn.disabled = False
            self.reset_range_btn.disabled = False
            self.separate_btn.disabled = False

            self._update_range_badge()
            self.page.update()
        except Exception as ex:
            self.file_status.value = f"Error loading track: {ex}"
            self.file_status.color = "#FF5252"
            self.page.update()

    def _on_range_slider_changed(self, value):
        if not self.song_item:
            return
        if self.start_pos_slider.value >= self.end_pos_slider.value:
            if self.start_pos_slider.value >= self.song_item.duration_seconds - 0.5:
                self.start_pos_slider.set_value(self.song_item.duration_seconds - 0.5)
            self.end_pos_slider.set_value(self.start_pos_slider.value + 0.5)
        self._update_range_badge()

    def _update_range_badge(self):
        if not self.song_item:
            return
        s = self.start_pos_slider.value
        e = self.end_pos_slider.value
        tot = self.song_item.duration_seconds
        if s <= 0.05 and e >= tot - 0.05:
            self.range_info_badge.content.value = f"Full Track (00:00.0 - {self.song_item.duration_formatted})"
        else:
            diff = e - s
            self.range_info_badge.content.value = f"Range: {s:.1f}s - {e:.1f}s ({diff:.1f}s segment)"
        self.page.update()

    def _set_start_from_playhead(self, e):
        if not self.song_item or not self.input_player:
            return
        pos = min(self.input_player.current_pos, self.end_pos_slider.value - 0.5)
        self.start_pos_slider.set_value(max(0.0, pos))
        self._update_range_badge()

    def _set_end_from_playhead(self, e):
        if not self.song_item or not self.input_player:
            return
        pos = max(self.input_player.current_pos, self.start_pos_slider.value + 0.5)
        self.end_pos_slider.set_value(min(self.song_item.duration_seconds, pos))
        self._update_range_badge()

    def _reset_full_range(self, e):
        if not self.song_item:
            return
        self.start_pos_slider.set_value(0.0)
        self.end_pos_slider.set_value(self.song_item.duration_seconds)
        self._update_range_badge()

    def _start_separation(self, e):
        if not self.song_item or self.is_processing:
            return

        self.is_processing = True
        self.separate_btn.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0.05
        self.progress_label.visible = True
        self.progress_label.value = "Starting Demucs Neural Splitter..."
        self.progress_spinner.visible = True
        self.page.update()

        thread = threading.Thread(target=self._run_separation_thread, daemon=True)
        thread.start()

    def _run_separation_thread(self):
        try:
            # Determine audio segment
            s_sec = self.start_pos_slider.value
            e_sec = self.end_pos_slider.value
            fs = self.song_item.sample_rate

            s_frame = int(s_sec * fs)
            e_frame = int(e_sec * fs)
            input_samples = self.song_item.samples[s_frame:e_frame]

            model_name = self.model_dropdown.value
            device = self.device_dropdown.value
            shifts = int(self.shifts_dropdown.value)

            def _progress_cb(fraction: float, msg: str):
                self.progress_bar.value = max(0.0, min(1.0, fraction))
                self.progress_label.value = msg
                try:
                    self.page.update()
                except Exception:
                    pass

            stems, out_sr = separate_stems_demucs(
                samples=input_samples,
                fs=fs,
                model_name=model_name,
                device=device,
                shifts=shifts,
                progress_callback=_progress_cb,
            )

            self.extracted_stems = stems
            self.extracted_sr = out_sr

            # Render players on UI thread
            self._render_stems_ui(stems, out_sr)

            self.progress_label.value = f"Separation complete! {len(stems)} stems extracted."
            self.progress_bar.value = 1.0
            self.progress_spinner.visible = False
            self.export_all_btn.disabled = False
            self.export_instrumental_btn.disabled = False

        except Exception as ex:
            self.progress_label.value = f"Error during separation: {ex}"
            self.progress_bar.value = 0.0
            self.progress_spinner.visible = False
        finally:
            self.is_processing = False
            self.separate_btn.disabled = False
            try:
                self.page.update()
            except Exception:
                pass

    def _render_stems_ui(self, stems: dict, fs: int):
        self.stems_deck.controls.clear()
        stem_count = len(stems)
        self.stems_badge.content.value = f"{stem_count} Stems Ready"
        self.stems_badge.content.color = GREEN_ACCENT

        track_title = self.song_item.title if self.song_item else "track"

        # Present stems in standardized order
        preferred_order = ["vocals", "drums", "bass", "guitar", "piano", "other"]
        sorted_keys = [k for k in preferred_order if k in stems] + [k for k in stems if k not in preferred_order]

        for stem_name in sorted_keys:
            stem_data = stems[stem_name]
            cfg = STEM_CONFIG.get(stem_name.lower(), {
                "title": f"🎵 {stem_name.capitalize()}",
                "color": CYAN_ACCENT,
                "desc": "Separated stem",
            })

            player = DesktopAudioPlayer(title=cfg["title"], color_accent=cfg["color"])
            player.load_audio(stem_data, fs, filename_prefix=f"{track_title}_{stem_name}")
            
            stem_card = create_card(
                ft.Column([
                    ft.Row([
                        ft.Text(cfg["title"], size=16, weight=ft.FontWeight.BOLD, color=cfg["color"]),
                        create_badge(f"Stereo {fs}Hz", cfg["color"]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(cfg["desc"], size=12, color=TEXT_MUTED),
                    player,
                ], spacing=6)
            )
            self.stems_deck.controls.append(stem_card)

        try:
            self.page.update()
        except Exception:
            pass

    def _on_folder_selected_for_export(self, e: ft.FilePickerResultEvent):
        if not e.path or not self.extracted_stems:
            return

        out_dir = e.path
        track_title = self.song_item.title if self.song_item else "track"
        stems_folder = os.path.join(out_dir, f"{track_title}_Demucs_Stems")
        os.makedirs(stems_folder, exist_ok=True)

        saved_files = []
        for stem_name, stem_data in self.extracted_stems.items():
            dest_file = os.path.join(stems_folder, f"{stem_name}.wav")
            save_audio(dest_file, stem_data, self.extracted_sr)
            saved_files.append(stem_name)

        # Also write instrumental mix
        instr_data = create_instrumental_mix(self.extracted_stems)
        instr_file = os.path.join(stems_folder, "instrumental.wav")
        save_audio(instr_file, instr_data, self.extracted_sr)

        self.progress_label.value = f"Saved {len(saved_files)} stems + instrumental to: {stems_folder}"
        self.progress_label.visible = True
        self.page.update()

    def _on_instrumental_save_selected(self, e: ft.FilePickerResultEvent):
        if not e.path or not self.extracted_stems:
            return
        instr_data = create_instrumental_mix(self.extracted_stems)
        save_audio(e.path, instr_data, self.extracted_sr)
        self.progress_label.value = f"Instrumental mix saved: {os.path.basename(e.path)}"
        self.progress_label.visible = True
        self.page.update()
