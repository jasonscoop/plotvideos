"""Reconcile ``videos.store_dir`` and ``works/videos`` with :meth:`StorePath.build_prefix`.

- **Idempotent.** Safe to re-run (e.g. after changing shard rules, or if ``store_dir`` drifted).
- Moves ``{VIDEOS_DIR}/{old}/`` → ``{VIDEOS_DIR}/{new}/`` when prefixes differ and the old folder exists.
- Always sets ``store_dir`` to the canonical ``{id % 100 :02d}/{id}`` for every row.

Run from repo root (venv with crawler deps):

  python scripts/python/migrate_video_dirs_to_id_layout.py

``original_id`` removal is separate; see ``scripts/sql/drop_videos_original_id.sql``.
"""

import shutil

from loguru import logger

from core.config import VIDEOS_DIR
from core.connection import get_db
from core.models import Video
from core.schemas import StorePath


def main() -> None:
    moved = 0
    skipped_dest = 0
    with get_db() as session:
        for v in session.query(Video).order_by(Video.id.asc()).all():
            new_prefix = StorePath.build_prefix(v.id)
            old_prefix = (v.store_dir or "").strip("/")
            old_path = VIDEOS_DIR / old_prefix if old_prefix else None
            new_path = VIDEOS_DIR / new_prefix

            if (
                old_prefix != new_prefix
                and old_path
                and old_path.exists()
                and old_path.is_dir()
            ):
                new_path.parent.mkdir(parents=True, exist_ok=True)
                if new_path.exists():
                    logger.warning(
                        "Skip move id=%s: destination already exists %s",
                        v.id,
                        new_path,
                    )
                    skipped_dest += 1
                else:
                    shutil.move(str(old_path), str(new_path))
                    logger.info("Moved id=%s %s -> %s", v.id, old_prefix, new_prefix)
                    moved += 1

            v.store_dir = new_prefix

        session.commit()

    logger.info(
        "Done: canonical store_dir for all videos; moved %s dir(s), %s skip (dest exists).",
        moved,
        skipped_dest,
    )


if __name__ == "__main__":
    main()
