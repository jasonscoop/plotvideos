import json
import os
import re
import logging
import time
from typing import List
from xml.sax.saxutils import unescape
from edge_tts import SubMaker, submaker
from edge_tts.submaker import mktimestamp
from moviepy.video.tools import subtitles
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import SpeechRecognizer

from src.lib.config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
from src.utils import utils

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


def create_subtitle(words: List[dict], text: str, subtitle_file: str):
    """
    优化字幕文件
    1. 将字幕文件按照标点符号分割成多行
    2. 逐行匹配字幕文件中的文本
    3. 生成新的字幕文件
    """

    text = _format_text(text)

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

    def match_line(_subs: List[str], _sub_index: int):
        _sub_line = " ".join(_subs)
        if len(script_lines) <= _sub_index:
            return ""

        _line = script_lines[_sub_index]
        if _sub_line.casefold() == _line.casefold():
            return script_lines[_sub_index].strip()

        script_lines_words = script_lines[_sub_index].split()
        set1 = {s.casefold() for s in _subs}
        set2 = {s.casefold() for s in script_lines_words}
        if len(_subs) == len(script_lines_words) and set1 & set2:
            return script_lines[_sub_index].strip()

        _sub_line_ = re.sub(r"[^\w\s']", "", _sub_line)
        _line_ = re.sub(r"[^\w\s']", "", _line)
        if _sub_line_.casefold() == _line_.casefold():
            return _line_.strip()

        _sub_line_ = re.sub(r"\W+", "", _sub_line)
        _line_ = re.sub(r"\W+", "", _line)
        if _sub_line_.casefold() == _line_.casefold():
            return _line.strip()

        return ""

    sub_line = ""
    subs = []
    try:
        for word in words:
            sub = word["sub"]
            _start_time, end_time = word["start_time"], word["end_time"]
            if start_time < 0:
                start_time = _start_time

            sub = unescape(sub)
            sub_line += " " + sub
            subs.append(sub)
            sub_text = match_line(subs, sub_index)
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
            with open("sub_items.json", "w", encoding="utf-8") as file:
                file.write(json.dumps(sub_items, ensure_ascii=False, indent=2))

            with open("script_lines.json", "w", encoding="utf-8") as file:
                file.write(json.dumps(script_lines, ensure_ascii=False, indent=2))

            logging.warning(
                f"failed, sub_items len: {len(sub_items)}, script_lines len: {len(script_lines)}"
            )

    except Exception as e:
        logging.error(f"failed, error: {str(e)}")


def format_json_list(path):
    items = json.loads(open(path).read())
    texts = []
    words = []

    for item in items:
        texts.append(item["Display"])
        for word in item["Words"]:
            words.append({
                "sub": word["Word"],
                "start_time": word["Offset"],
                "end_time": word["Offset"] + word["Duration"],
            })

    return " ".join(texts), words


if __name__ == '__main__':
    text, words = format_json_list("/Users/garymeng/code/more/wuse/works/661bb3bde2251-small.srt-nbests.json")
    create_subtitle(words=words, text=text, subtitle_file="/Users/garymeng/code/more/wuse/works/661bb3bde2251-small.srt-nbests.srt")