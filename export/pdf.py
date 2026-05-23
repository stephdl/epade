from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pathlib import Path
import db

COPYRIGHT = "© Monfort JC, Lezy AM, Papin A, Tezenas S · www.psychoge.fr"
SEUIL = 17

import sys as _sys
if getattr(_sys, "frozen", False):
    _BASE = Path(_sys.executable).parent
else:
    _BASE = Path(__file__).parent.parent

FONT_DIR = _BASE / "assets" / "fonts"
FONT_REG  = str(FONT_DIR / "LiberationSans-Regular.ttf")
FONT_BOLD = str(FONT_DIR / "LiberationSans-Bold.ttf")
FONT_IT   = str(FONT_DIR / "LiberationSans-Italic.ttf")


class EpadePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("Sans", "", FONT_REG)
        self.add_font("Sans", "B", FONT_BOLD)
        self.add_font("Sans", "I", FONT_IT)
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)
        self.add_page()

    def _nl(self):
        return {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}

    def header_epade(self):
        self.set_font("Sans", "B", 13)
        self.cell(0, 8, "ÉPADE — Échelle d'évaluation des Personnes Âgées", **self._nl())
        self.set_font("Sans", "", 9)
        self.cell(0, 5, "Symptômes et Syndromes DÉconcertants  ·  PGI-DSS", **self._nl())
        self.set_font("Sans", "I", 8)
        self.cell(0, 5, COPYRIGHT, **self._nl())
        self.ln(2)
        self.set_draw_color(100, 100, 100)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(4)

    def section_title(self, text, color=(60, 80, 160)):
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Sans", "B", 10)
        self.cell(0, 7, f"  {text}", fill=True, **self._nl())
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def field_row(self, label, value, label_w=50):
        self.set_font("Sans", "B", 9)
        self.cell(label_w, 6, label)
        self.set_font("Sans", "", 9)
        val = str(value)[:80] if value else "-"
        self.cell(self.epw - label_w, 6, val,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def row(self, widths, texts, border=0, fill=False, align="L"):
        self.set_font("Sans", "", 8)
        for w, t in zip(widths, texts):
            self.cell(w, 6, str(t)[:40], border=border, fill=fill, align=align)
        self.ln()


# ── Fiche complète ────────────────────────────────────────────────────────────

def export_fiche_complete(conn, eval_id, path):
    ev = db.get_evaluation(conn, eval_id)
    patient = db.get_patient(conn, ev["patient_id"])

    pdf = EpadePDF()
    pdf.header_epade()

    pdf.section_title("Identification du patient")
    pdf.field_row("Patient :", f"{patient['nom'].upper()} {patient['prenom']}")
    pdf.field_row("Date de naissance :", patient["date_naissance"])
    if patient["numero_dossier"]:
        pdf.field_row("N° dossier :", patient["numero_dossier"])
    if patient["service_chambre"]:
        pdf.field_row("Service / Chambre :", patient["service_chambre"])
    if patient["date_admission"]:
        pdf.field_row("Admis le :", patient["date_admission"])
    if patient["medecin_referent"]:
        pdf.field_row("Médecin référent :", patient["medecin_referent"])
    cf_nom  = patient["contact_famille_nom"] or ""
    cf_tel  = patient["contact_famille_tel"] or ""
    cf_lien = patient["contact_famille_lien"] or ""
    if cf_nom or cf_tel:
        cf_str = cf_nom
        if cf_lien:
            cf_str += f"  ({cf_lien})"
        if cf_tel:
            cf_str += f"  — {cf_tel}"
        pdf.field_row("Contact famille :", cf_str)
    pdf.field_row("Soignant :", ev["soignant"])
    pdf.field_row("Période évaluée :", f"Du {ev['periode_du']} au {ev['periode_au']}")
    pdf.field_row("Durée :", ev["duree"])
    pdf.field_row("Date de cotation :", ev["date_cotation"])
    pdf.ln(4)

    dom_colors = {
        "A": (200, 70,  70),
        "B": (70,  110, 190),
        "C": (70,  170, 70),
        "D": (190, 150, 30),
    }

    # 3 colonnes : clé (10) | libellé (140) | score (30)
    col_w = [10, 140, 30]
    label_w = 52  # largeur du label pour réflexion/attitude

    for dom, (nom_dom, items) in db.DOMAINES.items():
        pdf.section_title(f"Domaine {dom} — {nom_dom}", color=dom_colors[dom])

        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Sans", "B", 8)
        for w, h in zip(col_w, ["", "Item", "Score"]):
            pdf.cell(w, 6, h, border=1, fill=True)
        pdf.ln()

        for item_key in items:
            score = ev[item_key]
            score_str = str(score) if score is not None else "—"
            pdf.set_font("Sans", "B", 8)
            pdf.cell(col_w[0], 6, item_key.upper(), border=1)
            pdf.set_font("Sans", "", 8)
            pdf.cell(col_w[1], 6, db.ITEMS[item_key], border=1)
            pdf.cell(col_w[2], 6, score_str, border=1, align="C")
            pdf.ln()

            note = ev[f"note_{item_key}"] or ""
            if note.strip():
                pdf.set_font("Sans", "I", 7)
                pdf.set_x(pdf.l_margin + col_w[0] + 2)
                pdf.multi_cell(col_w[1] + col_w[2] - 2, 4,
                               f"Note soignant : {note}",
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        score_dom = db.score_domaine(ev, dom)
        pdf.set_font("Sans", "B", 9)
        pdf.cell(0, 6, f"Score domaine {dom} : {score_dom} / 16", align="R", **pdf._nl())

        # Réflexion — cause et attitude (par domaine, avec retour à la ligne auto)
        cause_val = ev[f"cause_{dom.lower()}"] or ""
        att_val   = ev[f"attitude_{dom.lower()}"] or ""
        if cause_val:
            pdf.set_font("Sans", "B", 8)
            pdf.cell(label_w, 5, "Réflexion — cause :")
            pdf.set_font("Sans", "", 8)
            pdf.multi_cell(0, 5, cause_val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if att_val:
            pdf.set_font("Sans", "B", 8)
            pdf.cell(label_w, 5, "Attitude appropriée :")
            pdf.set_font("Sans", "", 8)
            pdf.multi_cell(0, 5, att_val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    total = db.score_total(ev)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Sans", "B", 12)
    pdf.cell(0, 10, f"SCORE TOTAL ÉPADE : {total} / 64", fill=True, align="C", **pdf._nl())
    if total > SEUIL:
        pdf.set_text_color(200, 0, 0)
        pdf.set_font("Sans", "B", 10)
        pdf.cell(0, 7, "Score critique — rechercher une cause réversible", align="C", **pdf._nl())
        pdf.set_text_color(0, 0, 0)

    pdf.ln(4)
    pdf.set_font("Sans", "I", 8)
    pdf.cell(0, 5, "Règle : le score retenu est le PLUS ÉLEVÉ observé sur la période (marée haute).", **pdf._nl())

    pdf.output(str(path))


# ── Résumé scores ─────────────────────────────────────────────────────────────

def export_resume(conn, eval_id, path):
    ev = db.get_evaluation(conn, eval_id)
    patient = db.get_patient(conn, ev["patient_id"])

    pdf = EpadePDF()
    pdf.header_epade()

    pdf.section_title("Identification")
    pdf.field_row("Patient :", f"{patient['nom'].upper()} {patient['prenom']}")
    if patient["service_chambre"]:
        pdf.field_row("Service / Chambre :", patient["service_chambre"])
    if patient["medecin_referent"]:
        pdf.field_row("Médecin référent :", patient["medecin_referent"])
    pdf.field_row("Soignant :", ev["soignant"])
    pdf.field_row("Période :", f"Du {ev['periode_du']} au {ev['periode_au']}")
    pdf.field_row("Date de cotation :", ev["date_cotation"])
    pdf.ln(6)

    pdf.section_title("Scores par domaine")

    for dom, (nom_dom, _) in db.DOMAINES.items():
        score = db.score_domaine(ev, dom)
        pdf.set_font("Sans", "B", 10)
        pdf.cell(70, 8, f"Domaine {dom} — {nom_dom}")
        pdf.set_font("Sans", "", 10)
        pdf.cell(20, 8, f"{score} / 16", align="R")
        x = pdf.get_x() + 5
        y = pdf.get_y()
        bar_w = 75
        pdf.set_fill_color(210, 210, 210)
        pdf.rect(x, y + 2, bar_w, 4, style="F")
        fill_color = (200, 50, 50) if score > 8 else (50, 160, 50)
        pdf.set_fill_color(*fill_color)
        pdf.rect(x, y + 2, bar_w * score / 16, 4, style="F")
        pdf.ln(8)

    pdf.ln(4)
    total = db.score_total(ev)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Sans", "B", 13)
    pdf.cell(0, 12, f"SCORE TOTAL : {total} / 64", fill=True, align="C", **pdf._nl())
    if total > SEUIL:
        pdf.set_text_color(200, 0, 0)
        pdf.set_font("Sans", "B", 10)
        pdf.cell(0, 7, "Score > 17 — rechercher une cause réversible", align="C", **pdf._nl())
        pdf.set_text_color(0, 0, 0)

    pdf.output(str(path))


# ── Historique patient ────────────────────────────────────────────────────────

def export_historique(conn, patient_id, path):
    patient = db.get_patient(conn, patient_id)
    evals = db.get_evaluations_patient(conn, patient_id)

    pdf = EpadePDF()
    pdf.header_epade()

    pdf.section_title("Patient")
    pdf.field_row("Nom :", f"{patient['nom'].upper()} {patient['prenom']}")
    pdf.field_row("Date de naissance :", patient["date_naissance"])
    if patient["numero_dossier"]:
        pdf.field_row("N° dossier :", patient["numero_dossier"])
    if patient["service_chambre"]:
        pdf.field_row("Service / Chambre :", patient["service_chambre"])
    if patient["medecin_referent"]:
        pdf.field_row("Médecin référent :", patient["medecin_referent"])
    pdf.ln(6)

    pdf.section_title("Historique des évaluations")

    cols    = [38, 24, 34, 12, 12, 12, 12, 16, 20]
    headers = ["Date", "Soignant", "Période", "A", "B", "C", "D", "Total", "Statut"]
    pdf.set_fill_color(210, 210, 210)
    pdf.set_font("Sans", "B", 8)
    for w, h in zip(cols, headers):
        pdf.cell(w, 6, h, border=1, fill=True, align="C")
    pdf.ln()

    finalisees = [e for e in evals if e["finalisee"]]
    for ev in finalisees:
        total = db.score_total(ev)
        if total > SEUIL:
            pdf.set_text_color(200, 0, 0)
        pdf.set_font("Sans", "", 8)
        row = [
            (ev["date_cotation"] or "")[:19],
            ev["soignant"] or "",
            f'{ev["periode_du"]} > {ev["periode_au"]}',
            str(db.score_domaine(ev, "A")),
            str(db.score_domaine(ev, "B")),
            str(db.score_domaine(ev, "C")),
            str(db.score_domaine(ev, "D")),
            str(total),
            "Verrouillée",
        ]
        for w, val in zip(cols, row):
            pdf.cell(w, 6, val[:22], border=1, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    if not finalisees:
        pdf.set_font("Sans", "I", 9)
        pdf.cell(0, 8, "Aucune évaluation finalisée.", **pdf._nl())

    pdf.output(str(path))
