import pytest

from src.utils.string_utils import get_lang


@pytest.mark.parametrize("s, expected", [
    ("I am very happy", "en"),
    ("I'm very happy", "en"),
    ("You're my friend", "en"),
    ("I'm sure you're not sure what you will", "en"),
    ('咋的了呀啊', 'zh'),
    ("应该是这个", "zh"),
    ("哎", "zh"),
    ("哎，这回行了", "zh"),
    ("回家", "zh"),
    ("안녕하세요", "ko"),
    ("私はプログラミングが好きです", "ja"),
    ("مرحبا!ُ", "ar"),
    ("哎呀", "zh"),
    ("咦？", "zh"),
    ("诶", "zh"),
    ("哈哈哈哈", "zh"),
    ("我艹", "zh"),
    ("哇", "zh"),
])
def test_get_lang(s, expected):
    assert get_lang(s) == expected
