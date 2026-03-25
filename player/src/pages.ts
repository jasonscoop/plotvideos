import { Hono } from "hono";
import type { Env } from "./index";
import { indexPage, watchPage, taxonomyListingPage, type NavTaxonomyItem } from "./html";
import { DEFAULT_LANG, isValidLang, langPrefix, t } from "./i18n";
import { fetchVttCues, orderedSubtitleUrls } from "./vtt";
import { parseTaxonomySlugParam } from "./slug";

export const pageRoutes = new Hono<Env>();

/** Parse `/video/<slug>.html` segment: accepts `123` or `123.0` (float artifact), returns INTEGER slug or null. */
function parsePublicSlugParam(slugParam: string): number | null {
  const s = slugParam.replace(/\.html$/i, "").trim();
  if (!/^\d+(\.0+)?$/.test(s)) return null;
  const n = Number(s);
  if (!Number.isFinite(n)) return null;
  return Math.trunc(n);
}

const TOP_NAV_TAGS_SQL = `SELECT t.name AS name, t.slug AS slug, COUNT(vt.video_id) AS count
FROM tags t
INNER JOIN video_tags vt ON vt.tag_id = t.id
GROUP BY t.id
ORDER BY count DESC
LIMIT 15`;

const TOP_NAV_CATEGORIES_SQL = `SELECT c.name AS name, c.slug AS slug, COUNT(vc.video_id) AS count
FROM categories c
INNER JOIN video_categories vc ON vc.category_id = c.id
GROUP BY c.id
ORDER BY count DESC
LIMIT 15`;

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

async function resolveIndex(c: any, lang: string) {
  const db = c.env.DB;
  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 24;
  const q = c.req.query("q")?.trim() || "";

  let countSql = "SELECT COUNT(*) as total FROM videos";
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
    countSql += " WHERE title LIKE ?";
    listSql += where;
    params.push(`%${q}%`);
    if (lang !== DEFAULT_LANG) params.push(`%${q}%`);
  }

  listSql += " ORDER BY " + (lang === DEFAULT_LANG ? "" : "v.") + "created_at DESC LIMIT ? OFFSET ?";

  const countParams = q ? [`%${q}%`] : [];
  const [countResult, listResult, navTags, navCategories] = await Promise.all([
    db.prepare(countSql).bind(...countParams).first<{ total: number }>(),
    db.prepare(listSql).bind(...params, pageSize, (page - 1) * pageSize).all(),
    db.prepare(TOP_NAV_TAGS_SQL).all<NavTaxonomyItem>(),
    db.prepare(TOP_NAV_CATEGORIES_SQL).all<NavTaxonomyItem>(),
  ]);

  const total = countResult?.total || 0;
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  const videos = listResult.results.map((row: any) => ({
    ...row,
    title: row.tr_title || row.title,
  }));

  return c.html(
    indexPage(lang, videos as any, page, totalPages, total, q, navTags.results, navCategories.results, null)
  );
}

