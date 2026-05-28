import sqlite3
from datetime import datetime
from pathlib import Path

import sys as _sys
if getattr(_sys, "frozen", False):
    # Exécution depuis un binaire PyInstaller — base à côté de l'exe
    DB_PATH = Path(_sys.executable).parent / "data" / "epade.db"
else:
    DB_PATH = Path(__file__).parent / "data" / "epade.db"

SCORE_COLS = [f"{d}{i}" for d in "abcd" for i in range(1, 5)]
NOTE_COLS  = [f"note_{d}{i}" for d in "abcd" for i in range(1, 5)]

ITEMS = {
    "a1": "Regard / Mimique",
    "a2": "Voix",
    "a3": "Paroles (menaces, insultes…)",
    "a4": "Gestes (frappes, crachats…)",
    "b1": "Communication / Regard",
    "b2": "Mobilisation (lit, fauteuil…)",
    "b3": "Alimentation / Boisson",
    "b4": "Soins (toilette, médicaments…)",
    "c1": "Ordres / Demandes / Écholalie répétés",
    "c2": "Paroles anxieuses / Appels à l'aide",
    "c3": "Paroles dépressives (vie/mort)",
    "c4": "Paroles à côté de la réalité / Délire",
    "d1": "Sphère locomotrice (fugues, automutilations…)",
    "d2": "Sphère alimentaire / Orale",
    "d3": "Sphères urinaire et anale",
    "d4": "Sphère sexuelle / Génitale",
}

CRITERES = {
    "a1": {
        4: "Regard de haine ou mimique de fureur",
        3: "Regard de colère ou mimique de colère",
        2: "Regard noir ou mimique grimaçante",
        1: "Regard hostile ou mimique hostile",
        0: "Regard normal et mimique normale",
    },
    "a2": {
        4: "Hurlements",
        3: "Cris",
        2: "Gémissement ou ronchonnement ou grognement",
        1: "Voix hostile",
        0: "Voix normale",
    },
    "a3": {
        4: "Menaces",
        3: "Accusations ou insultes avec personnalisation de l'insulte",
        2: "Insultes sans personnalisation de l'insulte",
        1: "Reproches ou disqualifications",
        0: "Absence d'agression verbale",
    },
    "a4": {
        4: "Attaque des personnes avec danger réel (morsure, coup de poing)",
        3: "Attaque des personnes sans danger réel (agrippe, griffe, gifle, crachats)",
        2: "Geste de menace sur les personnes (index levé, poing serré)",
        1: "Renverse, jette au sol, détruit ou vole les objets (poche de stomie…)",
        0: "Absence d'agression physique",
    },
    "b1": {
        4: "Communication impossible (pseudocoma)",
        3: "Communication limitée au minimum avec les yeux",
        2: "Communication obtenue avec négociation",
        1: "Se met à parler avec quelques paroles simples",
        0: "Communique et parle de façon habituelle",
    },
    "b2": {
        4: "Mobilisation impossible (pas de lever, grabatisation)",
        3: "Mobilisation limitée au minimum avec passage du lit au fauteuil",
        2: "Mobilisation obtenue avec négociation et aide physique",
        1: "Se met à se déplacer avec quelques paroles simples",
        0: "Se déplace et se laisse mobiliser de façon habituelle",
    },
    "b3": {
        4: "Alimentation et boisson impossibles (risque vital)",
        3: "Alimentation et boisson limitées au minimum (recrache)",
        2: "Alimentation et boisson obtenues avec négociation et aide physique",
        1: "Se met à manger et boire avec quelques paroles simples",
        0: "Mange et boit de façon habituelle",
    },
    "b4": {
        4: "Soins impossibles (risque vital)",
        3: "Soins limités au minimum",
        2: "Soins obtenus avec négociation et aide physique",
        1: "Se met à accepter les soins avec quelques paroles simples",
        0: "Les soins sont effectués de façon habituelle",
    },
    "c1": {
        4: "Ordres ou exigences contradictoires sans réponse possible",
        3: "Demandes incessantes ne pouvant pas être satisfaites",
        2: "Paroles ou mots répétés en boucle (écholalie)",
        1: "Paroles en quantité excessive (logorrhée, euphorie)",
        0: "Paroles en quantité habituelle",
    },
    "c2": {
        4: "Paroles anxieuses ou plaintes corporelles avec crise d'angoisse",
        3: "Paroles anxieuses ou plaintes corporelles avec appels fréquents",
        2: "Paroles anxieuses ou plaintes corporelles avec appel épisodique",
        1: "Paroles anxieuses ou plaintes corporelles sans appel",
        0: "Absence de parole anxieuse ou de plainte corporelle",
    },
    "c3": {
        4: "Tentative de suicide ou comportement équivalent",
        3: "Paroles exprimant un projet de se suicider",
        2: "Paroles exprimant un désir de mort (« Je veux mourir »)",
        1: "Paroles exprimant une perte du désir de vivre",
        0: "Paroles habituelles sur la vie et sur la mort",
    },
    "c4": {
        4: "Paroles délirantes ou hallucinations avec passage à l'acte",
        3: "Paroles délirantes ou hallucinations sans passage à l'acte (certitude)",
        2: "Paroles délirantes, hallucinations, mensonges ou fabulations (probabilité)",
        1: "Paroles délirantes, hallucinations, mensonges ou fabulations (possibilité)",
        0: "Absence de parole délirante, d'hallucination, de mensonge ou de fabulation",
    },
    "d1": {
        4: "Disparitions (« fugues »), automutilations (doigt écrasé, chutes au sol)",
        3: "Déambulation avec intrusions dans les chambres, kleptomanie",
        2: "Déambulation avec suivi à la trace des soignants",
        1: "Agitation (bouge les bras ou les jambes, tourne en rond)",
        0: "Comportement locomoteur habituel",
    },
    "d2": {
        4: "Mange des choses toxiques ou non comestibles (ex. : produit ménager)",
        3: "Mange des choses dégoûtantes (ex. : excréments)",
        2: "Mange trop et trop vite avec risque de fausses routes (gloutonnerie)",
        1: "Mange trop (boulimie)",
        0: "Comportement oral habituel",
    },
    "d3": {
        4: "Étale ses excréments",
        3: "Défécations inadaptées ou refus inadapté des protections",
        2: "Mictions inadaptées constantes",
        1: "Mictions inadaptées par épisodes",
        0: "Fonctions sphinctériennes habituelles",
    },
    "d4": {
        4: "Agression sexuelle sur personne vulnérable ou masturbation traumatique",
        3: "Contacts à caractère sexuel inadaptés (attouchements sexuels)",
        2: "Gestes à caractère sexuel inadaptés (exhibition, masturbation en public)",
        1: "Propositions à caractère sexuel, érotisation, préoccupations sexuelles envahissantes",
        0: "Vie sexuelle sans particularités",
    },
}

