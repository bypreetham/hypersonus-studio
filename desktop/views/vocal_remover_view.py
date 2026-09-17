import os
import flet as ft
from desktop.theme import create_card, PINK_ACCENT, TEXT_PRIMARY, TEXT_MUTED
from desktop.components.dsp_slider import DSPSlider
from desktop.components.audio_player import DesktopAudioPlayer
from utils.audio_io import load_audio
from utils.vocal_remover import remove_vocals_phase

class VocalRemoverView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

        self.samples = None
        self.fs = None
        self.filename = None

        # File Picker
        self.file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.page.overlay.append(self.file_picker)

        self.file_status = ft.Text("No audio file selected", size=13, color=TEXT_MUTED)
        self.select_btn = ft.ElevatedButton(
            "Select Stereo Audio File",
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
                        ft.Text("Input Stereo Track", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        self.file_status,
                    ], spacing=4),
                    self.select_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # DSP Controls
        self.bass_checkbox = ft.Checkbox(
            label="Preserve Sub-Bass & Kick Drum",
            value=True,
            active_color=PINK_ACCENT,
        )
        self.bass_slider = DSPSlider("Bass Protection Cutoff", 60, 250, 140, step=10, unit=" Hz")
        self.gain_slider = DSPSlider("Output Gain Compensation", 0.8, 2.0, 1.2, step=0.1, unit="x")

        sliders_card = create_card(
            ft.Column([
                ft.Text("🎛️ Phase Inversion Parameters", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                self.bass_checkbox,
                ft.Row([
                    ft.Column([self.bass_slider], expand=True),
                    ft.Column([self.gain_slider], expand=True),
                ], spacing=20),
            ], spacing=12)
        )

        # Process Action
        self.progress_ring = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=3, color=PINK_ACCENT)
        self.process_btn = ft.FilledButton(
            "Remove Center Lead Vocals",
            icon=ft.Icons.MIC_OFF_ROUNDED,
            disabled=True,
            on_click=self._process_audio,
        )

        action_row = ft.Row([self.process_btn, self.progress_ring], alignment=ft.MainAxisAlignment.START)

        # Audio Players
        self.orig_player = DesktopAudioPlayer("Original Song", PINK_ACCENT)
        self.proc_player = DesktopAudioPlayer("Instrumental (Karaoke Backing)", PINK_ACCENT)

        players_row = ft.Row([
            ft.Container(self.orig_player, expand=True),
            ft.Container(self.proc_player, expand=True),
        ], spacing=16)

        self.controls = [
            ft.Text("🎙️ Fast Center-Channel Vocal Remover", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Instantly suppresses center-panned vocals via stereo phase cancellation with intelligent bass retention.", size=13, color=TEXT_MUTED),
            file_card,
            sliders_card,
            action_row,
            players_row,
        ]

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files or len(e.files) == 0:
            return
        path = e.files[0].path
        try:
            self.samples, self.fs = load_audio(path)
            self.filename = os.path.basename(path)
            if self.samples.ndim < 2 or self.samples.shape[1] < 2:
                self.file_status.value = f"Warning: {self.filename} is Mono (Phase cancellation needs Stereo)."
                self.file_status.color = PINK_ACCENT
            else:
                self.file_status.value = f"Loaded: {self.filename}"
                self.file_status.color = PINK_ACCENT
                self.process_btn.disabled = False

            self.orig_player.load_samples(self.samples, self.fs, self.filename)
            self.update()
        except Exception as ex:
            self.file_status.value = f"Error: {ex}"
            self.update()

    def _process_audio(self, e):
        if self.samples is None or self.fs is None:
            return

        self.progress_ring.visible = True
        self.process_btn.disabled = True
        self.update()

        try:
            processed = remove_vocals_phase(
                samples=self.samples,
                fs=self.fs,
                preserve_bass=self.bass_checkbox.value,
                bass_cutoff_hz=self.bass_slider.get_value(),
                gain_boost=self.gain_slider.get_value(),
            )
            base_name, _ = os.path.splitext(self.filename)
            self.proc_player.load_samples(processed, self.fs, f"{base_name}_Instrumental.wav")
        except Exception as ex:
            self.file_status.value = f"Error: {ex}"
        finally:
            self.progress_ring.visible = False
            self.process_btn.disabled = False
            self.update()
