#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import db
from gui.main_window import MainWindow

if __name__ == "__main__":
    conn = db.init_db()
    app = MainWindow(conn)
    app.mainloop()
    conn.close()
