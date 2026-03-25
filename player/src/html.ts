import { t, LANGUAGES, langPrefix, nativeName, isRtl } from "./i18n";

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
    <div class="yt-lang-wrap">
      <button class="yt-lang-btn" type="button">${nativeName(currentLang)} ${CHEVRON_SVG}</button>
      <div class="yt-lang-menu">${items}</div>
    </div>`;
}

export function layout(
  title: string,
  lang: string,
  content: string,
  q = "",
  path = "/",
  opts?: { playerAssets?: boolean }
) {
  const prefix = langPrefix(lang);
  const dir = isRtl(lang) ? ' dir="rtl"' : "";
  const playerCss = opts?.playerAssets
    ? `<link href="https://cdn.jsdelivr.net/npm/video.js@8/dist/video-js.min.css" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@2.0.0/dist/videojs-hls-quality-selector.css" rel="stylesheet" />`
    : "";
  return `<!DOCTYPE html>
<html lang="${lang}"${dir}>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  ${playerCss}
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
  <script src="/lang-dropdown.js" defer></script>
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

/** Safe embedding of JSON inside a `<script type="application/json">` block. */
export function escJsonForScript(obj: unknown): string {
  return JSON.stringify(obj).replace(/</g, "\\u003c");
}

function videoWatchPath(v: { id: number; slug?: number | null }): string {
  if (v.slug == null) return `/videos/${v.id}`;
  const n = Number(v.slug);
  if (!Number.isFinite(n)) return `/videos/${v.id}`;
  return `/video/${Math.trunc(n)}.html`;
}

interface VideoCard {
  id: number;
  slug?: number | null;
  title: string;
  duration: number;
  thumbnail_url: string;
}

interface TagItem {
  tag: string;
  count: number;
}

function homeSidebar(lang: string, prefix: string, q: string, topTags: TagItem[]): string {
  if (!topTags.length) return "";
  const sidebarItems = topTags
    .map((tg) => {
      const active = q === tg.tag ? " active" : "";
      return `<a href="${prefix}/?q=${encodeURIComponent(tg.tag)}" class="yt-nav-item${active}" title="${esc(tg.tag)}">${esc(tg.tag)}</a>`;
    })
    .join("");
  return `<nav class="yt-home-sidebar">
        <a href="${prefix}/" class="yt-nav-item${!q ? " active" : ""}">🏠 ${t(lang, "latest_videos")}</a>
        <div class="yt-nav-heading">Tags</div>
        ${sidebarItems}
      </nav>`;
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

  const sidebar = homeSidebar(lang, prefix, q, topTags);

  const cards = videos
    .map(
      (v) => `
    <a href="${prefix}${videoWatchPath(v)}" class="yt-card">
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
  slug?: number | null;
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
  slug?: number | null;
  title: string;
  duration: number;
  thumbnail_url: string;
}

export function watchPage(
  lang: string,
  video: WatchData,
  subtitleTracks: SubTrack[],
  recommended: RecommendedVideo[] = [],
  topTags: TagItem[] = []
) {
  const prefix = langPrefix(lang);
  const sidebar = homeSidebar(lang, prefix, "", topTags);

  const tracks = subtitleTracks
    .map(
      (tr) =>
        `<track kind="subtitles" src="${esc(tr.url)}" srclang="${esc(tr.lang)}" label="${esc(tr.label)}"${tr.isDefault ? " default" : ""} />`
    )
    .join("\n        ");

  const allTags = [
    ...(video.keyword ? [video.keyword] : []),
    ...video.categories,
    ...video.tags,
  ];
  const tagsHtml = allTags
    .map((tag) => `<a class="yt-tag" href="${prefix}/?q=${encodeURIComponent(tag)}">#${esc(tag)}</a>`)
    .join("");

  const watchConfig = {
    pageLang: lang,
    sources: [
      ...(video.hls_url
        ? [{ src: video.hls_url, type: "application/x-mpegURL" as const }]
        : []),
      ...(video.video_url ? [{ src: video.video_url, type: "video/mp4" as const }] : []),
    ],
    subMap: Object.fromEntries(subtitleTracks.map((st) => [st.lang, st.url])),
  };

  const watchBody = `
  <div class="yt-watch">
    <div class="yt-watch-main">
      <div class="yt-player-wrap">
        <video
          id="video-player"
          class="video-js vjs-big-play-centered"
          controls
          preload="auto"
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
        <div class="yt-transcript-header" id="transcript-panel-toggle" role="button" tabindex="0">
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
      <a href="${prefix}${videoWatchPath(r)}" class="yt-card">
        <div class="yt-thumb">
          ${r.thumbnail_url ? `<img src="${esc(r.thumbnail_url)}" alt="${esc(r.title)}" loading="lazy" />` : ""}
          ${r.duration ? `<span class="yt-duration">${fmtDuration(r.duration)}</span>` : ""}
        </div>
        <div class="yt-card-meta">
          <div class="yt-card-title">${esc(r.title)}</div>
        </div>
      </a>`).join("")}
  </div>
  <script type="application/json" id="watch-page-config">${escJsonForScript(watchConfig)}</script>
  <script src="https://cdn.jsdelivr.net/npm/video.js@8/dist/video.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@4/dist/videojs-contrib-quality-levels.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@2.0.0/dist/videojs-hls-quality-selector.min.js"></script>
  <script src="/watch-page.js" defer></script>`;

  const content = `<div class="yt-home">${sidebar}<div class="yt-home-main yt-watch-page-main">${watchBody}</div></div>`;

  return layout(`${video.title} - LuckVideos`, lang, content, "", videoWatchPath(video), {
    playerAssets: true,
  });
}
