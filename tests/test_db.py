import pytest
import sqlite3
from db import (
    init_db, creer_patient, get_patient, modifier_patient, rechercher_patients,
    archiver_patient, restaurer_patient, supprimer_patient,
    creer_evaluation, get_evaluation, get_evaluations_patient,
    mettre_a_jour_evaluation, valider_champs_requis, finaliser_evaluation,
    supprimer_evaluation, score_domaine, score_total, SCORE_COLS,
)


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


def _eval_complete(conn, eval_id):
    """Remplit tous les champs requis d'une évaluation."""
    champs = {"soignant": "Martin", "periode_du": "2026-05-01", "periode_au": "2026-05-07"}
    champs.update({col: 2 for col in SCORE_COLS})
    mettre_a_jour_evaluation(conn, eval_id, **champs)


# ── Patients ────────────────────────────────────────────────────────────────

def test_creer_et_recuperer_patient(conn):
    pid = creer_patient(conn, "Dupont", "Marie", "01/01/1940")
    p = get_patient(conn, pid)
    assert p["nom"] == "Dupont"
    assert p["prenom"] == "Marie"
    assert p["date_naissance"] == "01/01/1940"


def test_recherche_patient_insensible_casse(conn):
    creer_patient(conn, "Dupont", "Marie")
    creer_patient(conn, "Martin", "Jean")
    res = rechercher_patients(conn, "dup")
    assert len(res) == 1
    assert res[0]["nom"] == "Dupont"


def test_recherche_patient_vide_retourne_tous(conn):
    creer_patient(conn, "Dupont", "Marie")
    creer_patient(conn, "Martin", "Jean")
    res = rechercher_patients(conn, "")
    assert len(res) == 2


def test_recherche_par_prenom(conn):
    creer_patient(conn, "Dupont", "Marie")
    creer_patient(conn, "Martin", "Jean")
    res = rechercher_patients(conn, "jean")
    assert len(res) == 1
    assert res[0]["prenom"] == "Jean"


def test_creer_patient_avec_champs_etendus(conn):
    pid = creer_patient(conn, "Dupont", "Marie", "01/01/1940",
                        telephone="0601020304",
                        medecin_referent="Dr Leroy",
                        service_chambre="Gériatrie / chambre 12",
                        contact_famille_nom="Dupont Paul",
                        contact_famille_tel="0612131415",
                        contact_famille_lien="Fils")
    p = get_patient(conn, pid)
    assert p["telephone"] == "0601020304"
    assert p["medecin_referent"] == "Dr Leroy"
    assert p["service_chambre"] == "Gériatrie / chambre 12"
    assert p["contact_famille_nom"] == "Dupont Paul"
    assert p["contact_famille_lien"] == "Fils"


