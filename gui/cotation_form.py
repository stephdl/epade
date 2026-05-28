import contextlib
import tkinter as tk
from tkinter import ttk, messagebox
from gui.datepicker import LargeDateEntry
from utils import open_url
import db

SCORE_LABELS = ["— Non renseigné —", "0 — Absent", "1 — Léger",
                "2 — Moyen", "3 — Fort", "4 — Très fort"]

_NIVEAUX = ["absent", "léger", "moyen", "fort", "très fort"]


def score_labels(item_key):
    criteres = db.CRITERES.get(item_key, {})
    labels = [SCORE_LABELS[0]]
    for score in range(4, -1, -1):
        desc = criteres.get(score, "")
        niveau = _NIVEAUX[score]
        labels.append(f"{score} — ({niveau}) {desc}" if desc else SCORE_LABELS[score + 1])
    return labels

SECTION_BG = {"A": "#fff0f0", "B": "#f0f4ff", "C": "#f0fff4", "D": "#fffdf0"}

AUTRE_MARKER = "Autre (champ libre)"

ROLES_REFERENT = ["Médecin coordonateur", "Médecin traitant", "IDEC", "IDE"]
PARTICIPANTS_FIXES = [
    ("MT",   "participant_mt"),
    ("MCO",  "participant_mco"),
    ("IDEC", "participant_idec"),
    ("IDE",  "participant_ide"),
    ("AS",   "participant_as"),
    ("ASH",  "participant_ash"),
]

# Alias pour repérer les "Autre..." dans les listes
def _is_autre(val, autre_label=None):
    if autre_label is not None:
        return val == autre_label
    return val and "champ libre" in val.lower()


def _score_from_label(label):
    if not label or label == SCORE_LABELS[0]:
        return None
    return int(label[0])


def _label_from_score(score, item_key=None):
    if score is None:
        return SCORE_LABELS[0]
    if item_key:
        return score_labels(item_key)[5 - score]
    return SCORE_LABELS[score + 1]


def _match_option(value, options):
    """Retourne la valeur si elle est dans la liste, sinon None."""
    return value if value in options else None


_VIDE = "—"


