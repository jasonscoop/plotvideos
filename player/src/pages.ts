import { Hono } from "hono";
import type { Env } from "./index";
import { indexPage, watchPage, taxonomyListingPage, type NavTaxonomyItem } from "./html";
import { gaMeasurementIdFromEnv } from "./analytics";
import { siteNameFromEnv } from "./site";
import { DEFAULT_LANG, isValidLang, langPrefix, t } from "./i18n";
import { fetchVttCues, orderedSubtitleUrls } from "./vtt";
import {
  parseTaxonomySlugParam,
  parseIdOffset,
  videoIdFromPublicWatchSegment,
  publicWatchSegmentFromVideoId,
} from "./slug";

export const pageRoutes = new Hono<Env>();

function parsePublicWatchSegmentParam(slugParam: string): number | null {
  const s = slugParam.replace(/\.html$/i, "").trim();
  if (!/^\d+(\.0+)?$/.test(s)) return null;
  const n = Number(s);
  if (!Number.isFinite(n)) return null;
  return Math.trunc(n);
}

async function resolveLangId(db: D1Database, code: string): Promise<number> {
  const row = await db.prepare("SELECT id FROM languages WHERE code = ?").bind(code).first<{ id: number }>();
  return row?.id ?? 0;
}

const NAV_TAGS_SQL = "SELECT name, slug, video_count AS count FROM tags WHERE lang_id = ? ORDER BY video_count DESC LIMIT 15";
const NAV_CATEGORIES_SQL = "SELECT name, slug, video_count AS count FROM categories WHERE lang_id = ? ORDER BY video_count DESC LIMIT 15";

async function fetchNavTaxonomies(db: D1Database, langId: number): Promise<[NavTaxonomyItem[], NavTaxonomyItem[]]> {
  const [tags, cats] = await Promise.all([
    db.prepare(NAV_TAGS_SQL).bind(langId).all<NavTaxonomyItem>(),
    db.prepare(NAV_CATEGORIES_SQL).bind(langId).all<NavTaxonomyItem>(),
  ]);
  return [tags.results, cats.results];
}

function watchSlugOffset(c: { env: Env["Bindings"] }): number {
  return parseIdOffset(c.env.ID_OFFSET);
}

function pageContext(c: any) {
  return {
    siteName: siteNameFromEnv(c.env),
    gaMeasurementId: gaMeasurementIdFromEnv(c.env),
    origin: new URL(c.req.url).origin,
  };
}

async function applyTranslatedTitles(db: D1Database, videos: any[], langId: number): Promise<void> {
  if (!videos.length || langId <= 0) return;
  const ids = videos.map((v: any) => v.id);
  const placeholders = ids.map(() => "?").join(",");
  const rows = await db
    .prepare(`SELECT video_id, title FROM title_translations WHERE lang_id = ? AND video_id IN (${placeholders})`)
    .bind(langId, ...ids)
    .all<{ video_id: number; title: string }>();
  const titleMap = new Map(rows.results.map((r) => [r.video_id, r.title]));
  for (const v of videos) {
    v.title = titleMap.get(v.id) || v.title;
  }
}

async function resolveIndex(c: any, lang: string) {
  const db = c.env.DB;
  const { siteName, gaMeasurementId, origin } = pageContext(c);
  const slugOffset = watchSlugOffset(c);
  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 15;
  const q = c.req.query("q")?.trim() || "";
  const langId = await resolveLangId(db, lang);

  let listSql = "SELECT * FROM videos";
  const params: any[] = [];

  if (q) {
    listSql += " WHERE title LIKE ?";
    params.push(`%${q}%`);
  }

  listSql += " ORDER BY random_key DESC LIMIT ? OFFSET ?";

  const [listResult, navTags, navCategories] = await Promise.all([
    db.prepare(listSql).bind(...params, pageSize + 1, (page - 1) * pageSize).all(),
    db.prepare(NAV_TAGS_SQL).bind(langId).all<NavTaxonomyItem>(),
    db.prepare(NAV_CATEGORIES_SQL).bind(langId).all<NavTaxonomyItem>(),
  ]);

  const hasNext = listResult.results.length > pageSize;
  const videos = listResult.results.slice(0, pageSize) as any[];
  if (lang !== DEFAULT_LANG) await applyTranslatedTitles(db, videos, langId);

  return c.html(
    indexPage(
      lang,
      videos as any,
      page,
      hasNext,
      q,
      navTags.results,
      navCategories.results,
      null,
      slugOffset,
      siteName,
      gaMeasurementId,
      origin
    )
  );
}

