__version__ = "dev"  # remplacé par le tag git lors du build CI


def _detect_version():
    """En mode développement, lit le tag git courant."""
    import subprocess
    from pathlib import Path
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            cwd=Path(__file__).parent,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()
    except Exception:
        return "dev"


if __version__ == "dev":
    __version__ = _detect_version()
