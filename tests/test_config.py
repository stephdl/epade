import pytest
import config


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    """Redirige CONFIG_PATH vers un fichier temporaire pour chaque test."""
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")


def test_load_defaults_sans_fichier():
    cfg = config.load()
    assert cfg["scaling"] == 1.0
    assert cfg["filedialog_fontsize"] == 11


def test_save_et_reload():
    config.save({"scaling": 1.5})
    cfg = config.load()
    assert cfg["scaling"] == 1.5


def test_save_merge_avec_existant():
    config.save({"scaling": 1.25})
    config.save({"autre_cle": "valeur"})
    cfg = config.load()
    assert cfg["scaling"] == 1.25
    assert cfg["autre_cle"] == "valeur"


def test_save_ecrase_valeur_existante():
    config.save({"scaling": 1.75})
    config.save({"scaling": 1.0})
    assert config.load()["scaling"] == 1.0


def test_load_fichier_corrompu_retourne_defaults(tmp_path, monkeypatch):
    p = tmp_path / "config_bad.json"
    p.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", p)
    cfg = config.load()
    assert cfg["scaling"] == 1.0
