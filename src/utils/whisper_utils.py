from pathlib import Path

from faster_whisper import WhisperModel

from src.lib.config import MODELS_DIR, WHISPER_DEVICE, WHISPER_NUM_WORKERS, WHISPER_CPU_THREADS, WHISPER_COMPUTE_TYPE, \
    WHISPER_MODEL
from src.lib.schemas import StorePath
from src.utils.string_utils import end_with_stop_char


def get_whisper_model() -> WhisperModel:
    download_root = MODELS_DIR.joinpath("whisper").joinpath(WHISPER_MODEL)
    download_root.mkdir(parents=True, exist_ok=True)
    return WhisperModel(
        model_size_or_path=WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
        cpu_threads=WHISPER_CPU_THREADS,
        num_workers=WHISPER_NUM_WORKERS,
        download_root=download_root.as_posix(),
        local_files_only=False,
    )


def whisper_transcribe(video_path: StorePath):
    audio_path = Path(video_path.audio)
    segments, _ = get_whisper_model().transcribe(
        audio_path.as_posix(),
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    subtitles, sub_text = convert_to_subtitles(segments)

    items = []
    for subtitle in subtitles:
        text = subtitle.get("msg").strip()
        if text:
            items.append(text_to_vtt(text, subtitle.get("start_time"), subtitle.get("end_time")))
    vtt_content = "WEBVTT\n\n" + "\n".join(items)
    return vtt_content, sub_text


def convert_to_subtitles(segments) -> (list, str):
    subtitles = []
    subtitle_content = ""
    for segment in segments:
        subtitle_content += segment.text
        words_idx = 0
        words_len = len(segment.words)

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

    return subtitles, subtitle_content


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


if __name__ == '__main__':
    model = get_whisper_model()
    print(model.model.device)  # 应输出 "metal"
