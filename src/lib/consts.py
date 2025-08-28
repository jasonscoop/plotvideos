from src.utils.id_utils import (
    PornhubIdExtractor,
    XhamsterIdExtractor,
    XvideosIdExtractor,
    EpornerIdExtractor,
    YouJizzIdExtractor,
    RedTubeIdExtractor,
    YouPornIdExtractor,
    SpankBangIdExtractor,
    YoutubeIdExtractor,
)

DB_ERROR_LOG_LENGTH = 1000
AZURE_STT_MAX_AUDIO_SIZE = 250 * 1024 * 1024
AZURE_STT_MAX_DURATION = 2 * 60 * 60

FASTTEXT_LANG_ALIAS = {
    # Chinese and Dialects
    "zh": "zh",
    "zh-cn": "zh",
    "zh-tw": "zh",
    "yue": "zh",  # Cantonese
    "wuu": "zh",  # Shanghainese
    "hak": "zh",  # Hakka
    "nan": "zh",  # Min Nan
    "lzh": "zh",  # Classical Chinese
    "cdo": "zh",  # Min Dong
    "hsn": "zh",  # Xiang (Hunanese)
    "xmf": "zh",  # 🛑 Mistaken as Chinese – normalize
}

NO_SPACE_LOCALES = {
    "zh-CN",  # Chinese (Simplified) - Mainland China
    "zh-TW",  # Chinese (Traditional) - Taiwan
    "zh-HK",  # Chinese (Traditional) - Hong Kong
    "ja-JP",  # Japanese
    "ko-KR",  # Korean (semi-space-using, context-dependent)
    "th-TH",  # Thai
    "lo-LA",  # Lao
    "km-KH",  # Khmer (Cambodian)
    "my-MM",  # Burmese (Myanmar)
    "dz-BT",  # Dzongkha (Bhutan)
    "bo-CN",  # Tibetan
    "mn-MN",  # Mongolian (Traditional script - no spaces)
}

WEBSITES = {
    "www.pornhub.com": ("ph", PornhubIdExtractor),
    "www.xhamster.com": ("xh", XhamsterIdExtractor),
    "www.xvideos.com": ("xv", XvideosIdExtractor),
    "www.eporner.com": ("ep", EpornerIdExtractor),
    "www.youjizz.com": ("yj", YouJizzIdExtractor),
    "www.redtube.com": ("rt", RedTubeIdExtractor),
    "www.youporn.com": ("yp", YouPornIdExtractor),
    "www.pornhd.com": ("pd", PornhubIdExtractor),
    "spankbang.com": ("sb", SpankBangIdExtractor),
    "www.youtube.com": ("yt", YoutubeIdExtractor),
}
