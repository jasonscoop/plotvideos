from typing import List

from crawler.lib.connection import get_db
from crawler.lib.models import Language


class LanguageCrud:
    @staticmethod
    def get_all() -> List[Language]:
        with get_db() as db:
            return db.query(Language).filter(Language.enabled == True).all()
