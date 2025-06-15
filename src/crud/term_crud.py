from collections import defaultdict
from typing import List, Dict

from sqlalchemy import select

from src.lib.connection import get_db
from src.lib.models import Term


class TermCrud:
    @staticmethod
    def get_translations(terms: List[str]) -> Dict[str, Dict[str, str]]:
        with get_db() as session:
            stmt = select(Term).where(Term.term.in_(terms))
            results = session.execute(stmt).scalars().all()

            # Group translations by language using defaultdict
            translations_by_lang = defaultdict(dict)
            for term in results:
                translations_by_lang[term.lang][term.term] = term.translation

            return dict(translations_by_lang)

    @staticmethod
    def create(term: str, lang: str, translation: str):
        with get_db() as session:
            term_obj = Term(term=term, lang=lang, translation=translation)
            session.add(term_obj)
            session.commit()
