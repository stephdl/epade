# ÉPADE — Application de cotation psychogériatrique

## Objectif

Application desktop (tkinter + SQLite) pour gérer les cotations ÉPADE (Échelle d'évaluation
des Personnes Âgées — Symptômes et Syndromes DÉconcertants / PGI-DSS). Remplace un fichier
Excel fragile. Chaque évaluation est verrouillée définitivement après validation, l'historique
est immuable.

## Lancer l'application

```bash
python main.py
```

## Lancer les tests

```bash
pytest tests/
```

## Installer (double-clic Linux)

```bash
bash install.sh
```

## Dépendances

```bash
pip install fpdf2 tkcalendar pytest
```

---

## Architecture

```
epade/
├── main.py                  # point d'entrée : crée la fenêtre tkinter et ouvre la DB
├── db.py                    # toute la logique SQLite (schéma + CRUD)
├── gui/
│   ├── main_window.py       # fenêtre principale : liste patients + liste évaluations
│   ├── patient_form.py      # dialog création/édition patient (dual-mode)
│   ├── cotation_form.py     # formulaire de cotation (saisie ou lecture seule)
│   ├── datepicker.py        # LargeDateEntry : champ date + popup calendrier visible
│   └── export_dialog.py     # choix du type d'export PDF
├── export/
│   └── pdf.py               # 3 types d'export PDF (fiche complète, résumé, historique)
├── tests/
│   ├── test_db.py           # tests CRUD SQLite (base en mémoire)
│   ├── test_validation.py   # tests des règles de validation métier
│   └── test_pdf.py          # tests de génération PDF
├── data/
│   └── epade.db             # base SQLite créée automatiquement au premier lancement
├── EPADE.desktop            # raccourci Linux
├── README.md                # guide d'installation
└── install.sh               # installe dépendances + raccourci
```

---

## Schéma SQLite (db.py)

### Table `patients`

| Colonne | Type | Remarque |
|---|---|---|
| id | INTEGER PK | auto |
| nom | TEXT NOT NULL | |
| prenom | TEXT NOT NULL | |
| date_naissance | TEXT | format JJ/MM/AAAA |
| telephone | TEXT | optionnel |
| adresse | TEXT | optionnel |
| contact_famille_nom | TEXT | optionnel |
| contact_famille_tel | TEXT | optionnel |
| contact_famille_lien | TEXT | optionnel (ex. "Fille") |
| medecin_referent | TEXT | optionnel |
| service_chambre | TEXT | optionnel (ex. "Gériatrie / ch. 12") |
| numero_dossier | TEXT | optionnel |
| date_admission | TEXT | optionnel |
| archive | INTEGER | 0=actif, 1=archivé (masqué de la liste) |
| created_at | TEXT | datetime auto |

### Table `evaluations`

| Colonne | Type | Remarque |
|---|---|---|
| id | INTEGER PK | auto |
| patient_id | INTEGER | FK → patients.id |
| soignant | TEXT NOT NULL | obligatoire |
| periode_du | TEXT NOT NULL | date début YYYY-MM-DD |
| periode_au | TEXT NOT NULL | date fin YYYY-MM-DD |
| duree | TEXT | optionnel |
| date_cotation | TEXT | NULL → rempli automatiquement à la validation |
| a1…d4 | INTEGER | 16 scores, NULL = non renseigné |
| note_a1…note_d4 | TEXT | 16 notes libres soignant |
| cause_a…cause_d | TEXT | réflexion cause par domaine |
| attitude_a…attitude_d | TEXT | attitude appropriée par domaine |
| finalisee | INTEGER | 0=brouillon, 1=verrouillée |

Migration automatique : `init_db()` ajoute les colonnes manquantes sur une base existante
via `ALTER TABLE ADD COLUMN` — pas besoin de recréer la base.

---

## Fonctions publiques db.py

### Patients
| Fonction | Description |
|---|---|
| `creer_patient(conn, nom, prenom, ddn, **extra)` | Crée un patient avec les champs optionnels |
| `get_patient(conn, patient_id)` | Récupère un patient par id |
| `modifier_patient(conn, patient_id, **champs)` | Met à jour les champs d'un patient |
| `rechercher_patients(conn, query, inclure_archives=False)` | Recherche par nom/prénom, exclut les archivés par défaut |
| `archiver_patient(conn, patient_id)` | Masque le patient (archive=1), conserve les évaluations |
| `restaurer_patient(conn, patient_id)` | Réactive un patient archivé |
| `supprimer_patient(conn, patient_id)` | Supprime définitivement patient + toutes ses évaluations |

