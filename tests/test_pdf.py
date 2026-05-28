import pytest
import tempfile
from pathlib import Path
from db import (
    init_db, creer_patient, creer_evaluation,
    mettre_a_jour_evaluation, finaliser_evaluation, SCORE_COLS,
)
from export.pdf import export_fiche_complete, export_resume, export_historique


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


@pytest.fixture
def eval_finalisee(conn):
    pid = creer_patient(conn, "Dupont", "Marie", "01/01/1940")
    eid = creer_evaluation(conn, pid)
    champs = {"referent": "Martin Lucie", "role_referent": "IDEC",
              "periode_du": "2026-05-01", "periode_au": "2026-05-07",
              "duree": "15 min"}
    champs.update({col: 2 for col in SCORE_COLS})
    champs["a1"] = 4
    mettre_a_jour_evaluation(conn, eid, **champs)
    finaliser_evaluation(conn, eid)
    return conn, eid, pid


def test_export_fiche_complete(eval_finalisee):
    conn, eid, pid = eval_finalisee
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    export_fiche_complete(conn, eid, path)
    assert path.exists()
    assert path.stat().st_size > 1000
    path.unlink()


def test_export_resume(eval_finalisee):
    conn, eid, pid = eval_finalisee
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    export_resume(conn, eid, path)
    assert path.exists()
    assert path.stat().st_size > 500
    path.unlink()


def test_export_historique(eval_finalisee):
    conn, eid, pid = eval_finalisee
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    export_historique(conn, pid, path)
    assert path.exists()
    assert path.stat().st_size > 500
    path.unlink()


def test_export_historique_sans_evaluations(conn):
    pid = creer_patient(conn, "Martin", "Jean")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    export_historique(conn, pid, path)
    assert path.exists()
    assert path.stat().st_size > 0
    path.unlink()
