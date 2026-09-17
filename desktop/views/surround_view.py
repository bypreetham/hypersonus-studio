import os
import flet as ft
from desktop.theme import create_card, PURPLE_ACCENT, TEXT_PRIMARY, TEXT_MUTED
from desktop.components.dsp_slider import DSPSlider
from desktop.components.audio_player import DesktopAudioPlayer
from utils.audio_io import load_audio
from utils.spatializer import apply_surround_split

class SurroundView(ft.Column):
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
                        ft.Text("Input Audio Track", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        self.file_status,
                    ], spacing=4),
                    self.select_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # DSP Controls
        self.swap_checkbox = ft.Checkbox(
            label="Swap Ears (Left: Vocals, Right: Instruments)",
            value=False,
            active_color=PURPLE_ACCENT,
        )
        self.crossfeed_slider = DSPSlider("Crossfeed Blend (Reduces Fatigue)", 0.0, 0.35, 0.12, step=0.01, unit="")
        self.lowcut_slider = DSPSlider("Vocal Filter Lowcut", 100, 1000, 250, step=50, unit=" Hz")
        self.highcut_slider = DSPSlider("Vocal Filter Highcut", 2000, 10000, 6000, step=250, unit=" Hz")

        sliders_card = create_card(
            ft.Column([
                ft.Text("🎛️ Channel Splitting Controls", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                self.swap_checkbox,
                ft.Row([
                    ft.Column([self.crossfeed_slider], expand=True),
                    ft.Column([self.lowcut_slider, self.highcut_slider], expand=True, spacing=10),
                ], spacing=20),
            ], spacing=12)
        )

        # Process Action
        self.progress_ring = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=3, color=PURPLE_ACCENT)
        self.process_btn = ft.FilledButton(
            "Process Surround Sound",
            icon=ft.Icons.HEADSET_ROUNDED,
            disabled=True,
            on_click=self._process_audio,
        )

        action_row = ft.Row([self.process_btn, self.progress_ring], alignment=ft.MainAxisAlignment.START)

        # Audio Players
        self.orig_player = DesktopAudioPlayer("Original Track", PURPLE_ACCENT)
        self.proc_player = DesktopAudioPlayer("Binaural Surround Audio", PURPLE_ACCENT)

        players_row = ft.Row([
            ft.Container(self.orig_player, expand=True),
            ft.Container(self.proc_player, expand=True),
        ], spacing=16)

        self.controls = [
            ft.Text("🎧 Binaural Surround Sound Splitter", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Directs vocals and backing instruments into distinct directional stereo channels with anti-fatigue blending.", size=13, color=TEXT_MUTED),
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
            self.file_status.value = f"Loaded: {self.filename}"
            self.file_status.color = PURPLE_ACCENT
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
            processed = apply_surround_split(
                samples=self.samples,
                fs=self.fs,
                lowcut=self.lowcut_slider.get_value(),
                highcut=self.highcut_slider.get_value(),
                swap_channels=self.swap_checkbox.value,
                crossfeed=self.crossfeed_slider.get_value(),
            )
            base_name, _ = os.path.splitext(self.filename)
            self.proc_player.load_samples(processed, self.fs, f"{base_name}_Surround_Split.wav")
        except Exception as ex:
            self.file_status.value = f"Error: {ex}"
        finally:
            self.progress_ring.visible = False
            self.process_btn.disabled = False
            self.update()
