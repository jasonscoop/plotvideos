import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse, parse_qs


class IdExtractor(ABC):
    @abstractmethod
    def get(self, url):
        raise NotImplementedError


class PornhubIdExtractor(IdExtractor):
    """https://www.site.com/view_video.php?viewkey=ph63ce905f3fbf2"""

    def get(self, url):
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query).get('viewkey', [""])[0]


class EpornerIdExtractor(IdExtractor):
    """https://www.site.com/video-gKxXbZQXx8C/jealousy-and-erection-and-excitement-rental-wife-akemi/"""

    def get(self, url):
        match = re.search(r'/video-([a-zA-Z0-9]+)/', url)
        return match.group(1) if match else ""


class RedTubeIdExtractor(IdExtractor):
    """https://www.redtube.com/190319601"""

    def get(self, url):
        match = re.search(r'redtube\.com/(\d+)', url)
        return match.group(1) if match else ""


class xHamsterIdExtractor(IdExtractor):
    """https://xhamster.com/videos/chinese-teen-gets-the-bbc-xhwG44u"""

    def get(self, url):
        return url.split("-")[-1]


class XvideosIdExtractor(IdExtractor):
    """https://www.xvideos.com/video.ulluaud2445/chinese_housewife_xian_erai_had_a_passionate_fuck_with_a_new_guy."""

    def get(self, url):
        match = re.search(r'www\.xvideos\.com/video\.(\w+)/', url)
        return match.group(1) if match else ""


class YouPornIdExtractor(IdExtractor):
    """
    https://www.youporn.com/watch/17133601/incredible-first-meeting-with-stepsis/
    https://www.youporn.com/watch/190632121/
    """

    def get(self, url):
        match = re.search(r'/watch/(\d+)/', url)
        return match.group(1) if match else ""


class PornHDIdExtractor(IdExtractor):
    """
    http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video
    https://www.pornhd.com/videos/13548/superb-jessica-jaymes-suck-and-fuck-a-big-schlong-hd-porn-movie
    """

    def get(self, url):
        match = re.search(r'www\.pornhd\.com/videos/(\d+)/', url)
        return match.group(1) if match else ""


class SpankBangIdExtractor(IdExtractor):
    """
    https://spankbang.com/1t5k2/video/fap+hero+era
    https://spankbang.com/831zc/video/abbi+secraa+huge+tits
    """

    def get(self, url):
        match = re.search(r'//spankbang\.com/(\w+)/', url)
        return match.group(1) if match else ""


class YouJizzIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'-(\d+)\.html$', url)
        return match.group(1) if match else ""
