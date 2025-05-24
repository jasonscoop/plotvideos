import json
import os
import logging
from pathlib import Path
from xml.sax.saxutils import unescape
from edge_tts.submaker import mktimestamp
from moviepy.video.tools import subtitles

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


def create_subtitle(flatted_sub: FlattedSub, subtitle_file: Path):
    """
    优化字幕文件
    1. 将字幕文件按照标点符号分割成多行
    2. 逐行匹配字幕文件中的文本
    3. 生成新的字幕文件
    """

    text = _format_text(flatted_sub.text)

    def formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
        """
        1
        00:00:00,000 --> 00:00:02,360
        跑步是一项简单易行的运动
        """
        start_t = mktimestamp(start_time).replace(".", ",")
        end_t = mktimestamp(end_time).replace(".", ",")
        return f"{idx}\n" f"{start_t} --> {end_t}\n" f"{sub_text}\n"

    start_time = -1.0
    sub_items = []
    sub_index = 0

    script_lines = utils.split_string_by_punctuations(text)
    sub_line = ""
    subs = []
    try:
        for sub_word in flatted_sub.words:
            sub = sub_word.word
            _start_time, end_time = sub_word.start_time, sub_word.end_time
            if start_time < 0:
                start_time = _start_time

            sub = unescape(sub)
            sub_line += " " + sub
            subs.append(sub)
            current_line = script_lines[sub_index]
            current_line_words = current_line.split()
            sub_text = ""
            if len(current_line_words) == len(subs) and compute_sentence_similarity(current_line, " ".join(subs)):
                sub_text = " ".join(current_line_words)

            # sub_text = match_line(subs, sub_index)
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
                sub_line = ""
                subs = []

        if len(sub_items) == len(script_lines):
            with open(subtitle_file, "w", encoding="utf-8") as file:
                file.write("\n".join(sub_items) + "\n")
            try:
                sbs = subtitles.file_to_subtitles(subtitle_file, encoding="utf-8")
                duration = max([tb for ((ta, tb), txt) in sbs])
                logging.info(
                    f"completed, subtitle file created: {subtitle_file}, duration: {duration}"
                )
            except Exception as e:
                logging.error(f"failed, error: {str(e)}")
                os.remove(subtitle_file)
        else:
            with open("../../works/sub_items.json", "w", encoding="utf-8") as file:
                file.write(json.dumps(sub_items, ensure_ascii=False, indent=2))

            with open("../../works/script_lines.json", "w", encoding="utf-8") as file:
                file.write(json.dumps(script_lines, ensure_ascii=False, indent=2))

            logging.warning(
                f"failed, sub_items len: {len(sub_items)}, script_lines len: {len(script_lines)}"
            )

    except Exception as e:
        logging.error(f"failed, error: {str(e)}")


def generate_subtitle(video_path: Path):
    wav_path = video_path.with_suffix(".wav")
    subtitle_path = video_path.with_suffix(".srt")

    duration = media_to_wav(video_path, wav_path)
    logging.info(f"Converted {video_path} to {wav_path}")

    azure_results = get_azure_results(wav_path, duration)
    flatted_sub = flat_azure_result(azure_results)
    logging.info(f"Got the azure results")

    create_subtitle(flatted_sub, subtitle_path)
    logging.info(f"Subtitle generated")

