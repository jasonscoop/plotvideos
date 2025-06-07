import pytest

from src.utils.string_utils import get_lang, hash_to_base62, get_tokens


@pytest.mark.parametrize("s, expected", [
    ("I am very happy", ["en"]),
    ("I'm very happy", ["en"]),
    ("You're my friend", ["en"]),
    ("I'm sure you're not sure what you will", ["en"]),
    ('咋的了呀啊', ['zh']),
    ("应该是这个", ["zh"]),
    ("哎", ["zh"]),
    ("哎，这回行了", ["zh"]),
    ("回家", ["zh"]),
    ("안녕하세요", ["ko"]),
    ("私はプログラミングが好きです", ["ja"]),
    ("もちろん、一緒に行こうよ、just for a little adventure!", ["ja", "en"]),
    ("مرحبا!ُ", ["ar"]),
    ("哎呀", ["zh"]),
    ("咦？", ["zh"]),
    ("诶", ["zh"]),
    ("哈哈哈哈", ["zh"]),
    ("我艹", ["zh"]),
    ("哇", ["zh"]),
    ("这个字叫 Hello how are you", ["zh", "en"]),
    ("这个字叫哈哈 グが好きです", ["zh", "ja"])
])
def test_get_lang(s, expected):
    assert get_lang(s) == expected


def test_hash_to_base62():
    assert hash_to_base62("abc", 12) == ""


@pytest.mark.parametrize("s, expected", [
    ("这个字叫哈哈 グが好きです", 13),
    ("I'm sure you're not sure what you will", 10),
    ("这个字叫 Hello how are you", 9),
])
def test_get_tokens(s, expected):
    assert get_tokens(s) == expected
