import { Hono } from "hono";
import type { Env } from "./index";
import { indexPage, watchPage, taxonomyListingPage, type NavTaxonomyItem } from "./html";
import { gaMeasurementIdFromEnv } from "./analytics";
import { siteNameFromEnv } from "./site";
import { DEFAULT_LANG, isValidLang, langPrefix, t } from "./i18n";
import { fetchVttCues, orderedSubtitleUrls } from "./vtt";
import {
  parseTaxonomySlugParam,
  parseSlugOffsetValue,
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
  return parseSlugOffsetValue(c.env.SLUG_OFFSET_VALUE);
}

function pageContext(c: any) {
  return {
    siteName: siteNameFromEnv(c.env),
    gaMeasurementId: gaMeasurementIdFromEnv(c.env),
    origin: new URL(c.req.url).origin,
  };
}

async function resolveIndex(c: any, lang: string) {
  const db = c.env.DB;
  const { siteName, gaMeasurementId, origin } = pageContext(c);
  const slugOffset = watchSlugOffset(c);
  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 15;
  const q = c.req.query("q")?.trim() || "";
  const langId = await resolveLangId(db, lang);

  let listSql: string;
  const params: any[] = [];

  if (lang === DEFAULT_LANG) {
    listSql = "SELECT * FROM videos";
  } else {
    listSql = `SELECT v.*, tt.title AS tr_title
               FROM videos v
               LEFT JOIN title_translations tt ON tt.video_id = v.id AND tt.lang_id = ?`;
    params.push(langId);
  }

  if (q) {
    const where = lang === DEFAULT_LANG
      ? " WHERE title LIKE ?"
      : " WHERE (tt.title LIKE ? OR v.title LIKE ?)";
    listSql += where;
    params.push(`%${q}%`);
    if (lang !== DEFAULT_LANG) params.push(`%${q}%`);
  }

  listSql +=
    " ORDER BY " + (lang === DEFAULT_LANG ? "" : "v.") + "random_key DESC LIMIT ? OFFSET ?";

  const [listResult, navTags, navCategories] = await Promise.all([
    db.prepare(listSql).bind(...params, pageSize + 1, (page - 1) * pageSize).all(),
    db.prepare(NAV_TAGS_SQL).bind(langId).all<NavTaxonomyItem>(),
    db.prepare(NAV_CATEGORIES_SQL).bind(langId).all<NavTaxonomyItem>(),
  ]);

  const hasNext = listResult.results.length > pageSize;
  const videos = listResult.results.slice(0, pageSize).map((row: any) => ({
    ...row,
    title: row.tr_title || row.title,
  }));

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

  const listResult =
    lang === DEFAULT_LANG
      ? await db
          .prepare(
            `SELECT v.* FROM videos v
             INNER JOIN video_tags vt ON v.id = vt.video_id
             WHERE vt.tag_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(row.id, pageSize + 1, offset)
          .all()
      : await db
          .prepare(
            `SELECT v.*, tt.title AS tr_title FROM videos v
             INNER JOIN video_tags vt ON v.id = vt.video_id
             LEFT JOIN title_translations tt ON tt.video_id = v.id AND tt.lang_id = ?
             WHERE vt.tag_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(langId, row.id, pageSize + 1, offset)
          .all();

  const hasNext = listResult.results.length > pageSize;
  const videos = listResult.results.slice(0, pageSize).map((r: any) => ({
    ...r,
    title: r.tr_title || r.title,
  }));

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

  const listResult =
    lang === DEFAULT_LANG
      ? await db
          .prepare(
            `SELECT v.* FROM videos v
             INNER JOIN video_categories vc ON v.id = vc.video_id
             WHERE vc.category_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(row.id, pageSize + 1, offset)
          .all()
      : await db
          .prepare(
            `SELECT v.*, tt.title AS tr_title FROM videos v
             INNER JOIN video_categories vc ON v.id = vc.video_id
             LEFT JOIN title_translations tt ON tt.video_id = v.id AND tt.lang_id = ?
             WHERE vc.category_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(langId, row.id, pageSize + 1, offset)
          .all();

  const hasNext = listResult.results.length > pageSize;
  const videos = listResult.results.slice(0, pageSize).map((r: any) => ({
    ...r,
    title: r.tr_title || r.title,
  }));

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

  const [titleResult, subsResult, recResult, navTags, navCategories, videoTagRows, videoCatRows] = await Promise.all([
    db
      .prepare("SELECT title FROM title_translations WHERE video_id = ? AND lang_id = ?")
      .bind(id, langId)
      .first<{ title: string }>(),
    db
      .prepare(
        `SELECT l.code AS lang, l.name AS label, st.url
         FROM subtitle_tracks st INNER JOIN languages l ON l.id = st.lang_id
         WHERE st.video_id = ?`
      )
      .bind(id)
      .all<{ lang: string; label: string; url: string }>(),
    lang === "en"
      ? db
          .prepare("SELECT id, title, duration, thumbnail_url FROM videos WHERE id != ? ORDER BY RANDOM() LIMIT 10")
          .bind(id)
          .all<any>()
      : db
          .prepare(
            `SELECT v.id, COALESCE(tt.title, v.title) AS title, v.duration, v.thumbnail_url
             FROM videos v LEFT JOIN title_translations tt ON tt.video_id = v.id AND tt.lang_id = ?
             WHERE v.id != ? ORDER BY RANDOM() LIMIT 10`
          )
          .bind(langId, id)
          .all<any>(),
    db.prepare(NAV_TAGS_SQL).bind(langId).all<NavTaxonomyItem>(),
    db.prepare(NAV_CATEGORIES_SQL).bind(langId).all<NavTaxonomyItem>(),
    db.prepare(
      `SELECT t.name, t.slug FROM tags t
       INNER JOIN video_tags vt ON vt.tag_id = t.id
       WHERE vt.video_id = ? AND t.lang_id = ?`
    ).bind(id, langId).all<{ name: string; slug: string }>(),
    db.prepare(
      `SELECT c.name, c.slug, vc.is_keyword FROM categories c
       INNER JOIN video_categories vc ON vc.category_id = c.id
       WHERE vc.video_id = ? AND c.lang_id = ?`
    ).bind(id, langId).all<{ name: string; slug: string; is_keyword: number }>(),
  ]);

  const subtitleTracks = subsResult.results.map((s) => ({
    ...s,
    isDefault: s.lang === lang,
  }));

  const displayTitle = titleResult?.title || video.title;

  const keywordRow = videoCatRows.results.find((r) => r.is_keyword === 1);
  const kwName = keywordRow?.name?.trim() || "";
  const kwLower = kwName.toLowerCase();
  const keywordLink = keywordRow ? { name: keywordRow.name, slug: keywordRow.slug } : null;

  const tagLinks = videoTagRows.results
    .map((r) => ({ name: r.name.trim(), slug: r.slug }))
    .filter((x) => x.name && (!kwLower || x.name.toLowerCase() !== kwLower));

  const categoryLinks = videoCatRows.results
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
      },
      subtitleTracks,
      recResult.results,
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
