import asyncio
from typing import List, Dict

from loguru import logger
from src.utils.log_utils import init_logging
from src.crud.term_crud import TermCrud
from src.crud.video_crud import VideoCrud
from src.lib.models import Video


def process_translations(translations: Dict[str, List[str]], original_text: str) -> List[Dict[str, str]]:
    """Convert translations from dict of lists to list of dict format."""
    result = []
    for lang, translations_list in translations.items():
        for translation in translations_list:
            result.append({
                "text": original_text,
                "lang": lang,
                "translation": translation
            })
    return result


async def convert_video(video: Video):
    """Convert a single video's translations."""
    try:
        # Process tag translations
        tag_terms = []
        if video.tag_translations:
            for tag in video.tags:
                tag_terms.extend(process_translations(video.tag_translations, tag))

        # Process category translations
        category_terms = []
        if video.category_translations:
            for category in video.categories:
                category_terms.extend(process_translations(video.category_translations, category))

        # Save all terms to terms table
        all_terms = tag_terms + category_terms
        for term in all_terms:
            TermCrud.create(term["text"], term["lang"], term["translation"])

        logger.info(f"Converted video {video.id}")

    except Exception as e:
        logger.error(f"Error converting video {video.id}: {str(e)}")
        raise


async def main():
    """Main function to convert all videos."""
    last_id = 0
    batch_size = 10

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size)
        if not videos:
            break

        first_id = videos[0].id
        last_id = videos[-1].id
        for video in videos:
            await convert_video(video)

        logger.info(f"Processed {first_id} - {last_id}")


if __name__ == "__main__":
    init_logging("convert")
    asyncio.run(main())
