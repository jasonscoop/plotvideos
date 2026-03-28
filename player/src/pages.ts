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

/** Parse `/video/<n>.html` segment: accepts `123` or `123.0` (float artifact), returns INTEGER or null. */
function parsePublicWatchSegmentParam(slugParam: string): number | null {
  const s = slugParam.replace(/\.html$/i, "").trim();
  if (!/^\d+(\.0+)?$/.test(s)) return null;
  const n = Number(s);
  if (!Number.isFinite(n)) return null;
  return Math.trunc(n);
}

const TOP_NAV_TAGS_SQL = `SELECT name, slug, video_count AS count FROM tags ORDER BY video_count DESC LIMIT 15`;

const TOP_NAV_CATEGORIES_SQL = `SELECT name, slug, video_count AS count FROM categories ORDER BY video_count DESC LIMIT 15`;

async function fetchNavTaxonomies(db: D1Database): Promise<[NavTaxonomyItem[], NavTaxonomyItem[]]> {
  const [tags, cats] = await Promise.all([
    db.prepare(TOP_NAV_TAGS_SQL).all<NavTaxonomyItem>(),
    db.prepare(TOP_NAV_CATEGORIES_SQL).all<NavTaxonomyItem>(),
  ]);
  return [tags.results, cats.results];
}

async function fetchNameSlugMap(
  db: D1Database,
  table: "tags" | "categories",
  names: string[]
): Promise<Map<string, string>> {
  const uniq = [...new Set(names.map((n) => n.trim()).filter(Boolean))];
  if (!uniq.length) return new Map();
  const ph = uniq.map(() => "?").join(",");
  const rows = await db
    .prepare(`SELECT name, slug FROM ${table} WHERE name IN (${ph})`)
    .bind(...uniq)
    .all<{ name: string; slug: string }>();
  return new Map(rows.results.map((r) => [r.name, r.slug]));
}

function watchSlugOffset(c: { env: Env["Bindings"] }): number {
  return parseSlugOffsetValue(c.env.SLUG_OFFSET_VALUE);
}

function pageContext(env: Env["Bindings"]) {
  return {
    siteName: siteNameFromEnv(env),
    gaMeasurementId: gaMeasurementIdFromEnv(env),
  };
}

async function resolveIndex(c: any, lang: string) {
  const db = c.env.DB;
  const { siteName, gaMeasurementId } = pageContext(c.env);
  const slugOffset = watchSlugOffset(c);
  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 15;
  const q = c.req.query("q")?.trim() || "";

  let listSql: string;
  const params: any[] = [];

  if (lang === DEFAULT_LANG) {
    listSql = "SELECT * FROM videos";
  } else {
    listSql = `SELECT v.*, vt.title AS tr_title
               FROM videos v
               LEFT JOIN video_translations vt ON vt.video_id = v.id AND vt.lang = ?`;
    params.push(lang);
  }

  if (q) {
    const where = lang === DEFAULT_LANG
      ? " WHERE title LIKE ?"
      : " WHERE (vt.title LIKE ? OR v.title LIKE ?)";
    listSql += where;
    params.push(`%${q}%`);
    if (lang !== DEFAULT_LANG) params.push(`%${q}%`);
  }

  listSql +=
    " ORDER BY " + (lang === DEFAULT_LANG ? "" : "v.") + "random_key DESC LIMIT ? OFFSET ?";

  const [listResult, navTags, navCategories] = await Promise.all([
    db.prepare(listSql).bind(...params, pageSize + 1, (page - 1) * pageSize).all(),
    db.prepare(TOP_NAV_TAGS_SQL).all<NavTaxonomyItem>(),
    db.prepare(TOP_NAV_CATEGORIES_SQL).all<NavTaxonomyItem>(),
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
      gaMeasurementId
    )
  );
}

