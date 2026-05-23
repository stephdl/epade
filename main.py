#!/usr/bin/env python3
# EPADE - Application de cotation psychogeriatrique
# Copyright (C) 2026  Stephane de Labrusse <stephdl@de-labrusse.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import db
import config
from version import __version__
from gui.main_window import MainWindow

if __name__ == "__main__":
    conn = db.init_db()
    cfg = config.load()
    app = MainWindow(conn, scaling=cfg.get("scaling", 1.0), version=__version__)
    app.mainloop()
    conn.close()
