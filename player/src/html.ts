import { t, LANGUAGES, langPrefix, nativeName, isRtl } from "./i18n";
import { publicWatchSegmentFromVideoId } from "./slug";
import { DEFAULT_SITE_NAME } from "./site";
import type { VttCue } from "./vtt";

const GLOBAL_CSS = `
<link href="/styles.css" rel="stylesheet" />
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
  opts?: {
    playerAssets?: boolean;
    jsonLd?: string;
    siteName?: string;
    gaMeasurementId?: string;
    description?: string;
    origin?: string;
    hreflangPath?: string;
    ogImage?: string;
    noindex?: boolean;
  }
) {
  const brand = opts?.siteName?.trim() || DEFAULT_SITE_NAME;
  const prefix = langPrefix(lang);
  const dir = isRtl(lang) ? ' dir="rtl"' : "";
  const gaId = opts?.gaMeasurementId?.trim();
  const gaHead =
    gaId !== undefined && gaId !== ""
      ? `<script async src="https://www.googletagmanager.com/gtag/js?id=${esc(gaId)}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","${esc(gaId)}");</script>`
      : "";
  const playerCss = opts?.playerAssets
    ? `<link href="https://cdn.jsdelivr.net/npm/video.js@8/dist/video-js.min.css" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@2.0.0/dist/videojs-hls-quality-selector.css" rel="stylesheet" />`
    : "";
  const jsonLdTag = opts?.jsonLd
    ? `<script type="application/ld+json">${opts.jsonLd}</script>`
    : "";

  const desc = opts?.description?.trim();
  const descTag = desc ? `<meta name="description" content="${esc(desc)}" />` : "";

  const origin = opts?.origin;
  const canonicalUrl = origin ? `${origin}${prefix}${path}` : "";
  const canonicalTag = canonicalUrl ? `<link rel="canonical" href="${canonicalUrl}" />` : "";

  const hreflangTags = origin && opts?.hreflangPath
    ? LANGUAGES.map(
        (l) => `<link rel="alternate" hreflang="${l.code}" href="${origin}${langPrefix(l.code)}${opts.hreflangPath}" />`
      ).join("\n  ") +
      `\n  <link rel="alternate" hreflang="x-default" href="${origin}${opts.hreflangPath}" />`
    : "";

  const ogTags = origin
    ? [
        `<meta property="og:title" content="${esc(title)}" />`,
        desc ? `<meta property="og:description" content="${esc(desc)}" />` : "",
        `<meta property="og:url" content="${canonicalUrl}" />`,
        `<meta property="og:site_name" content="${esc(brand)}" />`,
        opts?.ogImage ? `<meta property="og:image" content="${esc(opts.ogImage)}" />` : "",
      ]
        .filter(Boolean)
        .join("\n  ")
    : "";

  const robotsTag = opts?.noindex ? `<meta name="robots" content="noindex, follow" />` : "";

  return `<!DOCTYPE html>
<html lang="${lang}"${dir}>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  ${descTag}
  ${robotsTag}
  ${canonicalTag}
  ${hreflangTags}
  ${ogTags}
  <link rel="icon" href="/logo.svg" type="image/svg+xml" />
  ${gaHead}
  ${jsonLdTag}
  ${playerCss}
  ${GLOBAL_CSS}
</head>
<body>
  <header class="yt-header">
    <button class="yt-menu-btn" type="button" aria-label="Menu"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"/></svg></button>
    <a href="${prefix}/" class="yt-logo"><img src="/logo.svg" alt="" class="yt-logo-icon" /> ${esc(brand)}</a>
    <form action="${prefix}/" method="get" class="yt-search">
      <input type="text" name="q" value="${esc(q)}" placeholder="${t(lang, "search_placeholder")}" />
      <button type="submit">${t(lang, "search")}</button>
    </form>
    <button class="yt-search-toggle" type="button" aria-label="Search"><svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zM9.5 14C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg></button>
    ${langDropdown(lang, path)}
  </header>
  ${content}
  <div class="yt-sidebar-overlay"></div>
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

function durationIso8601(seconds: number): string | undefined {
  if (!seconds || seconds <= 0) return undefined;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  let p = "PT";
  if (h) p += `${h}H`;
  if (m) p += `${m}M`;
  if (s || (!h && !m)) p += `${s}S`;
  return p;
}

function videoWatchPath(v: { id: number }, slugOffset: number): string {
  return `/video/${publicWatchSegmentFromVideoId(v.id, slugOffset)}.html`;
}

interface VideoCard {
  id: number;
  title: string;
  duration: number;
  thumbnail_url: string;
}

/** Sidebar navigation item (tag or category with URL slug). */
export interface NavTaxonomyItem {
  name: string;
  slug: string;
  count: number;
}

export type ActiveTaxonomy =
  | { kind: "tag"; slug: string }
  | { kind: "category"; slug: string }
  | null;

function tagPageHref(prefix: string, slug: string): string {
  return `${prefix}/tag/${slug}.html`;
}

function categoryPageHref(prefix: string, slug: string): string {
  return `${prefix}/category/${slug}.html`;
}

function homeSidebar(
  lang: string,
  prefix: string,
  navTags: NavTaxonomyItem[],
  navCategories: NavTaxonomyItem[],
  active: ActiveTaxonomy
): string {
  if (!navTags.length && !navCategories.length) return "";
  const homeActive = !active ? " active" : "";
  const tagItems = navTags
    .map((tg) => {
      const isActive = active?.kind === "tag" && active.slug === tg.slug ? " active" : "";
      return `<a href="${tagPageHref(prefix, tg.slug)}" class="yt-nav-item${isActive}" title="${esc(
        tg.name
      )}">${esc(tg.name)} <span class="yt-nav-count">${tg.count}</span></a>`;
    })
    .join("");
  const catItems = navCategories
    .map((cg) => {
      const isActive = active?.kind === "category" && active.slug === cg.slug ? " active" : "";
      return `<a href="${categoryPageHref(prefix, cg.slug)}" class="yt-nav-item${isActive}" title="${esc(
        cg.name
      )}">${esc(cg.name)} <span class="yt-nav-count">${cg.count}</span></a>`;
    })
    .join("");
  return `<nav class="yt-home-sidebar">
        <a href="${prefix}/" class="yt-nav-item${homeActive}">🏠 ${t(lang, "latest_videos")}</a>
        ${
          catItems
            ? `<div class="yt-nav-heading">${t(lang, "categories")}</div>
        ${catItems}`
            : ""
        }
        ${
          tagItems
            ? `<div class="yt-nav-heading">${t(lang, "tags")}</div>
        ${tagItems}`
            : ""
        }
      </nav>`;
}

