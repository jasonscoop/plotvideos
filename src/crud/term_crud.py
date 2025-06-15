from collections import defaultdict
from typing import List, Dict

from sqlalchemy import select

from src.lib.connection import get_db
from src.lib.models import Term


class TermCrud:
    @staticmethod
    def get_translations(texts: List[str]) -> Dict[str, Dict[str, str]]:
        with get_db() as session:
            stmt = select(Term).where(Term.text.in_(texts))
            results = session.execute(stmt).scalars().all()

            # Group translations by language using defaultdict
            translations_by_lang = defaultdict(dict)
            for term in results:
                translations_by_lang[term.lang][term.text] = term.translation

            return dict(translations_by_lang)

    @staticmethod
    def create(text: str, lang: str, translation: str):
        with get_db() as session:
            old = session.query(Term).filter(Term.text == text, Term.lang == lang).first()
            if old:
                return
            term_obj = Term(text=text, lang=lang, translation=translation)
            session.add(term_obj)
            session.commit()
