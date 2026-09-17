import flet as ft
from desktop.theme import CYAN_ACCENT, TEXT_PRIMARY, TEXT_MUTED

class DSPSlider(ft.Column):
    def __init__(
        self,
        title: str,
        min_val: float,
        max_val: float,
        value: float,
        step: float = 0.1,
        unit: str = "",
        on_change = None,
    ):
        super().__init__()
        self.title_str = title
        self.unit = unit
        self.value = value
        self.on_change_callback = on_change

        self.value_label = ft.Text(
            f"{value:.2f}{unit}" if isinstance(value, float) else f"{value}{unit}",
            color=CYAN_ACCENT,
            weight=ft.FontWeight.BOLD,
            size=12,
        )

        self.slider = ft.Slider(
            min=min_val,
            max=max_val,
            value=value,
            divisions=int((max_val - min_val) / step) if step > 0 else None,
            active_color=CYAN_ACCENT,
            inactive_color="#21262D",
            on_change=self._handle_change,
        )

        self.controls = [
            ft.Row(
                controls=[
                    ft.Text(title, color=TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500),
                    self.value_label,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            self.slider,
        ]
        self.spacing = 2

    def _handle_change(self, e):
        self.value = self.slider.value
        val_str = f"{self.value:.2f}" if self.slider.divisions and self.slider.divisions > 20 else f"{self.value:.1f}"
        self.value_label.value = f"{val_str}{self.unit}"
        self.update()
        if self.on_change_callback:
            self.on_change_callback(self.value)

    def get_value(self) -> float:
        return float(self.slider.value)