def test_modifier_patient(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    modifier_patient(conn, pid, telephone="0600000000", adresse="1 rue de la Paix")
    p = get_patient(conn, pid)
    assert p["telephone"] == "0600000000"
    assert p["adresse"] == "1 rue de la Paix"
    assert p["nom"] == "Dupont"  # champs non modifiés intacts


def test_archiver_et_restaurer_patient(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    assert len(rechercher_patients(conn, "")) == 1

    archiver_patient(conn, pid)
    assert len(rechercher_patients(conn, "")) == 0
    assert len(rechercher_patients(conn, "", inclure_archives=True)) == 1

    restaurer_patient(conn, pid)
    assert len(rechercher_patients(conn, "")) == 1


def test_supprimer_patient_supprime_evaluations(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    creer_evaluation(conn, pid)
    creer_evaluation(conn, pid)
    assert len(get_evaluations_patient(conn, pid)) == 2

    supprimer_patient(conn, pid)
    assert get_patient(conn, pid) is None
    assert len(get_evaluations_patient(conn, pid)) == 0


def test_recherche_exclut_archives_par_defaut(conn):
    pid1 = creer_patient(conn, "Actif", "Patient")
    pid2 = creer_patient(conn, "Archive", "Patient")
    archiver_patient(conn, pid2)
    res = rechercher_patients(conn, "")
    noms = [r["nom"] for r in res]
    assert "Actif" in noms
    assert "Archive" not in noms


# ── Évaluations ─────────────────────────────────────────────────────────────

def test_creer_evaluation_brouillon(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    ev = get_evaluation(conn, eid)
    assert ev["finalisee"] == 0
    assert ev["date_cotation"] is None


def test_mettre_a_jour_evaluation(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    mettre_a_jour_evaluation(conn, eid, soignant="Lucie", a1=3)
    ev = get_evaluation(conn, eid)
    assert ev["soignant"] == "Lucie"
    assert ev["a1"] == 3


def test_finaliser_evaluation(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    _eval_complete(conn, eid)
    finaliser_evaluation(conn, eid)
    ev = get_evaluation(conn, eid)
    assert ev["finalisee"] == 1
    assert ev["date_cotation"] is not None


def test_impossible_modifier_evaluation_finalisee(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    _eval_complete(conn, eid)
    finaliser_evaluation(conn, eid)
    with pytest.raises(ValueError):
        mettre_a_jour_evaluation(conn, eid, soignant="Autre")


def test_get_evaluations_patient(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid1 = creer_evaluation(conn, pid)
    eid2 = creer_evaluation(conn, pid)
    evs = get_evaluations_patient(conn, pid)
    ids = [e["id"] for e in evs]
    assert eid1 in ids and eid2 in ids


# ── Scores ───────────────────────────────────────────────────────────────────

def test_score_domaine_et_total(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    mettre_a_jour_evaluation(conn, eid, a1=4, a2=3, a3=2, a4=1,
                                        b1=0, b2=0, b3=0, b4=0,
                                        c1=1, c2=1, c3=1, c4=1,
                                        d1=2, d2=2, d3=2, d4=2)
    ev = get_evaluation(conn, eid)
    assert score_domaine(ev, "A") == 10
    assert score_domaine(ev, "B") == 0
    assert score_domaine(ev, "C") == 4
    assert score_domaine(ev, "D") == 8
    assert score_total(ev) == 22


def test_score_total_max(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    mettre_a_jour_evaluation(conn, eid, **{col: 4 for col in SCORE_COLS})
    ev = get_evaluation(conn, eid)
    assert score_total(ev) == 64


def test_score_total_tous_zero(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    mettre_a_jour_evaluation(conn, eid, **{col: 0 for col in SCORE_COLS})
    ev = get_evaluation(conn, eid)
    assert score_total(ev) == 0


def test_score_total_avec_scores_null(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    # scores NULL comptent pour 0
    ev = get_evaluation(conn, eid)
    assert score_total(ev) == 0
    assert score_domaine(ev, "A") == 0


def test_get_evaluations_patient_ordre_desc(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid1 = creer_evaluation(conn, pid)
    eid2 = creer_evaluation(conn, pid)
    champs = {"soignant": "X", "periode_du": "2026-01-01", "periode_au": "2026-01-07"}
    champs.update({col: 1 for col in SCORE_COLS})
    mettre_a_jour_evaluation(conn, eid1, **{**champs})
    finaliser_evaluation(conn, eid1)
    mettre_a_jour_evaluation(conn, eid2, **{**champs, "periode_du": "2026-03-01",
                                            "periode_au": "2026-03-07"})
    finaliser_evaluation(conn, eid2)
    evs = get_evaluations_patient(conn, pid)
    # Le plus récent (eid2) doit être en premier
    assert evs[0]["id"] == eid2
    assert evs[1]["id"] == eid1


def test_get_patient_inexistant_retourne_none(conn):
    assert get_patient(conn, 99999) is None


# ── Suppression brouillon ────────────────────────────────────────────────────

def test_supprimer_evaluation_brouillon(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    supprimer_evaluation(conn, eid)
    assert get_evaluation(conn, eid) is None


def test_supprimer_evaluation_finalisee_interdit(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    champs = {"soignant": "Martin", "periode_du": "2026-05-01", "periode_au": "2026-05-07"}
    champs.update({col: 2 for col in SCORE_COLS})
    mettre_a_jour_evaluation(conn, eid, **champs)
    finaliser_evaluation(conn, eid)
    with pytest.raises(ValueError):
        supprimer_evaluation(conn, eid)


def test_supprimer_evaluation_inexistante(conn):
    with pytest.raises(ValueError):
        supprimer_evaluation(conn, 99999)
