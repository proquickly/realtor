from __future__ import annotations

import flet as ft

from .app import main as app_main


def main() -> None:
    # Launch Flet in web browser
    ft.app(target=app_main, view=ft.WEB_BROWSER)
