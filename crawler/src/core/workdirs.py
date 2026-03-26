"""Local `works/` layout — only import this from pipeline workers / scripts that use disk.

The HTTP API does not need these paths; keep imports out of `api` and thin `core` modules.
"""

from pathlib import Path


def _project_root() -> Path:
    """Directory that contains `pyproject.toml` (Python project root, e.g. `crawler/` or `/workspace` in Docker)."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not find pyproject.toml above workdirs.py")


def _works_dir(project_root: Path) -> Path:
    """Resolve `works/`: repo sibling first, then project-local (e.g. Docker `/workspace/works`)."""
    repo_works = project_root.parent / "works"
    local_works = project_root / "works"
    if repo_works.is_dir():
        return repo_works
    if local_works.is_dir():
        return local_works
    # Never default to `/works` when project_root is `/workspace` (parent is `/`).
    return local_works


WORKS_DIR = _works_dir(_project_root())

VIDEOS_DIR = WORKS_DIR.joinpath("videos")
LOGS_DIR = WORKS_DIR.joinpath("logs")
MODELS_DIR = WORKS_DIR.joinpath("models")

# Create tree when this module loads (crawler / scheduler only — not API).
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
