import json

from loguru import logger

from src.lib.consts import SubtitleType, Language
from src.lib.models import Video
from src.lib.schemas import StorePath, PreDetectResult
from src.utils.audio_utils import detect_talking_whisper
from src.utils.azure_stt_utils import media_to_wav, get_azure_results
from src.utils.string_utils import get_lang, split_by_stop_chars


def mktimestamp(time_unit: float) -> str:
    """
    mktimestamp returns the timecode of the subtitle.

    The timecode is in the format of 00:00:00.000.

    Returns:
        str: The timecode of the subtitle.
    """
    hour = math.floor(time_unit / 10 ** 7 / 3600)
    minute = math.floor((time_unit / 10 ** 7 / 60) % 60)
    seconds = (time_unit / 10 ** 7) % 60
    return f"{hour:02d}:{minute:02d}:{seconds:06.3f}"


def srt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time).replace(".", ",")
    end_t = mktimestamp(end_time).replace(".", ",")
    return f"{idx}\n{start_t} --> {end_t}\n{sub_text}\n"


def vtt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time)
    end_t = mktimestamp(end_time)
    return f"{start_t} --> {end_t}\n{sub_text}\n"


def azure_stt_results_to_subtitle(azure_results, type) -> (str, str):
    formatter = vtt_formatter if type == SubtitleType.vtt else srt_formatter
    final_items = []
    subtitle_contents = []
    for i, item in enumerate(azure_results):
        final_items.append(formatter(
            idx=i + 1,
            start_time=item["Offset"],
            end_time=item["Offset"] + item["Duration"],
            sub_text=split_by_stop_chars(item["DisplayText"]).strip(),
        ))
        subtitle_contents.append(item["DisplayText"])

    header = "WEBVTT\n\n" if type == SubtitleType.vtt else ""
    return header + "\n".join(final_items) + "\n", "\n\n".join(subtitle_contents)


def generate_subtitle(video: Video) -> (str, int, PreDetectResult):
    path = StorePath(video.host, video.original_id)
    video_path = path.parent / video.filename
    if not video_path.exists():
        raise Exception(f"Video {video.original_id}-{video_path} does not exist")

    media_to_wav(video_path, path.wav)
    language = Language.from_short_code(get_lang(video.title))

    detected_result = detect_talking_whisper(video_path)

    azure_results = get_azure_results(path.wav, video.duration, language)
    path.azure_results.write_text(json.dumps(azure_results, indent=2, ensure_ascii=False))

    vtt_content, subtitle_content = azure_stt_results_to_subtitle(azure_results, SubtitleType.vtt)
    path.vtt.write_text(vtt_content)

    logger.info(f"[{video_path.name}] Generated subtitle, detected as '{language}'")
    return subtitle_content.strip(), detected_result
