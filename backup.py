#!/usr/bin/env python3
"""
Sauvegarde automatique de la base EPADE.

Usage :
  python backup.py
  python backup.py --dest /chemin/vers/dossier --keep 31
  python backup.py --dest \\\\serveur\\partage\\epade --keep 31  (Windows réseau)

Arguments :
  --dest  Dossier de destination (local ou réseau). Défaut : ./sauvegardes/
  --keep  Nombre de sauvegardes à conserver. Défaut : 31 (1 mois à 1/jour)

Conçu pour être appelé par cron (Linux) ou le Planificateur de tâches (Windows).
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Résolution du chemin de base — identique à db.py, supporte PyInstaller
if getattr(sys, "frozen", False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).parent

DB_PATH = _BASE / "data" / "epade.db"


def backup(dest: Path, keep: int) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Démarrage sauvegarde EPADE", flush=True)

    if not DB_PATH.exists():
        print(f"[ERREUR] Base introuvable : {DB_PATH}", flush=True)
        sys.exit(1)

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"[ERREUR] Impossible de créer {dest} : {e}", flush=True)
        sys.exit(1)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = dest / f"epade_{stamp}.db"
    shutil.copy2(DB_PATH, dst)
    size_kb = dst.stat().st_size // 1024
    print(f"[OK] {dst}  ({size_kb} Ko)", flush=True)

    # Rotation : ne conserver que les N plus récentes
    copies = sorted(dest.glob("epade_*.db"), reverse=True)
    for old in copies[keep:]:
        old.unlink()
        print(f"[ROT] supprimé {old.name}", flush=True)

    print(f"[INFO] {min(len(copies), keep)}/{keep} sauvegardes conservées", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Sauvegarde automatique de la base EPADE avec rotation."
    )
    ap.add_argument(
        "--dest",
        default=str(_BASE / "sauvegardes"),
        help="Dossier de destination (local ou chemin réseau). Défaut : ./sauvegardes/",
    )
    ap.add_argument(
        "--keep",
        type=int,
        default=31,
        help="Nombre de sauvegardes à conserver. Défaut : 31",
    )
    args = ap.parse_args()
    backup(Path(args.dest), args.keep)
