import pytest

from src.utils.sentence_utils import compute_sentence_similarity, normalize_sentence


@pytest.mark.parametrize("input1, input2, expected", [
    ("I'm very happy", "I am very happy", 0.95),
    ("I'm very happy", "I am very happy", 0.95),
    ("I'm 10 years old", "I am ten years old", 0.95),
    ("I'm 10 years old", "I am 10 years old.", 0.95),
    ("You Look Great", "you look great", 0.95),
    ("You look great", "you look good", 0.95),
    ("he comes from USA", "He comes from usa", 0.85),
    ("10 years", "ten years", 0.95),
    ("10", "ten", 0.85),
])
def test_compute_sentence_similarity(input1, input2, expected):
    actual = compute_sentence_similarity(input1, input2)
    assert actual > expected


@pytest.mark.parametrize("sentence, expected", [
    ("I am very happy", "I am very happy"),
    ("i'm very happy", "I'm very happy"),
    ("  I am 10 years old.", "I am 10 years old"),
    ("I'm 10 years old!!!", "I'm 10 years old"),
    ("I'm 10 years old~~~", "I'm 10 years old~~~"),
    ("我今年10岁了！", "我今年10岁了"),
    ("我今年10岁了～～～", "我今年10岁了~~~"),
    ("he Comes From USA", "He comes from USA"),
    ("he Comes From China", "He comes from china"),
    ("ok", "Ok"),
])
def test_normalize_sentence(sentence, expected):
    assert normalize_sentence(sentence) == expected
