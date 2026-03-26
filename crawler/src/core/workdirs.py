from pathlib import Path


def _project_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not find pyproject.toml above workdirs.py")


def _works_dir(project_root: Path) -> Path:
    repo_works = project_root.parent / "works"
    local_works = project_root / "works"
    if repo_works.is_dir():
        return repo_works
    if local_works.is_dir():
        return local_works
    return local_works


WORKS_DIR = _works_dir(_project_root())

VIDEOS_DIR = WORKS_DIR.joinpath("videos")
LOGS_DIR = WORKS_DIR.joinpath("logs")
MODELS_DIR = WORKS_DIR.joinpath("models")

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
