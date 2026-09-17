import os
import flet as ft
from desktop.theme import create_card, AMBER_ACCENT, CYAN_ACCENT, TEXT_PRIMARY, TEXT_MUTED
from desktop.components.audio_player import DesktopAudioPlayer
from utils.audio_io import load_audio
from utils.stem_separator import separate_stems, is_spleeter_available

class StemSeparatorView(ft.Column):
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
                        ft.Text("Input Song for Stem Extraction", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        self.file_status,
                    ], spacing=4),
                    self.select_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Engine Selection
        spleeter_ok = is_spleeter_available()
        engine_options = [ft.dropdown.Option("dsp", "Spectral DSP (Instant)")]
        if spleeter_ok:
            engine_options.insert(0, ft.dropdown.Option("spleeter", "Spleeter (Deep Learning Neural Network)"))

        self.engine_dropdown = ft.Dropdown(
            label="Separation Engine",
            options=engine_options,
            value="spleeter" if spleeter_ok else "dsp",
            width=350,
        )

        engine_card = create_card(
            ft.Column([
                ft.Text("⚙️ Engine Architecture", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                self.engine_dropdown,
                ft.Text(
                    "Spleeter isolates vocals with neural networks. Spectral DSP provides high-speed harmonic-percussive separation.",
                    size=12,
                    color=TEXT_MUTED,
                ),
            ], spacing=8)
        )

        # Process Action
        self.progress_ring = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=3, color=AMBER_ACCENT)
        self.process_btn = ft.FilledButton(
            "Extract BGM & Vocals",
            icon=ft.Icons.AUTO_AWESOME_ROUNDED,
            disabled=True,
            on_click=self._process_audio,
        )

        action_row = ft.Row([self.process_btn, self.progress_ring], alignment=ft.MainAxisAlignment.START)

        # Stems Audio Players
        self.bgm_player = DesktopAudioPlayer("Isolated BGM (Accompaniment)", AMBER_ACCENT)
        self.voc_player = DesktopAudioPlayer("Isolated Vocals (Acapella)", CYAN_ACCENT)

        players_row = ft.Row([
            ft.Container(self.bgm_player, expand=True),
            ft.Container(self.voc_player, expand=True),
        ], spacing=16)

        self.controls = [
            ft.Text("🎼 AI BGM & Vocal Extractor", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Decomposes full songs into independent studio stems: Background Music and clean Acapella.", size=13, color=TEXT_MUTED),
            file_card,
            engine_card,
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
            self.file_status.color = AMBER_ACCENT
            self.process_btn.disabled = False
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
            engine_choice = self.engine_dropdown.value or "dsp"
            vocals, bgm, engine_used = separate_stems(
                samples=self.samples,
                fs=self.fs,
                engine=engine_choice,
            )
            base_name, _ = os.path.splitext(self.filename)
            self.bgm_player.load_samples(bgm, self.fs, f"{base_name}_BGM.wav")
            self.voc_player.load_samples(vocals, self.fs, f"{base_name}_Vocals.wav")
            self.file_status.value = f"Separation complete via {engine_used}!"
        except Exception as ex:
            self.file_status.value = f"Error: {ex}"
        finally:
            self.progress_ring.visible = False
            self.process_btn.disabled = False
            self.update()
