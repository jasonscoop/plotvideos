from typing import List, Dict
from uuid import UUID

from sqlalchemy import delete

from crawler.lib.connection import get_db
from crawler.lib.models import TitleTranslation


class TitleTranslationCrud:
    @classmethod
    def create_or_update(cls, video_id: UUID, lang: str, translated_title: str) -> TitleTranslation:
        """Create or update a single translation for a video"""
        with get_db() as session:
            translation = (
                session.query(TitleTranslation)
                .filter(
                    TitleTranslation.video_id == video_id,
                    TitleTranslation.lang == lang,
                )
                .first()
            )

            if translation:
                translation.translated_title = translated_title
            else:
                translation = TitleTranslation(
                    video_id=video_id, lang=lang, translated_title=translated_title
                )
                session.add(translation)

            session.commit()
            session.refresh(translation)
            return translation

    @classmethod
    def batch_create_or_update(cls, video_id: UUID, translations: Dict[str, str]) -> List[TitleTranslation]:
        """Create or update multiple translations for a video
        
        Args:
            video_id: The ID of the video
            translations: Dictionary mapping language codes to translated titles
                         e.g., {"en": "Hello", "es": "Hola", "ja": "こんにちは"}
        
        Returns:
            List of created/updated TitleTranslation objects
        """
        with get_db() as session:
            # Get existing translations for this video
            existing = (
                session.query(TitleTranslation)
                .filter(TitleTranslation.video_id == video_id)
                .all()
            )
            
            # Create lookup dictionary for existing translations
            existing_by_lang = {t.lang: t for t in existing}
            
            result = []
            for lang, translated_title in translations.items():
                if lang in existing_by_lang:
                    # Update existing
                    existing_by_lang[lang].translated_title = translated_title
                    result.append(existing_by_lang[lang])
                else:
                    # Create new
                    translation = TitleTranslation(
                        video_id=video_id, lang=lang, translated_title=translated_title
                    )
                    session.add(translation)
                    result.append(translation)
            
            session.commit()
            for t in result:
                session.refresh(t)
            
            return result

    @classmethod
    def get_by_video_id(cls, video_id: UUID) -> List[TitleTranslation]:
        """Get all translations for a video"""
        with get_db() as session:
            return (
                session.query(TitleTranslation)
                .filter(TitleTranslation.video_id == video_id)
                .all()
            )

    @classmethod
    def get_by_video_id_as_dict(cls, video_id: UUID) -> Dict[str, str]:
        """Get all translations for a video as a dictionary
        
        Returns:
            Dictionary mapping language codes to translated titles
            e.g., {"en": "Hello", "es": "Hola", "ja": "こんにちは"}
        """
        with get_db() as session:
            translations = (
                session.query(TitleTranslation)
                .filter(TitleTranslation.video_id == video_id)
                .all()
            )
            return {t.lang: t.translated_title for t in translations}

    @classmethod
    def get_by_video_id_and_lang(cls, video_id: UUID, lang: str) -> TitleTranslation | None:
        """Get a specific translation for a video and language"""
        with get_db() as session:
            return (
                session.query(TitleTranslation)
                .filter(
                    TitleTranslation.video_id == video_id,
                    TitleTranslation.lang == lang,
                )
                .first()
            )

    @classmethod
    def delete_by_video_id(cls, video_id: UUID) -> int:
        """Delete all translations for a video
        
        Returns:
            Number of translations deleted
        """
        with get_db() as session:
            result = session.execute(
                delete(TitleTranslation).where(
                    TitleTranslation.video_id == video_id
                )
            )
            session.commit()
            return result.rowcount

    @classmethod
    def delete_by_video_id_and_lang(cls, video_id: UUID, lang: str) -> bool:
        """Delete a specific translation for a video and language
        
        Returns:
            True if a translation was deleted, False otherwise
        """
        with get_db() as session:
            result = session.execute(
                delete(TitleTranslation).where(
                    TitleTranslation.video_id == video_id,
                    TitleTranslation.lang == lang,
                )
            )
            session.commit()
            return result.rowcount > 0

