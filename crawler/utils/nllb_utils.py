from typing import List
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from loguru import logger

from crawler.core.config import NLLB_MODEL, NLLB_DEVICE, NLLB_MAX_LENGTH, MODELS_DIR
from crawler.core.languages import Language

_model = None
_tokenizer = None

NLLB_CACHE_DIR = MODELS_DIR / "nllb"

LANG_CODE_MAP = {
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "ru": "rus_Cyrl",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "zh": "zho_Hans",
    "ar": "arb_Arab",
    "hi": "hin_Deva",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "id": "ind_Latn",
    "ms": "zsm_Latn",
    "tr": "tur_Latn",
    "pl": "pol_Latn",
    "nl": "nld_Latn",
    "sv": "swe_Latn",
    "da": "dan_Latn",
    "fi": "fin_Latn",
    "no": "nob_Latn",
    "cs": "ces_Latn",
    "el": "ell_Grek",
    "he": "heb_Hebr",
    "uk": "ukr_Cyrl",
    "ro": "ron_Latn",
    "hu": "hun_Latn",
    "bg": "bul_Cyrl",
    "hr": "hrv_Latn",
    "sk": "slk_Latn",
    "sl": "slv_Latn",
    "sr": "srp_Cyrl",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "mr": "mar_Deva",
    "ur": "urd_Arab",
    "fa": "pes_Arab",
    "af": "afr_Latn",
    "sw": "swh_Latn",
    "tl": "tgl_Latn",
    "ca": "cat_Latn",
    "eu": "eus_Latn",
    "gl": "glg_Latn",
    "cy": "cym_Latn",
    "ga": "gle_Latn",
    "mt": "mlt_Latn",
    "is": "isl_Latn",
    "et": "est_Latn",
    "lv": "lvs_Latn",
    "lt": "lit_Latn",
    "mk": "mkd_Cyrl",
    "sq": "als_Latn",
    "hy": "hye_Armn",
    "ka": "kat_Geor",
    "az": "azj_Latn",
    "kk": "kaz_Cyrl",
    "uz": "uzn_Latn",
    "mn": "khk_Cyrl",
    "my": "mya_Mymr",
    "km": "khm_Khmr",
    "lo": "lao_Laoo",
    "ne": "npi_Deva",
    "si": "sin_Sinh",
    "am": "amh_Ethi",
    "yo": "yor_Latn",
    "ig": "ibo_Latn",
    "ha": "hau_Latn",
    "zu": "zul_Latn",
    "xh": "xho_Latn",
}


def get_nllb_code(lang_code: str) -> str:
    return LANG_CODE_MAP.get(lang_code, f"{lang_code}_Latn")


def _load_model():
    global _model, _tokenizer
    if _model is None:
        NLLB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Loading NLLB model: {NLLB_MODEL} from {NLLB_CACHE_DIR}")
        _tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL, cache_dir=NLLB_CACHE_DIR)
        _model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL, cache_dir=NLLB_CACHE_DIR)
        if NLLB_DEVICE == "cuda" and torch.cuda.is_available():
            _model = _model.to("cuda")
        elif NLLB_DEVICE == "mps" and torch.backends.mps.is_available():
            _model = _model.to("mps")
        logger.info(f"NLLB model loaded on {NLLB_DEVICE}")
    return _model, _tokenizer


def nllb_translate(texts: List[str], target_lang: Language, source_lang: str = "eng_Latn") -> List[str]:
    model, tokenizer = _load_model()
    target_code = get_nllb_code(target_lang.code)
    
    tokenizer.src_lang = source_lang
    results = []
    
    for text in texts:
        if not text or not text.strip():
            results.append(text)
            continue
            
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=NLLB_MAX_LENGTH)
        if NLLB_DEVICE == "cuda" and torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        elif NLLB_DEVICE == "mps" and torch.backends.mps.is_available():
            inputs = {k: v.to("mps") for k, v in inputs.items()}
        
        translated = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_code),
            max_length=NLLB_MAX_LENGTH,
        )
        result = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
        results.append(result)
    
    return results


def nllb_translate_batch(texts: List[str], target_lang: Language, source_lang: str = "eng_Latn", batch_size: int = 8) -> List[str]:
    model, tokenizer = _load_model()
    target_code = get_nllb_code(target_lang.code)
    
    tokenizer.src_lang = source_lang
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        non_empty_indices = []
        non_empty_texts = []
        
        for j, text in enumerate(batch):
            if text and text.strip():
                non_empty_indices.append(j)
                non_empty_texts.append(text)
        
        batch_results = [""] * len(batch)
        
        if non_empty_texts:
            inputs = tokenizer(non_empty_texts, return_tensors="pt", padding=True, truncation=True, max_length=NLLB_MAX_LENGTH)
            if NLLB_DEVICE == "cuda" and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            elif NLLB_DEVICE == "mps" and torch.backends.mps.is_available():
                inputs = {k: v.to("mps") for k, v in inputs.items()}
            
            translated = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_code),
                max_length=NLLB_MAX_LENGTH,
            )
            decoded = tokenizer.batch_decode(translated, skip_special_tokens=True)
            
            for idx, j in enumerate(non_empty_indices):
                batch_results[j] = decoded[idx]
        
        for j, text in enumerate(batch):
            if not text or not text.strip():
                batch_results[j] = text
        
        results.extend(batch_results)
    
    return results
