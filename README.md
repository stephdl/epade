# ÉPADE — Application de cotation psychogériatrique

Application desktop pour gérer les cotations **ÉPADE** (Échelle d'évaluation des Personnes
Âgées — Symptômes et Syndromes DÉconcertants / PGI-DSS).

Remplace un fichier Excel fragile par une base de données locale. Chaque évaluation est
verrouillée définitivement après validation — l'historique est immuable.

---

## Prérequis

| Composant | Version minimale | Notes |
|---|---|---|
| Python | 3.10+ | Inclus sur la plupart des distributions Linux (3.9 en fin de vie oct. 2025) |
| tkinter | — | Parfois absent, voir ci-dessous |
| fpdf2 | 2.7+ | Export PDF |
| tkcalendar | 1.6+ | Sélecteurs de date |
| Liberation Sans | — | Polices pour l'export PDF |

---

## Installation sur Windows

### 1. Télécharger l'exécutable

Rendez-vous sur la page [Releases](https://github.com/stephdl/epade/releases) et téléchargez
le fichier `EPADE.exe` de la dernière version stable.

### 2. Organiser le dossier

Créez un dossier dédié (par exemple `C:\EPADE\`) et placez-y `EPADE.exe` :

```
C:\EPADE\
└── EPADE.exe
```

La base de données `data\epade.db` sera créée automatiquement dans ce même dossier
au premier lancement.

### 3. Lancer l'application

Double-cliquez sur `EPADE.exe`. Si Windows affiche un avertissement SmartScreen
("application non reconnue"), cliquez sur **Informations complémentaires** puis
**Exécuter quand même**.

### 4. Créer un raccourci bureau (optionnel)

Clic droit sur `EPADE.exe` → **Envoyer vers** → **Bureau (créer un raccourci)**.

> **Aucune installation de Python n'est requise** — tout est embarqué dans l'exe (Python 3.14).
> **Windows 10 ou 11 requis** — Windows 7 et 8 ne sont plus supportés.

---

## Installation sur Linux — Binaire autonome (recommandée)

Rendez-vous sur la page [Releases](https://github.com/stephdl/epade/releases) et téléchargez
l'archive `EPADE-linux-x86_64.tar.gz` de la dernière version.

```bash
# Extraire l'archive à l'emplacement définitif (local ou dossier réseau partagé)
tar -xzf EPADE-linux-x86_64.tar.gz

# Installer l'icône et le lanceur (une seule fois par poste)
cd EPADE-linux/
bash install.sh

# Lancer l'application
./EPADE
```

L'archive contient :

| Fichier | Rôle |
|---|---|
| `EPADE` | Binaire autonome |
| `epade.png` | Icône de l'application |
| `install.sh` | Installe l'icône et le lanceur (à lancer une fois par poste) |
| `LISEZMOI.txt` | Instructions détaillées |

`install.sh` installe l'icône dans `~/.local/share/icons/` et crée un lanceur dans
`~/.local/share/applications/` — il ne déplace pas le binaire.
Il peut être relancé sans danger si le dossier a été déplacé.

La base de données `data/epade.db` est créée automatiquement à côté du binaire.

> **Aucune installation de Python n'est requise** — tout est embarqué dans le binaire.
> Compatible avec Ubuntu 22.04+, Rocky/AlmaLinux 9+, Debian 12+, Fedora 37+ et toute distribution Linux récente.

---

## Installation sur Linux — Depuis les sources (Fedora / RHEL / CentOS)

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

## Installation sur Linux — Depuis les sources (Ubuntu / Debian / Linux Mint)

```bash
# Dépendances système
sudo apt install python3-tk fonts-liberation -y

# Dépendances Python
pip3 install --user fpdf2 tkcalendar

# Raccourci bureau
bash install.sh
```

---

## Installation sur macOS

> **Note importante** : je suis un gros barbu linuxien et je n'ai pas de Mac pour tester
> tout ça — ces instructions sont théoriques. Si vous testez et que ça fonctionne (ou pas),
> ouvrez une [issue](https://github.com/stephdl/epade/issues) pour me le faire savoir.
> Et si vous voulez contribuer à l'achat d'un Mac pour les tests... je suis ouvert aux
> donations. (je rigole. A moitié.)

### 1. Installer Python

Télécharger Python 3.10+ depuis [python.org](https://www.python.org/downloads/macos/) —
la version officielle inclut tkinter. Éviter la version Homebrew qui peut ne pas l'inclure.

### 2. Installer les dépendances Python

```bash
pip3 install fpdf2 tkcalendar
```

### 3. Lancer l'application

```bash
cd epade/
python3 main.py
```

### Notes spécifiques macOS

- La base de données est créée dans `epade/data/epade.db` — à côté du code
- Si une fenêtre de sécurité s'affiche ("développeur non identifié"), aller dans
  **Réglages Système → Confidentialité et sécurité** et autoriser l'application
- L'export PDF devrait fonctionner — les polices sont embarquées dans `assets/fonts/`
- Le rendu tkinter peut différer légèrement de Linux/Windows (c'est cosmétique)

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
4. **Remplir la cotation** — saisir soignant, période, les 16 scores (A1–D4) et les notes.
   Chaque score affiche le critère officiel ÉPADE dans le menu déroulant
   (`0 — (absent) Regard normal et mimique normale`, etc.)
5. **Supprimer un brouillon** — bouton `Supprimer brouillon` dans la liste des évaluations
   (uniquement pour les évaluations non encore verrouillées)
6. **Historique** — sélectionner un patient puis clic `Historique` : tableau de toutes les
   évaluations finalisées + graphique d'évolution du score total
7. **Valider** — `Valider et verrouiller` : date/heure inscrite automatiquement, fiche en lecture seule
8. **Exporter en PDF** — sélectionner une évaluation verrouillée, clic `Exporter PDF`
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

## Mise à jour de l'application

### Windows (exe)

La base de données **n'est pas incluse dans le `.exe`** — elle réside dans le dossier `data\` à côté de l'exécutable :

```
Dossier d'installation\
├── EPADE.exe          ← seul ce fichier est remplacé lors d'une mise à jour
└── data\
    └── epade.db       ← conservé intact entre les versions
```

**Procédure :**

1. **Sauvegarder** la base via le bouton `Sauvegarder la base` (par précaution)
2. Télécharger le nouveau `EPADE.exe` depuis la page [Releases](https://github.com/stephdl/epade/releases)
3. Remplacer l'ancien `EPADE.exe` par le nouveau — ne pas toucher au dossier `data\`
4. Lancer le nouveau `EPADE.exe` — la base est automatiquement migrée si nécessaire

> La migration de schéma est automatique : si une nouvelle version ajoute des champs,
> ils sont créés à l'ouverture sans perte de données.

### Linux — Binaire autonome

```
~/EPADE-linux/
├── EPADE        ← seul ce fichier est remplacé lors d'une mise à jour
├── epade.png
├── install.sh
└── data/
    └── epade.db ← conservé intact entre les versions
```

**Procédure :**

1. **Sauvegarder** la base via le bouton `Sauvegarder la base` (par précaution)
2. Télécharger la nouvelle archive `EPADE-linux-x86_64.tar.gz` depuis la page [Releases](https://github.com/stephdl/epade/releases)
3. Extraire et remplacer uniquement le fichier `EPADE` — ne pas toucher au dossier `data/`
4. Lancer le nouveau binaire — la base est automatiquement migrée si nécessaire
5. Relancer `bash install.sh` si vous souhaitez mettre à jour le lanceur

> La migration de schéma est automatique : si une nouvelle version ajoute des champs,
> ils sont créés à l'ouverture sans perte de données.

### Linux — Depuis les sources

```bash
cd epade/
git pull
python3 main.py
```

La base `data/epade.db` n'est pas versionnée — elle est préservée par le `.gitignore`.

---

## Structure des fichiers

```
epade/
├── main.py          # Point d'entrée
├── db.py            # Base SQLite (schéma + toutes les fonctions + CRITERES)
├── gui/
│   ├── main_window.py      # Fenêtre principale
│   ├── patient_form.py     # Formulaire patient (création / édition)
│   ├── cotation_form.py    # Formulaire de cotation
│   ├── historique_dialog.py # Historique patient (tableau + graphique)
│   ├── datepicker.py       # Sélecteur de date avec calendrier popup
│   └── export_dialog.py    # Choix du type d'export PDF
├── export/
│   └── pdf.py       # Génération PDF (fpdf2)
├── tests/           # 54 tests pytest (base en mémoire)
├── data/
│   └── epade.db     # Base SQLite (créée au premier lancement)
├── utils.py         # Utilitaires partagés (open_url — liens cliquables Linux)
├── backup.py        # Sauvegarde automatique (cron / Planificateur Windows)
├── backup.bat       # Wrapper Windows pour le Planificateur de tâches
├── install.sh       # Raccourci Linux depuis les sources
├── install-bin.sh   # Icône + lanceur pour le binaire (embarqué dans le tar.gz)
├── LISEZMOI.txt     # Instructions utilisateur (embarqué dans le tar.gz)
└── requirements.txt
```

---

## Usage multi-postes (dossier partagé)

La base de données peut résider sur un dossier réseau partagé (SMB/Windows) pour
permettre à plusieurs soignants de travailler simultanément.

- Chaque soignant crée **sa propre évaluation** (`+ Nouvelle évaluation`) : les lignes
  sont indépendantes, personne n'écrase le travail d'un autre.
- La base est configurée en mode **WAL** (Write-Ahead Logging) : les lectures ne
  bloquent pas les écritures et vice-versa, ce qui améliore la fiabilité en accès concurrent.
- Limitations : SQLite reste un moteur fichier — pour un usage intensif (>10 postes
  simultanés) ou sur un réseau instable, envisager une migration vers PostgreSQL/web.

> **Conseil** : désigner un poste référent pour les sauvegardes régulières via
> `Sauvegarder la base`.

---

## Sauvegarde des données

La base de données est un fichier unique : `data/epade.db`

**Depuis l'interface** (ponctuel) : boutons `Sauvegarder la base` et `Restaurer la base`
en haut à droite de la fenêtre principale.

---

## Sauvegarde automatique (script)

Le script `backup.py` copie la base avec un horodatage et supprime les plus anciennes
copies au-delà du nombre souhaité. Il ne nécessite aucune dépendance Python externe.

### Lancement manuel

```bash
# Destination locale (défaut : ./sauvegardes/)
python backup.py

# Destination personnalisée + rotation sur 31 jours
python backup.py --dest /mnt/nas/epade/sauvegardes --keep 31

# Chemin réseau Windows
python backup.py --dest "\\serveur\partage\epade\sauvegardes" --keep 31
```

### Linux — cron (toutes les nuits à 02h00)

```bash
crontab -e
```

Ajouter la ligne :

```
0 2 * * * /usr/bin/python3 /chemin/vers/epade/backup.py --dest /chemin/vers/epade/sauvegardes --keep 31 >> /var/log/epade_backup.log 2>&1
```

Pour une destination réseau NAS :

```
0 2 * * * /usr/bin/python3 /chemin/vers/epade/backup.py --dest /mnt/nas/epade/sauvegardes --keep 31 >> /var/log/epade_backup.log 2>&1
```

### Windows — Planificateur de tâches

Le fichier `backup.bat` est prêt à l'emploi. Ouvrir le fichier pour ajuster
`--dest` si besoin (réseau ou lettre de lecteur).

**Configuration du Planificateur :**

1. Ouvrir **Planificateur de tâches** (menu Démarrer → rechercher "planificateur")
2. **Créer une tâche de base**
3. Déclencheur : **Tous les jours** à **02:00**
4. Action : **Démarrer un programme** → pointer sur `backup.bat`
5. Cocher **Exécuter même si l'utilisateur n'est pas connecté**
6. Les logs s'accumulent dans `sauvegardes\backup.log`

Pour une destination réseau (dossier partagé) : modifier `backup.bat` :

```bat
python "%~dp0backup.py" --dest "\\serveur\partage\epade\sauvegardes" --keep 31 >> ...
```

> **Règle des 3-2-1** : idéalement 3 copies, sur 2 supports différents, dont 1 hors site
> (NAS réseau, cloud). Le script gère la rotation locale ; pour une copie distante,
> combiner avec rclone (OneDrive, Nextcloud…) ou Robocopy vers un partage réseau.

---

## Lancer les tests

```bash
pytest tests/
```

Les tests utilisent une base SQLite en mémoire — aucun fichier n'est créé ou modifié.

68 tests couvrent : CRUD patients/évaluations, règles de validation, génération PDF,
configuration, intégrité des critères ÉPADE et labels des combobox.

---

## Dépannage

### Windows

**L'exe ne démarre pas / fenêtre noire qui disparaît**
→ Lancer depuis un terminal (`cmd.exe`) pour voir le message d'erreur :
```
cd C:\EPADE
EPADE.exe
```

**Avertissement SmartScreen au premier lancement**
→ Cliquer sur **Informations complémentaires** puis **Exécuter quand même** — l'exe n'est pas signé.

**L'export PDF ne s'ouvre pas automatiquement**
→ Ouvrir le fichier manuellement depuis l'explorateur Windows — le PDF est bien créé à l'emplacement choisi.

### Linux

**`ModuleNotFoundError: No module named 'tkinter'`**
→ Installer `python3-tkinter` (dnf) ou `python3-tk` (apt), voir étape 2.

**L'export PDF affiche des carrés à la place des caractères accentués**
→ Les polices Liberation Sans sont manquantes, voir étape 3.

**`_tkinter.TclError: grab failed: window not viewable`**
→ Message d'avertissement non bloquant lié à l'affichage — l'application continue normalement.

---

## Références

Ce logiciel est une implémentation informatique de l'échelle **ÉPADE** (Échelle d'évaluation
des Personnes Âgées — Symptômes et Syndromes DÉconcertants / PGI-DSS).

**Auteurs de l'échelle :** Monfort JC, Lezy AM, Papin A, Tezenas S

Site officiel : [www.psychoge.fr](https://www.psychoge.fr)

---

## Licence

Ce logiciel est distribué sous licence **GNU General Public License v3.0**.
Voir le fichier [LICENSE](LICENSE) ou <https://www.gnu.org/licenses/gpl-3.0.html>.

Copyright (C) 2026  Stephane de Labrusse <stephdl@de-labrusse.fr>

