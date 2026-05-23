import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).parent

CONFIG_PATH = _BASE / "config.json"

_DEFAULTS = {
    "scaling": 1.0,
    "etablissement_nom": "",
    "etablissement_adresse": "",
    "etablissement_telephone": "",
    "filedialog_fontsize": 11,
}


def load():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {**_DEFAULTS, **data}
    except Exception:
        return dict(_DEFAULTS)


def save(data: dict):
    cfg = load()
    cfg.update(data)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
