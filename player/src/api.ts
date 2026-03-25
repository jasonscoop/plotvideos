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
  /** Optional override; default is original_id + SLUG_OFFSET_VALUE (public URL slug). */
  slug?: number;
  title: string;
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

function publicSlug(originalId: number, slugOffset: number, override?: number): number {
  if (override != null && Number.isFinite(override)) return Math.trunc(override);
  return originalId + slugOffset;
}

function parseSlugOffsetValue(raw: string | undefined): number {
  const n = parseInt(raw ?? "0", 10);
  return Number.isFinite(n) ? n : 0;
}

async function ingestVideo(db: D1Database, body: IngestPayload, slugOffset: number): Promise<number> {
  const slug = publicSlug(body.original_id, slugOffset, body.slug);
  const tagsJson = JSON.stringify(body.tags || []);
  const catsJson = JSON.stringify(body.categories || []);

  const result = await db
    .prepare(
      `INSERT INTO videos (original_id, slug, title,
        duration, width, height, thumbnail_url, video_url, hls_url,
        store_dir, keyword, tags, categories)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(original_id) DO UPDATE SET
        slug = excluded.slug,
        title = excluded.title,
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
      slug,
      body.title,
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

  if (!result) throw new Error("insert failed");

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

  return videoId;
}

async function syncLanguages(db: D1Database, crawlerUrl: string, crawlerKey: string): Promise<void> {
  const resp = await fetch(`${crawlerUrl}/languages`, {
    headers: { "X-API-Key": crawlerKey },
  });
  if (!resp.ok) throw new Error(`Crawler API error: ${resp.status}`);

  const languages: { code: string; name: string; locale: string }[] = await resp.json();
  if (!languages.length) return;

  const stmt = db.prepare(
    `INSERT INTO languages (code, name, locale) VALUES (?, ?, ?)
     ON CONFLICT(code) DO UPDATE SET name = excluded.name, locale = excluded.locale`
  );
  await db.batch(languages.map((l) => stmt.bind(l.code, l.name, l.locale)));
}

export async function syncFromCrawler(env: Env["Bindings"]): Promise<{ synced: number }> {
  const crawlerUrl = env.VIDEO_FETCH_API_URL;
  const crawlerKey = env.VIDEO_FETCH_API_KEY;
  const slugOffset = parseSlugOffsetValue(env.SLUG_OFFSET_VALUE);

  await syncLanguages(env.DB, crawlerUrl, crawlerKey);

  const maxRow = await env.DB
    .prepare("SELECT MAX(original_id) AS max_id FROM videos")
    .first<{ max_id: number | null }>();
  const afterId = maxRow?.max_id ?? 0;

  let synced = 0;
  let cursor = afterId;

  while (true) {
    const url = `${crawlerUrl}/videos?after_id=${cursor}&limit=50`;
    const resp = await fetch(url, {
      headers: { "X-API-Key": crawlerKey },
    });
    if (!resp.ok) throw new Error(`Crawler API error: ${resp.status}`);

    const videos: IngestPayload[] = await resp.json();
    if (!videos.length) break;

    for (const video of videos) {
      await ingestVideo(env.DB, video, slugOffset);
      synced++;
    }

    cursor = videos[videos.length - 1].original_id;
    if (videos.length < 50) break;
  }

  return { synced };
}

// Manual sync trigger
apiRoutes.post("/sync", async (c) => {
  try {
    const result = await syncFromCrawler(c.env);
    return c.json(result);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
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
