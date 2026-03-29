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

  videojs.addLanguage("en", { "subtitles off": "Off" });

  var player = videojs("video-player", {
    fluid: false,
    responsive: true,
    preferFullWindow: true,
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    html5: {
      vhs: { overrideNative: !videojs.browser.IS_SAFARI },
      // Fetch each .vtt only when that track’s mode becomes non-disabled (see Video.js TextTrack).
      preloadTextTracks: false,
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

  function updateMenuMaxHeight() {
    var h = player.el().clientHeight - 48;
    player.el().style.setProperty("--vjs-menu-max-h", Math.max(h, 100) + "px");
  }
  updateMenuMaxHeight();
  window.addEventListener("resize", updateMenuMaxHeight);

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

  var rotated = false;

  function toggleRotate() {
    rotated = !rotated;
    var wrap = document.querySelector(".yt-player-wrap");
    if (!wrap) return;

    if (rotated) {
      wrap.classList.add("yt-player-rotated");
      try {
        var fs = wrap.requestFullscreen || wrap.webkitRequestFullscreen;
        if (fs) fs.call(wrap).catch(function () {});
      } catch (e) {}
    } else {
      wrap.classList.remove("yt-player-rotated");
      try {
        var doc = document;
        if (doc.fullscreenElement || doc.webkitFullscreenElement) {
          (doc.exitFullscreen || doc.webkitExitFullscreen).call(doc);
        }
      } catch (e) {}
    }
  }

  function addRotateButton() {
    var controlBar = player.getChild("controlBar");
    var btn = controlBar.addChild("button", {});
    btn.addClass("vjs-rotate-btn");
    btn.el().title = "Rotate";
    btn.el().addEventListener("click", function (e) {
      e.stopPropagation();
      e.preventDefault();
      toggleRotate();
    });
  }

  player.ready(function () {
    addRotateButton();

    if (!subtitleTracks.length) return;

    if (player.readyState() >= 1) {
      addSubtitleTracksOnce();
    } else {
      player.one("loadedmetadata", addSubtitleTracksOnce);
    }
  });
})();