DOMAINES = {
    "A": ("VIOLENCES déconcertantes",  ["a1","a2","a3","a4"]),
    "B": ("REFUS déconcertants",       ["b1","b2","b3","b4"]),
    "C": ("PAROLES déconcertantes",    ["c1","c2","c3","c4"]),
    "D": ("ACTES déconcertants",       ["d1","d2","d3","d4"]),
}

LISTES = {
    "A": {
        "note": [
            "Crainte — Peur d'être agressé",
            "Crainte légère mais présente",
            "Peur marquée avec hypervigilance",
            "Sentiment d'insécurité permanent",
            "Autre note (champ libre)",
        ],
        "cause": [
            "Urgence du corps — Confusion agitée / Iatrogénie / Sevrage",
            "Urgence du corps — Douleur / Fracture / Inconfort",
            "Urgence du corps — Crise d'hypoglycémie / Épilepsie non convulsive",
            "Urgence du corps — Globe vésical / Fécalome",
            "Souffrance de l'esprit — Besoin non satisfait / Négligence / Maltraitance",
            "Souffrance de l'esprit — Hypomanie / Dépression hostile",
            "Souffrance de l'esprit — Personnalité borderline / sans empathie",
            "Souffrance de l'enfance — Enfant battu / Enfant à la rue",
            "Autre cause (champ libre)",
        ],
        "attitude": [
            "Chercher les motifs expliquant la violence",
            "Tenir l'insulte sans la prendre pour soi",
            "Valoriser le patient, demander son aide",
            "Oser poser une limite avec douceur",
            "Autre attitude (champ libre)",
        ],
    },
    "B": {
        "note": [
            "Impuissance — Embarras — Culpabilité",
            "Impuissance légère, ajustement possible",
            "Embarras marqué, remise en question",
            "Culpabilité forte, sentiment d'échec",
            "Autre note (champ libre)",
        ],
        "cause": [
            "Urgence du corps — Confusion ralentie / Iatrogénie / Surdosage (apathie aiguë)",
            "Urgence du corps — Douleur / Fracture / Inconfort",
            "Urgence du corps — Apnée du sommeil / Infection",
            "Souffrance de l'esprit — Besoin non satisfait / Négligence / Maltraitance",
            "Souffrance de l'esprit — Déficit psychotique",
            "Souffrance de l'esprit — Personnalité dominante devenue dépendante",
            "Souffrance de l'enfance — Enfant abandonné / Négligé / Rejeté",
            "Autre cause (champ libre)",
        ],
        "attitude": [
            "Reconnaître le droit au consentement — Accepter le droit au refus",
            "Donner raison à la personne qui refuse",
            "Partir pour mieux revenir",
            "Parler de tout et de rien, valoriser le patient",
            "Refaire la proposition / Demander son aide",
            "Oser dire que changer d'avis est possible",
            "Autre attitude (champ libre)",
        ],
    },
    "C": {
        "note": [
            "Inquiétude — Anxiété anticipatoire",
            "Légère inquiétude, situation gérable",
            "Anxiété anticipatoire modérée",
            "Anxiété forte, mobilisation permanente",
            "Autre note (champ libre)",
        ],
        "cause": [
            "Urgence du corps — Confusion anxieuse / Iatrogénie / Sevrage",
            "Urgence du corps — Douleur corporelle / Inconfort",
            "Urgence du corps — Péritonite / Embolie pulmonaire",
            "Souffrance de l'esprit — Besoin non satisfait / Négligence / Maltraitance",
            "Souffrance de l'esprit — Anxiété de séparation / d'abandon",
            "Souffrance de l'esprit — Épisode maniaque / Syndrome frontal",
            "Souffrance de l'esprit — Personnalité obsessionnelle / hypocondriaque",
            "Souffrance de l'enfance — Dissimulations / Non-dits",
            "Souffrance de l'enfance — Secrets de famille / Deuils non faits / NDE",
            "Autre cause (champ libre)",
        ],
        "attitude": [
            "Se taire — Tenir la plainte avec sollicitude",
            "Entendre, comprendre le sens caché",
            "Clarifier",
            "Reformuler avec empathie",
            "Oser exprimer un avis avec respect",
            "Autre attitude (champ libre)",
        ],
    },
    "D": {
        "note": [
            "Inquiétude — Anxiété anticipatoire",
            "Légère inquiétude, situation gérable",
            "Anxiété anticipatoire modérée",
            "Anxiété forte, vigilance continue",
            "Autre note (champ libre)",
        ],
        "cause": [
            "Urgence du corps — Confusion désinhibée / Iatrogénie / Sevrage",
            "Urgence du corps — Douleur corporelle / Inconfort / Prurit / Gale",
            "Urgence du corps — Hypoglycémie / Épilepsie",
            "Souffrance de l'esprit — Besoin non satisfait / Négligence / Maltraitance",
            "Souffrance de l'esprit — Peur de la mort / Ennui",
            "Souffrance de l'esprit — Épisode maniaque / Syndrome frontal",
            "Souffrance de l'esprit — Personnalité impulsive",
            "Souffrance de l'enfance — Ambiance incestuelle",
            "Souffrance de l'enfance — Incestes / Viols",
            "Autre cause (champ libre)",
        ],
        "attitude": [
            "Reconnaître l'enfant à l'œuvre (acte archaïque)",
            "Répondre aux actes par des activités — Faire diversion",
            "Répondre aux actes par des activités — Utiliser des médiations",
            "Répondre aux actes par des activités — Art thérapie / Activités (ré)créatives / Culture",
            "Autre attitude (champ libre)",
        ],
    },
}

