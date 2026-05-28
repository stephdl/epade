import tkinter as tk
from tkinter import ttk
import db
from utils import fix_wm_decorations

SEUIL = 17
_BAR_COLORS = {"A": "#e53935", "B": "#1e88e5", "C": "#2e7d32", "D": "#fb8c00"}


class HistoriqueDialog(tk.Toplevel):
    def __init__(self, parent, conn, patient_id):
        super().__init__(parent)
        self.title("Historique des évaluations")
        self.resizable(True, True)
        self.minsize(680, 400)
        fix_wm_decorations(self)

        patient = db.get_patient(conn, patient_id)
        evals = [e for e in db.get_evaluations_patient(conn, patient_id) if e["finalisee"]]

        nom = f"{patient['nom'].upper()} {patient['prenom']}"
        ttk.Label(self, text=f"Historique — {nom}",
                  font=("", 12, "bold")).pack(padx=20, pady=(14, 6))

        if not evals:
            ttk.Label(self, text="Aucune évaluation finalisée.",
                      foreground="gray", font=("", 10, "italic")).pack(pady=20)
            ttk.Button(self, text="Fermer", command=self.destroy).pack(pady=(0, 14))
            self._center(parent)
            return

        # PanedWindow vertical : tableau en haut, graphe en bas
        paned = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RAISED,
                               sashwidth=6, bg="#cccccc")
        paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        top_frm = ttk.Frame(paned)
        bot_frm = ttk.Frame(paned)
        paned.add(top_frm, stretch="always")
        paned.add(bot_frm, stretch="always")

        self._build_table(top_frm, evals)
        self._build_graph(bot_frm, list(reversed(evals)))

        ttk.Button(self, text="Fermer", command=self.destroy).pack(pady=(6, 12))
        self._center(parent)

    # ── Tableau ───────────────────────────────────────────────────────────

    def _build_table(self, parent, evals):
        if any(db.score_total(e) > SEUIL for e in evals):
            ttk.Label(parent,
                      text="En rouge : score > 17 — rechercher une cause réversible",
                      foreground="#c00000", font=("", 8, "italic")).pack(
                          padx=16, anchor="w", pady=(4, 2))

        frm = ttk.Frame(parent, padding=(16, 0, 16, 8))
        frm.pack(fill=tk.BOTH, expand=True)

        cols    = ("date", "soignant", "periode", "A", "B", "C", "D", "total")
        headers = ("Date cotation", "Soignant", "Période", "A", "B", "C", "D", "Total")
        widths  = (148, 130, 195, 36, 36, 36, 36, 52)
        stretch = (False, True, True, False, False, False, False, False)

        tree = ttk.Treeview(frm, columns=cols, show="headings",
                            height=min(len(evals), 8))
        for col, hdr, w, st in zip(cols, headers, widths, stretch):
            tree.heading(col, text=hdr)
            anchor = "center" if col in ("A", "B", "C", "D", "total") else "w"
            tree.column(col, width=w, anchor=anchor, stretch=st, minwidth=w)

        for ev in evals:
            total  = db.score_total(ev)
            periode = f"{ev['periode_du'] or '—'} → {ev['periode_au'] or '—'}"
            vals = (
                (ev["date_cotation"] or "")[:16],
                ev["soignant"] or "—",
                periode,
                db.score_domaine(ev, "A"),
                db.score_domaine(ev, "B"),
                db.score_domaine(ev, "C"),
                db.score_domaine(ev, "D"),
                total,
            )
            tree.insert("", tk.END, values=vals,
                        tags=("critique",) if total > SEUIL else ())

        tree.tag_configure("critique", foreground="#c00000")

        sb = tk.Scrollbar(frm, orient=tk.VERTICAL, command=tree.yview, width=16)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

    # ── Graphe ────────────────────────────────────────────────────────────

    BAR_SLOT = 120  # largeur fixe par évaluation (px)

    def _build_graph(self, parent, evals):
        ttk.Label(parent, text="Évolution du score total",
                  font=("", 10, "bold")).pack(padx=16, anchor="w", pady=(6, 2))

        self._graph_evals = evals

        # Cadre canvas + scrollbar horizontale
        frm = ttk.Frame(parent)
        frm.pack(padx=16, fill=tk.BOTH, expand=True)

        hbar = tk.Scrollbar(frm, orient=tk.HORIZONTAL, width=16)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)

        self._canvas = tk.Canvas(frm, bg="white",
                                 highlightthickness=1, highlightbackground="#cccccc",
                                 xscrollcommand=hbar.set)
        self._canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        hbar.config(command=self._canvas.xview)

        self._canvas.bind("<Configure>", self._redraw_graph)

        # Légende
        legend = ttk.Frame(parent)
        legend.pack(padx=16, pady=(4, 4), anchor="w")
        for dom, color in _BAR_COLORS.items():
            nom_dom = db.DOMAINES[dom][0]
            c = tk.Canvas(legend, width=32, height=32, highlightthickness=0)
            c.pack(side=tk.LEFT, padx=(0, 6))
            c.create_rectangle(1, 1, 31, 31, fill=color, outline="")
            ttk.Label(legend, text=f"{dom} — {nom_dom}",
                      font=("", 11)).pack(side=tk.LEFT, padx=(0, 20))

    def _redraw_graph(self, event=None):
        canvas = self._canvas
        evals  = self._graph_evals
        canvas.delete("all")

        C_H    = canvas.winfo_height()
        C_W_vis = canvas.winfo_width()
        if C_W_vis < 10 or C_H < 10:
            return

        ML, MR, MT, MB = 46, 16, 16, 30
        n      = len(evals)
        max_sc = 64
        bar_w  = 36

        # Largeur totale du contenu : au moins la fenêtre visible
        C_W = max(C_W_vis, ML + n * self.BAR_SLOT + MR)
        plot_h = C_H - MT - MB

        def px(i):  return ML + i * self.BAR_SLOT + self.BAR_SLOT // 2
        def py(sc): return MT + plot_h - (sc / max_sc) * plot_h

        canvas.configure(scrollregion=(0, 0, C_W, C_H))

        # Grille + labels axe Y (fixés à gauche, hors scroll)
        for val in (0, 16, 32, 48, 64):
            y = py(val)
            canvas.create_line(ML, y, C_W - MR, y, fill="#e0e0e0", dash=(4, 4))
            canvas.create_text(ML - 6, y, text=str(val), anchor="e",
                               font=("", 8), fill="#555555")

        # Seuil 17
        y17 = py(SEUIL)
        canvas.create_line(ML, y17, C_W - MR, y17,
                           fill="#e03030", dash=(6, 3), width=1)
        canvas.create_text(ML - 6, y17, text="17", anchor="e",
                           font=("", 8, "bold"), fill="#e03030")

        # Barres empilées
        for i, ev in enumerate(evals):
            x     = px(i)
            cumul = 0
            for dom in "ABCD":
                s = db.score_domaine(ev, dom)
                if s:
                    canvas.create_rectangle(
                        x - bar_w / 2, py(cumul + s),
                        x + bar_w / 2, py(cumul),
                        fill=_BAR_COLORS[dom], outline="white", width=1)
                cumul += s

            total = db.score_total(ev)
            color = "#c00000" if total > SEUIL else "#333333"
            canvas.create_text(x, py(total) - 8, text=str(total),
                               font=("", 8, "bold"), fill=color)

            d = (ev["date_cotation"] or "")[:10]
            date_lbl = f"{d[8:10]}-{d[5:7]}-{d[:4]}" if len(d) == 10 else d
            canvas.create_text(x, C_H - MB + 6, text=date_lbl,
                               font=("", 8), anchor="n", fill="#444444")

        # Axes
        canvas.create_line(ML, C_H - MB, C_W - MR, C_H - MB, fill="#999999")
        canvas.create_line(ML, MT, ML, C_H - MB, fill="#999999")

    # ── Centrage ──────────────────────────────────────────────────────────

    def _center(self, parent):
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 780)
        h = 650
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
