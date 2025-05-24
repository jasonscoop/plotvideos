import logging
from pathlib import Path
from xml.sax.saxutils import unescape
from edge_tts.submaker import mktimestamp

from src.lib.consts import SubtitleType
from src.lib.schemas import FlattedSub
from src.utils import utils
from src.utils.azure_stt_utils import media_to_wav, get_azure_results, flat_azure_result
from src.utils.sentence_utils import compute_sentence_similarity


def _format_text(text: str) -> str:
    # text = text.replace("\n", " ")
    text = text.replace("[", " ")
    text = text.replace("]", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    text = text.replace("{", " ")
    text = text.replace("}", " ")
    text = text.strip()
    return text


def srt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time).replace(".", ",")
    end_t = mktimestamp(end_time).replace(".", ",")
    return f"{idx}\n{start_t} --> {end_t}\n{sub_text}\n"


def vtt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time)
    end_t = mktimestamp(end_time)
    return f"{start_t} --> {end_t}\n{sub_text}\n"


def create_subtitle(flatted_sub: FlattedSub, type: SubtitleType = SubtitleType.vtt) -> str:
    text = _format_text(flatted_sub.text)

    start_time = -1.0
    sub_items = []
    sub_index = 0

    script_lines = utils.split_string_by_punctuations(text)
    subs = []
    formatter = vtt_formatter if type == SubtitleType.vtt else srt_formatter

    for sub_word in flatted_sub.words:
        sub = sub_word.word
        _start_time, end_time = sub_word.start_time, sub_word.end_time
        if start_time < 0:
            start_time = _start_time

        sub = unescape(sub)
        subs.append(sub)
        current_line = script_lines[sub_index]
        current_line_words = current_line.split()
        sub_text = ""
        if len(current_line_words) == len(subs) and compute_sentence_similarity(current_line, " ".join(subs)):
            sub_text = " ".join(current_line_words)

        if sub_text:
            sub_index += 1
            line = formatter(
                idx=sub_index,
                start_time=start_time,
                end_time=end_time,
                sub_text=sub_text,
            )
            sub_items.append(line)
            start_time = -1.0
            subs = []

    if len(sub_items) != len(script_lines):
        logging.error(f"failed, sub_items len: {len(sub_items)}, script_lines len: {len(script_lines)}")
        return ""

    header = "WEBVTT\n\n" if type == SubtitleType.vtt else ""
    return header + "\n".join(sub_items) + "\n"


def generate_subtitle(video_path: Path, type: SubtitleType):
    wav_path = video_path.with_suffix(".wav")
    subtitle_path = video_path.with_suffix(f".{type.value}")

    duration = media_to_wav(video_path, wav_path)
    logging.info(f"Converted {video_path} to {wav_path}")

    azure_results = get_azure_results(wav_path, duration)
    flatted_sub = flat_azure_result(azure_results)
    logging.info(f"Got the azure results")

    subtitle = create_subtitle(flatted_sub, subtitle_path, type)
    logging.info(f"Subtitle generated")
