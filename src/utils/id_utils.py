import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse, parse_qs


class IdExtractor(ABC):
    @abstractmethod
    def get(self, url):
        raise NotImplementedError


class PornhubIdExtractor(IdExtractor):
    def get(self, url):
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query).get('viewkey', [""])[0]


class EpornerIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'/video-([a-zA-Z0-9]+)/', url)
        return match.group(1) if match else ""


class RedTubeIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'redtube\.com/(\d+)', url)
        return match.group(1) if match else ""


class XhamsterIdExtractor(IdExtractor):
    def get(self, url):
        return url.split("-")[-1]


class XvideosIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'www\.xvideos\.com/video\.(\w+)/', url)
        return match.group(1) if match else ""


class YouPornIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'/watch/(\d+)/', url)
        return match.group(1) if match else ""


class PornHDIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'www\.pornhd\.com/videos/(\d+)/', url)
        return match.group(1) if match else ""


class SpankBangIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'//spankbang\.com/(\w+)/', url)
        return match.group(1) if match else ""


class YouJizzIdExtractor(IdExtractor):
    def get(self, url):
        match = re.search(r'-(\d+)\.html$', url)
        return match.group(1) if match else ""


class YoutubeIdExtractor(IdExtractor):
    def get(self, url):
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query).get('v', [""])[0]