### Évaluations
| Fonction | Description |
|---|---|
| `creer_evaluation(conn, patient_id)` | Crée un brouillon vide |
| `get_evaluation(conn, eval_id)` | Récupère une évaluation |
| `get_evaluations_patient(conn, patient_id)` | Liste toutes les évaluations d'un patient |
| `mettre_a_jour_evaluation(conn, eval_id, **champs)` | Met à jour un brouillon (lève ValueError si finalisée) |
| `valider_champs_requis(conn, eval_id)` | Retourne la liste des champs manquants (vide = OK) |
| `finaliser_evaluation(conn, eval_id)` | Verrouille l'évaluation (lève ValueError si champs manquants) |
| `score_domaine(row, domaine)` | Somme des scores pour A/B/C/D |
| `score_total(row)` | Score total sur 64 |

---

## Règles métier critiques

### Validation (cotation_form.py → db.finaliser_evaluation)

La validation est **refusée** si l'un de ces champs est absent :
- `soignant` (non vide)
- `periode_du` et `periode_au` (non nulles)
- Les 16 scores `a1` à `d4` (non NULL)

En cas d'échec : un dialog liste **exactement** les champs manquants.

### Contraintes sur les dates de période

Contrôlées dans `cotation_form.py` via `LargeDateEntry` :
- `periode_du` et `periode_au` ≤ date du jour (pas de date future)
- `periode_au` ≥ `periode_du`
- Le calendrier popup bloque les dates futures via `maxdate=date.today()`

### Verrouillage

Quand `finalisee=1` :
- `date_cotation` est inscrite automatiquement (datetime locale)
- Plus aucun `UPDATE` ne doit toucher cette ligne (db.py vérifie `finalisee=0` avant tout UPDATE)
- Le formulaire passe en mode `state=disabled` complet

### Sauvegarde automatique (brouillon)

Chaque modification d'un champ dans `cotation_form.py` déclenche immédiatement un
`UPDATE evaluations SET … WHERE id=? AND finalisee=0`. La saisie est donc persistée
en continu — pas de bouton "Sauvegarder".

### Archivage vs suppression

- **Archiver** : `archive=1`, patient masqué de la liste principale, évaluations conservées. Réversible.
- **Supprimer** : cascade DELETE sur evaluations puis patients. Irréversible. Double confirmation requise.

---

## Interface (gui/)

### main_window.py — Fenêtre principale

- Colonne gauche : liste patients avec recherche temps réel, case "Archivés" pour afficher les archivés (en gris, préfixe ✕)
- Boutons patient : `+ Nouveau` | `Modifier` | `Archiver` (devient `Restaurer` si patient archivé)
- Colonne droite : évaluations du patient sélectionné (3 lignes par éval : statut/date/soignant, scores, ligne vide)
- `exportselection=False` sur les deux Listbox — indispensable pour ne pas perdre la sélection au clic sur les boutons

### patient_form.py — Formulaire patient

Dual-mode : `PatientForm(parent, conn)` → création, `PatientForm(parent, conn, patient_id=X)` → édition.
En mode édition, bouton "Supprimer définitivement" (double confirmation).
`result` vaut le patient_id, ou `"deleted"` après suppression.

### cotation_form.py — Formulaire de cotation

- Scrollable via Canvas + ttk.Scrollbar
- En-tête : soignant, période (LargeDateEntry), durée, date cotation (auto)
- 4 sections A/B/C/D avec items, scores (Combobox), notes soignant (Combobox + champ libre)
- Réflexion-cause et attitude appropriée par domaine (Combobox + champ libre)
- Score domaine et total mis à jour en temps réel
- Mode lecture seule (finalisée) : tous les widgets `state=disabled`

### datepicker.py — LargeDateEntry

