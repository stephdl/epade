import contextlib
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date as _date
from tkcalendar import Calendar


_CAL_KW = dict(
    locale="fr_FR",
    date_pattern="yyyy-mm-dd",
    showweeknumbers=False,
    font=("", 13),
    background="white",
    foreground="#1c3a6a",
    headersbackground="#1c3a6a",
    headersforeground="white",
    selectbackground="#1c5a8a",
    selectforeground="white",
    normalbackground="white",
    normalforeground="#111",
    weekendbackground="#f0f4fa",
    weekendforeground="#444",
    othermonthbackground="#f5f5f5",
    othermonthforeground="#aaa",
    arrowcolor="white",
)


def _make_cal_photo(size=20):
    """Icône calendrier dessinée pixel par pixel — aucune dépendance police/emoji."""
    img = tk.PhotoImage(width=size, height=size)

    def fill(color, x1, y1, x2, y2):
        for y in range(y1, y2):
            row = " ".join([color] * (x2 - x1))
            img.put("{" + row + "}", to=(x1, y, x2, y + 1))

    fill("#d9d9d9", 0, 0, size, size)          # fond gris
    fill("#888888", 0, 0, size, 1)             # bord haut
    fill("#888888", 0, size - 1, size, size)   # bord bas
    fill("#888888", 0, 0, 1, size)             # bord gauche
    fill("#888888", size - 1, 0, size, size)   # bord droit
    fill("#1c5a8a", 1, 1, size - 1, 6)        # en-tête bleu
    fill("#ffffff", 1, 6, size - 1, size - 1)  # corps blanc
    fill("#555555", 5, 0, 7, 5)               # anneau gauche
    fill("#555555", size - 7, 0, size - 5, 5) # anneau droit
    for row in range(2):                       # points-dates
        for col in range(3):
            px, py = 3 + col * 5, 8 + row * 4
            if px + 3 < size - 1:
                fill("#1c5a8a", px, py, px + 3, py + 2)
    return img


class LargeDateEntry(ttk.Frame):
    """
    Champ date (texte YYYY-MM-DD) + bouton icône calendrier.
    API : get_date() → datetime.date|None, set_date(str|date), get() → str.
    """

    def __init__(self, parent, on_change=None, state="normal", **kw):
        super().__init__(parent)
        self._on_change = on_change
        self._var = tk.StringVar()
        self._var.trace_add("write", self._on_text_change)

        self._entry = ttk.Entry(self, textvariable=self._var, width=12, state=state)
        self._entry.pack(side=tk.LEFT)

        if state != "disabled":
            self._icon = _make_cal_photo(20)   # garder la référence
            self._btn = tk.Button(
                self, image=self._icon, relief="groove", bd=1,
                cursor="hand2", command=self._open,
                padx=2, pady=2,
            )
            self._btn.pack(side=tk.LEFT, padx=(4, 0))

        self._cal_win = None
        self._suppress = False

    # ── API publique ──────────────────────────────────────────────────────

    def get_date(self):
        try:
            return datetime.strptime(self._var.get().strip(), "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            return None

    def set_date(self, val):
        self._suppress = True
        if isinstance(val, _date):
            self._var.set(val.strftime("%Y-%m-%d"))
        else:
            self._var.set(str(val) if val else "")
        self._suppress = False

    def get(self):
        return self._var.get()

    # ── Popup calendrier ──────────────────────────────────────────────────

    def _open(self):
        if self._cal_win and self._cal_win.winfo_exists():
            self._cal_win.destroy()
            self._cal_win = None
            return

        win = tk.Toplevel(self)
        win.title("Choisir une date")
        win.resizable(False, False)
        self._cal_win = win

        from datetime import date as _date
        cal = Calendar(win, selectmode="day", maxdate=_date.today(), **_CAL_KW)
        cal.pack(padx=12, pady=(12, 4))

        with contextlib.suppress(Exception):
            s = ttk.Style()
            pfx = cal._style_pfx
            s.configure(pfx + ".TButton", font=("", 13, "bold"), padding=6)

        current = self.get_date()
        if current:
            with contextlib.suppress(Exception):
                cal.set_date(current)

        ttk.Button(win, text="✔  Valider",
                   command=lambda: self._pick(cal, win)).pack(pady=(4, 12))

        win.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        sw = win.winfo_screenwidth()
        if x + win.winfo_width() > sw:
            x = sw - win.winfo_width() - 4
        win.geometry(f"+{x}+{y}")
        try:
            win.grab_set()
        except Exception:
            win.after(100, win.grab_set)

    def _pick(self, cal, win):
        self._var.set(cal.get_date())
        win.destroy()
        self._cal_win = None
        if self._on_change:
            self._on_change()

    def _on_text_change(self, *_):
        if not self._suppress and self._on_change:
            self._on_change()
