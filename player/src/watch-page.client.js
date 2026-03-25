(function () {
  var cfgEl = document.getElementById("watch-page-config");
  if (!cfgEl || !cfgEl.textContent) return;

  var cfg;
  try {
    cfg = JSON.parse(cfgEl.textContent);
  } catch (e) {
    return;
  }

  var pageLang = cfg.pageLang;
  var sources = cfg.sources || [];
  var subtitleTracks = cfg.subtitleTracks || [];

  if (typeof videojs === "undefined") return;

  var player = videojs("video-player", {
    fluid: false,
    responsive: true,
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    html5: {
      vhs: { overrideNative: !videojs.browser.IS_SAFARI },
    },
    sources: sources,
    tracks: subtitleTracks.map(function (t) {
      return {
        kind: t.kind,
        src: t.src,
        srclang: t.srclang,
        label: t.label,
        default: !!t.default,
      };
    }),
  });
  player.hlsQualitySelector({ displayCurrentQuality: true });

  var savedLang = localStorage.getItem("subtitle_lang");
  var preferredLang = savedLang || pageLang;

  player.ready(function () {
    var tracks = player.textTracks();
    for (var i = 0; i < tracks.length; i++) {
      if (tracks[i].language === preferredLang) {
        tracks[i].mode = "showing";
      } else if (tracks[i].kind === "subtitles") {
        tracks[i].mode = "disabled";
      }
    }

    tracks.addEventListener("change", function () {
      for (var i = 0; i < tracks.length; i++) {
        if (tracks[i].kind === "subtitles" && tracks[i].mode === "showing") {
          localStorage.setItem("subtitle_lang", tracks[i].language);
          return;
        }
      }
    });
  });
})();
