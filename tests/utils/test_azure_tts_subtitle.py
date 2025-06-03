import json

from src.utils.azure_stt_utils import get_azure_results
from tests import AUDIOS_DIR


def test_get_azure_results():
    j = get_azure_results(AUDIOS_DIR / "clip3.wav", 300, ["en", "ja"])
    # json_file = json.loads(AUDIOS_DIR.joinpath("clip1.json").read_text())
    json_file = AUDIOS_DIR / "clip3.json"
    json_file.write_text(json.dumps(j, indent=2, ensure_ascii=False))
    # azure_results = json.loads(json_file1.read_text())
    # vtt = azure_stt_results_to_subtitle(azure_results, SubtitleType.vtt)
    #
    # json_file1.with_suffix(".generated6.vtt").write_text(vtt)
    #
    # audio = VIDEOS_DIR / "贾冰原来拍过那么多搞笑电影！每个片段拎出来都会笑死的程度~#贾冰 #狂飙 #搞笑 [tsYnuJI0u4I].wav"
    # j = get_azure_results(audio, 300, Language.CHINESE)
    # json_file2 = audio.with_suffix(".azure-result-6.json")
    # # j = json.loads(json_file2.read_text())
    # json_file2.write_text(json.dumps(j, indent=2, ensure_ascii=False))
    # azure_results = json.loads(json_file2.read_text())
    # vtt = azure_stt_results_to_subtitle(azure_results, SubtitleType.vtt)
    #
    # json_file2.with_suffix(".generated6.vtt").write_text(vtt)
