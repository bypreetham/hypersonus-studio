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
        page.window.width = 1040
        page.window.height = 680
        page.window.min_width = 800
        page.window.min_height = 520
        page.window.title_bar_hidden = False
        page.window.title_bar_buttons_hidden = False
        page.window.frameless = False
        page.window.minimizable = True
        page.window.maximizable = True
        page.window.resizable = True
        page.window.center()

    def minimize_window(e):
        page.window.minimized = True
        page.update()

    def maximize_window(e):
        page.window.maximized = not page.window.maximized
        page.update()

    def close_window(e):
        page.window.close()

    # Top Window Control Bar with Drag Area
    window_title_bar = ft.WindowDragArea(
        content=ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED, color=CYAN_ACCENT, size=18),
                            ft.Text("Hypersonus Studio", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REMOVE_ROUNDED,
                                icon_color=TEXT_MUTED,
                                icon_size=18,
                                tooltip="Minimize",
                                on_click=minimize_window,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CROP_SQUARE_ROUNDED,
                                icon_color=TEXT_MUTED,
                                icon_size=16,
                                tooltip="Maximize / Restore",
                                on_click=maximize_window,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_color="#FF5252",
                                icon_size=18,
                                tooltip="Close",
                                on_click=close_window,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor="#13171F",
            padding=ft.padding.symmetric(horizontal=12, vertical=2),
            border=ft.border.only(bottom=ft.border.BorderSide(1, "#21262D")),
        )
    )

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
                    ft.Text("Studio", weight=ft.FontWeight.BOLD, size=13, color=TEXT_PRIMARY),
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

    # Main Layout with Title Bar
    page.add(
        ft.Column(
            controls=[
                window_title_bar,
                ft.Row(
                    controls=[
                        nav_rail,
                        ft.VerticalDivider(width=1, color="#21262D"),
                        content_area,
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
