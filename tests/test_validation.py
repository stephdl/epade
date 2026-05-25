import pytest
from db import (
    init_db, creer_patient, creer_evaluation,
    mettre_a_jour_evaluation, valider_champs_requis,
    finaliser_evaluation, SCORE_COLS,
)


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


@pytest.fixture
def eval_vide(conn):
    pid = creer_patient(conn, "Dupont", "Marie")
    eid = creer_evaluation(conn, pid)
    return conn, eid


def _remplir_tout(conn, eid):
    champs = {"soignant": "Martin", "periode_du": "2026-05-01", "periode_au": "2026-05-07"}
    champs.update({col: 1 for col in SCORE_COLS})
    mettre_a_jour_evaluation(conn, eid, **champs)


def test_validation_refusee_soignant_vide(eval_vide):
    conn, eid = eval_vide
    mettre_a_jour_evaluation(conn, eid, periode_du="2026-05-01", periode_au="2026-05-07")
    mettre_a_jour_evaluation(conn, eid, **{col: 1 for col in SCORE_COLS})
    manquants = valider_champs_requis(conn, eid)
    noms = [m.lower() for m in manquants]
    assert any("soignant" in m for m in noms)


def test_validation_refusee_periode_du_manquante(eval_vide):
    conn, eid = eval_vide
    _remplir_tout(conn, eid)
    mettre_a_jour_evaluation(conn, eid, periode_du="")
    manquants = valider_champs_requis(conn, eid)
    assert any("début" in m for m in manquants)


def test_validation_refusee_periode_au_manquante(eval_vide):
    conn, eid = eval_vide
    _remplir_tout(conn, eid)
    mettre_a_jour_evaluation(conn, eid, periode_au="")
    manquants = valider_champs_requis(conn, eid)
    assert any("fin" in m for m in manquants)


def test_validation_refusee_score_manquant(eval_vide):
    conn, eid = eval_vide
    _remplir_tout(conn, eid)
    mettre_a_jour_evaluation(conn, eid, a1=None)
    manquants = valider_champs_requis(conn, eid)
    assert any("A1" in m for m in manquants)


def test_validation_acceptee_si_tout_rempli(eval_vide):
    conn, eid = eval_vide
    _remplir_tout(conn, eid)
    assert valider_champs_requis(conn, eid) == []


def test_liste_exacte_des_champs_manquants(eval_vide):
    conn, eid = eval_vide
    # Rien de rempli sauf quelques scores
    mettre_a_jour_evaluation(conn, eid, a1=2, a2=1)
    manquants = valider_champs_requis(conn, eid)
    # Doit signaler soignant, periode_du, periode_au, et les 14 scores manquants
    assert any("Soignant" in m for m in manquants)
    assert any("début" in m for m in manquants)
    assert any("fin" in m for m in manquants)
    assert len(manquants) == 3 + 14  # soignant + 2 périodes + 14 scores


def test_finaliser_verrouille_definitivement(eval_vide):
    conn, eid = eval_vide
    _remplir_tout(conn, eid)
    finaliser_evaluation(conn, eid)
    with pytest.raises(ValueError):
        mettre_a_jour_evaluation(conn, eid, soignant="Nouveau")


def test_score_zero_est_valide(eval_vide):
    """Score 0 (absent) est une valeur valide, pas un champ manquant."""
    conn, eid = eval_vide
    champs = {"soignant": "Martin", "periode_du": "2026-05-01", "periode_au": "2026-05-07"}
    champs.update({col: 0 for col in SCORE_COLS})
    mettre_a_jour_evaluation(conn, eid, **champs)
    assert valider_champs_requis(conn, eid) == []


def test_score_quatre_est_valide(eval_vide):
    """Score 4 (très fort) est la valeur maximale valide."""
    conn, eid = eval_vide
    champs = {"soignant": "Martin", "periode_du": "2026-05-01", "periode_au": "2026-05-07"}
    champs.update({col: 4 for col in SCORE_COLS})
    mettre_a_jour_evaluation(conn, eid, **champs)
    assert valider_champs_requis(conn, eid) == []


def test_double_finalisation_interdit(eval_vide):
    """Finaliser une évaluation déjà finalisée lève ValueError."""
    conn, eid = eval_vide
    _remplir_tout(conn, eid)
    finaliser_evaluation(conn, eid)
    with pytest.raises(ValueError):
        finaliser_evaluation(conn, eid)


def test_finaliser_leve_erreur_si_incomplet(eval_vide):
    conn, eid = eval_vide
    with pytest.raises(ValueError):
        finaliser_evaluation(conn, eid)
