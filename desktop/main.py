import flet as ft
from desktop.theme import BG_COLOR, SURFACE_COLOR, CYAN_ACCENT, TEXT_PRIMARY, TEXT_MUTED
from desktop.views import HomeView, PingPongView, SurroundView, VocalRemoverView, StemSeparatorView

def main(page: ft.Page):
    # Window Configuration
    page.title = "Hypersonus Studio"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_COLOR
    page.padding = 0

    if hasattr(page, "window"):
        page.window.width = 1220
        page.window.height = 840
        page.window.min_width = 960
        page.window.min_height = 680
        page.window.center()

    # Content Container
    content_area = ft.Container(expand=True, padding=24)

    def navigate_to(index: int):
        nav_rail.selected_index = index
        render_view(index)
        page.update()

    # Views Registry
    views = [
        lambda: HomeView(on_navigate=navigate_to),
        lambda: PingPongView(page),
        lambda: SurroundView(page),
        lambda: VocalRemoverView(page),
        lambda: StemSeparatorView(page),
    ]

    def render_view(index: int):
        content_area.content = views[index]()
        page.update()

    def on_nav_change(e):
        render_view(e.control.selected_index)

    # Navigation Rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=110,
        min_extended_width=200,
        bgcolor=SURFACE_COLOR,
        indicator_color=CYAN_ACCENT,
        leading=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED, color=CYAN_ACCENT, size=32),
                    ft.Text("Hypersonus", weight=ft.FontWeight.BOLD, size=13, color=TEXT_PRIMARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=ft.padding.symmetric(vertical=16),
        ),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_ROUNDED,
                selected_icon=ft.Icons.HOME_ROUNDED,
                label="Home",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SURROUND_SOUND_ROUNDED,
                selected_icon=ft.Icons.SURROUND_SOUND_ROUNDED,
                label="3D Ping-Pong",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.HEADPHONES_ROUNDED,
                selected_icon=ft.Icons.HEADPHONES_ROUNDED,
                label="Surround",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.MIC_OFF_ROUNDED,
                selected_icon=ft.Icons.MIC_OFF_ROUNDED,
                label="Vocal Remover",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                selected_icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                label="BGM Extractor",
            ),
        ],
        on_change=on_nav_change,
    )

    # Initial View
    render_view(0)

    # Main Layout
    page.add(
        ft.Row(
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1, color="#21262D"),
                content_area,
            ],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
