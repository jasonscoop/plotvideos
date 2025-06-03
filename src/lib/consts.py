from src.utils.id_utils import PornhubIdExtractor, XhamsterIdExtractor, XvideosIdExtractor, EpornerIdExtractor, \
    YouJizzIdExtractor, RedTubeIdExtractor, YouPornIdExtractor, SpankBangIdExtractor

DB_ERROR_LOG_LENGTH = 1000

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

ID_EXTRACTOR_MAP = {
    "www.pornhub.com": PornhubIdExtractor,
    "www.xhamster.com": XhamsterIdExtractor,
    "www.xvideos.com": XvideosIdExtractor,
    "www.eporner.com": EpornerIdExtractor,
    "www.youjizz.com": YouJizzIdExtractor,
    "www.redtube.com": RedTubeIdExtractor,
    "www.youporn.com": YouPornIdExtractor,
    "www.pornhd.com": PornhubIdExtractor,
    "spankbang.com": SpankBangIdExtractor,
}

BUNNEY_COLLECTION_MAP = {
    "www.pornhub.com": "e3edc1ee-ecab-4451-bff2-fdeafb779415",
    "www.xhamster.com": "af16977f-15cf-4e1c-8b85-b6bf6dfc59e2",
    "www.xvideos.com": "a9d247b3-b562-44ed-8c6f-aa05d4532811",
    "www.eporner.com": "0ed26c1b-56ad-4057-b89e-3cc013b773ed",
    "www.youjizz.com": "49ed13c7-1491-4f55-9728-e78ad45814a4",
    "www.redtube.com": "e5682a25-bd3a-4111-8e60-8ad077ff6fe9",
    "www.youporn.com": "dcf8cba2-896e-41f1-b6aa-ef281b27b47d",
    "www.pornhd.com": "2df6932e-6079-47a8-b469-57eeda34a0cd",
    "spankbang.com": "97e2e3e6-0103-4179-898b-94b0bb7ed1b5",
}

VIDEO_EMBED_TEMPLATE = """<!-- wp:bunnycdn/block-stream-video {{"library_id":"{library_id}","collection_id":"","video_id":"{video_id}","token_authentication":false,"responsive":true}} -->
<div class="wp-block-bunnycdn-block-stream-video"><div style="position:relative;padding-top:56.25%;width:100%"><iframe src="https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay=false&amp;loop=false&amp;muted=false&amp;preload=false&amp;responsive=true" loading="lazy" style="border:0;position:absolute;top:0;height:100%;width:100%" allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;" allowfullscreen></iframe></div></div>
<!-- /wp:bunnycdn/block-stream-video -->"""