class _SmartCombobox(ttk.Combobox):
    """ttk.Combobox qui ouvre le popup vers le haut quand il manque de place vers le bas."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('postcommand', self._on_post)
        super().__init__(*args, **kwargs)

    def _on_post(self):
        self.after_idle(self._reposition_popup)

    def _reposition_popup(self):
        try:
            popdown = self.tk.call('ttk::combobox::PopdownWindow', self)
        except tk.TclError:
            return
        self.tk.call('update', 'idletasks')
        try:
            popup_h = int(self.tk.call('winfo', 'reqheight', popdown))
        except tk.TclError:
            return
        cb_x = self.winfo_rootx()
        cb_y = self.winfo_rooty()
        cb_h = self.winfo_height()
        screen_h = self.winfo_screenheight()
        if cb_y + cb_h + popup_h > screen_h:
            new_y = max(0, cb_y - popup_h)
            self.tk.call('wm', 'geometry', popdown, f'+{cb_x}+{new_y}')


class _DropdownLibre(ttk.Frame):
    """Combobox + Entry pour champ libre (visible si 'Autre...' sélectionné)."""

    def __init__(self, parent, choices, state="readonly", on_change=None,
                 autre_label=None, include_vide=True, **kw):
        super().__init__(parent, **kw)
        self.columnconfigure(0, weight=1)
        self._autre_label = autre_label  # None = comportement original (détection par "champ libre")
        if include_vide:
            self._choices = [_VIDE] + list(choices)
        else:
            self._choices = list(choices)
        self._on_change = on_change

        default_val = _VIDE if include_vide else (self._choices[0] if self._choices else "")
        self._var = tk.StringVar(value=default_val)
        self._cb = _SmartCombobox(self, textvariable=self._var, values=self._choices,
                                  state=state, width=42)
        self._cb.grid(row=0, column=0, sticky="ew")

        self._libre_var = tk.StringVar()
        self._libre = ttk.Entry(self, textvariable=self._libre_var, width=30)
        # caché par défaut (column 1, pas de grid tant que non affiché)

        self._var.trace_add("write", self._on_select)
        self._libre_var.trace_add("write", self._on_libre_change)

    def _is_autre_val(self, val):
        return _is_autre(val, self._autre_label)

    def _on_select(self, *_):
        val = self._var.get()
        if self._is_autre_val(val):
            self._libre.grid(row=0, column=1, padx=(6, 0))
        else:
            self._libre.grid_remove()
            self._libre_var.set("")
        if self._on_change:
            self._on_change()

    def _on_libre_change(self, *_):
        if self._on_change:
            self._on_change()

    def get(self):
        """Retourne la valeur finale à stocker en base."""
        val = self._var.get()
        if not val or val == _VIDE:
            return ""
        if self._is_autre_val(val):
            return self._libre_var.get().strip()
        return val

    def set(self, value):
        """Charge une valeur : sélectionne dans la liste ou 'Autre...' + texte libre."""
        if not value:
            self._var.set(_VIDE if _VIDE in self._choices else (self._choices[0] if self._choices else ""))
            self._libre_var.set("")
            self._libre.grid_remove()
            return
        match = _match_option(value, self._choices)
        if match:
            self._var.set(match)
        else:
            autre_opt = next((o for o in self._choices if self._is_autre_val(o)), None)
            if autre_opt:
                self._var.set(autre_opt)
                self._libre_var.set(value)
                self._libre.grid(row=0, column=1, padx=(6, 0))
            else:
                self._var.set(value)

    def disable(self):
        self._cb.configure(state="disabled")
        self._libre.configure(state="disabled")


class CotationForm(tk.Toplevel):
    def __init__(self, parent, conn, eval_id):
        super().__init__(parent)
        self.conn = conn
        self.eval_id = eval_id
        self.ev = db.get_evaluation(conn, eval_id)
        self.patient = db.get_patient(conn, self.ev["patient_id"])
        self.locked = bool(self.ev["finalisee"])

        self.title("Cotation ÉPADE" + (" [verrouillée]" if self.locked else ""))
        self.geometry("1000x720")
        self.update_idletasks()
        try:
            self.grab_set()
        except Exception:
            self.after(100, self.grab_set)

        self._score_vars  = {}
        self._note_wdg    = {}   # _DropdownLibre par item
        self._cause_wdg   = {}   # _DropdownLibre par domaine
        self._attitude_wdg = {}  # _DropdownLibre par domaine
        self._score_dom_vars = {}
        self._role_referent_wdg = None
        self._referent_var = None
        self._participant_vars = {}
        self._participant_libre_var = None

        self._build()
        self._load_data()

    # ── Construction ─────────────────────────────────────────────────────

    def _build(self):
        canvas = tk.Canvas(self, highlightthickness=0)
        vsb = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview, width=16)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._inner = ttk.Frame(canvas, padding=14)
        win = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        self._build_header()
        ttk.Separator(self._inner).pack(fill=tk.X, pady=8)
        for dom in "ABCD":
            self._build_domaine(dom)
            ttk.Separator(self._inner).pack(fill=tk.X, pady=4)
        self._build_total()
        self._build_footer()

        # Binder la molette sur tous les widgets après leur création.
        # bind_all ne fonctionne pas car les class-bindings ttk appellent break
        # sur Button-4/5 avant que "all" soit atteint.
        def _scroll(e):
            canvas.yview_scroll(-1 if e.num == 4 else 1, "units")

        def _scroll_win(e):
            canvas.yview_scroll(int(-1 * e.delta / 120), "units")

        def _apply(w):
            w.bind("<Button-4>", _scroll, add="+")
            w.bind("<Button-5>", _scroll, add="+")
            w.bind("<MouseWheel>", _scroll_win, add="+")
            for child in w.winfo_children():
                _apply(child)

        _apply(self._inner)
        canvas.bind("<Button-4>", _scroll, add="+")
        canvas.bind("<Button-5>", _scroll, add="+")
        canvas.bind("<MouseWheel>", _scroll_win, add="+")

    def _build_header(self):
        _PDF_URL = "https://www.psychoge.fr/_files/ugd/3d0eb6_fe86bd3112324bfd8d8dc27c86e44003.pdf"
        hdr = ttk.Frame(self._inner)
        hdr.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(hdr, text="Identification", font=("", 10, "bold")).pack(side=tk.LEFT)
        lbl_pdf = ttk.Label(hdr, text="Document officiel ÉPADE (PDF)",
                            foreground="#2563EB", cursor="hand2", font=("", 9))
        lbl_pdf.pack(side=tk.RIGHT)
        lbl_pdf.bind("<Button-1>", lambda _: open_url(_PDF_URL))

        f = ttk.LabelFrame(self._inner, text="", padding=10)
        f.pack(fill=tk.X, pady=(0, 4))

        state = "disabled" if self.locked else "normal"
        cb_state = "disabled" if self.locked else "readonly"
        pad = {"padx": (0, 8), "pady": 4}

        # Patient
        ttk.Label(f, text="Patient :").grid(row=0, column=0, sticky="w", **pad)
        nom = f"{self.patient['nom'].upper()} {self.patient['prenom']}"
        ddn = self.patient["date_naissance"] or ""
        ttk.Label(f, text=f"{nom}  {ddn}", font=("", 10, "bold")).grid(
            row=0, column=1, columnspan=3, sticky="w", pady=4)

        # Référent (row 1) : rôle (dropdown) + nom (entry)
        ttk.Label(f, text="Référent * :").grid(row=1, column=0, sticky="w", **pad)
        ref_frame = ttk.Frame(f)
        ref_frame.grid(row=1, column=1, columnspan=3, sticky="w", pady=4)

        self._role_referent_wdg = _DropdownLibre(
            ref_frame,
            ROLES_REFERENT,
            state=cb_state,
            on_change=self._autosave_header,
            autre_label="Saisie libre",
            include_vide=False,
        )
        self._role_referent_wdg._cb.configure(width=28)
        self._role_referent_wdg.pack(side=tk.LEFT)
        if self.locked:
            self._role_referent_wdg.disable()

        ttk.Label(ref_frame, text="  Nom :").pack(side=tk.LEFT)
        self._referent_var = tk.StringVar()
        ttk.Entry(ref_frame, textvariable=self._referent_var, state=state, width=28).pack(
            side=tk.LEFT, padx=(4, 0))
        if not self.locked:
            self._referent_var.trace_add("write", lambda *_: self._autosave_header())

        # Participants (row 2)
        ttk.Label(f, text="Participants :").grid(row=2, column=0, sticky="w", **pad)
        part_frame = ttk.Frame(f)
        part_frame.grid(row=2, column=1, columnspan=3, sticky="w", pady=4)

        self._participant_vars = {}
        for label, col in PARTICIPANTS_FIXES:
            var = tk.BooleanVar()
            self._participant_vars[col] = var
            cb = ttk.Checkbutton(part_frame, text=label, variable=var,
                                 state=state)
            cb.pack(side=tk.LEFT, padx=(0, 6))
            if not self.locked:
                var.trace_add("write", lambda *_: self._autosave_header())

        self._participant_libre_var = tk.StringVar()
        ttk.Entry(part_frame, textvariable=self._participant_libre_var,
                  state=state, width=18).pack(side=tk.LEFT, padx=(8, 0))
        if not self.locked:
            self._participant_libre_var.trace_add("write", lambda *_: self._autosave_header())

        # Période (row 3)
        ttk.Label(f, text="Période * :").grid(row=3, column=0, sticky="w", **pad)
        pf = ttk.Frame(f)
        pf.grid(row=3, column=1, columnspan=3, sticky="w", pady=4)
        ttk.Label(pf, text="Du").pack(side=tk.LEFT, padx=(0, 4))

        if self.locked:
            self._du_var = tk.StringVar()
            self._au_var = tk.StringVar()
            ttk.Entry(pf, textvariable=self._du_var, state="disabled", width=14).pack(side=tk.LEFT)
            ttk.Label(pf, text="  au").pack(side=tk.LEFT, padx=(8, 4))
            ttk.Entry(pf, textvariable=self._au_var, state="disabled", width=14).pack(side=tk.LEFT)
        else:
            self._du_entry = LargeDateEntry(pf, on_change=self._on_du_change)
            self._du_entry.pack(side=tk.LEFT)
            ttk.Label(pf, text="  au").pack(side=tk.LEFT, padx=(8, 4))
            self._au_entry = LargeDateEntry(pf, on_change=self._on_au_change)
            self._au_entry.pack(side=tk.LEFT)

        # Durée (row 4)
        ttk.Label(f, text="Durée :").grid(row=4, column=0, sticky="w", **pad)
        self._duree_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._duree_var, state=state, width=22).grid(
            row=4, column=1, sticky="w", pady=4)
        if not self.locked:
            self._duree_var.trace_add("write", lambda *_: self._autosave_header())

        # Date cotation (row 5)
        ttk.Label(f, text="Date de cotation :").grid(row=5, column=0, sticky="w", **pad)
        date_txt = self.ev["date_cotation"] or "— sera remplie automatiquement à la validation —"
        ttk.Label(f, text=date_txt, foreground="gray").grid(
            row=5, column=1, columnspan=3, sticky="w", pady=4)

    def _build_domaine(self, dom):
        nom_dom, items = db.DOMAINES[dom]
        bg = SECTION_BG[dom]
        listes = db.LISTES[dom]

        f = tk.LabelFrame(self._inner, text=f"Domaine {dom} — {nom_dom}",
                          bg=bg, padx=8, pady=6, font=("", 10, "bold"))
        f.pack(fill=tk.X, pady=3)
        f.columnconfigure(1, weight=2)
        f.columnconfigure(2, weight=1)

        cb_state = "disabled" if self.locked else "readonly"

        # En-tête colonnes
        tk.Label(f, text="Item", bg=bg, font=("", 8, "bold"), width=36, anchor="w").grid(
            row=0, column=0, sticky="w")
        tk.Label(f, text="Score", bg=bg, font=("", 8, "bold"), width=20, anchor="w").grid(
            row=0, column=1, padx=6, sticky="w")
        tk.Label(f, text="Note soignant", bg=bg, font=("", 8, "bold"), anchor="w").grid(
            row=0, column=2, padx=6, sticky="w")

        # Lignes items
        for i, item_key in enumerate(items, start=1):
            row_bg = bg

            tk.Label(f, text=f"{item_key.upper()} — {db.ITEMS[item_key]}",
                     bg=row_bg, anchor="w", width=36).grid(
                row=i, column=0, sticky="w", pady=2)

            score_var = tk.StringVar(value=SCORE_LABELS[0])
            self._score_vars[item_key] = score_var
            _SmartCombobox(f, textvariable=score_var, values=score_labels(item_key),
                           state=cb_state, width=55).grid(
                row=i, column=1, padx=6, pady=2, sticky="ew")
            if not self.locked:
                score_var.trace_add("write", lambda *_, k=item_key: self._autosave_score(k))

            note_wdg = _DropdownLibre(
                f, listes["note"], state=cb_state,
                on_change=lambda k=item_key: self._autosave_note(k))
            note_wdg.grid(row=i, column=2, padx=6, pady=2, sticky="ew")
            if self.locked:
                note_wdg.disable()
            self._note_wdg[item_key] = note_wdg

        next_row = len(items) + 1

        # Score domaine
        sv = tk.StringVar(value=f"Score domaine {dom} : 0 / 16")
        self._score_dom_vars[dom] = sv
        tk.Label(f, textvariable=sv, bg=bg, font=("", 9, "italic"), anchor="e").grid(
            row=next_row, column=0, columnspan=3, sticky="e", pady=(2, 6))
        next_row += 1

        # Séparateur intérieur
        tk.Frame(f, bg="#cccccc", height=1).grid(
            row=next_row, column=0, columnspan=3, sticky="ew", pady=4)
        next_row += 1

        # Réflexion — cause
        tk.Label(f, text="Réflexion — cause :", bg=bg, font=("", 9, "bold"),
                 anchor="w").grid(row=next_row, column=0, sticky="w", pady=2)
        cause_wdg = _DropdownLibre(
            f, listes["cause"], state=cb_state,
            on_change=lambda d=dom: self._autosave_dom(d))
        cause_wdg.grid(row=next_row, column=1, columnspan=2, padx=6, pady=2, sticky="ew")
        if self.locked:
            cause_wdg.disable()
        self._cause_wdg[dom] = cause_wdg
        next_row += 1

        # Attitude appropriée
        tk.Label(f, text="Attitude appropriée :", bg=bg, font=("", 9, "bold"),
                 anchor="w").grid(row=next_row, column=0, sticky="w", pady=2)
        att_wdg = _DropdownLibre(
            f, listes["attitude"], state=cb_state,
            on_change=lambda d=dom: self._autosave_dom(d))
        att_wdg.grid(row=next_row, column=1, columnspan=2, padx=6, pady=2, sticky="ew")
        if self.locked:
            att_wdg.disable()
        self._attitude_wdg[dom] = att_wdg

    def _build_total(self):
        f = ttk.Frame(self._inner)
        f.pack(fill=tk.X, pady=8)
        self._seuil_var = tk.StringVar()
        ttk.Label(f, textvariable=self._seuil_var, foreground="red",
                  font=("", 10, "bold")).pack(side=tk.LEFT, padx=8)
        self._total_var = tk.StringVar(value="SCORE TOTAL : 0 / 64")
        ttk.Label(f, textvariable=self._total_var,
                  font=("", 12, "bold")).pack(side=tk.RIGHT)

    def _build_footer(self):
        f = ttk.Frame(self._inner)
        f.pack(fill=tk.X, pady=(8, 4))
        if self.locked:
            ttk.Button(f, text="Fermer", command=self.destroy).pack(side=tk.RIGHT)
        else:
            ttk.Button(f, text="Annuler", command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0))
            ttk.Button(f, text="Valider et verrouiller",
                       command=self._valider).pack(side=tk.RIGHT)


    # ── Chargement ────────────────────────────────────────────────────────

    def _load_data(self):
        ev = self.ev
        # Référent
        self._role_referent_wdg.set(ev["role_referent"] or "")
        self._referent_var.set(ev["referent"] or "")
        # Participants
        for label, col in PARTICIPANTS_FIXES:
            self._participant_vars[col].set(bool(ev[col]))
        self._participant_libre_var.set(ev["participant_libre"] or "")
        self._duree_var.set(ev["duree"] or "")

        if self.locked:
            self._du_var.set(ev["periode_du"] or "")
            self._au_var.set(ev["periode_au"] or "")
        else:
            for attr, key in (("_du_entry", "periode_du"), ("_au_entry", "periode_au")):
                val = ev[key]
                if val:
                    with contextlib.suppress(Exception):
                        getattr(self, attr).set_date(val)

        for key in db.SCORE_COLS:
            self._score_vars[key].set(_label_from_score(ev[key], item_key=key))
        for key in db.NOTE_COLS:
            item_key = key[5:]
            self._note_wdg[item_key].set(ev[key] or "")

        for dom in "ABCD":
            self._cause_wdg[dom].set(ev[f"cause_{dom.lower()}"] or "")
            self._attitude_wdg[dom].set(ev[f"attitude_{dom.lower()}"] or "")

        self._update_scores()

    # ── Sauvegarde automatique ────────────────────────────────────────────

    def _on_du_change(self):
        from datetime import date as _date
        today = _date.today()
        du = self._du_entry.get_date()
        if du and du > today:
            messagebox.showwarning(
                "Date invalide",
                "La date de début ne peut pas être dans le futur.",
                parent=self)
            self._du_entry.set_date(today)
            du = today
        au = self._au_entry.get_date()
        if du and au and au < du:
            self._au_entry.set_date(du)
        self._autosave_header()

    def _on_au_change(self):
        from datetime import date as _date
        today = _date.today()
        du = self._du_entry.get_date()
        au = self._au_entry.get_date()
        if au and au > today:
            messagebox.showwarning(
                "Date invalide",
                "La date de fin ne peut pas être dans le futur.",
                parent=self)
            self._au_entry.set_date(today)
            au = today
        if du and au and au < du:
            messagebox.showwarning(
                "Date invalide",
                "La date de fin ne peut pas être antérieure à la date de début.\n"
                "La date de fin a été ramenée à la date de début.",
                parent=self)
            self._au_entry.set_date(du)
        self._autosave_header()

    def _autosave_header(self):
        if self.locked:
            return
        try:
            du = self._du_entry.get_date().strftime("%Y-%m-%d")
            au = self._au_entry.get_date().strftime("%Y-%m-%d")
        except Exception:
            du, au = "", ""
        champs = dict(
            referent=self._referent_var.get(),
            role_referent=self._role_referent_wdg.get(),
            periode_du=du,
            periode_au=au,
            duree=self._duree_var.get(),
            participant_libre=self._participant_libre_var.get(),
        )
        for label, col in PARTICIPANTS_FIXES:
            champs[col] = int(self._participant_vars[col].get())
        db.mettre_a_jour_evaluation(self.conn, self.eval_id, **champs)

    def _autosave_score(self, item_key):
        if self.locked:
            return
        val = _score_from_label(self._score_vars[item_key].get())
        db.mettre_a_jour_evaluation(self.conn, self.eval_id, **{item_key: val})
        self._update_scores()

    def _autosave_note(self, item_key):
        if self.locked:
            return
        db.mettre_a_jour_evaluation(self.conn, self.eval_id,
                                    **{f"note_{item_key}": self._note_wdg[item_key].get()})

    def _autosave_dom(self, dom):
        if self.locked:
            return
        d = dom.lower()
        db.mettre_a_jour_evaluation(self.conn, self.eval_id,
                                    **{f"cause_{d}": self._cause_wdg[dom].get(),
                                       f"attitude_{d}": self._attitude_wdg[dom].get()})

    # ── Scores temps réel ─────────────────────────────────────────────────

    def _update_scores(self):
        ev = db.get_evaluation(self.conn, self.eval_id)
        total = db.score_total(ev)
        self._total_var.set(f"SCORE TOTAL : {total} / 64")
        self._seuil_var.set(
            "Score > 17 — rechercher cause réversible" if total > 17 else "")
        for dom, (_, items) in db.DOMAINES.items():
            score = sum(ev[c] or 0 for c in items)
            self._score_dom_vars[dom].set(f"Score domaine {dom} : {score} / 16")

    # ── Validation ────────────────────────────────────────────────────────

    def _valider(self):
        self._autosave_header()
        manquants = db.valider_champs_requis(self.conn, self.eval_id)
        if manquants:
            messagebox.showwarning(
                "Champs manquants",
                "Impossible de valider. Champs manquants :\n\n• " + "\n• ".join(manquants),
                parent=self)
            return
        if not messagebox.askyesno(
                "Confirmer", "Cette évaluation sera verrouillée définitivement.\nContinuer ?",
                parent=self):
            return
        db.finaliser_evaluation(self.conn, self.eval_id)
        messagebox.showinfo("Validée", "L'évaluation est verrouillée.", parent=self)
        self.destroy()
