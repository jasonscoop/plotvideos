import { t, LANGUAGES, langPrefix, nativeName, isRtl, type LangCode } from "./i18n";

const GLOBAL_CSS = `
<style>
  :root { --yt-bg: #0f0f0f; --yt-surface: #272727; --yt-hover: #3f3f3f; --yt-border: #3f3f3f; --yt-text: #f1f1f1; --yt-text2: #aaa; --yt-blue: #3ea6ff; }
  * { box-sizing: border-box; }
  body { background: var(--yt-bg); color: var(--yt-text); font-family: Roboto, Arial, sans-serif; margin: 0; min-height: 100vh; }
  a { color: inherit; text-decoration: none; }

  .yt-header { position: sticky; top: 0; z-index: 200; background: var(--yt-bg); border-bottom: 1px solid var(--yt-border); height: 56px; display: flex; align-items: center; padding: 0 16px; gap: 8px; }
  .yt-logo { display: flex; align-items: center; gap: 4px; font-size: 18px; font-weight: 700; white-space: nowrap; }
  .yt-logo-icon { width: 32px; height: 22px; background: #f00; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
  .yt-logo-icon::after { content: ''; width: 0; height: 0; border-style: solid; border-width: 6px 0 6px 10px; border-color: transparent transparent transparent #fff; }
  .yt-search { flex: 1; max-width: 540px; margin: 0 auto; display: flex; }
  .yt-search input { flex: 1; background: var(--yt-bg); border: 1px solid var(--yt-border); border-radius: 20px 0 0 20px; padding: 6px 16px; color: var(--yt-text); font-size: 14px; outline: none; }
  .yt-search input:focus { border-color: var(--yt-blue); }
  .yt-search button { background: var(--yt-surface); border: 1px solid var(--yt-border); border-left: 0; border-radius: 0 20px 20px 0; padding: 0 20px; cursor: pointer; color: var(--yt-text); font-size: 14px; }
  .yt-search button:hover { background: var(--yt-hover); }

  .yt-lang-wrap { position: relative; }
  .yt-lang-btn { background: var(--yt-surface); border: 1px solid var(--yt-border); border-radius: 20px; padding: 6px 14px; color: var(--yt-text); font-size: 13px; cursor: pointer; white-space: nowrap; display: flex; align-items: center; gap: 4px; }
  .yt-lang-btn:hover { background: var(--yt-hover); }
  .yt-lang-btn svg { width: 12px; height: 12px; fill: var(--yt-text2); }
  .yt-lang-menu { display: none; position: absolute; top: 100%; right: 0; margin-top: 4px; background: var(--yt-surface); border: 1px solid var(--yt-border); border-radius: 12px; padding: 8px 0; min-width: 160px; z-index: 100; box-shadow: 0 4px 16px rgba(0,0,0,.4); max-height: calc(100vh - 70px); overflow-y: auto; }
  .yt-lang-wrap.open .yt-lang-menu { display: block; }
  .yt-lang-menu a { display: block; padding: 8px 16px; font-size: 13px; color: var(--yt-text); }
  .yt-lang-menu a:hover { background: var(--yt-hover); }
  .yt-lang-menu a.active { color: var(--yt-blue); }

  .yt-home { max-width: 1400px; margin: 0 auto; padding: 0 24px; display: flex; gap: 0; }
  .yt-home-sidebar { width: 200px; flex-shrink: 0; position: sticky; top: 56px; height: calc(100vh - 56px); overflow-y: auto; padding: 12px 0; border-right: 1px solid var(--yt-border); }
  .yt-home-sidebar::-webkit-scrollbar { width: 4px; }
  .yt-home-sidebar::-webkit-scrollbar-thumb { background: var(--yt-hover); border-radius: 2px; }
  .yt-home-main { flex: 1; min-width: 0; padding-left: 24px; }
  .yt-nav-item { display: block; padding: 8px 12px; font-size: 13px; color: var(--yt-text); border-radius: 8px; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .yt-nav-item:hover { background: var(--yt-surface); }
  .yt-nav-item.active { background: var(--yt-surface); color: var(--yt-blue); font-weight: 500; }
  .yt-nav-heading { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--yt-text2); padding: 16px 12px 6px; }
  .yt-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; padding: 24px 0; }
  .yt-card { display: block; cursor: pointer; }
  .yt-card:hover .yt-card-title { color: var(--yt-text); }
  .yt-thumb { position: relative; width: 100%; padding-bottom: 56.25%; background: #181818; border-radius: 12px; overflow: hidden; }
  .yt-thumb img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
  .yt-thumb-empty { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #555; font-size: 13px; }
  .yt-duration { position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,.8); color: #fff; font-size: 12px; font-weight: 500; padding: 2px 6px; border-radius: 4px; letter-spacing: .5px; }
  .yt-card-meta { padding: 12px 0 0; }
  .yt-card-title { font-size: 14px; font-weight: 500; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin: 0 0 4px; color: var(--yt-text); }
  .yt-card-sub { font-size: 12px; color: var(--yt-text2); line-height: 1.5; }

  .yt-pagination { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 16px 0 32px; }
  .yt-pagination a, .yt-pagination span { font-size: 13px; padding: 8px 16px; border-radius: 20px; }
  .yt-pagination a { background: var(--yt-surface); color: var(--yt-text); }
  .yt-pagination a:hover { background: var(--yt-hover); }
  .yt-pagination .yt-page-info { color: var(--yt-text2); }

  .yt-watch { max-width: 1400px; margin: 0 auto; padding: 24px 24px 48px; display: flex; gap: 24px; align-items: flex-start; }
  .yt-watch-main { flex: 1; min-width: 0; }
  .yt-watch-sidebar { width: 400px; flex-shrink: 0; display: flex; flex-direction: column; overflow: hidden; }
  .yt-sidebar-card { display: flex; gap: 8px; flex: 1; cursor: pointer; border-radius: 8px; padding: 4px; }
  .yt-sidebar-card:hover { background: var(--yt-surface); }
  .yt-sidebar-thumb { position: relative; width: 168px; min-width: 168px; aspect-ratio: 16/9; background: #181818; border-radius: 8px; overflow: hidden; }
  .yt-sidebar-thumb img { width: 100%; height: 100%; object-fit: cover; }
  .yt-sidebar-dur { position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,.8); color: #fff; font-size: 11px; font-weight: 500; padding: 1px 4px; border-radius: 3px; }
  .yt-sidebar-info { flex: 1; min-width: 0; padding-top: 2px; }
  .yt-sidebar-title { font-size: 13px; font-weight: 500; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; color: var(--yt-text); margin: 0; }
  .yt-sidebar-sub { font-size: 12px; color: var(--yt-text2); margin-top: 4px; }
  .yt-player-wrap { width: 100%; aspect-ratio: 4/3; border-radius: 12px; overflow: hidden; background: #000; min-height: 360px; max-height: 500px; margin: 0 auto; }
  .video-js .vjs-menu .vjs-menu-content { max-height: 250px; overflow-y: auto; }
  .video-js { width: 100% !important; height: 100% !important; }
  .video-js .vjs-poster { background-size: cover; }
  .video-js .vjs-big-play-button { top: 50%; left: 50%; transform: translate(-50%,-50%); width: 68px; height: 48px; background: rgba(255,0,0,.85); border: none; border-radius: 14px; line-height: 48px; font-size: 24px; transition: background .15s, opacity .15s; }
  .video-js:hover .vjs-big-play-button { background: rgba(255,0,0,1); }
  .video-js .vjs-big-play-button .vjs-icon-placeholder::before { font-size: 28px; }
  .video-js .vjs-control-bar { height: 38px; font-size: 13px; }
  .video-js .vjs-control { width: 38px; }
  .video-js .vjs-time-control { font-size: 12px; line-height: 38px; padding: 0 5px; }
  .video-js .vjs-progress-control { height: 38px; }
  .video-js .vjs-progress-holder { height: 3px; }
  .video-js .vjs-play-progress, .video-js .vjs-load-progress { height: 100%; }
  .video-js .vjs-progress-holder:hover { height: 5px; }
  .video-js .vjs-icon-placeholder::before { font-size: 18px; line-height: 38px; }
  .video-js .vjs-playback-rate .vjs-playback-rate-value { font-size: 12px; line-height: 38px; }
  .yt-title { font-size: 20px; font-weight: 600; line-height: 1.4; margin: 16px 0 0; }
  .yt-meta-row { display: flex; align-items: center; gap: 12px; margin: 8px 0 0; font-size: 13px; color: var(--yt-text2); flex-wrap: wrap; }
  .yt-desc-box { background: var(--yt-surface); border-radius: 12px; padding: 12px 16px; margin: 16px 0 0; font-size: 13px; line-height: 1.6; }
  .yt-tag { display: inline-block; background: rgba(255,255,255,.1); border-radius: 8px; padding: 4px 12px; margin: 2px 4px 2px 0; font-size: 12px; color: var(--yt-blue); }
  .yt-tag:hover { background: rgba(255,255,255,.2); }
  .yt-original { font-size: 13px; color: var(--yt-text2); margin: 4px 0 0; }

  @media (max-width: 1024px) {
    .yt-watch { flex-direction: column; padding: 16px 16px 32px; align-items: center; }
    .yt-watch-main { width: 100%; max-width: 720px; }
    .yt-watch-sidebar { width: 100%; max-width: 720px; flex-direction: row; overflow-x: auto; gap: 12px; height: auto !important; }
    .yt-sidebar-card { flex: 0 0 200px; flex-direction: column; }
    .yt-sidebar-thumb { width: 100%; min-width: 100%; }
    .yt-player-wrap { max-height: none; aspect-ratio: 16/9; }
    .yt-home-sidebar { display: none; }
    .yt-home-main { padding-left: 0; }
  }
  @media (max-width: 640px) {
    .yt-grid { grid-template-columns: 1fr; gap: 12px; }
    .yt-search { max-width: none; margin: 0 0 0 12px; }
    .yt-watch { padding: 0 0 32px; gap: 16px; }
    .yt-player-wrap { border-radius: 0; min-height: 200px; }
    .yt-title { padding: 0 12px; font-size: 16px; }
    .yt-meta-row { padding: 0 12px; }
    .yt-desc-box { margin: 0 12px; }
    .yt-watch-sidebar { padding: 0 12px; }
    .yt-sidebar-card { flex: 0 0 160px; }
  }
</style>
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
    <a href="${prefix}/videos/${v.id}" class="yt-card">
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
    .map((tag) => `<a class="yt-tag" href="${prefix}/?q=${encodeURIComponent(tag)}">${esc(tag)}</a>`)
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
      ${video.original_title && video.original_title !== video.title ? `<p class="yt-original">${t(lang, "original")}: ${esc(video.original_title)}</p>` : ""}

      <div class="yt-meta-row">
        ${video.duration ? `<span>${fmtDuration(video.duration)}</span>` : ""}
        ${subtitleTracks.length ? `<span>&middot;</span><span>${subtitleTracks.length} ${t(lang, "subtitles")}</span>` : ""}
      </div>

      ${tagsHtml ? `<div class="yt-desc-box">${tagsHtml}</div>` : ""}
    </div>
    <div class="yt-watch-sidebar">
      ${recommended.map((r) => `
        <a href="${prefix}/videos/${r.id}" class="yt-sidebar-card">
          <div class="yt-sidebar-thumb">
            ${r.thumbnail_url ? `<img src="${esc(r.thumbnail_url)}" alt="${esc(r.title)}" loading="lazy" />` : ""}
            ${r.duration ? `<span class="yt-sidebar-dur">${fmtDuration(r.duration)}</span>` : ""}
          </div>
          <div class="yt-sidebar-info">
            <p class="yt-sidebar-title">${esc(r.title)}</p>
          </div>
        </a>`).join("")}
    </div>
  </div>
  <script>
  (function(){
    function syncHeight(){
      var p=document.querySelector('.yt-player-wrap'), s=document.querySelector('.yt-watch-sidebar');
      if(p&&s) s.style.height=p.offsetHeight+'px';
    }
    syncHeight();
    window.addEventListener('resize',syncHeight);
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

    player.ready(function(){
      var tracks = player.textTracks();
      for (var i = 0; i < tracks.length; i++) {
        if (tracks[i].language === preferredLang) {
          tracks[i].mode = 'showing';
        } else if (tracks[i].kind === 'subtitles') {
          tracks[i].mode = 'disabled';
        }
      }

      tracks.addEventListener('change', function(){
        for (var i = 0; i < tracks.length; i++) {
          if (tracks[i].kind === 'subtitles' && tracks[i].mode === 'showing') {
            localStorage.setItem('subtitle_lang', tracks[i].language);
            break;
          }
        }
      });
    });
  })();
  </script>`,
    "",
    `/videos/${video.id}`
  );
}
