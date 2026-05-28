import updater


def test_parse_version_avec_prefixe_v():
    assert updater._parse_version("v1.0.9") == (1, 0, 9)


def test_parse_version_sans_prefixe():
    assert updater._parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_invalide_retourne_zero():
    assert updater._parse_version("dev") == (0,)


def test_nouvelle_version_detectee():
    assert updater._parse_version("v1.0.9") > updater._parse_version("v1.0.8")


def test_meme_version_non_detectee():
    assert not (updater._parse_version("v1.0.8") > updater._parse_version("v1.0.8"))


def test_version_majeure_detectee():
    assert updater._parse_version("v2.0.0") > updater._parse_version("v1.9.9")


def test_version_dev_toujours_mise_a_jour():
    assert updater._parse_version("v1.0.1") > updater._parse_version("dev")


def test_parse_version_prerelease_extrait_base():
    assert updater._parse_version("1.2.2-dev.1") == (1, 2, 2)


def test_prerelease_pas_de_mise_a_jour_meme_base():
    # 1.2.2-dev.1 en cours, stable 1.2.2 dispo → pas de mise à jour
    assert not (updater._parse_version("v1.2.2") > updater._parse_version("1.2.2-dev.1"))


def test_prerelease_mise_a_jour_version_suivante():
    # 1.2.2-dev.1 en cours, stable 1.2.3 dispo → mise à jour
    assert updater._parse_version("v1.2.3") > updater._parse_version("1.2.2-dev.1")
