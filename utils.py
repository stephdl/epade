import os
import subprocess
import sys
import webbrowser


def fix_wm_decorations(window) -> None:
    """Force les décorations complètes (réduire/agrandir/fermer) sur Linux.

    Quand un Toplevel est créé avec un parent, le WM reçoit WM_TRANSIENT_FOR
    et supprime les boutons réduire/agrandir sur GNOME/KDE. Ce hint corrige ça.
    Sans effet sur Windows et macOS.
    """
    if sys.platform.startswith("linux"):
        try:
            window.wm_attributes("-type", "normal")
        except Exception:
            pass


def open_url(url: str) -> None:
    """Ouvre une URL dans le navigateur par défaut.

    Sur Linux en binaire PyInstaller, webbrowser échoue silencieusement car
    LD_LIBRARY_PATH est surchargé par les libs bundlées. On appelle xdg-open
    via subprocess avec LD_LIBRARY_PATH_ORIG restauré pour que le navigateur
    charge ses propres bibliothèques système.
    """
    if sys.platform.startswith("linux"):
        try:
            env = os.environ.copy()
            orig = env.pop("LD_LIBRARY_PATH_ORIG", None)
            if orig is not None:
                env["LD_LIBRARY_PATH"] = orig
            else:
                env.pop("LD_LIBRARY_PATH", None)
            subprocess.Popen(["xdg-open", url], env=env)  # nosec B603, B607
            return
        except FileNotFoundError:
            pass
    webbrowser.open_new(url)
