(function () {
  function syncTranscriptPanelHeight() {
    var p = document.querySelector(".yt-player-wrap");
    var t = document.getElementById("transcript-panel");
    if (p && t) t.style.height = p.offsetHeight + "px";
  }

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
  var subMap = cfg.subMap || {};

  syncTranscriptPanelHeight();
  window.addEventListener("resize", syncTranscriptPanelHeight);

  var transcriptToggle = document.getElementById("transcript-panel-toggle");
  function toggleTranscriptCollapsed() {
    var p = document.getElementById("transcript-panel");
    if (!p) return;
    p.classList.toggle("collapsed");
    localStorage.setItem("transcript_hidden", p.classList.contains("collapsed") ? "1" : "0");
  }
  if (transcriptToggle) {
    transcriptToggle.addEventListener("click", toggleTranscriptCollapsed);
    transcriptToggle.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        toggleTranscriptCollapsed();
      }
    });
  }

  if (typeof videojs === "undefined") return;

  var player = videojs("video-player", {
    fluid: false,
    responsive: true,
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    html5: {
      vhs: { overrideNative: !videojs.browser.IS_SAFARI },
    },
    sources: sources,
  });
  player.hlsQualitySelector({ displayCurrentQuality: true });

  var savedLang = localStorage.getItem("subtitle_lang");
  var preferredLang = savedLang || pageLang;

  function parseVTT(text) {
    var cues = [],
      blocks = text.split(/\n\n+/);
    for (var i = 0; i < blocks.length; i++) {
      var lines = blocks[i].trim().split("\n");
      for (var j = 0; j < lines.length; j++) {
        var m = lines[j].match(
          /(\d{2}:\d{2}[.:]\d{2,3})\s*-->\s*(\d{2}:\d{2}[.:]\d{2,3})/
        );
        if (m) {
          var txt = lines
            .slice(j + 1)
            .join(" ")
            .replace(/<[^>]+>/g, "")
            .trim();
          if (txt) cues.push({ start: toSec(m[1]), end: toSec(m[2]), text: txt });
          break;
        }
      }
    }
    return cues;
  }
  function toSec(t) {
    var p = t.replace(".", ":").split(":");
    if (p.length === 3) return +p[0] * 60 + +p[1] + +p[2] / 1000;
    return +p[0] * 3600 + +p[1] * 60 + +p[2] + +(p[3] || 0) / 1000;
  }
  function fmtTime(s) {
    var m = Math.floor(s / 60),
      sec = Math.floor(s % 60);
    return m + ":" + (sec < 10 ? "0" : "") + sec;
  }
  function renderTranscript(cues) {
    var panel = document.getElementById("transcript-panel");
    var list = document.getElementById("transcript-list");
    if (!panel || !list) return;
    panel.style.display = "";
    if (localStorage.getItem("transcript_hidden") === "1") panel.classList.add("collapsed");
    else panel.classList.remove("collapsed");
    list.innerHTML = cues
      .map(function (c, i) {
        return (
          '<div class="yt-cue" data-idx="' +
          i +
          '" data-start="' +
          c.start +
          '"><span class="yt-cue-time">' +
          fmtTime(c.start) +
          '</span><span class="yt-cue-text">' +
          c.text +
          "</span></div>"
        );
      })
      .join("");
    list.onclick = function (e) {
      var el = e.target.closest(".yt-cue");
      if (el) player.currentTime(+el.dataset.start);
    };
    window._transcriptCues = cues;
  }
  function fetchVTT(url) {
    return fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error(String(r.status));
        return r.text();
      })
      .then(function (text) {
        var cues = parseVTT(text);
        if (!cues.length) throw new Error("empty");
        return cues;
      });
  }
  function loadTranscript(lang) {
    var urls = [];
    if (subMap[lang]) urls.push(subMap[lang]);
    var keys = Object.keys(subMap);
    for (var i = 0; i < keys.length; i++) {
      if (keys[i] !== lang && subMap[keys[i]]) urls.push(subMap[keys[i]]);
    }
    var panel = document.getElementById("transcript-panel");
    if (!urls.length) {
      if (panel) panel.style.display = "none";
      return;
    }
    (function tryNext(idx) {
      if (idx >= urls.length) {
        if (panel) panel.style.display = "none";
        return;
      }
      fetchVTT(urls[idx])
        .then(renderTranscript)
        .catch(function () {
          tryNext(idx + 1);
        });
    })(0);
  }

  player.ready(function () {
    var tracks = player.textTracks();
    for (var i = 0; i < tracks.length; i++) {
      if (tracks[i].language === preferredLang) {
        tracks[i].mode = "showing";
      } else if (tracks[i].kind === "subtitles") {
        tracks[i].mode = "disabled";
      }
    }

    loadTranscript(preferredLang);

    tracks.addEventListener("change", function () {
      for (var i = 0; i < tracks.length; i++) {
        if (tracks[i].kind === "subtitles" && tracks[i].mode === "showing") {
          localStorage.setItem("subtitle_lang", tracks[i].language);
          loadTranscript(tracks[i].language);
          return;
        }
      }
    });

    player.on("timeupdate", function () {
      var cues = window._transcriptCues;
      if (!cues) return;
      var ct = player.currentTime(),
        els = document.querySelectorAll(".yt-cue");
      var activeIdx = -1;
      for (var i = 0; i < cues.length; i++) {
        if (ct >= cues[i].start && ct < cues[i].end) {
          activeIdx = i;
          break;
        }
      }
      for (var j = 0; j < els.length; j++) {
        els[j].classList.toggle("active", j === activeIdx);
      }
      if (activeIdx >= 0 && els[activeIdx]) {
        els[activeIdx].scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    });
  });
})();
