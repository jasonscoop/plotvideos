import webvtt


def is_valid_vtt(vtt_content: str) -> bool:
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
