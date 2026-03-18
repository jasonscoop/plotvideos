import { Hono } from "hono";
import type { Env } from "./index";
import { indexPage, watchPage } from "./html";
import { DEFAULT_LANG, isValidLang } from "./i18n";

export const pageRoutes = new Hono<Env>();

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
  const [countResult, listResult] = await Promise.all([
    db.prepare(countSql).bind(...countParams).first<{ total: number }>(),
    db.prepare(listSql).bind(...params, pageSize, (page - 1) * pageSize).all(),
  ]);

  const total = countResult?.total || 0;
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  const videos = listResult.results.map((row: any) => ({
    ...row,
    title: row.tr_title || row.title,
  }));

  return c.html(indexPage(lang, videos as any, page, totalPages, total, q));
}

async function resolveWatch(c: any, lang: string) {
  const db = c.env.DB;
  const id = c.req.param("id");

  const video = await db
    .prepare("SELECT * FROM videos WHERE id = ?")
    .bind(id)
    .first<any>();

  if (!video) return c.text("Video not found", 404);

  const [translationResult, subsResult] = await Promise.all([
    db
      .prepare("SELECT title, keyword, tags, categories FROM video_translations WHERE video_id = ? AND lang = ?")
      .bind(id, lang)
      .first<any>(),
    db
      .prepare("SELECT lang, label, url FROM subtitle_tracks WHERE video_id = ?")
      .bind(id)
      .all<{ lang: string; label: string; url: string }>(),
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

  return c.html(
    watchPage(
      lang,
      {
        id: video.id,
        title: displayTitle,
        original_title: video.title,
        host: video.host,
        duration: video.duration,
        thumbnail_url: video.thumbnail_url,
        video_url: video.video_url,
        hls_url: video.hls_url,
        keyword: displayKeyword,
        tags: displayTags,
        categories: displayCategories,
      },
      subtitleTracks
    )
  );
}

pageRoutes.get("/", (c) => resolveIndex(c, DEFAULT_LANG));
pageRoutes.get("/videos/:id", (c) => resolveWatch(c, DEFAULT_LANG));

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
