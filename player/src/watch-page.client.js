(function () {
  var cfgEl = document.getElementById("watch-page-config");
  if (!cfgEl || !cfgEl.textContent) return;

  var cfg;
  try {
    cfg = JSON.parse(cfgEl.textContent);
  } catch (e) {
    return;
  }

  var CAP_OFF = "__off__";
  var pageLang = cfg.pageLang;
  var sources = cfg.sources || [];
  var subtitleTracks = cfg.subtitleTracks || [];
  var savedRaw = localStorage.getItem("subtitle_lang");
  var captionChoice =
    savedRaw === CAP_OFF ? CAP_OFF : savedRaw ? savedRaw : pageLang;

  if (typeof videojs === "undefined") return;

  var player = videojs("video-player", {
    fluid: false,
    responsive: true,
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    html5: {
      vhs: { overrideNative: !videojs.browser.IS_SAFARI },
    },
    sources: sources,
    controlBar: {
      children: [
        "playToggle",
        "volumePanel",
        "currentTimeDisplay",
        "timeDivider",
        "durationDisplay",
        "progressControl",
        "remainingTimeDisplay",
        "subtitlesButton",
        "playbackRateMenuButton",
        "fullscreenToggle",
      ],
    },
  });
  player.hlsQualitySelector({ displayCurrentQuality: true });

  function trackLang(tt) {
    return (tt.language || tt.srclang || "").trim();
  }

  /** If saved language is not available for this video, use the first track. */
  function normalizeCaptionChoice() {
    if (captionChoice === CAP_OFF) return;
    var ok = false;
    for (var i = 0; i < subtitleTracks.length; i++) {
      if (subtitleTracks[i].srclang === captionChoice) {
        ok = true;
        break;
      }
    }
    if (!ok && subtitleTracks[0]) {
      captionChoice = subtitleTracks[0].srclang;
      localStorage.setItem("subtitle_lang", captionChoice);
    }
  }

  function applyCaptionChoice() {
    normalizeCaptionChoice();
    var tracks = player.textTracks();
    var i;
    var tt;

    if (captionChoice === CAP_OFF) {
      for (i = 0; i < tracks.length; i++) {
        tt = tracks[i];
        if (tt.kind === "subtitles" || tt.kind === "captions") {
          tt.mode = "disabled";
        }
      }
      return;
    }

    for (i = 0; i < tracks.length; i++) {
      tt = tracks[i];
      if (tt.kind !== "subtitles" && tt.kind !== "captions") continue;
      tt.mode = trackLang(tt) === captionChoice ? "showing" : "disabled";
    }
  }

  function persistSubtitleFromPlayer() {
    var list = player.textTracks();
    var i;
    var tt;
    for (i = 0; i < list.length; i++) {
      tt = list[i];
      if (tt.kind !== "subtitles" && tt.kind !== "captions") continue;
      if (tt.mode === "showing") {
        localStorage.setItem("subtitle_lang", trackLang(tt));
        return;
      }
    }
    localStorage.setItem("subtitle_lang", CAP_OFF);
  }

  function addSubtitleTracksOnce() {
    if (player.__lvSubsAdded) return;
    player.__lvSubsAdded = true;

    subtitleTracks.forEach(function (t) {
      player.addRemoteTextTrack(
        {
          kind: t.kind || "subtitles",
          label: t.label,
          srclang: t.srclang,
          src: t.src,
          default: false,
        },
        false
      );
    });

    applyCaptionChoice();

    player.on("texttrackchange", persistSubtitleFromPlayer);
  }

  player.ready(function () {
    if (!subtitleTracks.length) return;

    if (player.readyState() >= 1) {
      addSubtitleTracksOnce();
    } else {
      player.one("loadedmetadata", addSubtitleTracksOnce);
    }
  });
})();
