import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import db
from gui.cotation_form import score_labels, _score_from_label, SCORE_LABELS

ALL_ITEMS = list(db.ITEMS.keys())  # 16 items a1..d4


# ── Intégrité du dictionnaire CRITERES ──────────────────────────────────────

def test_criteres_contient_tous_les_items():
    manquants = [k for k in ALL_ITEMS if k not in db.CRITERES]
    assert manquants == [], f"Items manquants dans CRITERES : {manquants}"


def test_criteres_cinq_niveaux_par_item():
    for item in ALL_ITEMS:
        niveaux = set(db.CRITERES[item].keys())
        assert niveaux == {0, 1, 2, 3, 4}, \
            f"{item} : niveaux attendus {{0,1,2,3,4}}, trouvés {niveaux}"


def test_criteres_aucune_description_vide():
    for item, niveaux in db.CRITERES.items():
        for score, desc in niveaux.items():
            assert desc and desc.strip(), \
                f"{item} niveau {score} : description vide"


def test_criteres_descriptions_sont_des_chaines():
    for item, niveaux in db.CRITERES.items():
        for score, desc in niveaux.items():
            assert isinstance(desc, str), \
                f"{item} niveau {score} : attendu str, trouvé {type(desc)}"


# ── score_labels() ───────────────────────────────────────────────────────────

def test_score_labels_retourne_six_elements():
    for item in ALL_ITEMS:
        labels = score_labels(item)
        assert len(labels) == 6, \
            f"{item} : attendu 6 labels, trouvé {len(labels)}"


def test_score_labels_premier_element_non_renseigne():
    for item in ALL_ITEMS:
        assert score_labels(item)[0] == SCORE_LABELS[0]


def test_score_labels_contient_le_score():
    # Les scores sont affichés de 4 à 0 (ordre décroissant)
    for item in ALL_ITEMS:
        labels = score_labels(item)
        scores_attendus = [4, 3, 2, 1, 0]
        for idx, (label, score) in enumerate(zip(labels[1:], scores_attendus)):
            assert label.startswith(str(score)), \
                f"{item} position {idx+1} : attendu '{score}', label : '{label}'"


def test_score_labels_contient_la_description():
    # Labels en ordre décroissant : index 1=score4, 2=score3, ... 5=score0
    for item in ALL_ITEMS:
        labels = score_labels(item)
        for score in range(5):
            desc = db.CRITERES[item][score]
            assert desc in labels[5 - score], \
                f"{item} niveau {score} : description absente du label"


# ── _score_from_label() ──────────────────────────────────────────────────────

def test_score_from_label_non_renseigne():
    assert _score_from_label(SCORE_LABELS[0]) is None


def test_score_from_label_vide():
    assert _score_from_label("") is None
    assert _score_from_label(None) is None


def test_score_from_label_extrait_entier():
    for item in ALL_ITEMS:
        labels = score_labels(item)
        for score in range(5):
            assert _score_from_label(labels[5 - score]) == score
