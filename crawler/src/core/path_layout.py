from dataclasses import dataclass


def store_prefix(video_id: int) -> str:
    if not video_id:
        raise ValueError("video id is required")
    vid = int(video_id)
    shard = f"{vid % 100:02d}"
    return f"{shard}/{vid}"


@dataclass(frozen=True)
class VideoCdnKeys:
    prefix: str
    translated_s3_key: str
    thumbnail_s3_key: str
    video_s3_key: str
    hls_master_s3_key: str


def video_cdn_keys(video_id: int) -> VideoCdnKeys:
    p = store_prefix(video_id)
    hls_p = f"{p}/hls"
    return VideoCdnKeys(
        prefix=p,
        translated_s3_key=f"{p}/subtitles/",
        thumbnail_s3_key=f"{p}/thumbnail.webp",
        video_s3_key=f"{p}/video.mp4",
        hls_master_s3_key=f"{hls_p}/master.m3u8",
    )
