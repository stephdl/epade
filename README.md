# ÉPADE — Application de cotation psychogériatrique

Application desktop pour gérer les cotations **ÉPADE** (Échelle d'évaluation des Personnes
Âgées — Symptômes et Syndromes DÉconcertants / PGI-DSS).

Remplace un fichier Excel fragile par une base de données locale. Chaque évaluation est
verrouillée définitivement après validation — l'historique est immuable.

---

## Prérequis

| Composant | Version minimale | Notes |
|---|---|---|
| Python | 3.9+ | Inclus sur la plupart des distributions Linux |
| tkinter | — | Parfois absent, voir ci-dessous |
| fpdf2 | 2.7+ | Export PDF |
| tkcalendar | 1.6+ | Sélecteurs de date |
| Liberation Sans | — | Polices pour l'export PDF |

---

## Installation sur Linux (Fedora / RHEL / CentOS)

### 1. Cloner ou copier le dossier

```bash
git clone <url-du-dépôt> epade
cd epade
```

### 2. Installer tkinter (si absent)

```bash
# Fedora / RHEL 9+ / CentOS Stream
sudo dnf install python3-tkinter -y

# Ubuntu / Debian / Linux Mint
sudo apt install python3-tk -y
```

> **Vérification** : `python3 -c "import tkinter; print('OK')"` doit afficher `OK`.

### 3. Installer les polices Liberation Sans (pour l'export PDF)

```bash
# Fedora / RHEL
sudo dnf install liberation-sans-fonts -y

# Ubuntu / Debian
sudo apt install fonts-liberation -y
```

### 4. Installer les dépendances Python

```bash
pip3 install --user fpdf2 tkcalendar
```

Ou avec le fichier requirements :

```bash
pip3 install --user -r requirements.txt
```

### 5. Installer le raccourci bureau (optionnel)

```bash
bash install.sh
```

Ce script rend `main.py` exécutable et crée une entrée dans vos applications
(`~/.local/share/applications/epade.desktop`) pour un lancement par double-clic.

---

## Installation sur Ubuntu / Debian / Linux Mint

```bash
# Dépendances système
sudo apt install python3-tk fonts-liberation -y

# Dépendances Python
pip3 install --user fpdf2 tkcalendar

# Raccourci bureau
bash install.sh
```

---

## Lancement

```bash
# Depuis le dossier epade/
python3 main.py
```

Ou double-clic sur l'icône si `install.sh` a été exécuté.

La base de données est créée automatiquement à la première ouverture dans `data/epade.db`.

---

## Utilisation rapide

1. **Créer un patient** — bouton `+ Nouveau` dans la colonne gauche
2. **Modifier la fiche** — sélectionner le patient puis `Modifier` (téléphone, médecin, contact famille…)
3. **Nouvelle évaluation** — sélectionner le patient puis `+ Nouvelle évaluation`
4. **Remplir la cotation** — saisir soignant, période, les 16 scores (A1–D4) et les notes
5. **Valider** — `Valider et verrouiller` : date/heure inscrite automatiquement, fiche en lecture seule
6. **Exporter en PDF** — sélectionner une évaluation verrouillée, clic `Exporter PDF`
   - *Fiche complète* — tous les items, scores, notes, causes, attitudes
   - *Résumé des scores* — vue synthétique avec barres de progression
   - *Historique patient* — tableau de toutes les évaluations

### Archivage / suppression d'un patient

| Action | Où | Effet |
|---|---|---|
| **Archiver** | Bouton `Archiver` (fenêtre principale) | Patient masqué de la liste, évaluations conservées |
| **Afficher les archivés** | Case `Archivés` près de la recherche | Patients archivés visibles en gris |
| **Restaurer** | Bouton `Restaurer` (patient archivé sélectionné) | Patient de nouveau actif |
| **Supprimer définitivement** | Bouton dans `Modifier` | Double confirmation — irréversible |

### Sauvegarde et restauration de la base

Deux boutons sont disponibles en haut à droite de la fenêtre principale :

| Bouton | Action |
|---|---|
| **Sauvegarder la base** | Copie `epade.db` vers l'emplacement de votre choix (clé USB, réseau, cloud…). Le nom proposé par défaut inclut la date : `epade_sauvegarde_2026-05-23.db` |
| **Restaurer la base** | Remplace la base active par une sauvegarde choisie. Une confirmation est demandée avant l'opération. La liste des patients est rechargée immédiatement — pas besoin de relancer l'application |

> **Conseil** : sauvegardez régulièrement, surtout avant une mise à jour de l'application.

---

## Structure des fichiers

```
epade/
├── main.py          # Point d'entrée
├── db.py            # Base SQLite (schéma + toutes les fonctions)
├── gui/
│   ├── main_window.py    # Fenêtre principale
│   ├── patient_form.py   # Formulaire patient (création / édition)
│   ├── cotation_form.py  # Formulaire de cotation
│   └── export_dialog.py  # Choix du type d'export PDF
├── export/
│   └── pdf.py       # Génération PDF (fpdf2)
├── tests/           # Tests pytest (base en mémoire)
├── data/
│   └── epade.db     # Base SQLite (créée au premier lancement)
├── install.sh       # Installe le raccourci Linux
└── requirements.txt
```

---

## Sauvegarde des données

La base de données est un fichier unique : `data/epade.db`

**Depuis l'interface** (recommandé) : boutons `Sauvegarder la base` et `Restaurer la base`
en haut à droite de la fenêtre principale.

**Manuellement** (Linux) :
```bash
# Sauvegarde
cp data/epade.db ~/Sauvegardes/epade_$(date +%Y%m%d).db

# Restauration (application fermée)
cp ~/Sauvegardes/epade_20260523.db data/epade.db
```

---

## Lancer les tests

```bash
pytest tests/
```

Les tests utilisent une base SQLite en mémoire — aucun fichier n'est créé ou modifié.

---

## Dépannage

**`ModuleNotFoundError: No module named 'tkinter'`**
→ Installer `python3-tkinter` (dnf) ou `python3-tk` (apt), voir étape 2.

**L'export PDF affiche des carrés à la place des caractères accentués**
→ Les polices Liberation Sans sont manquantes, voir étape 3.

**`_tkinter.TclError: grab failed: window not viewable`**
→ Message d'avertissement non bloquant lié à l'affichage — l'application continue normalement.

---

## Copyright de l'échelle ÉPADE

© Monfort JC, Lezy AM, Papin A, Tezenas S · [www.psychoge.fr](http://www.psychoge.fr)
