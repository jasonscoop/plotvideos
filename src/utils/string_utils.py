import re

import fasttext
import requests
from src.lib.config import MODELS_DIR
from src.lib.consts import FASTTEXT_LANG_ALIAS

fasttext_model = None

STOP_CHARS = (
    ".!?,:;…‥"      # English & common
    "。！？，、；："  # Chinese/Japanese
    "।"             # Hindi
    "܀።፧"           # Semitic (Syriac, Ge‘ez)
    "؟؛"            # Arabic/Persian
    "၊။"            # Burmese
    "⸮⁇⁈⁉"          # Rare multilingual
)


def get_fasttext_model() -> fasttext.FastText:
    global fasttext_model
    if fasttext_model is not None:
        return fasttext_model

    model_file = MODELS_DIR / "fasttext" / "lid.176.bin"
    if not model_file.exists():
        model_file.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin")
        response.raise_for_status()
        model_file.write_bytes(response.content)
    fasttext_model = fasttext.load_model(model_file.as_posix())
    return fasttext_model


def is_cjk(text: str) -> bool:
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # Common CJK Unified Ideographs
            return True
    return False


def get_lang(text: str) -> str:
    labels, prob = get_fasttext_model().predict(text, k=1)
    code = labels[0].replace("__label__", "")
    code = FASTTEXT_LANG_ALIAS.get(code, code)
    if is_cjk(text) and code not in {"zh", "ja", "ko"}:
        return "zh"

    return code


def split_by_stop_chars(text: str) -> str:
    sentences = re.split(f"[{re.escape(STOP_CHARS)}]", text)
    return "\n".join([s.strip() for s in sentences])