async function resolveTagListing(c: any, lang: string) {
  const slug = parseTaxonomySlugParam(c.req.param("slug"));
  if (!slug) return c.text("Not found", 404);

  const { siteName, gaMeasurementId, origin } = pageContext(c);
  const db = c.env.DB;
  const langId = await resolveLangId(db, lang);
  const row = await db
    .prepare("SELECT id, name, slug FROM tags WHERE slug = ?")
    .bind(slug)
    .first<{ id: number; name: string; slug: string }>();
  if (!row) return c.text("Not found", 404);

  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 15;
  const offset = (page - 1) * pageSize;

  const tagVideoIds = await db
    .prepare("SELECT video_id FROM video_tags WHERE tag_id = ? ORDER BY video_id DESC LIMIT ? OFFSET ?")
    .bind(row.id, pageSize + 1, offset)
    .all<{ video_id: number }>();

  const hasNext = tagVideoIds.results.length > pageSize;
  const ids = tagVideoIds.results.slice(0, pageSize).map((r) => r.video_id);
  let videos: any[] = [];
  if (ids.length) {
    const placeholders = ids.map(() => "?").join(",");
    const vResult = await db
      .prepare(`SELECT * FROM videos WHERE id IN (${placeholders})`)
      .bind(...ids)
      .all();
    const videoMap = new Map(vResult.results.map((v: any) => [v.id, v]));
    videos = ids.map((vid) => videoMap.get(vid)).filter(Boolean) as any[];
    if (lang !== DEFAULT_LANG) await applyTranslatedTitles(db, videos, langId);
  }

  const [navTags, navCategories] = await fetchNavTaxonomies(db, langId);
  const prefix = langPrefix(lang);
  const browserTitle = t(lang, "tag_page_title").replace("{name}", row.name);
  const slugOffset = watchSlugOffset(c);

  return c.html(
    taxonomyListingPage(
      lang,
      "tag",
      row.name,
      row.slug,
      videos as any,
      page,
      hasNext,
      navTags,
      navCategories,
      browserTitle,
      `${prefix}/tag/${row.slug}.html`,
      slugOffset,
      siteName,
      gaMeasurementId,
      origin
    )
  );
}

async function resolveCategoryListing(c: any, lang: string) {
  const slug = parseTaxonomySlugParam(c.req.param("slug"));
  if (!slug) return c.text("Not found", 404);

  const { siteName, gaMeasurementId, origin } = pageContext(c);
  const db = c.env.DB;
  const langId = await resolveLangId(db, lang);
  const row = await db
    .prepare("SELECT id, name, slug FROM categories WHERE slug = ?")
    .bind(slug)
    .first<{ id: number; name: string; slug: string }>();
  if (!row) return c.text("Not found", 404);

  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 15;
  const offset = (page - 1) * pageSize;

  const catVideoIds = await db
    .prepare("SELECT video_id FROM video_categories WHERE category_id = ? ORDER BY video_id DESC LIMIT ? OFFSET ?")
    .bind(row.id, pageSize + 1, offset)
    .all<{ video_id: number }>();

  const hasNext = catVideoIds.results.length > pageSize;
  const ids = catVideoIds.results.slice(0, pageSize).map((r) => r.video_id);
  let videos: any[] = [];
  if (ids.length) {
    const placeholders = ids.map(() => "?").join(",");
    const vResult = await db
      .prepare(`SELECT * FROM videos WHERE id IN (${placeholders})`)
      .bind(...ids)
      .all();
    const videoMap = new Map(vResult.results.map((v: any) => [v.id, v]));
    videos = ids.map((vid) => videoMap.get(vid)).filter(Boolean) as any[];
    if (lang !== DEFAULT_LANG) await applyTranslatedTitles(db, videos, langId);
  }

  const [navTags, navCategories] = await fetchNavTaxonomies(db, langId);
  const prefix = langPrefix(lang);
  const browserTitle = t(lang, "category_page_title").replace("{name}", row.name);
  const slugOffset = watchSlugOffset(c);

  return c.html(
    taxonomyListingPage(
      lang,
      "category",
      row.name,
      row.slug,
      videos as any,
      page,
      hasNext,
      navTags,
      navCategories,
      browserTitle,
      `${prefix}/category/${row.slug}.html`,
      slugOffset,
      siteName,
      gaMeasurementId,
      origin
    )
  );
}

