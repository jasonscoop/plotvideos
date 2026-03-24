import { t, LANGUAGES, langPrefix, nativeName, isRtl, type LangCode } from "./i18n";

const GLOBAL_CSS = `
<link href="/styles.css" rel="stylesheet" />
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet" />
`;

const CHEVRON_SVG = `<svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>`;

function langDropdown(currentLang: string, currentPath: string) {
  const items = LANGUAGES.map((l) => {
    const prefix = l.code === "en" ? "" : `/${l.code}`;
    const cleanPath = currentPath.replace(/^\/(en|de|fr|nl|ja|ko|pt|ar|es|zh)(\/|$)/, "/");
    const href = prefix + (cleanPath === "/" ? "/" : cleanPath);
    const active = l.code === currentLang ? ' class="active"' : "";
    return `<a href="${href}"${active}>${l.native}</a>`;
  }).join("");

  return `
    <div class="yt-lang-wrap" id="lang-dropdown">
      <button class="yt-lang-btn" type="button">${nativeName(currentLang)} ${CHEVRON_SVG}</button>
      <div class="yt-lang-menu">${items}</div>
    </div>
    <script>
      (function(){
        var w=document.getElementById('lang-dropdown'), b=w.querySelector('.yt-lang-btn');
        b.onclick=function(e){e.stopPropagation();w.classList.toggle('open')};
        document.addEventListener('click',function(){w.classList.remove('open')});
      })();
    </script>`;
}

export function layout(title: string, lang: string, content: string, q = "", path = "/") {
  const prefix = langPrefix(lang);
  const dir = isRtl(lang) ? ' dir="rtl"' : "";
  return `<!DOCTYPE html>
<html lang="${lang}"${dir}>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <link href="https://cdn.jsdelivr.net/npm/video.js@8/dist/video-js.min.css" rel="stylesheet" />
  ${GLOBAL_CSS}
</head>
<body>
  <header class="yt-header">
    <a href="${prefix}/" class="yt-logo"><span class="yt-logo-icon"></span> LuckVideos</a>
    <form action="${prefix}/" method="get" class="yt-search">
      <input type="text" name="q" value="${esc(q)}" placeholder="${t(lang, "search_placeholder")}" />
      <button type="submit">${t(lang, "search")}</button>
    </form>
    ${langDropdown(lang, path)}
  </header>
  ${content}
</body>
</html>`;
}

export function fmtDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

interface VideoCard {
  id: number;
  slug?: string;
  title: string;
  duration: number;
  thumbnail_url: string;
}

interface TagItem {
  tag: string;
  count: number;
}

export function indexPage(
  lang: string,
  videos: VideoCard[],
  page: number,
  totalPages: number,
  total: number,
  q: string,
  topTags: TagItem[] = []
) {
  const prefix = langPrefix(lang);
  const qParam = q ? `&q=${encodeURIComponent(q)}` : "";

  const sidebarItems = topTags
    .map((tg) => {
      const active = q === tg.tag ? " active" : "";
      return `<a href="${prefix}/?q=${encodeURIComponent(tg.tag)}" class="yt-nav-item${active}" title="${esc(tg.tag)}">${esc(tg.tag)}</a>`;
    })
    .join("");

  const sidebar = topTags.length
    ? `<nav class="yt-home-sidebar">
        <a href="${prefix}/" class="yt-nav-item${!q ? " active" : ""}">🏠 ${t(lang, "latest_videos")}</a>
        <div class="yt-nav-heading">Tags</div>
        ${sidebarItems}
      </nav>`
    : "";

  const cards = videos
    .map(
      (v) => `
    <a href="${prefix}${v.slug ? `/video/${v.slug}.html` : `/videos/${v.id}`}" class="yt-card">
      <div class="yt-thumb">
        ${
          v.thumbnail_url
            ? `<img src="${esc(v.thumbnail_url)}" alt="${esc(v.title)}" loading="lazy" />`
            : `<div class="yt-thumb-empty">${t(lang, "no_thumbnail")}</div>`
        }
        ${v.duration ? `<span class="yt-duration">${fmtDuration(v.duration)}</span>` : ""}
      </div>
      <div class="yt-card-meta">
        <div class="yt-card-title">${esc(v.title)}</div>
      </div>
    </a>`
    )
    .join("");

  const pagination = `
    <div class="yt-pagination">
      ${page > 1 ? `<a href="${prefix}/?page=${page - 1}${qParam}">${t(lang, "previous")}</a>` : ""}
      <span class="yt-page-info">${page} / ${totalPages} &middot; ${total} ${t(lang, "videos")}</span>
      ${page < totalPages ? `<a href="${prefix}/?page=${page + 1}${qParam}">${t(lang, "next")}</a>` : ""}
    </div>`;

  const main = videos.length
    ? `<div class="yt-home-main"><div class="yt-grid">${cards}</div>${pagination}</div>`
    : `<div class="yt-home-main" style="padding:48px 0;color:var(--yt-text2)">${t(lang, "no_videos")}</div>`;

  const content = `<div class="yt-home">${sidebar}${main}</div>`;

  return layout("LuckVideos", lang, content, q, "/");
}

