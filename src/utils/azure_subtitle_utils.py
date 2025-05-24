import json
import logging
import traceback
from pathlib import Path
from xml.sax.saxutils import unescape
from edge_tts.submaker import mktimestamp


from src.lib.consts import SubtitleType, BigLanguage
from src.lib.schemas import FlattedSub
from src.utils.azure_stt_utils import media_to_wav, get_azure_results, flat_azure_result
from src.utils.log_utils import init_logging
from src.utils.sentence_utils import is_similar_sentence, split_to_words, join_to_text, split_to_sentences, get_lang


def remove_brackets(text: str) -> str:
    return text.translate(str.maketrans({
        "[": " ",
        "]": " ",
        "(": " ",
        ")": " ",
        "{": " ",
        "}": " "
    })).strip()


def srt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time).replace(".", ",")
    end_t = mktimestamp(end_time).replace(".", ",")
    return f"{idx}\n{start_t} --> {end_t}\n{sub_text}\n"


def vtt_formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
    start_t = mktimestamp(start_time)
    end_t = mktimestamp(end_time)
    return f"{start_t} --> {end_t}\n{sub_text}\n"


def create_subtitle(flatted_sub: FlattedSub, type: SubtitleType = SubtitleType.vtt) -> str:
    if not flatted_sub.text.strip() or len(flatted_sub.words) == 0:
        return ""

    formatter = vtt_formatter if type == SubtitleType.vtt else srt_formatter
    script_lines = split_to_sentences(remove_brackets(flatted_sub.text))

    start_time = -1.0
    final_items = []
    realtime_i = 0
    realtime_words = []

    script_line = script_lines[realtime_i]
    detected_language = get_lang(script_line)
    script_line_words = split_to_words(script_line, detected_language)

    for i, sub_word in enumerate(flatted_sub.words):
        if start_time < 0:
            start_time = sub_word.start_time

        realtime_words.append(unescape(sub_word.word))
        realtime_line = join_to_text(realtime_words, detected_language)

        if len(script_line_words) == len(realtime_words) and (script_line == realtime_line or is_similar_sentence(script_line, realtime_line)):
            realtime_i += 1
            line = formatter(
                idx=realtime_i,
                start_time=start_time,
                end_time=sub_word.end_time,
                sub_text=script_line,
            )
            final_items.append(line)
            start_time = -1.0
            realtime_words = []
            if realtime_i == len(script_lines):
                break
            script_line = script_lines[realtime_i]
            detected_language = get_lang(script_line)
            script_line_words = split_to_words(script_line, detected_language)

    if len(final_items) != len(script_lines):
        logging.error(f"failed, sub_items len: {len(final_items)}, script_lines len: {len(script_lines)}")
        return ""

    header = "WEBVTT\n\n" if type == SubtitleType.vtt else ""
    return header + "\n".join(final_items) + "\n"


def generate_subtitle(video_path: Path, sub_type: SubtitleType):
    wav_path = video_path.with_suffix(".wav")
    subtitle_path = video_path.with_suffix(f".{sub_type.value}")
    azure_results_file = video_path.with_suffix(f".azure-results.json")
    azure_flatted_result_file = video_path.with_suffix(f".azure-flatted-results.json")

    duration = media_to_wav(video_path, wav_path)
    logging.info(f"[{video_path.name}] Converted wav")

    language = BigLanguage.from_short_code(get_lang(video_path.stem))
    logging.info(f"[{video_path.name}] Detected language: {language}")

    azure_results = get_azure_results(wav_path, duration, language)
    azure_results_file.write_text(json.dumps(azure_results, indent=2, ensure_ascii=False))
    logging.info(f"[{video_path.name}] Wrote azure_results")

    flatted_sub = flat_azure_result(azure_results)
    azure_flatted_result_file.write_text(flatted_sub.model_dump_json())
    logging.info(f"[{video_path.name}] Wrote azure_flatted_results")

    subtitle = create_subtitle(flatted_sub, sub_type)
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
        if os.path.isfile(full_path) and (full_path.endswith(".mp4")or full_path.endswith(".webm")):
            files.append(full_path)

    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        futures = []
        for f in files:
            futures.append(executor.submit(generate_subtitle, Path(f), SubtitleType.vtt))

        for future in as_completed(futures):
            try:
                future.result()  # This raises any exceptions from the thread
            except Exception as e:
                traceback.print_exc()
