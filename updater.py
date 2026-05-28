import threading
import urllib.request
import json

_GITHUB_API = "https://api.github.com/repos/stephdl/epade/releases/latest"
_RELEASES_BASE = "https://github.com/stephdl/epade/releases/tag"


def _parse_version(tag: str) -> tuple:
    try:
        base = tag.lstrip("v").split("-")[0]  # ignore suffixe pre-release (ex. -dev.1)
        return tuple(int(x) for x in base.split("."))
    except ValueError:
        return (0,)


def check_update_async(current_version: str, callback):
    """Vérifie en arrière-plan si une nouvelle version est disponible sur GitHub.

    Appelle callback(latest_tag, releases_url) si une mise à jour existe,
    depuis le thread principal via after() — le callback doit planifier
    l'appel Tk lui-même (after(0, ...)).
    """
    def _run():
        try:
            req = urllib.request.Request(
                _GITHUB_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "epade-app",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310 — URL HTTPS constante
                data = json.loads(resp.read())
            latest_tag = data.get("tag_name", "")
            if latest_tag and _parse_version(latest_tag) > _parse_version(current_version):
                tag_url = f"{_RELEASES_BASE}/{latest_tag}"
                callback(latest_tag, tag_url)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
