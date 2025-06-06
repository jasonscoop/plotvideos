from src.utils.id_utils import (
    PornhubIdExtractor,
    XhamsterIdExtractor,
    XvideosIdExtractor,
    EpornerIdExtractor,
    YouJizzIdExtractor,
    RedTubeIdExtractor,
    YouPornIdExtractor,
    SpankBangIdExtractor,
    YoutubeIdExtractor
)

DB_ERROR_LOG_LENGTH = 1000
WP_TERM_MAX_LENGTH = 180

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

WEBSITES = {
    "www.pornhub.com": {
        "id_extractor": PornhubIdExtractor,
        "bunny_collection_id": "e3edc1ee-ecab-4451-bff2-fdeafb779415",
    },
    "www.xhamster.com": {
        "id_extractor": XhamsterIdExtractor,
        "bunny_collection_id": "af16977f-15cf-4e1c-8b85-b6bf6dfc59e2",
    },
    "www.xvideos.com": {
        "id_extractor": XvideosIdExtractor,
        "bunny_collection_id": "a9d247b3-b562-44ed-8c6f-aa05d4532811",
    },
    "www.eporner.com": {
        "id_extractor": EpornerIdExtractor,
        "bunny_collection_id": "0ed26c1b-56ad-4057-b89e-3cc013b773ed",
    },
    "www.youjizz.com": {
        "id_extractor": YouJizzIdExtractor,
        "bunny_collection_id": "49ed13c7-1491-4f55-9728-e78ad45814a4",
    },
    "www.redtube.com": {
        "id_extractor": RedTubeIdExtractor,
        "bunny_collection_id": "e5682a25-bd3a-4111-8e60-8ad077ff6fe9",
    },
    "www.youporn.com": {
        "id_extractor": YouPornIdExtractor,
        "bunny_collection_id": "dcf8cba2-896e-41f1-b6aa-ef281b27b47d",
    },
    "www.pornhd.com": {
        "id_extractor": PornhubIdExtractor,
        "bunny_collection_id": "2df6932e-6079-47a8-b469-57eeda34a0cd",
    },
    "spankbang.com": {
        "id_extractor": SpankBangIdExtractor,
        "bunny_collection_id": "97e2e3e6-0103-4179-898b-94b0bb7ed1b5",
    },
    "www.youtube.com": {
        "id_extractor": YoutubeIdExtractor,
        "bunny_collection_id": "05e03c5f-35c4-4db7-b8eb-ab60caabfc8a",
    }
}

VIDEO_EMBED_TEMPLATE = '<iframe src="https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay=false&amp;loop=false&amp;muted=false&amp;preload=false&amp;responsive=true" loading="lazy" allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;" allowfullscreen></iframe>'
