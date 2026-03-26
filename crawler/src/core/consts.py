from pathlib import Path


def _project_root() -> Path:
    """Directory that contains `pyproject.toml` (Python project root, e.g. `crawler/` or `/workspace` in Docker)."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not find pyproject.toml above consts.py")


def _works_dir(project_root: Path) -> Path:
    """Prefer repo-root `works/` (sibling of `crawler/`); else `crawler/works` (e.g. Docker mount)."""
    repo_works = project_root.parent / "works"
    local_works = project_root / "works"
    if repo_works.is_dir():
        return repo_works
    if local_works.is_dir():
        return local_works
    return repo_works


WORKS_DIR = _works_dir(_project_root())

VIDEOS_DIR = WORKS_DIR.joinpath("videos")
VIDEOS_DIR.mkdir(exist_ok=True)
LOGS_DIR = WORKS_DIR.joinpath("logs")
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR = WORKS_DIR.joinpath("models")

DB_ERROR_LOG_LENGTH = 1000

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]
