import json
import logging
import traceback
from pathlib import Path
from edge_tts.submaker import mktimestamp

from src.lib.consts import SubtitleType, BigLanguage
from src.utils.azure_stt_utils import media_to_wav, get_azure_results
from src.utils.log_utils import init_logging
from src.utils.string_utils import get_lang, replace_stop_chars


def srt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time).replace(".", ",")
    end_t = mktimestamp(end_time).replace(".", ",")
    return f"{idx}\n{start_t} --> {end_t}\n{sub_text}\n"


def vtt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time)
    end_t = mktimestamp(end_time)
    return f"{start_t} --> {end_t}\n{sub_text}\n"


def simple_create_subtitle(azure_results, type) -> str:
    formatter = vtt_formatter if type == SubtitleType.vtt else srt_formatter
    final_items = []
    for i, item in enumerate(azure_results):
        try:
            line = formatter(
                idx=i + 1,
                start_time=item["Offset"],
                end_time=item["Offset"] + item["Duration"],
                sub_text=replace_stop_chars(item["DisplayText"]).strip(),
            )
        except Exception:
            pass
        final_items.append(line)

    header = "WEBVTT\n\n" if type == SubtitleType.vtt else ""
    return header + "\n".join(final_items) + "\n"


def generate_subtitle(video_path: Path, sub_type: SubtitleType):
    wav_path = video_path.with_suffix(".wav")
    subtitle_path = video_path.with_suffix(f".{sub_type.value}")
    azure_results_file = video_path.with_suffix(f".azure-results.json")

    duration = media_to_wav(video_path, wav_path)
    logging.info(f"[{video_path.name}] Converted wav")

    language = BigLanguage.from_short_code(get_lang(video_path.stem))
    logging.info(f"[{video_path.name}] Detected language: {language}")

    azure_results = get_azure_results(wav_path, duration, language)
    azure_results_file.write_text(json.dumps(azure_results, indent=2, ensure_ascii=False))
    logging.info(f"[{video_path.name}] Wrote azure_results")

    subtitle = simple_create_subtitle(azure_results, sub_type)
    subtitle_path.write_text(subtitle)

    logging.info(f"[{video_path.name}] Generated subtitle")


if __name__ == '__main__':
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    init_logging("batch-convert")
    dir_path = "/Users/garymeng/code/more/wuse/tests/files/mp4"
    files = []
    for filename in os.listdir(dir_path):
        full_path = os.path.join(dir_path, filename)
        if os.path.isfile(full_path) and (full_path.endswith(".mp4") or full_path.endswith(".webm")):
            files.append(full_path)

    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        futures = []
        for f in files:
            futures.append(executor.submit(simple_create_subtitle, Path(f), SubtitleType.vtt))

        for future in as_completed(futures):
            try:
                future.result()  # This raises any exceptions from the thread
            except Exception as e:
                traceback.print_exc()
