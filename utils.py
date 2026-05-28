import subprocess
import sys
import webbrowser


def open_url(url: str) -> None:
    """Ouvre une URL dans le navigateur par défaut.

    Sur Linux, xdg-open est appelé directement via subprocess car webbrowser
    échoue silencieusement dans un binaire PyInstaller (PATH épuré).
    """
    if sys.platform.startswith("linux"):
        try:
            subprocess.Popen(["xdg-open", url])  # nosec B603, B607
            return
        except FileNotFoundError:
            pass
    webbrowser.open_new(url)
