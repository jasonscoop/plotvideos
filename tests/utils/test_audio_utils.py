from src.utils.audio_utils import detect_talking_whisper, detect_languages


def test_detect_speech():
    print("6542f0127499b", detect_talking_whisper(
        "/Users/garymeng/code/more/wuse/works/videos/www.pornhub.com/65/6542f0127499b/audio.wav"))
    print("6829f8210d126",
          detect_talking_whisper(
              "/Users/garymeng/code/more/wuse/works/videos/www.pornhub.com/68/6829f8210d126/audio.wav"))
    print("68334391e0051",
          detect_talking_whisper(
              "/Users/garymeng/code/more/wuse/works/videos/www.pornhub.com/68/68334391e0051/audio.wav"))


def test_detect_languages():
    langs = detect_languages("/Users/garymeng/code/more/wuse/works/videos/www.pornhub.com/68/6808ced982194/audio.wav")
    assert langs == []
