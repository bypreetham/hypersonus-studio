import os
import time
import threading
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
        self.duration = 0.0
        self.is_playing = False
        self.current_pos = 0.0
        self.suggested_filename = "output.wav"

        self._playback_start_wall = 0.0
        self._playback_start_pos = 0.0
        self._stop_event = threading.Event()
        self._tracker_thread = None

        # UI Controls
        self.status_text = ft.Text("No audio loaded", size=12, color=TEXT_MUTED)
        self.info_text = ft.Text("", size=11, color=TEXT_MUTED)
        self.time_display = ft.Text("00:00.0 / 00:00.0", size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

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

        # Interactive Seekbar
        self.seekbar = ft.Slider(
            min=0.0,
            max=100.0,
            value=0.0,
            disabled=True,
            active_color=color_accent,
            inactive_color="#21262D",
            on_change=self._on_seek_change,
        )

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
                # Seekbar Row with Timestamps
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Position", size=11, color=TEXT_MUTED),
                                self.time_display,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.seekbar,
                    ],
                    spacing=2,
                ),
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
        self.stop_audio(None)
        self.samples = samples
        self.fs = fs
        self.suggested_filename = suggested_filename
        self.duration = float(samples.shape[0] / fs) if fs > 0 else 0.0
        self.current_pos = 0.0

        self.play_btn.disabled = False
        self.stop_btn.disabled = False
        self.export_btn.disabled = False
        self.seekbar.disabled = False
        self.seekbar.max = max(0.1, self.duration)
        self.seekbar.value = 0.0

        info = get_audio_info(samples, fs)
        self.info_text.value = f"Duration: {info['duration_formatted']} | Rate: {info['sample_rate']} Hz | {info['channel_str']}"
        self.status_text.value = "Ready to play"
        self.status_text.color = GREEN_ACCENT
        self._update_time_display()
        self.update()

    def _format_time(self, seconds: float) -> str:
        s = max(0.0, float(seconds))
        mins = int(s // 60)
        secs = int(s % 60)
        tenths = int((s - int(s)) * 10)
        return f"{mins:02d}:{secs:02d}.{tenths}"

    def _update_time_display(self):
        cur_str = self._format_time(self.current_pos)
        tot_str = self._format_time(self.duration)
        self.time_display.value = f"{cur_str} / {tot_str}"

    def toggle_play(self, e):
        if self.samples is None or self.fs is None:
            return

        if not self.is_playing:
            self._start_playback(self.current_pos)
        else:
            self._pause_playback()

    def _start_playback(self, from_seconds: float):
        if self.samples is None:
            return

        start_sec = max(0.0, min(float(from_seconds), self.duration))
        if start_sec >= self.duration - 0.05:
            start_sec = 0.0  # Loop or restart if at the very end

        self.current_pos = start_sec
        start_frame = int(start_sec * self.fs)
        play_samples = self.samples[start_frame:]

        try:
            sd.stop()
            sd.play(play_samples, self.fs)
            self.is_playing = True
            self._playback_start_wall = time.time()
            self._playback_start_pos = start_sec
            self._stop_event.clear()

            self.play_btn.icon = ft.Icons.PAUSE_ROUNDED
            self.status_text.value = "Playing..."
            self.status_text.color = self.color_accent
            self.update()

            # Start background progress tracker
            if self._tracker_thread is None or not self._tracker_thread.is_alive():
                self._tracker_thread = threading.Thread(target=self._track_progress, daemon=True)
                self._tracker_thread.start()
        except Exception as ex:
            self.status_text.value = f"Audio Error: {ex}"
            self.update()

    def _pause_playback(self):
        sd.stop()
        self.is_playing = False
        self._stop_event.set()
        self.play_btn.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.status_text.value = "Paused"
        self.status_text.color = TEXT_MUTED
        self.update()

    def stop_audio(self, e=None):
        sd.stop()
        self.is_playing = False
        self._stop_event.set()
        self.current_pos = 0.0
        self.seekbar.value = 0.0
        self.play_btn.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.status_text.value = "Stopped"
        self.status_text.color = TEXT_MUTED
        self._update_time_display()
        try:
            self.update()
        except Exception:
            pass

    def _track_progress(self):
        while not self._stop_event.is_set() and self.is_playing:
            time.sleep(0.08)
            elapsed = time.time() - self._playback_start_wall
            pos = self._playback_start_pos + elapsed

            if pos >= self.duration:
                # Playback finished
                self.is_playing = False
                self.current_pos = self.duration
                self.seekbar.value = self.duration
                self.play_btn.icon = ft.Icons.PLAY_ARROW_ROUNDED
                self.status_text.value = "Finished"
                self.status_text.color = TEXT_MUTED
                self._update_time_display()
                try:
                    self.update()
                except Exception:
                    pass
                break
            else:
                self.current_pos = pos
                self.seekbar.value = pos
                self._update_time_display()
                try:
                    self.update()
                except Exception:
                    pass

    def _on_seek_change(self, e):
        seek_target = float(self.seekbar.value)
        self.current_pos = seek_target
        self._update_time_display()
        if self.is_playing:
            self._start_playback(seek_target)
        else:
            self.update()

    def get_current_position(self) -> float:
        """Returns the current playhead position in seconds."""
        return float(self.current_pos)

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
