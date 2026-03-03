import pytest

from src.utils.string_utils import hash_to_base62, get_tokens


def test_hash_to_base62():
    assert hash_to_base62("abc", 12) == ""


@pytest.mark.parametrize(
    "s, expected",
    [
        ("这个字叫哈哈 グが好きです", 13),
        ("I'm sure you're not sure what you will", 10),
        ("这个字叫 Hello how are you", 9),
    ],
)
def test_get_tokens(s, expected):
    assert get_tokens(s) == expected
