@echo off
REM Sauvegarde automatique EPADE
REM Modifie --dest et --keep selon tes besoins.
REM
REM Exemples de destinations :
REM   Local            : --dest "%~dp0sauvegardes"
REM   Dossier réseau   : --dest "\\serveur\partage\epade\sauvegardes"
REM   Lettre de lecteur: --dest "Z:\Sauvegardes\EPADE"

python "%~dp0backup.py" --dest "%~dp0sauvegardes" --keep 31 >> "%~dp0sauvegardes\backup.log" 2>&1