CAUSES = {
    "a1": "Urgence du corps — Confusion agitée / Iatrogénie / Sevrage",
    "a2": "Urgence du corps — Confusion agitée / Iatrogénie / Sevrage",
    "a3": "Urgence du corps — Confusion agitée / Iatrogénie / Sevrage",
    "a4": "Urgence du corps — Confusion agitée / Iatrogénie / Sevrage",
    "b1": "Urgence du corps — Confusion ralentie / Iatrogénie / Surdosage (apathie aiguë)",
    "b2": "Urgence du corps — Confusion ralentie / Iatrogénie / Surdosage (apathie aiguë)",
    "b3": "Urgence du corps — Confusion ralentie / Iatrogénie / Surdosage (apathie aiguë)",
    "b4": "Urgence du corps — Confusion ralentie / Iatrogénie / Surdosage (apathie aiguë)",
    "c1": "Urgence du corps — Confusion anxieuse / Iatrogénie / Sevrage",
    "c2": "Urgence du corps — Confusion anxieuse / Iatrogénie / Sevrage",
    "c3": "Urgence du corps — Confusion anxieuse / Iatrogénie / Sevrage",
    "c4": "Urgence du corps — Confusion anxieuse / Iatrogénie / Sevrage",
    "d1": "Urgence du corps — Confusion désinhibée / Iatrogénie / Sevrage",
    "d2": "Urgence du corps — Confusion désinhibée / Iatrogénie / Sevrage",
    "d3": "Urgence du corps — Confusion désinhibée / Iatrogénie / Sevrage",
    "d4": "Urgence du corps — Confusion désinhibée / Iatrogénie / Sevrage",
}

