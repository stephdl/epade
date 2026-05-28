import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
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


# ── Dialogs custom (remplacement de messagebox) ───────────────────────────────

def _dialog(parent, title, message, buttons):
    """Crée un dialog modal centré sur parent, largeur minimum 460px."""
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.minsize(460, 1)
    fix_wm_decorations(dlg)
    result = [None]

    outer = ttk.Frame(dlg, padding=(20, 16, 20, 14))
    outer.pack(fill=tk.BOTH, expand=True)

    ttk.Label(outer, text=message, wraplength=420, justify=tk.LEFT).pack(
        anchor=tk.W, pady=(0, 14))
    ttk.Separator(outer).pack(fill=tk.X, pady=(0, 12))

    btn_frame = ttk.Frame(outer)
    btn_frame.pack()

    def _close(v):
        result[0] = v
        dlg.destroy()

    for text, value in buttons:
        ttk.Button(btn_frame, text=text,
                   command=lambda v=value: _close(v)).pack(side=tk.LEFT, padx=6)

    dlg.update_idletasks()
    px = parent.winfo_rootx() + parent.winfo_width() // 2
    py = parent.winfo_rooty() + parent.winfo_height() // 2
    w = max(dlg.winfo_reqwidth(), 460)
    h = dlg.winfo_reqheight()
    dlg.geometry(f"+{max(0, px - w // 2)}+{max(0, py - h // 2)}")
    try:
        dlg.grab_set()
    except Exception:
        dlg.after(100, dlg.grab_set)
    dlg.wait_window()
    return result[0]


def showinfo(parent, title, message, **_):
    _dialog(parent, title, message, [("OK", None)])


def showwarning(parent, title, message, **_):
    _dialog(parent, title, message, [("OK", None)])


def showerror(parent, title, message, **_):
    _dialog(parent, title, message, [("OK", None)])


def askyesno(parent, title, message, **_):
    return _dialog(parent, title, message, [("Oui", True), ("Non", False)])
