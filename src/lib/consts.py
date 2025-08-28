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