async function resolveTagListing(c: any, lang: string) {
  const slug = parseTaxonomySlugParam(c.req.param("slug"));
  if (!slug) return c.text("Not found", 404);

  const db = c.env.DB;
  const row = await db
    .prepare("SELECT id, name, slug FROM tags WHERE slug = ?")
    .bind(slug)
    .first<{ id: number; name: string; slug: string }>();
  if (!row) return c.text("Not found", 404);

  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 24;
  const offset = (page - 1) * pageSize;

  const countResult = await db
    .prepare(
      `SELECT COUNT(*) AS total FROM videos v
       INNER JOIN video_tags vt ON v.id = vt.video_id WHERE vt.tag_id = ?`
    )
    .bind(row.id)
    .first<{ total: number }>();
  const total = countResult?.total ?? 0;
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  const listResult =
    lang === DEFAULT_LANG
      ? await db
          .prepare(
            `SELECT v.* FROM videos v
             INNER JOIN video_tags vt ON v.id = vt.video_id WHERE vt.tag_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(row.id, pageSize, offset)
          .all()
      : await db
          .prepare(
            `SELECT v.*, vt2.title AS tr_title FROM videos v
             INNER JOIN video_tags vt ON v.id = vt.video_id
             LEFT JOIN video_translations vt2 ON vt2.video_id = v.id AND vt2.lang = ?
             WHERE vt.tag_id = ? ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(lang, row.id, pageSize, offset)
          .all();

  const videos = listResult.results.map((r: any) => ({
    ...r,
    title: r.tr_title || r.title,
  }));

  const [navTags, navCategories] = await fetchNavTaxonomies(db);
  const prefix = langPrefix(lang);
  const pagePath = `${prefix}/tag/${row.slug}.html`;
  const browserTitle = t(lang, "tag_page_title").replace("{name}", row.name);

  return c.html(
    taxonomyListingPage(
      lang,
      "tag",
      row.name,
      row.slug,
      videos as any,
      page,
      totalPages,
      total,
      navTags,
      navCategories,
      browserTitle,
      pagePath
    )
  );
}

async function resolveCategoryListing(c: any, lang: string) {
  const slug = parseTaxonomySlugParam(c.req.param("slug"));
  if (!slug) return c.text("Not found", 404);

  const db = c.env.DB;
  const row = await db
    .prepare("SELECT id, name, slug FROM categories WHERE slug = ?")
    .bind(slug)
    .first<{ id: number; name: string; slug: string }>();
  if (!row) return c.text("Not found", 404);

  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = 24;
  const offset = (page - 1) * pageSize;

  const countResult = await db
    .prepare(
      `SELECT COUNT(*) AS total FROM videos v
       INNER JOIN video_categories vc ON v.id = vc.video_id WHERE vc.category_id = ?`
    )
    .bind(row.id)
    .first<{ total: number }>();
  const total = countResult?.total ?? 0;
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  const listResult =
    lang === DEFAULT_LANG
      ? await db
          .prepare(
            `SELECT v.* FROM videos v
             INNER JOIN video_categories vc ON v.id = vc.video_id WHERE vc.category_id = ?
             ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(row.id, pageSize, offset)
          .all()
      : await db
          .prepare(
            `SELECT v.*, vt2.title AS tr_title FROM videos v
             INNER JOIN video_categories vc ON v.id = vc.video_id
             LEFT JOIN video_translations vt2 ON vt2.video_id = v.id AND vt2.lang = ?
             WHERE vc.category_id = ? ORDER BY v.created_at DESC LIMIT ? OFFSET ?`
          )
          .bind(lang, row.id, pageSize, offset)
          .all();

  const videos = listResult.results.map((r: any) => ({
    ...r,
    title: r.tr_title || r.title,
  }));

  const [navTags, navCategories] = await fetchNavTaxonomies(db);
  const prefix = langPrefix(lang);
  const pagePath = `${prefix}/category/${row.slug}.html`;
  const browserTitle = t(lang, "category_page_title").replace("{name}", row.name);

  return c.html(
    taxonomyListingPage(
      lang,
      "category",
      row.name,
      row.slug,
      videos as any,
      page,
      totalPages,
      total,
      navTags,
      navCategories,
      browserTitle,
      pagePath
    )
  );
}

async function resolveWatchBySlug(c: any, lang: string) {
  const db = c.env.DB;
  const slugNum = parsePublicSlugParam(c.req.param("slug"));
  if (slugNum == null) return c.text("Video not found", 404);

  const video = await db
    .prepare("SELECT * FROM videos WHERE slug = ?")
    .bind(slugNum)
    .first<any>();

  if (!video) return c.text("Video not found", 404);
  return _renderWatch(c, lang, video);
}

async function resolveWatch(c: any, lang: string) {
  const db = c.env.DB;
  const id = c.req.param("id");

  const video = await db
    .prepare("SELECT * FROM videos WHERE id = ?")
    .bind(id)
    .first<any>();

  if (!video) return c.text("Video not found", 404);

  const slug = video.slug;
  if (slug != null && Number.isFinite(Number(slug))) {
    return c.redirect(`${langPrefix(lang)}/video/${Math.trunc(Number(slug))}.html`, 302);
  }
  return _renderWatch(c, lang, video);
}

async function _renderWatch(c: any, lang: string, video: any) {
  const db = c.env.DB;
  const id = video.id;

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
          .prepare("SELECT id, slug, title, duration, thumbnail_url FROM videos WHERE id != ? ORDER BY RANDOM() LIMIT 10")
          .bind(id)
          .all<any>()
      : db
          .prepare(
            `SELECT v.id, v.slug, COALESCE(vt.title, v.title) AS title, v.duration, v.thumbnail_url
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

  const tagSlugMap = await fetchNameSlugMap(db, "tags", [
    displayKeyword,
    ...displayTags,
  ]);
  const catSlugMap = await fetchNameSlugMap(db, "categories", displayCategories);
  const kwTrim = displayKeyword.trim();
  const keywordLink =
    kwTrim && tagSlugMap.has(kwTrim) ? { name: kwTrim, slug: tagSlugMap.get(kwTrim)! } : null;
  const tagLinks = displayTags
    .map((t) => {
      const tr = t.trim();
      const sl = tagSlugMap.get(tr);
      return sl ? { name: tr, slug: sl } : null;
    })
    .filter((x): x is { name: string; slug: string } => x != null);
  const categoryLinks = displayCategories
    .map((c) => {
      const cr = c.trim();
      const sl = catSlugMap.get(cr);
      return sl ? { name: cr, slug: sl } : null;
    })
    .filter((x): x is { name: string; slug: string } => x != null);

  const vttUrls = orderedSubtitleUrls(subtitleTracks, lang);
  const seoTranscriptCues =
    vttUrls.length > 0 ? (await fetchVttCues(vttUrls)) ?? [] : [];

  return c.html(
    watchPage(
      lang,
      {
        id: video.id,
        slug: video.slug,
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
      { keyword: keywordLink, tags: tagLinks, categories: categoryLinks }
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
