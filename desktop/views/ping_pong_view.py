import os
import flet as ft
from desktop.theme import create_card, CYAN_ACCENT, TEXT_PRIMARY, TEXT_MUTED
from desktop.components.dsp_slider import DSPSlider
from desktop.components.audio_player import DesktopAudioPlayer
from utils.audio_io import load_audio
from utils.spatializer import apply_ping_pong_3d

class PingPongView(ft.Column):
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
            "Select Audio File (WAV, MP3, FLAC)",
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

        # DSP Tuning Sliders
        self.duration_slider = DSPSlider("Cycle Duration (Seconds per Pan)", 0.5, 5.0, 2.0, step=0.25, unit="s")
        self.depth_slider = DSPSlider("Panning Depth (Stereo Width)", 0.2, 1.0, 1.0, step=0.05, unit="")
        self.lowcut_slider = DSPSlider("Vocal Lowcut Filter", 100, 1000, 250, step=50, unit=" Hz")
        self.highcut_slider = DSPSlider("Vocal Highcut Filter", 2000, 10000, 6000, step=250, unit=" Hz")

        sliders_card = create_card(
            ft.Column([
                ft.Text("🎛️ Spatial & Filter Parameters", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Row([
                    ft.Column([self.duration_slider, self.depth_slider], expand=True, spacing=10),
                    ft.Column([self.lowcut_slider, self.highcut_slider], expand=True, spacing=10),
                ], spacing=20),
            ], spacing=12)
        )

        # Process Action
        self.progress_ring = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=3, color=CYAN_ACCENT)
        self.process_btn = ft.FilledButton(
            "Process 3D Ping-Pong Audio",
            icon=ft.Icons.ROCKET_LAUNCH_ROUNDED,
            disabled=True,
            on_click=self._process_audio,
        )

        action_row = ft.Row(
            controls=[self.process_btn, self.progress_ring],
            alignment=ft.MainAxisAlignment.START,
        )

        # Audio Players
        self.orig_player = DesktopAudioPlayer("Original Audio", CYAN_ACCENT)
        self.proc_player = DesktopAudioPlayer("Processed 3D Audio", CYAN_ACCENT)

        players_row = ft.Row(
            controls=[
                ft.Container(self.orig_player, expand=True),
                ft.Container(self.proc_player, expand=True),
            ],
            spacing=16,
        )

        self.controls = [
            ft.Text("🎵 3D Ping-Pong Spatializer", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Alternates non-vocal audio left and right in timed cycles while preserving centered vocals.", size=13, color=TEXT_MUTED),
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
            self.file_status.color = CYAN_ACCENT
            self.process_btn.disabled = False
            self.orig_player.load_samples(self.samples, self.fs, self.filename)
            self.update()
        except Exception as ex:
            self.file_status.value = f"Error loading file: {ex}"
            self.update()

    def _process_audio(self, e):
        if self.samples is None or self.fs is None:
            return

        self.progress_ring.visible = True
        self.process_btn.disabled = True
        self.update()

        try:
            processed = apply_ping_pong_3d(
                samples=self.samples,
                fs=self.fs,
                chunk_duration=self.duration_slider.get_value(),
                lowcut=self.lowcut_slider.get_value(),
                highcut=self.highcut_slider.get_value(),
                pan_depth=self.depth_slider.get_value(),
            )
            base_name, _ = os.path.splitext(self.filename)
            self.proc_player.load_samples(processed, self.fs, f"{base_name}_3D_PingPong.wav")
        except Exception as ex:
            self.file_status.value = f"Processing error: {ex}"
        finally:
            self.progress_ring.visible = False
            self.process_btn.disabled = False
            self.update()
