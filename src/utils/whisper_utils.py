import dataclasses
from pathlib import Path

from faster_whisper import WhisperModel
from faster_whisper.transcribe import TranscriptionInfo, Segment

from src.lib.config import MODELS_DIR
from src.utils.file_utils import save_json
from src.utils.string_utils import end_with_stop_char

_whisper_model: WhisperModel = None


def get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        download_root = MODELS_DIR.joinpath("whisper")
        _whisper_model = WhisperModel(
            "large-v3",
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=4,
            download_root=download_root.as_posix(),
            local_files_only=download_root.exists(),
        )
    return _whisper_model


def whisper_transcribe(audio_path: Path):
    audio_path = Path(audio_path)
    segments, info = get_whisper_model().transcribe(
        audio_path.as_posix(),
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    info: TranscriptionInfo = info
    save_json(audio_path.with_suffix(".info2.json"), dataclasses.asdict(info))

    subtitles, segment_list = convert_to_subtitles(segments)
    save_json(audio_path.with_suffix(".segments2.json"), segment_list)

    idx = 1
    items = []
    for subtitle in subtitles:
        text = subtitle.get("msg").strip()
        if text:
            items.append(text_to_vtt(text, subtitle.get("start_time"), subtitle.get("end_time")))
            idx += 1
    sub = "WEBVTT\n\n" + "\n".join(items)
    audio_path.with_suffix(".new2.vtt").write_text(sub)


def convert_to_subtitles(segments):
    subtitles = []
    segment_list = []
    for segment in segments:
        s: Segment = segment
        segment_list.append(dataclasses.asdict(s))
        words_idx = 0
        words_len = len(s.words)

        seg_start = 0
        seg_end = 0
        seg_text = ""

        if segment.words:
            is_segmented = False
            for word in segment.words:
                if not is_segmented:
                    seg_start = word.start
                    is_segmented = True

                seg_end = word.end
                # If it contains punctuation, then break the sentence.
                seg_text += word.word

                if end_with_stop_char(word.word):
                    # remove last char
                    seg_text = seg_text[:-1]
                    if not seg_text:
                        continue

                    if seg_text.strip():
                        subtitles.append({"msg": seg_text, "start_time": seg_start, "end_time": seg_end})

                    is_segmented = False
                    seg_text = ""

                if words_idx == 0 and segment.start < word.start:
                    seg_start = word.start
                if words_idx == (words_len - 1) and segment.end > word.end:
                    seg_end = word.end
                words_idx += 1

        if not seg_text:
            continue

        if seg_text.strip():
            subtitles.append({"msg": seg_text, "start_time": seg_start, "end_time": seg_end})

    return subtitles, segment_list


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
