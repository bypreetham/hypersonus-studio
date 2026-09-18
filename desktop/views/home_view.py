import shutil
import sys
import flet as ft
from desktop.theme import (
    create_card, create_badge, CYAN_ACCENT, PURPLE_ACCENT, PINK_ACCENT,
    AMBER_ACCENT, GREEN_ACCENT, TEXT_PRIMARY, TEXT_MUTED
)

class HomeView(ft.Column):
    def __init__(self, on_navigate=None):
        super().__init__()
        self.on_navigate = on_navigate
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20

        # Hero Banner
        hero = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("🎛️ Hypersonus Studio", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(
                        "Cross-Platform Desktop Audio Processing Suite. Real-time 3D spatialization, binaural channel splitting, phase-cancellation vocal removal, and neural stem isolation.",
                        size=14,
                        color=TEXT_MUTED,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.only(bottom=10),
        )

        # Hardware & Engine Diagnostics
        ffmpeg_found = shutil.which("ffmpeg") is not None
        try:
            import torch
            cuda_ready = torch.cuda.is_available()
            accel_text = f"CUDA ({torch.cuda.get_device_name(0)})" if cuda_ready else "CPU Mode"
        except BaseException:
            accel_text = "CPU Acceleration"

        sys_metrics = ft.Row(
            controls=[
                create_card(
                    ft.Column([
                        ft.Text("Python Runtime", size=12, color=TEXT_MUTED),
                        ft.Text(f"v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        create_badge("Active", GREEN_ACCENT),
                    ], spacing=4),
                    width=230,
                ),
                create_card(
                    ft.Column([
                        ft.Text("FFmpeg Engine", size=12, color=TEXT_MUTED),
                        ft.Text("Installed" if ffmpeg_found else "Missing", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        create_badge("Ready" if ffmpeg_found else "Install Required", GREEN_ACCENT if ffmpeg_found else AMBER_ACCENT),
                    ], spacing=4),
                    width=230,
                ),
                create_card(
                    ft.Column([
                        ft.Text("Acceleration", size=12, color=TEXT_MUTED),
                        ft.Text(accel_text, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        create_badge("Optimized", GREEN_ACCENT),
                    ], spacing=4),
                    width=230,
                ),
                create_card(
                    ft.Column([
                        ft.Text("Supported Formats", size=12, color=TEXT_MUTED),
                        ft.Text("WAV, MP3, FLAC, M4A", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        create_badge("Multi-Codec", CYAN_ACCENT),
                    ], spacing=4),
                    width=230,
                ),
            ],
            wrap=True,
            spacing=16,
        )

        # Feature Cards Grid
        modules_title = ft.Text("Available Audio Modules", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

        card1 = self._build_feature_card(
            "🎵 3D Ping-Pong Spatializer",
            "Alternates instruments left-to-right in smooth dynamic cycles while keeping lead vocals centered.",
            "3daudio.py",
            CYAN_ACCENT,
            1,
        )
        card2 = self._build_feature_card(
            "🎧 Binaural Surround Splitter",
            "Separates vocals and backing instruments into distinct directional stereo channels with anti-fatigue crossfeed.",
            "surroundSound.py",
            PURPLE_ACCENT,
            2,
        )
        card3 = self._build_feature_card(
            "🎹 BGM & Instrumental Extractor",
            "Removes center-panned vocals to extract clean backing music and instrumental karaoke tracks.",
            "vocal_remover.py",
            PINK_ACCENT,
            3,
        )
        card4 = self._build_feature_card(
            "🎤 Acapella Vocal Extractor",
            "Isolates lead singing and speech by suppressing background music with STFT center coherence masking.",
            "audionumpy.py",
            AMBER_ACCENT,
            4,
        )

        card5 = self._build_feature_card(
            "🧠 Demucs Multi-Stem Neural Splitter",
            "High-fidelity AI source separation into 4 Stems or 6 Stems (including dedicated Guitar & Piano).",
            "Demucs v4 Hybrid Transformer",
            CYAN_ACCENT,
            5,
        )

        grid = ft.Column(
            controls=[
                ft.Row([ft.Container(card1, expand=True), ft.Container(card2, expand=True)], spacing=16),
                ft.Row([ft.Container(card3, expand=True), ft.Container(card4, expand=True)], spacing=16),
                ft.Row([ft.Container(card5, expand=True)], spacing=16),
            ],
            spacing=16,
        )

        self.controls = [hero, sys_metrics, ft.Divider(color="#21262D", height=10), modules_title, grid]

    def _build_feature_card(self, title: str, desc: str, legacy_ref: str, color: str, nav_index: int):
        return create_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=color),
                            ft.IconButton(
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                icon_color=color,
                                tooltip=f"Open {title}",
                                on_click=lambda e: self.on_navigate(nav_index) if self.on_navigate else None,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(desc, size=13, color=TEXT_MUTED),
                    ft.Row([
                        create_badge(f"Engine: {legacy_ref}", color),
                    ]),
                ],
                spacing=8,
            )
        )
