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


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]