ATTITUDES = {
    "a1": "Chercher les motifs expliquant la violence",
    "a2": "Chercher les motifs expliquant la violence",
    "a3": "Chercher les motifs expliquant la violence",
    "a4": "Chercher les motifs expliquant la violence",
    "b1": "Reconnaître le droit au consentement — Accepter le droit au refus",
    "b2": "Reconnaître le droit au consentement — Accepter le droit au refus",
    "b3": "Reconnaître le droit au consentement — Accepter le droit au refus",
    "b4": "Reconnaître le droit au consentement — Accepter le droit au refus",
    "c1": "Se taire — Tenir la plainte avec sollicitude",
    "c2": "Se taire — Tenir la plainte avec sollicitude",
    "c3": "Se taire — Tenir la plainte avec sollicitude",
    "c4": "Se taire — Tenir la plainte avec sollicitude",
    "d1": "Reconnaître l'enfant à l'œuvre (acte archaïque)",
    "d2": "Reconnaître l'enfant à l'œuvre (acte archaïque)",
    "d3": "Reconnaître l'enfant à l'œuvre (acte archaïque)",
    "d4": "Reconnaître l'enfant à l'œuvre (acte archaïque)",
}


def _connect(db_path=None):
    path = db_path or DB_PATH
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


PATIENT_EXTRA_COLS = (
    "telephone", "adresse",
    "contact_famille_nom", "contact_famille_tel", "contact_famille_lien",
    "medecin_referent", "service_chambre", "numero_dossier", "date_admission",
)


