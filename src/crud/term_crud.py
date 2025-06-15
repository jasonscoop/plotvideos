from typing import List, Optional

from sqlalchemy import select

from src.lib.connection import get_db
from src.lib.models import Terms


class TermCrud:
    @staticmethod
    def get_translation(term: str, lang: str) -> Optional[str]:
        with get_db() as session:
            stmt = select(Terms).where(Terms.term == term, Terms.lang == lang)
            result = session.execute(stmt).scalar_one_or_none()
            return result.translation if result else None

    @staticmethod
    def batch_get_translations(terms: List[str], lang: str) -> dict[str, str]:
        with get_db() as session:
            stmt = select(Terms).where(Terms.term.in_(terms), Terms.lang == lang)
            results = session.execute(stmt).scalars().all()
            return {term.term: term.translation for term in results}

    @staticmethod
    def create(term: str, lang: str, translation: str):
        with get_db() as session:
            term_obj = Terms(term=term, lang=lang, translation=translation)
            session.add(term_obj)
            session.commit()
