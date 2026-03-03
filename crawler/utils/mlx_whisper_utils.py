from pathlib import Path

from crawler.lib.schemas import StorePath
from crawler.utils.file_utils import save_json
from crawler.utils.string_utils import end_with_stop_char


def mlx_whisper_transcribe(video_path: StorePath):
    from mlx_whisper import transcribe
    audio_path = Path(video_path.audio)
    result = transcribe(
        audio_path.as_posix(),
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo",  # default saving at ~/.cache/huggingface/hub
        word_timestamps=True,
    )
    save_json(video_path.segments, result)
    subtitles = convert_to_subtitles(result["segments"])

    idx = 1
    items = []
    for subtitle in subtitles:
        text = subtitle.get("msg").strip()
        if text:
            items.append(text_to_vtt(text, subtitle.get("start_time"), subtitle.get("end_time")))
            idx += 1
    sub = "WEBVTT\n\n" + "\n".join(items)
    video_path.vtt.write_text(sub)

    return sub, result["text"]


def convert_to_subtitles(segments) -> (list, list, str):
    subtitles = []

    for segment in segments:
        words_idx = 0
        words_len = len(segment["words"])

        seg_start = 0
        seg_end = 0
        seg_text = ""

        if segment["words"]:
            is_segmented = False
            for word in segment["words"]:
                if not is_segmented:
                    seg_start = word["start"]
                    is_segmented = True

                seg_end = word["end"]
                # If it contains punctuation, then break the sentence.
                seg_text += word["word"]

                if end_with_stop_char(word["word"]):
                    # remove last char
                    seg_text = seg_text[:-1]
                    if not seg_text:
                        continue

                    if seg_text.strip():
                        subtitles.append({"msg": seg_text, "start_time": seg_start, "end_time": seg_end})

                    is_segmented = False
                    seg_text = ""

                if words_idx == 0 and segment["start"] < word["start"]:
                    seg_start = word["start"]
                if words_idx == (words_len - 1) and segment["end"] > word["end"]:
                    seg_end = word["end"]
                words_idx += 1

        if not seg_text:
            continue

        if seg_text.strip():
            subtitles.append({"msg": seg_text, "start_time": seg_start, "end_time": seg_end})

    return subtitles


def time_convert_seconds_to_hmsm(seconds) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, seconds, milliseconds)


def capitalize_first_letter(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def text_to_vtt(msg: str, start_time: float, end_time: float) -> str:
    start_time = time_convert_seconds_to_hmsm(start_time)
    end_time = time_convert_seconds_to_hmsm(end_time)

    return f"{start_time} --> {end_time}\n{capitalize_first_letter(msg.strip())}\n"