export function indexPage(
  lang: string,
  videos: VideoCard[],
  page: number,
  hasNext: boolean,
  q: string,
  navTags: NavTaxonomyItem[] = [],
  navCategories: NavTaxonomyItem[] = [],
  activeTaxonomy: ActiveTaxonomy = null,
  slugOffset = 0,
  siteName: string,
  gaMeasurementId?: string,
  origin?: string
) {
  const prefix = langPrefix(lang);
  const qParam = q ? `&q=${encodeURIComponent(q)}` : "";

  const sidebar = homeSidebar(lang, prefix, navTags, navCategories, activeTaxonomy);

  const cards = videos
    .map(
      (v) => `
    <a href="${prefix}${videoWatchPath(v, slugOffset)}" class="yt-card">
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
      ${hasNext ? `<a href="${prefix}/?page=${page + 1}${qParam}">${t(lang, "next")}</a>` : ""}
    </div>`;

  const main = videos.length
    ? `<div class="yt-home-main"><div class="yt-grid">${cards}</div>${pagination}</div>`
    : `<div class="yt-home-main" style="padding:48px 0;color:var(--yt-text2)">${t(lang, "no_videos")}</div>`;

  const content = `<div class="yt-home">${sidebar}${main}</div>`;

  const pagePath = page > 1 ? `/?page=${page}` : "/";
  return layout(siteName, lang, content, q, pagePath, {
    siteName,
    gaMeasurementId,
    description: q ? undefined : `${siteName} - Watch the latest videos with subtitles`,
    origin,
    hreflangPath: q ? undefined : "/",
    noindex: !!q,
  });
}

export function taxonomyListingPage(
  lang: string,
  kind: "tag" | "category",
  taxName: string,
  taxSlug: string,
  videos: VideoCard[],
  page: number,
  hasNext: boolean,
  navTags: NavTaxonomyItem[],
  navCategories: NavTaxonomyItem[],
  browserTitle: string,
  currentPath: string,
  slugOffset = 0,
  siteName: string,
  gaMeasurementId?: string,
  origin?: string
) {
  const prefix = langPrefix(lang);
  const baseHref =
    kind === "tag" ? tagPageHref(prefix, taxSlug) : categoryPageHref(prefix, taxSlug);

  const sidebar = homeSidebar(lang, prefix, navTags, navCategories, {
    kind,
    slug: taxSlug,
  });

  const cards = videos
    .map(
      (v) => `
    <a href="${prefix}${videoWatchPath(v, slugOffset)}" class="yt-card">
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
      ${page > 1 ? `<a href="${baseHref}${page > 2 ? `?page=${page - 1}` : ""}">${t(lang, "previous")}</a>` : ""}
      ${hasNext ? `<a href="${baseHref}?page=${page + 1}">${t(lang, "next")}</a>` : ""}
    </div>`;

  const heading = `<h1 class="yt-taxonomy-title">${esc(
    kind === "tag" ? t(lang, "tag_page_title").replace("{name}", taxName) : t(lang, "category_page_title").replace("{name}", taxName)
  )}</h1>`;

  const main = videos.length
    ? `<div class="yt-home-main">${heading}<div class="yt-grid">${cards}</div>${pagination}</div>`
    : `<div class="yt-home-main">${heading}<div style="padding:24px 0;color:var(--yt-text2)">${t(
        lang,
        "no_videos"
      )}</div></div>`;

  const content = `<div class="yt-home">${sidebar}${main}</div>`;

  const barePath = `/${kind}/${taxSlug}.html`;
  const pagePath = page > 1 ? `${barePath}?page=${page}` : barePath;
  return layout(`${browserTitle} - ${siteName}`, lang, content, "", pagePath, {
    siteName,
    gaMeasurementId,
    description: `${browserTitle} - ${siteName}`,
    origin,
    hreflangPath: barePath,
  });
}

interface WatchData {
  id: number;
  title: string;
  original_title: string;
  duration: number;
  thumbnail_url: string;
  video_url: string;
  hls_url: string;
}

export interface WatchTaxonomyLinks {
  /** Crawler keyword; linked under `categories` for navigation and listings. */
  keyword: { name: string; slug: string } | null;
  tags: { name: string; slug: string }[];
  categories: { name: string; slug: string }[];
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

export function watchPage(
  lang: string,
  video: WatchData,
  subtitleTracks: SubTrack[],
  recommended: RecommendedVideo[] = [],
  navTags: NavTaxonomyItem[] = [],
  navCategories: NavTaxonomyItem[] = [],
  seoTranscriptCues: VttCue[] = [],
  taxonomyLinks: WatchTaxonomyLinks = { keyword: null, tags: [], categories: [] },
  slugOffset = 0,
  siteName: string,
  gaMeasurementId?: string,
  origin?: string
) {
  const prefix = langPrefix(lang);
  const sidebar = homeSidebar(lang, prefix, navTags, navCategories, null);

  const kw = taxonomyLinks.keyword;
  const kwName = kw?.name?.trim() || "";
  const tagPills = taxonomyLinks.tags.filter(
    (x) => !kwName || x.name.trim().toLowerCase() !== kwName.toLowerCase()
  );
  const tagParts: string[] = [];
  if (kw) {
    tagParts.push(
      `<a class="yt-tag yt-tag-keyword" href="${categoryPageHref(prefix, kw.slug)}">#${esc(kw.name)}</a>`
    );
  }
  for (const c of taxonomyLinks.categories) {
    tagParts.push(
      `<a class="yt-tag" href="${categoryPageHref(prefix, c.slug)}">#${esc(c.name)}</a>`
    );
  }
  for (const tg of tagPills) {
    tagParts.push(`<a class="yt-tag" href="${tagPageHref(prefix, tg.slug)}">#${esc(tg.name)}</a>`);
  }
  const tagsHtml = tagParts.join("");

  const watchConfig = {
    pageLang: lang,
    sources: [
      ...(video.hls_url
        ? [{ src: video.hls_url, type: "application/x-mpegURL" as const }]
        : []),
      ...(video.video_url ? [{ src: video.video_url, type: "video/mp4" as const }] : []),
    ],
    /** Passed to Video.js only — avoid inline track tags (browser would fetch VTT before Video.js / CORS). */
    subtitleTracks: subtitleTracks.map((tr) => ({
      kind: "subtitles" as const,
      src: tr.url,
      srclang: tr.lang,
      label: tr.label,
    })),
  };

  const seoTranscriptBlock =
    seoTranscriptCues.length > 0
      ? `<details class="yt-transcript-seo">
  <summary class="yt-transcript-seo-summary">${t(lang, "full_transcript")}</summary>
  <div class="yt-transcript-seo-body">
    ${seoTranscriptCues.map((c) => `<p>${esc(c.text)}</p>`).join("")}
  </div>
</details>`
      : "";

  const transcriptTextForLd = seoTranscriptCues.map((c) => c.text).join("\n");
  const isoDur = durationIso8601(video.duration);
  const ldData: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "VideoObject",
    name: video.title,
    description: video.title,
  };
  if (video.thumbnail_url) ldData.thumbnailUrl = video.thumbnail_url;
  if (isoDur) ldData.duration = isoDur;
  if (video.hls_url) ldData.contentUrl = video.hls_url;
  if (transcriptTextForLd) ldData.transcript = transcriptTextForLd;
  const jsonLd = escJsonForScript(ldData);

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
        ></video>
      </div>

      <h1 class="yt-title">${esc(video.title)}</h1>

      <div class="yt-meta-row">
        ${video.duration ? `<span>${fmtDuration(video.duration)}</span>` : ""}
        ${subtitleTracks.length ? `<span>&middot;</span><span>${subtitleTracks.length} ${t(lang, "subtitles")}</span>` : ""}
      </div>

      ${tagsHtml ? `<div style="margin-top:12px">${tagsHtml}</div>` : ""}
      ${seoTranscriptBlock}
    </div>
  </div>
  ${recommended.length ? `<h2 class="yt-recommended-title">${t(lang, "recommended")}</h2>` : ""}
  <div class="yt-recommended">
    ${recommended.map((r) => `
      <a href="${prefix}${videoWatchPath(r, slugOffset)}" class="yt-card">
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

  const watchPath = videoWatchPath(video, slugOffset);
  const desc = transcriptTextForLd
    ? transcriptTextForLd.substring(0, 160).replace(/\n/g, " ")
    : video.title;
  return layout(`${video.title} - ${siteName}`, lang, content, "", watchPath, {
    playerAssets: true,
    jsonLd,
    siteName,
    gaMeasurementId,
    description: desc,
    origin,
    hreflangPath: watchPath,
    ogImage: video.thumbnail_url,
  });
}