async function resolveWatchBySlug(c: any, lang: string) {
  const db = c.env.DB;
  const segment = parsePublicWatchSegmentParam(c.req.param("slug"));
  if (segment == null) return c.text("Video not found", 404);

  const offset = watchSlugOffset(c);
  const videoId = videoIdFromPublicWatchSegment(segment, offset);
  if (videoId < 1) return c.text("Video not found", 404);

  const video = await db.prepare("SELECT * FROM videos WHERE id = ?").bind(videoId).first<any>();

  if (!video) return c.text("Video not found", 404);
  return _renderWatch(c, lang, video);
}

async function resolveWatch(c: any, lang: string) {
  const db = c.env.DB;
  const id = Math.trunc(Number(c.req.param("id")));
  if (!Number.isFinite(id) || id < 1) return c.text("Video not found", 404);

  const video = await db
    .prepare("SELECT * FROM videos WHERE id = ?")
    .bind(id)
    .first<any>();

  if (!video) return c.text("Video not found", 404);

  const seg = publicWatchSegmentFromVideoId(video.id, watchSlugOffset(c));
  return c.redirect(`${langPrefix(lang)}/video/${seg}.html`, 302);
}

async function _renderWatch(c: any, lang: string, video: any) {
  const db = c.env.DB;
  const { siteName, gaMeasurementId, origin } = pageContext(c);
  const id = video.id;
  const slugOffset = watchSlugOffset(c);
  const langId = await resolveLangId(db, lang);

  const [titleResult, subRows, recResult, navTags, navCategories, videoTagIds, videoCatIds] = await Promise.all([
    db
      .prepare("SELECT title FROM title_translations WHERE video_id = ? AND lang_id = ?")
      .bind(id, langId)
      .first<{ title: string }>(),
    db
      .prepare("SELECT lang_id, url FROM subtitle_tracks WHERE video_id = ?")
      .bind(id)
      .all<{ lang_id: number; url: string }>(),
    db
      .prepare("SELECT id, title, duration, thumbnail_url FROM videos WHERE id != ? ORDER BY random_key DESC LIMIT 10")
      .bind(id)
      .all<any>(),
    db.prepare(NAV_TAGS_SQL).bind(langId).all<NavTaxonomyItem>(),
    db.prepare(NAV_CATEGORIES_SQL).bind(langId).all<NavTaxonomyItem>(),
    db
      .prepare("SELECT tag_id FROM video_tags WHERE video_id = ?")
      .bind(id)
      .all<{ tag_id: number }>(),
    db
      .prepare("SELECT category_id, is_keyword FROM video_categories WHERE video_id = ?")
      .bind(id)
      .all<{ category_id: number; is_keyword: number }>(),
  ]);

  const langIds = [...new Set(subRows.results.map((r) => r.lang_id))];
  let langMap = new Map<number, { code: string; name: string }>();
  if (langIds.length) {
    const ph = langIds.map(() => "?").join(",");
    const langRows = await db
      .prepare(`SELECT id, code, name FROM languages WHERE id IN (${ph})`)
      .bind(...langIds)
      .all<{ id: number; code: string; name: string }>();
    langMap = new Map(langRows.results.map((l) => [l.id, { code: l.code, name: l.name }]));
  }
  const subtitleTracks = subRows.results
    .map((s) => {
      const l = langMap.get(s.lang_id);
      return l ? { lang: l.code, label: l.name, url: s.url, isDefault: l.code === lang } : null;
    })
    .filter(Boolean) as { lang: string; label: string; url: string; isDefault: boolean }[];

  const recVideos = recResult.results as any[];
  if (lang !== DEFAULT_LANG) await applyTranslatedTitles(db, recVideos, langId);

  const tagIds = videoTagIds.results.map((r) => r.tag_id);
  let videoTagRows: { name: string; slug: string }[] = [];
  if (tagIds.length) {
    const ph = tagIds.map(() => "?").join(",");
    const tagResult = await db
      .prepare(`SELECT name, slug FROM tags WHERE id IN (${ph}) AND lang_id = ?`)
      .bind(...tagIds, langId)
      .all<{ name: string; slug: string }>();
    videoTagRows = tagResult.results;
  }

  const catEntries = videoCatIds.results;
  const catIds = catEntries.map((r) => r.category_id);
  let videoCatRows: { name: string; slug: string; is_keyword: number }[] = [];
  if (catIds.length) {
    const ph = catIds.map(() => "?").join(",");
    const catResult = await db
      .prepare(`SELECT id, name, slug FROM categories WHERE id IN (${ph}) AND lang_id = ?`)
      .bind(...catIds, langId)
      .all<{ id: number; name: string; slug: string }>();
    const kwSet = new Set(catEntries.filter((r) => r.is_keyword === 1).map((r) => r.category_id));
    videoCatRows = catResult.results.map((r) => ({
      name: r.name,
      slug: r.slug,
      is_keyword: kwSet.has(r.id) ? 1 : 0,
    }));
  }

  const displayTitle = titleResult?.title || video.title;

  const keywordRow = videoCatRows.find((r) => r.is_keyword === 1);
  const kwName = keywordRow?.name?.trim() || "";
  const kwLower = kwName.toLowerCase();
  const keywordLink = keywordRow ? { name: keywordRow.name, slug: keywordRow.slug } : null;

  const tagLinks = videoTagRows
    .map((r) => ({ name: r.name.trim(), slug: r.slug }))
    .filter((x) => x.name && (!kwLower || x.name.toLowerCase() !== kwLower));

  const categoryLinks = videoCatRows
    .filter((r) => r.is_keyword !== 1)
    .map((r) => ({ name: r.name.trim(), slug: r.slug }))
    .filter((x) => x.name && (!kwLower || x.name.toLowerCase() !== kwLower));

  const vttUrls = orderedSubtitleUrls(subtitleTracks, lang);
  const seoTranscriptCues =
    vttUrls.length > 0 ? (await fetchVttCues(vttUrls)) ?? [] : [];

  return c.html(
    watchPage(
      lang,
      {
        id: video.id,
        title: displayTitle,
        original_title: video.title,
        duration: video.duration,
        thumbnail_url: video.thumbnail_url,
        video_url: video.video_url,
        hls_url: video.hls_url,
        created_at: video.created_at,
      },
      subtitleTracks,
      recVideos,
      navTags.results,
      navCategories.results,
      seoTranscriptCues,
      { keyword: keywordLink, tags: tagLinks, categories: categoryLinks },
      slugOffset,
      siteName,
      gaMeasurementId,
      origin
    )
  );
}

pageRoutes.get("/", (c) => resolveIndex(c, DEFAULT_LANG));
pageRoutes.get("/videos/:id", (c) => resolveWatch(c, DEFAULT_LANG));
pageRoutes.get("/video/:slug", (c) => resolveWatchBySlug(c, DEFAULT_LANG));
pageRoutes.get("/tag/:slug", (c) => resolveTagListing(c, DEFAULT_LANG));
pageRoutes.get("/category/:slug", (c) => resolveCategoryListing(c, DEFAULT_LANG));

pageRoutes.get("/:lang/", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.text("Not found", 404);
  return resolveIndex(c, lang);
});

pageRoutes.get("/:lang/videos/:id", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.text("Not found", 404);
  return resolveWatch(c, lang);
});

pageRoutes.get("/:lang/video/:slug", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.text("Not found", 404);
  return resolveWatchBySlug(c, lang);
});

pageRoutes.get("/:lang/tag/:slug", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.text("Not found", 404);
  return resolveTagListing(c, lang);
});

pageRoutes.get("/:lang/category/:slug", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.text("Not found", 404);
  return resolveCategoryListing(c, lang);
});
