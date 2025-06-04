from src.utils.azure_stt_utils import get_language_candidates


def test_get_language_candidates():
    assert get_language_candidates(["en", "zh"]) == ["en-US", "zh-CN", "hi-IN", "es-ES"]
    assert get_language_candidates(["en", "zh", "sw", "ja", "ur"]) == ["en-US", "zh-CN", "sw-KE", "ja-JP"]
