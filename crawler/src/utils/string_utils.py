import hashlib
import math
import re
import string

import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")

STOP_CHARS = set(
    ".!?,:;…‥"  # English & common
    "。！？，、；："  # Chinese/Japanese
    "।"  # Hindi
    "܀።፧"  # Semitic (Syriac, Ge‘ez)
    "؟؛"  # Arabic/Persian
    "၊။"  # Burmese
    "⸮⁇⁈⁉"  # Rare multilingual
)


def end_with_stop_char(text: str) -> bool:
    if not text:
        return False

    for c in STOP_CHARS:
        if text.endswith(c):
            return True
    return False


BASE62_ALPHABET = string.digits + string.ascii_letters


def is_cjk(text: str) -> bool:
    for char in text:
        if "\u4e00" <= char <= "\u9fff":  # Common CJK Unified Ideographs
            return True
    return False


def split_by_stop_chars(text: str) -> str:
    sentences = re.split(f"[{re.escape(STOP_CHARS)}]", text)
    return "\n".join([s.strip() for s in sentences])


def base62_encode(num):
    if num == 0:
        return BASE62_ALPHABET[0]

    base62 = []
    while num:
        num, rem = divmod(num, 62)
        base62.append(BASE62_ALPHABET[rem])

    return "".join(reversed(base62))


def hash_to_base62(s, length: int = 10):
    bits_needed = math.ceil(length * math.log2(62))
    bytes_needed = math.ceil(bits_needed / 8)

    hash_bytes = hashlib.sha256(s.encode("utf-8")).digest()
    hash_int = int.from_bytes(hash_bytes[:bytes_needed], "big")
    base62 = base62_encode(hash_int)
    return base62[:length]


def get_tokens(text: str) -> int:
    return len(enc.encode(text))
