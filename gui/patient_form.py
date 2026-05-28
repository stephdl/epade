import tkinter as tk
from tkinter import ttk
import db
from utils import fix_wm_decorations, showwarning, askyesno


class PatientForm(tk.Toplevel):
    """Formulaire création (patient_id=None) ou édition (patient_id fourni)."""

    def __init__(self, parent, conn, patient_id=None):
        super().__init__(parent)
        self.conn = conn
        self.patient_id = patient_id
        self.result = None
        self._edit = patient_id is not None

        self.title("Modifier le patient" if self._edit else "Nouveau patient")
        self.resizable(False, False)
        fix_wm_decorations(self)
        self.update_idletasks()
        try:
            self.grab_set()
        except Exception:
            self.after(100, self.grab_set)
        self._build()
        if self._edit:
            self._load()
        self.wait_window()

    # ── Construction ─────────────────────────────────────────────────────

    def _build(self):
        pad = {"padx": 10, "pady": 5}
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        row = 0

        def lbl(text, r, bold=False):
            font = ("", 9, "bold") if bold else ("", 9)
            ttk.Label(frame, text=text, font=font).grid(
                row=r, column=0, sticky="w", **pad)

        def ent(r, width=34):
            e = ttk.Entry(frame, width=width)
            e.grid(row=r, column=1, sticky="ew", **pad)
            return e

        # ── Identité ──
        ttk.Label(frame, text="Identité", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 2))
        row += 1

        lbl("Nom *", row); self._nom = ent(row); row += 1
        lbl("Prénom *", row); self._prenom = ent(row); row += 1
        lbl("Date de naissance *", row); self._ddn = ent(row, 18); row += 1
        lbl("N° dossier", row); self._ndossier = ent(row, 18); row += 1

        ttk.Separator(frame).grid(row=row, columnspan=2, sticky="ew", pady=6); row += 1

        # ── Coordonnées ──
        ttk.Label(frame, text="Coordonnées", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 2))
        row += 1

        lbl("Service / Chambre", row); self._service = ent(row); row += 1
        lbl("Date d'admission", row); self._admission = ent(row, 18); row += 1
        lbl("Téléphone", row); self._tel = ent(row, 20); row += 1
        lbl("Adresse", row); self._adresse = ent(row); row += 1

        ttk.Separator(frame).grid(row=row, columnspan=2, sticky="ew", pady=6); row += 1

        # ── Suivi médical ──
        ttk.Label(frame, text="Suivi médical", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 2))
        row += 1

        lbl("Médecin référent", row); self._medecin = ent(row); row += 1

        ttk.Separator(frame).grid(row=row, columnspan=2, sticky="ew", pady=6); row += 1

        # ── Contact famille ──
        ttk.Label(frame, text="Contact famille", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 2))
        row += 1

        lbl("Nom", row); self._cf_nom = ent(row); row += 1
        lbl("Téléphone", row); self._cf_tel = ent(row, 20); row += 1
        lbl("Lien de parenté", row); self._cf_lien = ent(row, 22); row += 1

        ttk.Separator(frame).grid(row=row, columnspan=2, sticky="ew", pady=8); row += 1

        # ── Boutons ──
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, columnspan=2, pady=(0, 4))
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT, padx=4)
        label_btn = "Enregistrer" if self._edit else "Créer"
        ttk.Button(btn_frame, text=label_btn, command=self._valider).pack(side=tk.LEFT, padx=4)
        if self._edit:
            ttk.Button(btn_frame, text="Supprimer définitivement",
                       command=self._supprimer).pack(side=tk.RIGHT, padx=(16, 4))

        self._nom.focus()
        self.bind("<Return>", lambda e: self._valider())
        self.bind("<Escape>", lambda e: self.destroy())

    # ── Chargement (mode édition) ─────────────────────────────────────────

    def _load(self):
        p = db.get_patient(self.conn, self.patient_id)
        if p is None:
            return

        def fill(widget, key):
            val = p[key] or ""
            widget.delete(0, tk.END)
            widget.insert(0, val)

        fill(self._nom,      "nom")
        fill(self._prenom,   "prenom")
        fill(self._ddn,      "date_naissance")
        fill(self._ndossier, "numero_dossier")
        fill(self._service,  "service_chambre")
        fill(self._admission,"date_admission")
        fill(self._tel,      "telephone")
        fill(self._adresse,  "adresse")
        fill(self._medecin,  "medecin_referent")
        fill(self._cf_nom,   "contact_famille_nom")
        fill(self._cf_tel,   "contact_famille_tel")
        fill(self._cf_lien,  "contact_famille_lien")

    # ── Validation ────────────────────────────────────────────────────────

    def _valider(self):
        nom    = self._nom.get().strip()
        prenom = self._prenom.get().strip()
        ddn    = self._ddn.get().strip()
        if not nom or not prenom or not ddn:
            showwarning(self, "Champs manquants",
                        "Le nom, le prénom et la date de naissance sont obligatoires.")
            return

        champs = dict(
            nom=nom,
            prenom=prenom,
            date_naissance=self._ddn.get().strip() or None,
            numero_dossier=self._ndossier.get().strip() or None,
            service_chambre=self._service.get().strip() or None,
            date_admission=self._admission.get().strip() or None,
            telephone=self._tel.get().strip() or None,
            adresse=self._adresse.get().strip() or None,
            medecin_referent=self._medecin.get().strip() or None,
            contact_famille_nom=self._cf_nom.get().strip() or None,
            contact_famille_tel=self._cf_tel.get().strip() or None,
            contact_famille_lien=self._cf_lien.get().strip() or None,
        )

        if self._edit:
            db.modifier_patient(self.conn, self.patient_id, **champs)
            self.result = self.patient_id
        else:
            self.result = db.creer_patient(
                self.conn,
                champs.pop("nom"), champs.pop("prenom"),
                champs.pop("date_naissance"),
                **champs,
            )
        self.destroy()

    def _supprimer(self):
        p = db.get_patient(self.conn, self.patient_id)
        nom = f"{p['nom'].upper()} {p['prenom']}"
        if not askyesno(self, "Confirmer la suppression",
                        f"Supprimer définitivement {nom} ?\n\n"
                        "TOUTES ses évaluations seront effacées et cette action est IRRÉVERSIBLE."):
            return
        if not askyesno(self, "Dernière confirmation",
                        f"Êtes-vous absolument certain de vouloir supprimer {nom} ?"):
            return
        db.supprimer_patient(self.conn, self.patient_id)
        self.result = "deleted"
        self.destroy()
