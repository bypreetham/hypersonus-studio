import flet as ft

# Color Palette
BG_COLOR = "#0D1117"
SURFACE_COLOR = "#161B22"
CARD_BG = "#1C2128"
BORDER_COLOR = "#30363D"

CYAN_ACCENT = "#00E5FF"
PURPLE_ACCENT = "#7C4DFF"
PINK_ACCENT = "#FF4081"
AMBER_ACCENT = "#FFB300"
GREEN_ACCENT = "#00E676"

TEXT_PRIMARY = "#F0F6FC"
TEXT_MUTED = "#8B949E"

def create_card(content: ft.Control, width: int = None, padding: int = 16) -> ft.Container:
    """Create a sleek container card with border and dark surface."""
    return ft.Container(
        content=content,
        width=width,
        bgcolor=CARD_BG,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
        padding=padding,
    )

def create_badge(text: str, color: str = GREEN_ACCENT) -> ft.Container:
    """Create a status pill/badge."""
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color),
        bgcolor=ft.Colors.with_opacity(0.15, color),
        border_radius=6,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )
