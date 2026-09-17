import sys
import subprocess

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        # Launch Streamlit web view
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    else:
        # Launch Native Desktop App (Flet)
        import flet as ft
        from desktop.main import main
        ft.app(target=main)
