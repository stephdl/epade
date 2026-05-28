import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import unicodedata
import db
import export.pdf as pdf_export


def _safe(s):
    """Translitère les accents et remplace les espaces pour un nom de fichier propre."""
    nfkd = unicodedata.normalize("NFKD", s or "")
    ascii_s = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_s.replace(" ", "_").strip("_") or "inconnu"


class ExportChoixDialog(tk.Toplevel):
    def __init__(self, parent, conn, eval_id, patient_id):
        super().__init__(parent)
        self.conn = conn
        self.eval_id = eval_id
        self.patient_id = patient_id

        ev = db.get_evaluation(conn, eval_id)
        patient = db.get_patient(conn, patient_id)
        nom    = _safe(patient["nom"].upper())
        prenom = _safe(patient["prenom"])
        date   = (ev["date_cotation"] or "")[:10] or "brouillon"
        self._prefix = f"EPADE_{nom}_{prenom}_{date}"

        self.title("Exporter PDF")
        self.resizable(False, False)
        self.update_idletasks()
        try:
            self.grab_set()
        except Exception:
            self.after(100, self.grab_set)
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Choisir le type d'export :", font=("", 11, "bold")).pack(pady=(0, 12))

        ttk.Button(f, text="Fiche complète ÉPADE",
                   command=self._fiche_complete).pack(fill=tk.X, pady=3)
        ttk.Button(f, text="Résumé des scores",
                   command=self._resume).pack(fill=tk.X, pady=3)
        ttk.Button(f, text="Historique du patient",
                   command=self._historique).pack(fill=tk.X, pady=3)
        ttk.Separator(f).pack(fill=tk.X, pady=8)
        ttk.Button(f, text="Annuler", command=self.destroy).pack()

    def _ask_path(self, default_name):
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=default_name,
        )
        return Path(path) if path else None

    def _fiche_complete(self):
        path = self._ask_path(f"{self._prefix}_fiche.pdf")
        if path:
            pdf_export.export_fiche_complete(self.conn, self.eval_id, path)
            master = self.master
            self.destroy()
            messagebox.showinfo("Export réussi", f"PDF enregistré :\n{path}", parent=master)

    def _resume(self):
        path = self._ask_path(f"{self._prefix}_resume.pdf")
        if path:
            pdf_export.export_resume(self.conn, self.eval_id, path)
            master = self.master
            self.destroy()
            messagebox.showinfo("Export réussi", f"PDF enregistré :\n{path}", parent=master)

    def _historique(self):
        from datetime import date as _date
        today = _date.today().strftime("%Y-%m-%d")
        patient = db.get_patient(self.conn, self.patient_id)
        nom    = _safe(patient["nom"].upper())
        prenom = _safe(patient["prenom"])
        path = self._ask_path(f"EPADE_{nom}_{prenom}_historique_{today}.pdf")
        if path:
            pdf_export.export_historique(self.conn, self.patient_id, path)
            master = self.master
            self.destroy()
            messagebox.showinfo("Export réussi", f"PDF enregistré :\n{path}", parent=master)
