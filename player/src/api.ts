import { Hono } from "hono";
import type { Env } from "./index";

export const apiRoutes = new Hono<Env>();

interface TranslationPayload {
  title?: string;
  keyword?: string;
  tags?: string[];
  categories?: string[];
}

interface IngestPayload {
  original_id: number;
  title: string;
  host: string;
  duration?: number;
  width?: number;
  height?: number;
  thumbnail_url?: string;
  video_url?: string;
  hls_url?: string;
  store_dir?: string;
  keyword?: string;
  tags?: string[];
  categories?: string[];
  translations?: Record<string, TranslationPayload>;
  subtitle_tracks?: { lang: string; label: string; url: string }[];
}

apiRoutes.post("/videos", async (c) => {
  const db = c.env.DB;
  const body = await c.req.json<IngestPayload>();

  if (!body.original_id || !body.title) {
    return c.json({ error: "original_id and title are required" }, 400);
  }

  const tagsJson = JSON.stringify(body.tags || []);
  const catsJson = JSON.stringify(body.categories || []);

  const result = await db
    .prepare(
      `INSERT INTO videos (original_id, title, host,
        duration, width, height, thumbnail_url, video_url, hls_url,
        store_dir, keyword, tags, categories)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(original_id) DO UPDATE SET
        title = excluded.title,
        host = excluded.host,
        duration = excluded.duration,
        width = excluded.width,
        height = excluded.height,
        thumbnail_url = excluded.thumbnail_url,
        video_url = excluded.video_url,
        hls_url = excluded.hls_url,
        store_dir = excluded.store_dir,
        keyword = excluded.keyword,
        tags = excluded.tags,
        categories = excluded.categories
       RETURNING id`
    )
    .bind(
      body.original_id,
      body.title,
      body.host || "",
      body.duration || 0,
      body.width || 0,
      body.height || 0,
      body.thumbnail_url || "",
      body.video_url || "",
      body.hls_url || "",
      body.store_dir || "",
      body.keyword || "",
      tagsJson,
      catsJson
    )
    .first<{ id: number }>();

  if (!result) {
    return c.json({ error: "insert failed" }, 500);
  }

  const videoId = result.id;

  if (body.translations) {
    const stmt = db.prepare(
      `INSERT INTO video_translations (video_id, lang, title, keyword, tags, categories)
       VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(video_id, lang) DO UPDATE SET
        title = excluded.title,
        keyword = excluded.keyword,
        tags = excluded.tags,
        categories = excluded.categories`
    );
    const batch = Object.entries(body.translations).map(([lang, tr]) =>
      stmt.bind(
        videoId,
        lang,
        tr.title || "",
        tr.keyword || "",
        JSON.stringify(tr.tags || []),
        JSON.stringify(tr.categories || [])
      )
    );
    if (batch.length) await db.batch(batch);
  }

  if (body.subtitle_tracks) {
    const stmt = db.prepare(
      `INSERT INTO subtitle_tracks (video_id, lang, label, url)
       VALUES (?, ?, ?, ?) ON CONFLICT(video_id, lang) DO UPDATE SET label = excluded.label, url = excluded.url`
    );
    const batch = body.subtitle_tracks.map((t) =>
      stmt.bind(videoId, t.lang, t.label, t.url)
    );
    if (batch.length) await db.batch(batch);
  }

  return c.json({ id: videoId }, 201);
});

apiRoutes.get("/videos", async (c) => {
  const db = c.env.DB;
  const rows = await db
    .prepare("SELECT * FROM videos ORDER BY created_at DESC LIMIT 100")
    .all();
  return c.json(rows.results);
});

apiRoutes.get("/videos/:id", async (c) => {
  const db = c.env.DB;
  const id = c.req.param("id");
  const video = await db
    .prepare("SELECT * FROM videos WHERE id = ?")
    .bind(id)
    .first();
  if (!video) return c.json({ error: "not found" }, 404);

  const subs = await db
    .prepare("SELECT lang, label, url FROM subtitle_tracks WHERE video_id = ?")
    .bind(id)
    .all();
  const translations = await db
    .prepare("SELECT lang, title, keyword, tags, categories FROM video_translations WHERE video_id = ?")
    .bind(id)
    .all();

  return c.json({
    ...video,
    subtitle_tracks: subs.results,
    translations: Object.fromEntries(
      translations.results.map((r: any) => [r.lang, {
        title: r.title,
        keyword: r.keyword,
        tags: JSON.parse(r.tags || "[]"),
        categories: JSON.parse(r.categories || "[]"),
      }])
    ),
  });
});