def init_db(db_path=None):
    conn = _connect(db_path)
    score_defs  = ", ".join(f"{c} INTEGER" for c in SCORE_COLS)
    note_defs   = ", ".join(f"{c} TEXT" for c in NOTE_COLS)
    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS patients (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nom            TEXT NOT NULL,
            prenom         TEXT NOT NULL,
            date_naissance TEXT,
            telephone      TEXT,
            adresse        TEXT,
            contact_famille_nom  TEXT,
            contact_famille_tel  TEXT,
            contact_famille_lien TEXT,
            medecin_referent     TEXT,
            service_chambre      TEXT,
            numero_dossier       TEXT,
            date_admission       TEXT,
            archive        INTEGER DEFAULT 0,
            created_at     TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS evaluations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id    INTEGER NOT NULL REFERENCES patients(id),
            soignant      TEXT NOT NULL DEFAULT '',
            referent      TEXT NOT NULL DEFAULT '',
            role_referent TEXT NOT NULL DEFAULT '',
            participant_mt    INTEGER DEFAULT 0,
            participant_mco   INTEGER DEFAULT 0,
            participant_idec  INTEGER DEFAULT 0,
            participant_ide   INTEGER DEFAULT 0,
            participant_as    INTEGER DEFAULT 0,
            participant_ash   INTEGER DEFAULT 0,
            participant_libre TEXT,
            periode_du    TEXT NOT NULL DEFAULT '',
            periode_au    TEXT NOT NULL DEFAULT '',
            duree         TEXT,
            date_cotation TEXT,
            {score_defs},
            {note_defs},
            cause_a TEXT, cause_b TEXT, cause_c TEXT, cause_d TEXT,
            attitude_a TEXT, attitude_b TEXT, attitude_c TEXT, attitude_d TEXT,
            finalisee     INTEGER DEFAULT 0
        );
    """)
    # Migration : ajouter les colonnes manquantes sur base existante
    existing_patients = {row[1] for row in conn.execute("PRAGMA table_info(patients)")}
    for col in PATIENT_EXTRA_COLS:
        if col not in existing_patients:
            conn.execute(f"ALTER TABLE patients ADD COLUMN {col} TEXT")
    if "archive" not in existing_patients:
        conn.execute("ALTER TABLE patients ADD COLUMN archive INTEGER DEFAULT 0")
    existing_evals = {row[1] for row in conn.execute("PRAGMA table_info(evaluations)")}
    for col in ("cause_a","cause_b","cause_c","cause_d",
                "attitude_a","attitude_b","attitude_c","attitude_d"):
        if col not in existing_evals:
            conn.execute(f"ALTER TABLE evaluations ADD COLUMN {col} TEXT")
    # Migration : nouvelles colonnes référent et participants
    if "referent" not in existing_evals:
        conn.execute("ALTER TABLE evaluations ADD COLUMN referent TEXT NOT NULL DEFAULT ''")
    if "role_referent" not in existing_evals:
        conn.execute("ALTER TABLE evaluations ADD COLUMN role_referent TEXT NOT NULL DEFAULT ''")
    for pcol, pdef in (
        ("participant_mt",   "INTEGER DEFAULT 0"),
        ("participant_mco",  "INTEGER DEFAULT 0"),
        ("participant_idec", "INTEGER DEFAULT 0"),
        ("participant_ide",  "INTEGER DEFAULT 0"),
        ("participant_as",   "INTEGER DEFAULT 0"),
        ("participant_ash",  "INTEGER DEFAULT 0"),
        ("participant_libre", "TEXT"),
    ):
        if pcol not in existing_evals:
            conn.execute(f"ALTER TABLE evaluations ADD COLUMN {pcol} {pdef}")
    # Copier soignant → referent pour les évals existantes
    conn.execute(
        "UPDATE evaluations SET referent = soignant "
        "WHERE (referent IS NULL OR referent = '') AND soignant != ''"
    )
    conn.commit()
    return conn


# ── Patients ────────────────────────────────────────────────────────────────

def creer_patient(conn, nom, prenom, date_naissance=None, **extra):
    cols = "nom, prenom, date_naissance"
    vals = [nom.strip(), prenom.strip(), date_naissance]
    for k in PATIENT_EXTRA_COLS:
        if k in extra:
            cols += f", {k}"
            vals.append(extra[k] or None)
    placeholders = ", ".join("?" * len(vals))
    cur = conn.execute(f"INSERT INTO patients ({cols}) VALUES ({placeholders})", vals)  # nosec B608
    conn.commit()
    return cur.lastrowid


def modifier_patient(conn, patient_id, **champs):
    if not champs:
        return
    sets = ", ".join(f"{k}=?" for k in champs)
    conn.execute(f"UPDATE patients SET {sets} WHERE id=?", (*champs.values(), patient_id))  # nosec B608
    conn.commit()


def get_patient(conn, patient_id):
    return conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()


def rechercher_patients(conn, query="", inclure_archives=False):
    q = f"%{query.strip()}%"
    filtre = "" if inclure_archives else " AND (archive IS NULL OR archive=0)"
    return conn.execute(
        f"SELECT * FROM patients WHERE (nom LIKE ? OR prenom LIKE ?){filtre} ORDER BY nom, prenom",  # nosec B608
        (q, q),
    ).fetchall()


def archiver_patient(conn, patient_id):
    conn.execute("UPDATE patients SET archive=1 WHERE id=?", (patient_id,))
    conn.commit()


def restaurer_patient(conn, patient_id):
    conn.execute("UPDATE patients SET archive=0 WHERE id=?", (patient_id,))
    conn.commit()


def supprimer_patient(conn, patient_id):
    conn.execute("DELETE FROM evaluations WHERE patient_id=?", (patient_id,))
    conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    conn.commit()


# ── Évaluations ─────────────────────────────────────────────────────────────

def creer_evaluation(conn, patient_id):
    cur = conn.execute(
        "INSERT INTO evaluations (patient_id, soignant, periode_du, periode_au) VALUES (?,?,?,?)",
        (patient_id, "", "", ""),
    )
    conn.commit()
    return cur.lastrowid


def get_evaluation(conn, eval_id):
    return conn.execute("SELECT * FROM evaluations WHERE id=?", (eval_id,)).fetchone()


def get_evaluations_patient(conn, patient_id):
    return conn.execute(
        "SELECT * FROM evaluations WHERE patient_id=? ORDER BY date_cotation DESC, id DESC",
        (patient_id,),
    ).fetchall()


def supprimer_evaluation(conn, eval_id):
    """Supprime un brouillon (finalisee=0). Lève ValueError si finalisée."""
    row = conn.execute("SELECT finalisee FROM evaluations WHERE id=?", (eval_id,)).fetchone()
    if row is None:
        raise ValueError("Évaluation introuvable.")
    if row["finalisee"] == 1:
        raise ValueError("Impossible de supprimer une évaluation finalisée.")
    conn.execute("DELETE FROM evaluations WHERE id=? AND finalisee=0", (eval_id,))
    conn.commit()


def mettre_a_jour_evaluation(conn, eval_id, **champs):
    """Met à jour les champs d'un brouillon (finalisee=0 obligatoire)."""
    if not champs:
        return
    row = conn.execute("SELECT finalisee FROM evaluations WHERE id=?", (eval_id,)).fetchone()
    if row is None or row["finalisee"] == 1:
        raise ValueError("Évaluation introuvable ou déjà finalisée.")
    sets = ", ".join(f"{k}=?" for k in champs)
    conn.execute(
        f"UPDATE evaluations SET {sets} WHERE id=? AND finalisee=0",  # nosec B608
        (*champs.values(), eval_id),
    )
    conn.commit()


