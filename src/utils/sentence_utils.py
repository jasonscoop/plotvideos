import logging
from typing import List
from sentence_transformers import SentenceTransformer, util
import ftfy
import unicodedata
import fasttext

from src.lib.config import MODELS_DIR
from src.lib.consts import STOP_CHARS, NO_SPACE_LANGS

similarity_model = None
fasttext_model = fasttext.load_model(MODELS_DIR.joinpath("lid.176.bin").as_posix())


def is_similar_sentence(sentence1, sentence2):
    return compute_sentence_similarity(sentence1, sentence2) > 0.95


def compute_sentence_similarity(sentence1: str, sentence2: str) -> float:
    global similarity_model
    if similarity_model is None:
        similarity_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')

    s1 = normalize_sentence(sentence1)
    s2 = normalize_sentence(sentence2)

    embeddings = similarity_model.encode([s1, s2], convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    return similarity.item()


def normalize_sentence(sentence: str) -> str:
    """
      Normalize multilingual sentence:
      - Fix Unicode issues
      - Strip outer punctuation
      - Capitalize first word, lowercase the rest (preserve ALL-UPPER acronyms)
      """
    # Fix text (ftfy handles smart quotes, weird unicode, etc.)
    sentence = ftfy.fix_text(sentence)

    # Unicode normalize (NFKC converts full-width to half-width, e.g., Chinese punctuation)
    sentence = unicodedata.normalize('NFKC', sentence)

    # Remove extra outer symbols
    sentence = sentence.strip(" \n\t\r\"'.,!?()[]{}")

    # Tokenize
    words = sentence.split()
    if not words:
        return ""

    # First word capitalized, others lower unless all-uppercase
    cleaned_words = [words[0].capitalize()]
    for word in words[1:]:
        cleaned_words.append(word if word.isupper() else word.lower())

    return ' '.join(cleaned_words)


def split_to_sentences(s):
    result = []
    txt = ""

    previous_char = ""
    next_char = ""
    for i in range(len(s)):
        char = s[i]
        if char == "\n":
            result.append(txt.strip())
            txt = ""
            continue

        if i > 0:
            previous_char = s[i - 1]
        if i < len(s) - 1:
            next_char = s[i + 1]

        if char == "." and previous_char.isdigit() and next_char.isdigit():
            # # In the case of "withdraw 10,000, charged at 2.5% fee", the dot in "2.5" should not be treated as a line break marker
            txt += char
            continue

        if char not in STOP_CHARS:
            txt += char
        else:
            result.append(txt.strip())
            txt = ""
    result.append(txt.strip())
    # filter empty string
    result = list(filter(None, result))
    return result


def get_lang(text: str) -> str:
    labels, prob = fasttext_model.predict(text, k=1)
    return labels[0].replace("__label__", "")


def split_to_words(text: str, language: str) -> List[str]:
    if language in NO_SPACE_LANGS:
        return list(text)
    return text.split()


def join_to_text(words: List[str], language: str) -> str:
    if language in NO_SPACE_LANGS:
        return "".join(words)
    return " ".join(words)
