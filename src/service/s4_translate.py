from loguru import logger

from src.lib.consts import BigLanguage
from src.utils.llm_utils import ask_azure_openai
from src.utils.log_utils import init_logging
from tests import SUBTITLES_DIR

if __name__ == '__main__':
    init_logging("translate")
    vtt = SUBTITLES_DIR.joinpath("azure-results-661bb3bde2251.vtt").read_text()
    # expected = SUBTITLES_DIR.joinpath("azure-results-661bb3bde2251.zh-CN.vtt").read_text()

    for lang in BigLanguage:
        actual = ask_azure_openai(vtt, lang)
        SUBTITLES_DIR.joinpath(f"azure-results-661bb3bde2251.{lang.long_code}.vtt").write_text(actual)
        logger.info(f"Translated to [{lang.long_code}: {lang.full_name}]")