async function resolveTagListing(c: any, lang: string) {
  const slug = parseTaxonomySlugParam(c.req.param("slug"));
  if (!slug) return c.text("Not found", 404);

  const { siteName, gaMeasurementId } = pageContext(c.env);
  const db = c.env.DB;
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
             INNER JOIN video_tags vt ON v.id = vt.video_id WHERE vt.tag_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(row.id, pageSize + 1, offset)
          .all()
      : await db
          .prepare(
            `SELECT v.*, vt2.title AS tr_title FROM videos v
             INNER JOIN video_tags vt ON v.id = vt.video_id
             LEFT JOIN video_translations vt2 ON vt2.video_id = v.id AND vt2.lang = ?
             WHERE vt.tag_id = ? ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(lang, row.id, pageSize + 1, offset)
          .all();

  const hasNext = listResult.results.length > pageSize;
  const videos = listResult.results.slice(0, pageSize).map((r: any) => ({
    ...r,
    title: r.tr_title || r.title,
  }));

  const [navTags, navCategories] = await fetchNavTaxonomies(db);
  const prefix = langPrefix(lang);
  const pagePath = `${prefix}/tag/${row.slug}.html`;
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
      pagePath,
      slugOffset,
      siteName,
      gaMeasurementId
    )
  );
}

async function resolveCategoryListing(c: any, lang: string) {
  const slug = parseTaxonomySlugParam(c.req.param("slug"));
  if (!slug) return c.text("Not found", 404);

  const { siteName, gaMeasurementId } = pageContext(c.env);
  const db = c.env.DB;
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
             INNER JOIN video_categories vc ON v.id = vc.video_id WHERE vc.category_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(row.id, pageSize + 1, offset)
          .all()
      : await db
          .prepare(
            `SELECT v.*, vt2.title AS tr_title FROM videos v
             INNER JOIN video_categories vc ON v.id = vc.video_id
             LEFT JOIN video_translations vt2 ON vt2.video_id = v.id AND vt2.lang = ?
             WHERE vc.category_id = ? ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(lang, row.id, pageSize + 1, offset)
          .all();

  const hasNext = listResult.results.length > pageSize;
  const videos = listResult.results.slice(0, pageSize).map((r: any) => ({
    ...r,
    title: r.tr_title || r.title,
  }));

  const [navTags, navCategories] = await fetchNavTaxonomies(db);
  const prefix = langPrefix(lang);
  const pagePath = `${prefix}/category/${row.slug}.html`;
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
      pagePath,
      slugOffset,
      siteName,
      gaMeasurementId
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
  const { siteName, gaMeasurementId } = pageContext(c.env);
  const id = video.id;
  const slugOffset = watchSlugOffset(c);

  const [translationResult, subsResult, recResult, navTagsResult, navCategoriesResult] = await Promise.all([
    db
      .prepare("SELECT title, keyword, tags, categories FROM video_translations WHERE video_id = ? AND lang = ?")
      .bind(id, lang)
      .first<any>(),
    db
      .prepare("SELECT lang, label, url FROM subtitle_tracks WHERE video_id = ?")
      .bind(id)
      .all<{ lang: string; label: string; url: string }>(),
    lang === "en"
      ? db
          .prepare("SELECT id, title, duration, thumbnail_url FROM videos WHERE id != ? ORDER BY RANDOM() LIMIT 10")
          .bind(id)
          .all<any>()
      : db
          .prepare(
            `SELECT v.id, COALESCE(vt.title, v.title) AS title, v.duration, v.thumbnail_url
             FROM videos v LEFT JOIN video_translations vt ON vt.video_id = v.id AND vt.lang = ?
             WHERE v.id != ? ORDER BY RANDOM() LIMIT 10`
          )
          .bind(lang, id)
          .all<any>(),
    db.prepare(TOP_NAV_TAGS_SQL).all<NavTaxonomyItem>(),
    db.prepare(TOP_NAV_CATEGORIES_SQL).all<NavTaxonomyItem>(),
  ]);

  const subtitleTracks = subsResult.results.map((s) => ({
    ...s,
    isDefault: s.lang === lang,
  }));

  const displayTitle = translationResult?.title || video.title;
  const displayKeyword = translationResult?.keyword || video.keyword || "";
  const displayTags: string[] = translationResult?.tags
    ? JSON.parse(translationResult.tags)
    : JSON.parse(video.tags || "[]");
  const displayCategories: string[] = translationResult?.categories
    ? JSON.parse(translationResult.categories)
    : JSON.parse(video.categories || "[]");

  const tagSlugMap = await fetchNameSlugMap(db, "tags", displayTags);
  const catSlugMap = await fetchNameSlugMap(db, "categories", [
    displayKeyword,
    ...displayCategories,
  ]);
  const kwTrim = displayKeyword.trim();
  const kwLower = kwTrim.toLowerCase();
  const keywordLink =
    kwTrim && catSlugMap.has(kwTrim) ? { name: kwTrim, slug: catSlugMap.get(kwTrim)! } : null;
  const tagLinks = displayTags
    .map((t) => {
      const tr = t.trim();
      const sl = tagSlugMap.get(tr);
      return sl ? { name: tr, slug: sl } : null;
    })
    .filter((x): x is { name: string; slug: string } => x != null)
    .filter((x) => !kwLower || x.name.trim().toLowerCase() !== kwLower);
  const categoryLinks = displayCategories
    .map((c) => {
      const cr = c.trim();
      const sl = catSlugMap.get(cr);
      return sl ? { name: cr, slug: sl } : null;
    })
    .filter((x): x is { name: string; slug: string } => x != null)
    .filter((x) => !kwLower || x.name.trim().toLowerCase() !== kwLower);

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
        keyword: displayKeyword,
        tags: displayTags,
        categories: displayCategories,
      },
      subtitleTracks,
      recResult.results,
      navTagsResult.results,
      navCategoriesResult.results,
      seoTranscriptCues,
      { keyword: keywordLink, tags: tagLinks, categories: categoryLinks },
      slugOffset,
      siteName,
      gaMeasurementId
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
