#!/usr/bin/env python3
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
