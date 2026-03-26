from collections import defaultdict
from typing import List, Dict, Set

from sqlalchemy import select

from core.connection import get_db
from core.models import Term


class TermCrud:
    @staticmethod
    def get_translations(texts: List[str]) -> Dict[str, Set[str]]:
        with get_db() as session:
            stmt = select(Term).where(Term.text.in_(texts))
            results = session.execute(stmt).scalars().all()

            translations = defaultdict(set)
            for term in results:
                translations[term.lang].add(term.translation)

            return dict(translations)

    @staticmethod
    def get_translations_map(texts: List[str]) -> Dict[str, Dict[str, str]]:
        """Returns {lang: {original_text: translated_text}}"""
        with get_db() as session:
            stmt = select(Term).where(Term.text.in_(texts))
            results = session.execute(stmt).scalars().all()

            translations: Dict[str, Dict[str, str]] = defaultdict(dict)
            for term in results:
                translations[term.lang][term.text] = term.translation

            return dict(translations)

    @staticmethod
    def create(text: str, lang: str, translation: str):
        with get_db() as session:
            old = session.query(Term).filter(Term.text == text, Term.lang == lang).first()
            if old:
                return
            term_obj = Term(text=text, lang=lang, translation=translation)
            session.add(term_obj)
            session.commit()
