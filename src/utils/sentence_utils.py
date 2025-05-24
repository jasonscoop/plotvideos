from sentence_transformers import SentenceTransformer, util
import ftfy
import unicodedata

# Load the model once (globally)
model = None


def compute_sentence_similarity(sentence1: str, sentence2: str) -> float:
    global model
    if model is None:
        model = SentenceTransformer('distiluse-base-multilingual-cased-v2')

    s1 = normalize_sentence(sentence1)
    s2 = normalize_sentence(sentence2)

    embeddings = model.encode([s1, s2], convert_to_tensor=True)
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
