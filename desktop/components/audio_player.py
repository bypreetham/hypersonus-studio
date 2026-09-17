import os
import flet as ft
import sounddevice as sd
import numpy as np
from desktop.theme import create_card, CYAN_ACCENT, GREEN_ACCENT, PINK_ACCENT, TEXT_PRIMARY, TEXT_MUTED
from utils.audio_io import save_audio, get_audio_info

class DesktopAudioPlayer(ft.Container):
    def __init__(self, title: str = "Audio Player", color_accent: str = CYAN_ACCENT):
        super().__init__()
        self.title = title
        self.color_accent = color_accent
        self.samples = None
        self.fs = None
        self.is_playing = False

        self.status_text = ft.Text("No audio loaded", size=12, color=TEXT_MUTED)
        self.play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            icon_color=color_accent,
            icon_size=32,
            disabled=True,
            on_click=self.toggle_play,
        )
        self.stop_btn = ft.IconButton(
            icon=ft.Icons.STOP_ROUNDED,
            icon_color=PINK_ACCENT,
            icon_size=28,
            disabled=True,
            on_click=self.stop_audio,
        )
        self.export_btn = ft.OutlinedButton(
            "Export .WAV",
            icon=ft.Icons.DOWNLOAD_ROUNDED,
            disabled=True,
            on_click=self.export_file,
        )

        self.info_text = ft.Text("", size=11, color=TEXT_MUTED)

        card_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(self.title, weight=ft.FontWeight.BOLD, size=15, color=TEXT_PRIMARY),
                        self.status_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.info_text,
                ft.Divider(color="#21262D", height=1),
                ft.Row(
                    controls=[
                        ft.Row(controls=[self.play_btn, self.stop_btn], spacing=4),
                        self.export_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=8,
        )

        self.content = create_card(card_content)

    def load_samples(self, samples: np.ndarray, fs: int, suggested_filename: str = "output.wav"):
        self.samples = samples
        self.fs = fs
        self.suggested_filename = suggested_filename
        self.play_btn.disabled = False
        self.stop_btn.disabled = False
        self.export_btn.disabled = False

        info = get_audio_info(samples, fs)
        self.info_text.value = f"Duration: {info['duration_formatted']} | Rate: {info['sample_rate']} Hz | {info['channel_str']}"
        self.status_text.value = "Ready to play"
        self.status_text.color = GREEN_ACCENT
        self.update()

    def toggle_play(self, e):
        if self.samples is None or self.fs is None:
            return

        if not self.is_playing:
            try:
                # Stop any current playback
                sd.stop()
                sd.play(self.samples, self.fs)
                self.is_playing = True
                self.play_btn.icon = ft.Icons.PAUSE_ROUNDED
                self.status_text.value = "Playing..."
                self.status_text.color = self.color_accent
                self.update()
            except Exception as ex:
                self.status_text.value = f"Error: {ex}"
                self.update()
        else:
            self.stop_audio(e)

    def stop_audio(self, e):
        sd.stop()
        self.is_playing = False
        self.play_btn.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.status_text.value = "Stopped"
        self.status_text.color = TEXT_MUTED
        self.update()

    def export_file(self, e):
        if self.samples is None:
            return
        exports_dir = os.path.join(os.path.dirname(__file__), "..", "..", "exports")
        os.makedirs(exports_dir, exist_ok=True)
        out_path = os.path.join(exports_dir, self.suggested_filename)
        save_audio(out_path, self.samples, self.fs, format="WAV")
        self.status_text.value = f"Saved: {os.path.basename(out_path)}"
        self.status_text.color = GREEN_ACCENT
        self.update()