Remplace tkcalendar.DateEntry dont les flèches de navigation sont trop petites/invisibles.
- Champ Entry (YYYY-MM-DD) + bouton icône calendrier dessinée en `tk.PhotoImage` (pas d'emoji)
- Popup Toplevel avec `tkcalendar.Calendar` en police 13, `maxdate=today`
- Boutons nav agrandis via `ttk.Style` sur `cal._style_pfx + ".TButton"`
- API : `get_date()` → `datetime.date|None`, `set_date(str|date)`, `get()` → `str`

### export_dialog.py — Choix export PDF

Noms de fichiers pré-remplis : `EPADE_{NOM}_{Prenom}_{date}_fiche.pdf` (accents translitérés).

---

## Export PDF (export/pdf.py)

Polices : LiberationSans TTF (`/usr/share/fonts/liberation-sans-fonts/`) — nécessaires pour l'UTF-8.

| Fonction | Contenu |
|---|---|
| `export_fiche_complete(conn, eval_id, path)` | Fiche ÉPADE : identification patient complète, tableau items (score + note), cause et attitude par domaine, total, légende |
| `export_resume(conn, eval_id, path)` | Résumé : patient, soignant, période, barres de score A/B/C/D, total |
| `export_historique(conn, patient_id, path)` | Tableau de toutes les évaluations finalisées du patient |

---

## Tests (pytest — 27 tests, base :memory:)

### test_db.py (16 tests)
| Test | Ce qui est vérifié |
|---|---|
| `test_creer_et_recuperer_patient` | Création et lecture patient de base |
| `test_recherche_patient_insensible_casse` | Recherche "dup" trouve "Dupont" |
| `test_recherche_patient_vide_retourne_tous` | Query vide = tous les patients |
| `test_recherche_par_prenom` | Recherche sur le prénom |
| `test_creer_patient_avec_champs_etendus` | telephone, medecin, service, contact famille |
| `test_modifier_patient` | modifier_patient met à jour sans toucher les autres champs |
| `test_archiver_et_restaurer_patient` | archive masque, restaure réactive |
| `test_supprimer_patient_supprime_evaluations` | cascade DELETE evaluations |
| `test_recherche_exclut_archives_par_defaut` | patients archivés invisibles par défaut |
| `test_creer_evaluation_brouillon` | finalisee=0, date_cotation=NULL |
| `test_mettre_a_jour_evaluation` | UPDATE soignant et score |
| `test_finaliser_evaluation` | finalisee=1, date_cotation remplie |
| `test_impossible_modifier_evaluation_finalisee` | ValueError si finalisee=1 |
| `test_get_evaluations_patient` | liste les évaluations d'un patient |
| `test_score_domaine_et_total` | calculs A=10, B=0, C=4, D=8, total=22 |

### test_validation.py (8 tests)
| Test | Ce qui est vérifié |
|---|---|
| `test_validation_refusee_soignant_vide` | soignant vide bloque la validation |
| `test_validation_refusee_periode_du_manquante` | periode_du vide bloque |
| `test_validation_refusee_periode_au_manquante` | periode_au vide bloque |
| `test_validation_refusee_score_manquant` | un score NULL bloque |
| `test_validation_acceptee_si_tout_rempli` | liste vide = OK |
| `test_liste_exacte_des_champs_manquants` | 3 + 14 champs = 17 manquants précis |
| `test_finaliser_verrouille_definitivement` | ValueError après finalisation |
| `test_finaliser_leve_erreur_si_incomplet` | ValueError si champs manquants |

### test_pdf.py (4 tests)
| Test | Ce qui est vérifié |
|---|---|
| `test_export_fiche_complete` | PDF créé, taille > 1 000 octets |
| `test_export_resume` | PDF créé, taille > 500 octets |
| `test_export_historique` | PDF créé avec évaluations |
| `test_export_historique_sans_evaluations` | PDF créé même sans éval finalisée |

---

## Données de référence ÉPADE

### Items et leurs domaines

| Item | Libellé | Domaine |
|---|---|---|
| A1 | Regard / Mimique | VIOLENCES déconcertantes |
| A2 | Voix | VIOLENCES déconcertantes |
| A3 | Paroles (menaces, insultes…) | VIOLENCES déconcertantes |
| A4 | Gestes (frappes, crachats…) | VIOLENCES déconcertantes |
| B1 | Communication / Regard | REFUS déconcertants |
| B2 | Mobilisation (lit, fauteuil…) | REFUS déconcertants |
| B3 | Alimentation / Boisson | REFUS déconcertants |
| B4 | Soins (toilette, médicaments…) | REFUS déconcertants |
| C1 | Ordres / Demandes / Écholalie répétés | PAROLES déconcertantes |
| C2 | Paroles anxieuses / Appels à l'aide | PAROLES déconcertantes |
| C3 | Paroles dépressives (vie/mort) | PAROLES déconcertantes |
| C4 | Paroles à côté de la réalité / Délire | PAROLES déconcertantes |
| D1 | Sphère locomotrice (fugues, automutilations…) | ACTES déconcertants |
| D2 | Sphère alimentaire / Orale | ACTES déconcertants |
| D3 | Sphères urinaire et anale | ACTES déconcertants |
| D4 | Sphère sexuelle / Génitale | ACTES déconcertants |

### Score

- 0 = Absent, 1 = Léger, 2 = Moyen, 3 = Fort, 4 = Très fort
- Max par domaine : 16 pts — Max total : 64 pts
- **Seuil critique : score > 17** → rechercher cause réversible
- Règle de la marée haute : on retient le score le PLUS ÉLEVÉ observé sur la période

### Copyright

© Monfort JC, Lezy AM, Papin A, Tezenas S · www.psychoge.fr
