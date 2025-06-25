from io import StringIO

import webvtt


def is_valid_vtt(vtt_content: str) -> bool:
    if not vtt_content:
        return False

    try:
        vtt = webvtt.from_string(vtt_content)
        prev_start_ms = -1
        for i, caption in enumerate(vtt.captions):
            start_ms = time_to_ms(caption.start)
            end_ms = time_to_ms(caption.end)

            if start_ms >= end_ms:
                return False
            if start_ms <= prev_start_ms:
                return False
            prev_start_ms = start_ms

        return True
    except Exception as e:
        return False


def time_to_ms(ts):
    h, m, s_ms = ts.split(':')
    s, ms = s_ms.split('.')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def correct_vtt(vtt_content: str) -> str:
    """
    Attempt to correct an invalid VTT string by ensuring start < end and strictly increasing start times.
    Returns the corrected VTT string (or the original if already valid or uncorrectable).
    """
    if is_valid_vtt(vtt_content):
        return vtt_content

    if vtt_content.strip() == '':
        return "WEBVTT\n"

    try:
        vtt = webvtt.from_string(vtt_content)
    except Exception as e:
        return vtt_content

    corrected_captions = []
    last_end_ms = 0
    for caption in vtt.captions:
        start_ms = time_to_ms(caption.start)
        end_ms = time_to_ms(caption.end)

        # Ensure start is after last end
        if start_ms <= last_end_ms:
            start_ms = last_end_ms + 1
        # Ensure end is after start
        if end_ms <= start_ms:
            end_ms = start_ms + 1

        # Convert back to VTT time format
        def ms_to_vtt(ms):
            h = ms // 3600000
            m = (ms % 3600000) // 60000
            s = (ms % 60000) // 1000
            ms_rem = ms % 1000
            return f"{h:02d}:{m:02d}:{s:02d}.{ms_rem:03d}"

        corrected_caption = webvtt.Caption(
            ms_to_vtt(start_ms),
            ms_to_vtt(end_ms),
            caption.text
        )
        corrected_captions.append(corrected_caption)
        last_end_ms = end_ms

    # Build new VTT
    new_vtt = webvtt.WebVTT()
    for c in corrected_captions:
        new_vtt.captions.append(c)

    with StringIO() as buf:
        new_vtt.write(buf)
        return buf.getvalue()
