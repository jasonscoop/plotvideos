import pytest

from src.lib.id_utils import YouJizzIdExtractor, PornhubIdExtractor, EpornerIdExtractor, RedTubeIdExtractor, \
    XhamsterIdExtractor, YouPornIdExtractor, SpankBangIdExtractor, XvideosIdExtractor, PornHDIdExtractor


@pytest.mark.parametrize("extractor, expected, url", [
    (PornhubIdExtractor, "ph63ce905f3fbf2", "https://www.site.com/view_video.php?viewkey=ph63ce905f3fbf2"),
    (EpornerIdExtractor, "gKxXbZQXx8C", "https://www.site.com/video-gKxXbZQXx8C/jealousy-and-erection-and-excitement-rental-wife-akemi/"),
    (RedTubeIdExtractor, "190319601", "https://www.redtube.com/190319601"),
    (XhamsterIdExtractor, "xhwG44u", "https://xhamster.com/videos/chinese-teen-gets-the-bbc-xhwG44u"),
    (XvideosIdExtractor, "ulluaud2445", "https://www.xvideos.com/video.ulluaud2445/chinese_housewife_xian_erai_had_a_passionate_fuck_with_a_new_guy"),
    (YouPornIdExtractor, "17133601", "https://www.youporn.com/watch/17133601/incredible-first-meeting-with-stepsis/"),
    (YouPornIdExtractor, "190632121", "https://www.youporn.com/watch/190632121/"),
    (PornHDIdExtractor, "1962", "http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video"),
    (PornHDIdExtractor, "13548", "https://www.pornhd.com/videos/13548/superb-jessica-jaymes-suck-and-fuck-a-big-schlong-hd-porn-movie"),
    (SpankBangIdExtractor, "1t5k2", "https://spankbang.com/1t5k2/video/fap+hero+era"),
    (SpankBangIdExtractor, "831zc", "https://spankbang.com/831zc/video/abbi+secraa+huge+tits"),
    (YouJizzIdExtractor, "72029002", "https://www.youjizz.com/videos/chinese---https%3a%2f%2fstplayer.top%2f---50-min-72029002.html"),
    (YouJizzIdExtractor, "8073101", "https://www.youjizz.com/videos/very-hot-nipples-8073101.html"),
])
def test_extractor(extractor, expected, url):
    assert extractor().get(url) == expected
