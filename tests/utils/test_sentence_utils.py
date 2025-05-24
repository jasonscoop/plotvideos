import pytest

from src.utils.sentence_utils import compute_sentence_similarity, normalize_sentence, split_to_words, \
    split_to_sentences, get_lang, split_universal


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
    ("你照他，你照我干什么玩意儿？", "你 照 他 ， 你 照 我 干 什 么 玩 意 儿 ？", 0.95)
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


@pytest.mark.parametrize("s, expected", [
    ("I am very happy", ["I", "am", "very", "happy"]),
    ("I'm very happy", ["I'm", "very", "happy"]),
    ("You're my friend", ["You're", "my", "friend"]),
    ("应该是这个", ["应", "该", "是", "这", "个"]),
    ("哎", ["哎"]),
    ("哎，这回行了", ["哎", "，", "这", "回", "行", "了"]),
    ("回家", ["回", "家"]),
    ("私はプログラミングが好きです",
     ['私', 'は', 'プ', 'ロ', 'グ', 'ラ', 'ミ', 'ン', 'グ', 'が', '好', 'き', 'で', 'す']),
])
def test_get_tokens(s, expected):
    detected_language = get_lang(s)
    assert split_to_words(s, detected_language) == expected


@pytest.mark.parametrize("s, expected", [
    ("应该是逼这个争争这个呀啊啊对，这么回事啊。哎，这回行了，来来坐看着了。哎哎，这什么？",
     ["应该是逼这个争争这个呀啊啊对",
      "这么回事啊",
      "哎",
      "这回行了",
      "来来坐看着了",
      "哎哎",
      "这什么"]
     ),
    ("It's a special token used to represent any character, or word that the tokenizer, or model does not recognize, or that is not in its vocabulary.",
     ["It's a special token used to represent any character",
      "or word that the tokenizer",
      "or model does not recognize",
      "or that is not in its vocabulary"]
     ),
    ("When tokenizing text, if the tokenizer encounters a character or word outside its known vocabulary, it replaces it with [UNK].",
     [
         "When tokenizing text",
         "if the tokenizer encounters a character or word outside its known vocabulary",
         "it replaces it with [UNK]"
     ])
])
def test_split_to_sentences(s, expected):
    assert split_to_sentences(s) == expected


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


@pytest.mark.parametrize("s, expected", [
    ("I am very happy", ["I", "am", "very", "happy"]),
    ("I'm very happy", ["I'm", "very", "happy"]),
    ("You're my friend", ["You're", "my", "friend"]),
    ("应该是这个", ["应", "该", "是", "这", "个"]),
    ("哎", ["哎"]),
    ("哎，这回行了", ["哎", "，", "这", "回", "行", "了"]),
    ("回家", ["回", "家"]),
    ("私はプログラミングが好きです",
     ['私', 'は', 'プ', 'ロ', 'グ', 'ラ', 'ミ', 'ン', 'グ', 'が', '好', 'き', 'で', 'す']),
    (
            "This is my 最好的朋友OK? वह मेरा दोस्त है। كيف حالك؟ Привет! Bonjour. ¡Hola! আপনি কেমন আছেন? Olá, nasılsın?こんにちは",
            ['This', 'is', 'my', '最', '好', '的', '朋', '友', 'OK', '?', 'व', 'ह', 'म', 'े', 'र', 'ा', 'द', 'ो', 'स',
             '्', 'त', 'ह', 'ै', '।', 'ك', 'ي', 'ف', 'ح', 'ا', 'ل', 'ك', '؟', 'П', 'р', 'и', 'в', 'е', 'т', '!', 'B',
             'o', 'n', 'j', 'o', 'u', 'r', '.', '¡', 'H', 'o', 'l', 'a', '!', 'আ', 'প', 'ন', 'ি', 'ক', 'ে', 'ম', 'ন',
             'আ', 'ছ', 'ে', 'ন', '?', 'O', 'l', 'á', ',', 'n', 'a', 's', 'ı', 'l', 's', 'ı', 'n', '?', 'こ', 'ん', 'に',
             'ち', 'は']
    ),
])
def test_split_universal(s, expected):
    assert split_universal(s) == expected