interface WatchData {
  id: number;
  slug?: string;
  title: string;
  original_title: string;
  duration: number;
  thumbnail_url: string;
  video_url: string;
  hls_url: string;
  keyword: string;
  tags: string[];
  categories: string[];
}

interface SubTrack {
  lang: string;
  label: string;
  url: string;
  isDefault: boolean;
}

interface RecommendedVideo {
  id: number;
  slug?: string;
  title: string;
  duration: number;
  thumbnail_url: string;
}

export function watchPage(lang: string, video: WatchData, subtitleTracks: SubTrack[], recommended: RecommendedVideo[] = []) {
  const prefix = langPrefix(lang);

  const tracks = subtitleTracks
    .map(
      (t) =>
        `<track kind="subtitles" src="${esc(t.url)}" srclang="${esc(t.lang)}" label="${esc(t.label)}"${t.isDefault ? " default" : ""} />`
    )
    .join("\n        ");

  const hlsSrc = video.hls_url
    ? `{ src: ${JSON.stringify(video.hls_url)}, type: 'application/x-mpegURL' }`
    : "";
  const mp4Src = video.video_url
    ? `{ src: ${JSON.stringify(video.video_url)}, type: 'video/mp4' }`
    : "";
  const sources = [hlsSrc, mp4Src].filter(Boolean).join(", ");

  const allTags = [
    ...(video.keyword ? [video.keyword] : []),
    ...video.categories,
    ...video.tags,
  ];
  const tagsHtml = allTags
    .map((tag) => `<a class="yt-tag" href="${prefix}/?q=${encodeURIComponent(tag)}">#${esc(tag)}</a>`)
    .join("");

  return layout(
    `${video.title} - LuckVideos`,
    lang,
    `
  <div class="yt-watch">
    <div class="yt-watch-main">
      <div class="yt-player-wrap">
        <video
          id="video-player"
          class="video-js vjs-big-play-centered"
          controls
          preload="auto"
          crossorigin="anonymous"
          poster="${esc(video.thumbnail_url)}"
        >
          ${tracks}
        </video>
      </div>

      <h1 class="yt-title">${esc(video.title)}</h1>

      <div class="yt-meta-row">
        ${video.duration ? `<span>${fmtDuration(video.duration)}</span>` : ""}
        ${subtitleTracks.length ? `<span>&middot;</span><span>${subtitleTracks.length} ${t(lang, "subtitles")}</span>` : ""}
      </div>

      ${tagsHtml ? `<div style="margin-top:12px">${tagsHtml}</div>` : ""}
    </div>
    <div class="yt-watch-sidebar">
      <div class="yt-transcript" id="transcript-panel" style="display:none">
        <div class="yt-transcript-header" onclick="var p=document.getElementById('transcript-panel');p.classList.toggle('collapsed');localStorage.setItem('transcript_hidden',p.classList.contains('collapsed')?'1':'0')">
          <span>Transcript</span>
          <span class="yt-transcript-toggle">&#9650;</span>
        </div>
        <div class="yt-transcript-list" id="transcript-list"></div>
      </div>
    </div>
  </div>
  ${recommended.length ? `<h2 class="yt-recommended-title">${t(lang, "recommended")}</h2>` : ""}
  <div class="yt-recommended">
    ${recommended.map((r) => `
      <a href="${prefix}${r.slug ? `/video/${r.slug}.html` : `/videos/${r.id}`}" class="yt-card">
        <div class="yt-thumb">
          ${r.thumbnail_url ? `<img src="${esc(r.thumbnail_url)}" alt="${esc(r.title)}" loading="lazy" />` : ""}
          ${r.duration ? `<span class="yt-duration">${fmtDuration(r.duration)}</span>` : ""}
        </div>
        <div class="yt-card-meta">
          <div class="yt-card-title">${esc(r.title)}</div>
        </div>
      </a>`).join("")}
  </div>
  <script>
  (function(){
    function syncTranscript(){
      var p=document.querySelector('.yt-player-wrap'), t=document.getElementById('transcript-panel');
      if(p&&t) t.style.height=p.offsetHeight+'px';
    }
    syncTranscript();
    window.addEventListener('resize',syncTranscript);
  })();
  </script>
  <script src="https://cdn.jsdelivr.net/npm/video.js@8/dist/video.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@4/dist/videojs-contrib-quality-levels.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@2.0.0/dist/videojs-hls-quality-selector.min.js"></script>
  <link href="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@2.0.0/dist/videojs-hls-quality-selector.css" rel="stylesheet" />
  <script>
  (function(){
    var pageLang = ${JSON.stringify(lang)};
    var player = videojs('video-player', {
      fluid: false,
      responsive: true,
      playbackRates: [0.5, 1, 1.25, 1.5, 2],
      html5: {
        vhs: { overrideNative: !videojs.browser.IS_SAFARI }
      },
      sources: [${sources}]
    });
    player.hlsQualitySelector({ displayCurrentQuality: true });

    var savedLang = localStorage.getItem('subtitle_lang');
    var preferredLang = savedLang || pageLang;
    var subMap = ${JSON.stringify(Object.fromEntries(subtitleTracks.map((st) => [st.lang, st.url])))};

    function parseVTT(text) {
      var cues = [], blocks = text.split(/\\n\\n+/);
      for (var i = 0; i < blocks.length; i++) {
        var lines = blocks[i].trim().split('\\n');
        for (var j = 0; j < lines.length; j++) {
          var m = lines[j].match(/(\\d{2}:\\d{2}[:\\.]\\d{2,3})\\s*-->\\s*(\\d{2}:\\d{2}[:\\.]\\d{2,3})/);
          if (m) {
            var txt = lines.slice(j + 1).join(' ').replace(/<[^>]+>/g, '').trim();
            if (txt) cues.push({ start: toSec(m[1]), end: toSec(m[2]), text: txt });
            break;
          }
        }
      }
      return cues;
    }
    function toSec(t) {
      var p = t.replace('.', ':').split(':');
      if (p.length === 3) return +p[0]*60 + +p[1] + +p[2]/1000;
      return +p[0]*3600 + +p[1]*60 + +p[2] + +(p[3]||0)/1000;
    }
    function fmtTime(s) {
      var m = Math.floor(s/60), sec = Math.floor(s%60);
      return m + ':' + (sec<10?'0':'') + sec;
    }
    function renderTranscript(cues) {
      var panel = document.getElementById('transcript-panel');
      var list = document.getElementById('transcript-list');
      panel.style.display = '';
      if (localStorage.getItem('transcript_hidden') === '1') panel.classList.add('collapsed');
      else panel.classList.remove('collapsed');
      list.innerHTML = cues.map(function(c, i){
        return '<div class="yt-cue" data-idx="'+i+'" data-start="'+c.start+'"><span class="yt-cue-time">'+fmtTime(c.start)+'</span><span class="yt-cue-text">'+c.text+'</span></div>';
      }).join('');
      list.onclick = function(e){
        var el = e.target.closest('.yt-cue');
        if (el) player.currentTime(+el.dataset.start);
      };
      window._transcriptCues = cues;
    }
    function fetchVTT(url) {
      return fetch(url).then(function(r){
        if (!r.ok) throw new Error(r.status);
        return r.text();
      }).then(function(text){
        var cues = parseVTT(text);
        if (!cues.length) throw new Error('empty');
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
      if (!urls.length) { document.getElementById('transcript-panel').style.display='none'; return; }
      (function tryNext(idx) {
        if (idx >= urls.length) { document.getElementById('transcript-panel').style.display='none'; return; }
        fetchVTT(urls[idx]).then(renderTranscript).catch(function(){ tryNext(idx + 1); });
      })(0);
    }

    player.ready(function(){
      var tracks = player.textTracks();
      for (var i = 0; i < tracks.length; i++) {
        if (tracks[i].language === preferredLang) {
          tracks[i].mode = 'showing';
        } else if (tracks[i].kind === 'subtitles') {
          tracks[i].mode = 'disabled';
        }
      }

      loadTranscript(preferredLang);

      tracks.addEventListener('change', function(){
        for (var i = 0; i < tracks.length; i++) {
          if (tracks[i].kind === 'subtitles' && tracks[i].mode === 'showing') {
            localStorage.setItem('subtitle_lang', tracks[i].language);
            loadTranscript(tracks[i].language);
            return;
          }
        }
      });

      player.on('timeupdate', function(){
        var cues = window._transcriptCues;
        if (!cues) return;
        var ct = player.currentTime(), els = document.querySelectorAll('.yt-cue');
        var activeIdx = -1;
        for (var i = 0; i < cues.length; i++) {
          if (ct >= cues[i].start && ct < cues[i].end) { activeIdx = i; break; }
        }
        for (var i = 0; i < els.length; i++) {
          els[i].classList.toggle('active', i === activeIdx);
        }
        if (activeIdx >= 0 && els[activeIdx]) {
          els[activeIdx].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      });
    });
  })();
  </script>`,
    "",
    video.slug ? `/video/${video.slug}.html` : `/videos/${video.id}`
  );
}