def valider_champs_requis(conn, eval_id):
    """Retourne la liste des champs manquants. Liste vide = OK."""
    row = get_evaluation(conn, eval_id)
    if row is None:
        return ["Évaluation introuvable"]
    manquants = []
    if not (row["referent"] or "").strip():
        manquants.append("Référent (nom)")
    if not (row["role_referent"] or "").strip():
        manquants.append("Référent (rôle)")
    if not (row["periode_du"] or "").strip():
        manquants.append("Période — date de début")
    if not (row["periode_au"] or "").strip():
        manquants.append("Période — date de fin")
    for col in SCORE_COLS:
        if row[col] is None:
            manquants.append(f"Score {col.upper()} — {ITEMS[col]}")
    return manquants


def finaliser_evaluation(conn, eval_id):
    """Verrouille l'évaluation. Lève ValueError si déjà finalisée ou champs manquants."""
    row = conn.execute("SELECT finalisee FROM evaluations WHERE id=?", (eval_id,)).fetchone()
    if row is None:
        raise ValueError("Évaluation introuvable.")
    if row["finalisee"] == 1:
        raise ValueError("Cette évaluation est déjà finalisée.")
    manquants = valider_champs_requis(conn, eval_id)
    if manquants:
        raise ValueError("Champs manquants :\n• " + "\n• ".join(manquants))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE evaluations SET finalisee=1, date_cotation=? WHERE id=?",
        (now, eval_id),
    )
    conn.commit()


def score_domaine(row, domaine):
    """Somme des scores pour un domaine (lettre A/B/C/D)."""
    cols = DOMAINES[domaine.upper()][1]
    return sum(row[c] or 0 for c in cols)


def score_total(row):
    return sum(row[c] or 0 for c in SCORE_COLS)
