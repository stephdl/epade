import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import webbrowser
import db
import config
from gui.patient_form import PatientForm

_BASE_SIZES = {"title": 13, "section": 11, "list": 10}


class MainWindow(tk.Tk):
    def __init__(self, conn, scaling: float = 1.0, version: str = "dev"):
        super().__init__()
        self.conn = conn
        self._version = version
        self.title(f"ÉPADE {version} — Gestion des cotations")
        self.geometry("900x580")
        self.minsize(700, 420)
        self._scaling = 1.0
        self._init_fonts()
        self._show_archives = tk.BooleanVar(value=False)
        self._build()
        self._apply_scaling(scaling)
        self._refresh_patients()

    def _init_fonts(self):
        self._font_title = tkfont.Font(family="", size=_BASE_SIZES["title"], weight="bold")
        self._font_section = tkfont.Font(family="", size=_BASE_SIZES["section"], weight="bold")
        self._font_list = tkfont.Font(family="", size=_BASE_SIZES["list"])
        self._named_bases = {}
        for name in tkfont.names(self):
            try:
                f = tkfont.nametofont(name)
                self._named_bases[name] = abs(f.cget("size"))
            except Exception:
                pass

    def _apply_scaling(self, factor: float):
        self.tk.call("tk", "scaling", factor)
        self._font_title.configure(size=max(8, round(_BASE_SIZES["title"] * factor)))
        self._font_section.configure(size=max(8, round(_BASE_SIZES["section"] * factor)))
        self._font_list.configure(size=max(8, round(_BASE_SIZES["list"] * factor)))
        for name, base in self._named_bases.items():
            try:
                tkfont.nametofont(name).configure(size=max(6, round(base * factor)))
            except Exception:
                pass
        self._scaling = factor

    def _build(self):
        top = ttk.Frame(self, padding=(10, 8, 10, 0))
        top.pack(fill=tk.X)
        lbl_frame = ttk.Frame(top)
        lbl_frame.pack(side=tk.LEFT)
        ttk.Label(lbl_frame, text="ÉPADE — Cotations psychogériatriques",
                  font=self._font_title).pack(anchor="w")
        ttk.Label(lbl_frame, text=self._version,
                  font=("", 8), foreground="gray").pack(anchor="w")
        ttk.Button(top, text="Parametres",
                   command=self._ouvrir_parametres).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Sauvegarder la base",
                   command=self._sauvegarder_db).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(top, text="Restaurer la base",
                   command=self._restaurer_db).pack(side=tk.RIGHT)

        body = ttk.Frame(self, padding=(10, 8))
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=1, minsize=220)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(1, weight=1)

        # ── Colonne gauche — patients ──────────────────────────────────────
        search_frame = ttk.Frame(body)
        search_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(search_frame, text="Patients", font=self._font_section).pack(side=tk.LEFT)
        ttk.Checkbutton(search_frame, text="Archivés",
                        variable=self._show_archives,
                        command=self._refresh_patients).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Entry(search_frame, textvariable=tk.StringVar(), width=1).pack_forget()  # spacer trick
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_patients())
        ttk.Entry(search_frame, textvariable=self._search_var, width=14).pack(
            side=tk.RIGHT, padx=(4, 0))
        ttk.Label(search_frame, text="Rech. :").pack(side=tk.RIGHT)

        self._patient_lb = tk.Listbox(body, selectmode=tk.SINGLE,
                                      font=self._font_list, activestyle="none",
                                      exportselection=False)
        self._patient_lb.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self._patient_lb.bind("<<ListboxSelect>>", self._on_patient_select)

        sb_p = ttk.Scrollbar(body, command=self._patient_lb.yview)
        sb_p.grid(row=1, column=0, sticky="nse", padx=(0, 10))
        self._patient_lb.configure(yscrollcommand=sb_p.set)

        btn_patient = ttk.Frame(body)
        btn_patient.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(6, 0))
        for i in range(3):
            btn_patient.columnconfigure(i, weight=1)
        ttk.Button(btn_patient, text="+ Nouveau",
                   command=self._nouveau_patient).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(btn_patient, text="Modifier",
                   command=self._modifier_patient).grid(row=0, column=1, sticky="ew", padx=(0, 2))
        self._btn_archive = ttk.Button(btn_patient, text="Archiver",
                                       command=self._toggle_archive)
        self._btn_archive.grid(row=0, column=2, sticky="ew")

        # Séparateur vertical
        ttk.Separator(body, orient=tk.VERTICAL).grid(row=0, column=0,
            rowspan=3, sticky="nse", padx=(0, 10))

        # ── Colonne droite — évaluations ──────────────────────────────────
        self._eval_title = tk.StringVar(value="Évaluations")
        ttk.Label(body, textvariable=self._eval_title,
                  font=self._font_section).grid(row=0, column=1, sticky="w")

        self._eval_frame = ttk.Frame(body)
        self._eval_frame.grid(row=1, column=1, sticky="nsew")
        self._eval_frame.columnconfigure(0, weight=1)
        self._eval_frame.rowconfigure(0, weight=1)

        self._eval_lb = tk.Listbox(self._eval_frame, selectmode=tk.SINGLE,
                                   font=self._font_list, activestyle="none",
                                   exportselection=False)
        self._eval_lb.grid(row=0, column=0, sticky="nsew")
        self._eval_lb.bind("<Double-Button-1>", self._ouvrir_evaluation)

        sb_e = ttk.Scrollbar(self._eval_frame, command=self._eval_lb.yview)
        sb_e.grid(row=0, column=1, sticky="ns")
        self._eval_lb.configure(yscrollcommand=sb_e.set)

        btn_frame = ttk.Frame(body)
        btn_frame.grid(row=2, column=1, sticky="ew", pady=(6, 0))
        ttk.Button(btn_frame, text="+ Nouvelle évaluation",
                   command=self._nouvelle_evaluation).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text="Ouvrir",
                   command=self._ouvrir_evaluation).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text="Exporter PDF",
                   command=self._exporter_pdf).pack(side=tk.LEFT)

        self._patient_ids = []
        self._patient_archives = []
        self._eval_ids = []

        # ── Pied de page — référence échelle ─────────────────────────────
        footer = ttk.Frame(self, padding=(10, 2, 10, 6))
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, side=tk.BOTTOM)
        lbl_ref = ttk.Label(footer,
                            text="Echelle EPADE - Monfort JC, Lezy AM, Papin A, Tezenas S  |  www.psychoge.fr",
                            foreground="#2563EB", cursor="hand2", font=("", 8))
        lbl_ref.pack(side=tk.LEFT)
        lbl_ref.bind("<Button-1>", lambda _: webbrowser.open_new("https://www.psychoge.fr"))

    # ── Patients ─────────────────────────────────────────────────────────

    def _refresh_patients(self, *_):
        query = self._search_var.get()
        patients = db.rechercher_patients(self.conn, query,
                                          inclure_archives=self._show_archives.get())
        self._patient_ids = [p["id"] for p in patients]
        self._patient_archives = [bool(p["archive"]) for p in patients]
        self._patient_lb.delete(0, tk.END)
        for i, p in enumerate(patients):
            prefix = "[X] " if p["archive"] else "    "
            self._patient_lb.insert(tk.END, f"{prefix}{p['nom'].upper()} {p['prenom']}")
            if p["archive"]:
                self._patient_lb.itemconfig(i, foreground="gray")
        self._eval_lb.delete(0, tk.END)
        self._eval_ids = []
        self._eval_title.set("Évaluations")
        self._update_archive_btn()

    def _selected_patient_id(self):
        sel = self._patient_lb.curselection()
        if not sel:
            return None
        return self._patient_ids[sel[0]]

    def _selected_patient_is_archived(self):
        sel = self._patient_lb.curselection()
        if not sel:
            return False
        return self._patient_archives[sel[0]]

    def _update_archive_btn(self, *_):
        if self._selected_patient_is_archived():
            self._btn_archive.configure(text="Restaurer")
        else:
            self._btn_archive.configure(text="Archiver")

    def _on_patient_select(self, _event=None):
        self._update_archive_btn()
        pid = self._selected_patient_id()
        if pid is None:
            return
        p = db.get_patient(self.conn, pid)
        self._eval_title.set(f"Évaluations — {p['nom'].upper()} {p['prenom']}")
        self._refresh_evaluations(pid)

    def _nouveau_patient(self):
        form = PatientForm(self, self.conn)
        if form.result:
            self._search_var.set("")
            self._show_archives.set(False)
            self._refresh_patients()
            if form.result in self._patient_ids:
                idx = self._patient_ids.index(form.result)
                self._patient_lb.selection_set(idx)
                self._patient_lb.see(idx)
                self._on_patient_select()

    def _modifier_patient(self):
        pid = self._selected_patient_id()
        if pid is None:
            messagebox.showinfo("Sélection requise",
                                "Sélectionnez un patient dans la liste.", parent=self)
            return
        form = PatientForm(self, self.conn, patient_id=pid)
        if form.result == "deleted":
            self._refresh_patients()
        elif form.result:
            self._refresh_patients()
            if form.result in self._patient_ids:
                idx = self._patient_ids.index(form.result)
                self._patient_lb.selection_set(idx)
                self._patient_lb.see(idx)
                self._on_patient_select()

    def _toggle_archive(self):
        pid = self._selected_patient_id()
        if pid is None:
            messagebox.showinfo("Sélection requise",
                                "Sélectionnez un patient dans la liste.", parent=self)
            return
        if self._selected_patient_is_archived():
            db.restaurer_patient(self.conn, pid)
        else:
            p = db.get_patient(self.conn, pid)
            nom = f"{p['nom'].upper()} {p['prenom']}"
            if not messagebox.askyesno(
                    "Archiver", f"Archiver {nom} ?\nLe patient n'apparaîtra plus dans "
                    "la liste principale mais ses évaluations seront conservées.",
                    parent=self):
                return
            db.archiver_patient(self.conn, pid)
        self._refresh_patients()

    # ── Évaluations ───────────────────────────────────────────────────────

    def _refresh_evaluations(self, patient_id):
        evals = db.get_evaluations_patient(self.conn, patient_id)
        self._eval_ids_raw = evals
        self._eval_lb.delete(0, tk.END)
        for e in evals:
            statut = "[V]" if e["finalisee"] else "... brouillon"
            date_str = e["date_cotation"] if (e["finalisee"] and e["date_cotation"]) else "en cours"
            du = e["periode_du"] or "—"
            au = e["periode_au"] or "—"
            sa = db.score_domaine(e, "A")
            sb = db.score_domaine(e, "B")
            sc = db.score_domaine(e, "C")
            sd = db.score_domaine(e, "D")
            tot = db.score_total(e)
            self._eval_lb.insert(tk.END, f"  {statut}  {date_str}  |  {e['soignant'] or '—'}")
            self._eval_lb.insert(tk.END, f"     Du {du} au {au}  |  A:{sa} B:{sb} C:{sc} D:{sd}  Total:{tot}")
            self._eval_lb.insert(tk.END, "")

    def _selected_eval_id(self):
        sel = self._eval_lb.curselection()
        if not sel:
            return None
        idx = sel[0] // 3
        evals = getattr(self, "_eval_ids_raw", [])
        if idx >= len(evals):
            return None
        return evals[idx]["id"]

    def _nouvelle_evaluation(self):
        pid = self._selected_patient_id()
        if pid is None:
            messagebox.showinfo("Sélection requise",
                                "Sélectionnez un patient dans la liste.", parent=self)
            return
        eid = db.creer_evaluation(self.conn, pid)
        self._ouvrir_par_id(eid, pid)

    def _ouvrir_evaluation(self, _event=None):
        eid = self._selected_eval_id()
        pid = self._selected_patient_id()
        if eid is None or pid is None:
            messagebox.showinfo("Sélection requise",
                                "Sélectionnez une évaluation dans la liste.", parent=self)
            return
        self._ouvrir_par_id(eid, pid)

    def _ouvrir_par_id(self, eval_id, patient_id):
        from gui.cotation_form import CotationForm
        CotationForm(self, self.conn, eval_id)
        self._refresh_evaluations(patient_id)

    def _restaurer_db(self):
        from tkinter import filedialog
        from shutil import copy2
        from pathlib import Path
        if not messagebox.askyesno(
                "Restaurer la base",
                "La base active sera remplacée par la sauvegarde choisie.\n\n"
                "Toutes les données non sauvegardées seront perdues.\n\n"
                "Continuer ?",
                icon="warning", parent=self):
            return
        src = filedialog.askopenfilename(
            parent=self,
            title="Choisir une sauvegarde à restaurer",
            filetypes=[("Base ÉPADE", "*.db"), ("Tous les fichiers", "*.*")],
        )
        if not src:
            return
        dest = db.DB_PATH
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        copy2(src, dest)
        messagebox.showinfo(
            "Restauration réussie",
            "La base a été restaurée.\nL'application va redémarrer.",
            parent=self)
        self.conn.close()
        self.conn = db.init_db()
        self._refresh_patients()

    def _sauvegarder_db(self):
        from tkinter import filedialog
        from datetime import date
        from shutil import copy2
        from pathlib import Path
        src = db.DB_PATH
        if not Path(src).exists():
            messagebox.showwarning("Base introuvable",
                                   f"Le fichier base de données est introuvable :\n{src}",
                                   parent=self)
            return
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Sauvegarder la base de données",
            defaultextension=".db",
            filetypes=[("Base ÉPADE", "*.db"), ("Tous les fichiers", "*.*")],
            initialfile=f"epade_sauvegarde_{date.today()}.db",
        )
        if not dest:
            return
        copy2(src, dest)
        messagebox.showinfo("Sauvegarde réussie",
                            f"Base sauvegardée :\n{dest}", parent=self)

    def _exporter_pdf(self):
        eid = self._selected_eval_id()
        pid = self._selected_patient_id()
        if eid is None:
            messagebox.showinfo("Sélection requise",
                                "Sélectionnez une évaluation dans la liste.", parent=self)
            return
        ev = db.get_evaluation(self.conn, eid)
        if not ev["finalisee"]:
            messagebox.showwarning("Non finalisée",
                                   "Seules les évaluations verrouillées peuvent être exportées.",
                                   parent=self)
            return
        from gui.export_dialog import ExportChoixDialog
        ExportChoixDialog(self, self.conn, eid, pid)

    def _ouvrir_parametres(self):
        cfg = config.load()
        dlg = tk.Toplevel(self)
        dlg.title("Paramètres")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        # ── Taille interface ──────────────────────────────────────────────
        ttk.Label(dlg, text="Taille de l'interface", font=("", 11, "bold")).pack(
            padx=24, pady=(18, 6))

        scale_var = tk.DoubleVar(value=self._scaling)
        frm = ttk.Frame(dlg, padding=(24, 0, 24, 0))
        frm.pack(fill=tk.X)
        ttk.Label(frm, text="Petit").pack(side=tk.LEFT)
        ttk.Label(frm, text="Grand").pack(side=tk.RIGHT)
        slider = ttk.Scale(dlg, from_=0.75, to=2.0, orient=tk.HORIZONTAL,
                           variable=scale_var, length=320)
        slider.pack(padx=24, pady=4)
        preview_lbl = ttk.Label(dlg, text="")
        preview_lbl.pack(pady=(2, 8))

        _STEPS = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
        _saved_scaling = self._scaling

        def _snap_and_preview(*_):
            v = scale_var.get()
            snapped = min(_STEPS, key=lambda s: abs(s - v))
            scale_var.set(snapped)
            preview_lbl.configure(text=f"Zoom : {int(snapped * 100)}%")
            self._apply_scaling(snapped)

        slider.configure(command=_snap_and_preview)
        _snap_and_preview()

        ttk.Separator(dlg, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=16, pady=(8, 0))

        # ── Établissement ─────────────────────────────────────────────────
        ttk.Label(dlg, text="Établissement (en-tête des exports PDF)",
                  font=("", 11, "bold")).pack(padx=24, pady=(14, 6))

        etab_frm = ttk.Frame(dlg, padding=(24, 0, 24, 0))
        etab_frm.pack(fill=tk.X)
        etab_frm.columnconfigure(1, weight=1)

        def _field(row, label, key):
            ttk.Label(etab_frm, text=label).grid(row=row, column=0, sticky="w",
                                                  pady=3, padx=(0, 8))
            var = tk.StringVar(value=cfg.get(key, ""))
            ttk.Entry(etab_frm, textvariable=var, width=36).grid(row=row, column=1, sticky="ew")
            return var

        nom_var = _field(0, "Nom :", "etablissement_nom")
        adr_var = _field(1, "Adresse :", "etablissement_adresse")
        tel_var = _field(2, "Téléphone :", "etablissement_telephone")

        # ── Boutons ───────────────────────────────────────────────────────
        ttk.Separator(dlg, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=16, pady=(14, 0))

        def _apply():
            config.save({
                "scaling": self._scaling,
                "etablissement_nom": nom_var.get().strip(),
                "etablissement_adresse": adr_var.get().strip(),
                "etablissement_telephone": tel_var.get().strip(),
            })
            dlg.destroy()

        def _cancel():
            self._apply_scaling(_saved_scaling)
            dlg.destroy()

        btn_frm = ttk.Frame(dlg)
        btn_frm.pack(pady=(10, 16))
        ttk.Button(btn_frm, text="Appliquer", command=_apply).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frm, text="Annuler", command=_cancel).pack(side=tk.LEFT)

        dlg.protocol("WM_DELETE_WINDOW", _cancel)
