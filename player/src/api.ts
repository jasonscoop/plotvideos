import { Hono } from "hono";
import type { Env } from "./index";
import { slugify, generateVideoSlug, parseIdOffset } from "./slug";
import type { Settings } from "./settings";

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
  duration?: number;
  width?: number;
  height?: number;
  thumbnail_url?: string;
  video_url?: string;
  hls_url?: string;
  keyword?: string;
  tags?: string[];
  categories?: string[];
  translations?: Record<string, TranslationPayload>;
  subtitle_tracks?: { lang: string; url: string }[];
}

const LANG_ID = "(SELECT id FROM languages WHERE code = ?)";

async function getOrCreateTaxonomyId(
  db: D1Database,
  table: "tags" | "categories",
  name: string,
  langCode: string
): Promise<number | null> {
  const trimmed = name.trim();
  if (!trimmed) return null;
  const existing = await db
    .prepare(`SELECT t.id FROM ${table} t INNER JOIN languages l ON l.id = t.lang_id WHERE t.name = ? AND l.code = ?`)
    .bind(trimmed, langCode)
    .first<{ id: number }>();
  if (existing) return existing.id;
  const base = slugify(trimmed);
  for (let i = 0; i < 50; i++) {
    const slug = i === 0 ? base : `${base}-${i}`;
    try {
      const row = await db
        .prepare(`INSERT INTO ${table} (name, slug, lang_id) VALUES (?, ?, ${LANG_ID}) RETURNING id`)
        .bind(trimmed, slug, langCode)
        .first<{ id: number }>();
      if (row?.id != null) return row.id;
    } catch {
    }
  }
  return null;
}

async function syncVideoTaxonomiesForLang(
  db: D1Database,
  videoId: number,
  langCode: string,
  keyword: string,
  tags: string[],
  categories: string[]
): Promise<void> {
  const existingTagIds = await db
    .prepare(
      `SELECT vt.tag_id FROM video_tags vt
       INNER JOIN tags t ON t.id = vt.tag_id
       INNER JOIN languages l ON l.id = t.lang_id
       WHERE vt.video_id = ? AND l.code = ?`
    )
    .bind(videoId, langCode)
    .all<{ tag_id: number }>();
  for (const r of existingTagIds.results) {
    await db.prepare("DELETE FROM video_tags WHERE video_id = ? AND tag_id = ?").bind(videoId, r.tag_id).run();
  }

  const existingCatIds = await db
    .prepare(
      `SELECT vc.category_id FROM video_categories vc
       INNER JOIN categories c ON c.id = vc.category_id
       INNER JOIN languages l ON l.id = c.lang_id
       WHERE vc.video_id = ? AND l.code = ?`
    )
    .bind(videoId, langCode)
    .all<{ category_id: number }>();
  for (const r of existingCatIds.results) {
    await db.prepare("DELETE FROM video_categories WHERE video_id = ? AND category_id = ?").bind(videoId, r.category_id).run();
  }

  const tagNames = new Set<string>();
  for (const t of tags) {
    const x = typeof t === "string" ? t.trim() : "";
    if (x) tagNames.add(x);
  }

  for (const t of tagNames) {
    const id = await getOrCreateTaxonomyId(db, "tags", t, langCode);
    if (id != null) {
      await db
        .prepare("INSERT OR IGNORE INTO video_tags (video_id, tag_id) VALUES (?, ?)")
        .bind(videoId, id)
        .run();
    }
  }

  const kw = keyword?.trim();
  const categoryNames = new Set<string>();
  if (kw) categoryNames.add(kw);
  for (const c of categories) {
    const x = typeof c === "string" ? c.trim() : "";
    if (x) categoryNames.add(x);
  }

  for (const c of categoryNames) {
    const id = await getOrCreateTaxonomyId(db, "categories", c, langCode);
    if (id != null) {
      const isKeyword = c === kw ? 1 : 0;
      await db
        .prepare("INSERT OR IGNORE INTO video_categories (video_id, category_id, is_keyword) VALUES (?, ?, ?)")
        .bind(videoId, id, isKeyword)
        .run();
    }
  }

  await db.prepare("UPDATE tags SET video_count = (SELECT COUNT(*) FROM video_tags WHERE tag_id = tags.id) WHERE lang_id = " + LANG_ID).bind(langCode).run();
  await db.prepare("UPDATE categories SET video_count = (SELECT COUNT(*) FROM video_categories WHERE category_id = categories.id) WHERE lang_id = " + LANG_ID).bind(langCode).run();
}

function randomInt31(): number {
  return Math.floor(Math.random() * 2147483647);
}

export async function refreshRandomKeys(db: D1Database): Promise<void> {
  await db.prepare(`UPDATE videos SET random_key = RANDOM()`).run();
}

async function ingestVideo(db: D1Database, body: IngestPayload, settings: Settings): Promise<number> {
  const slug = generateVideoSlug(
    body.original_id,
    body.title,
    settings.slug_from,
    parseIdOffset(settings.id_offset)
  );

  const result = await db
    .prepare(
      `INSERT INTO videos (original_id, title,
        duration, width, height, thumbnail_url, video_url, hls_url,
        slug, random_key)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(original_id) DO UPDATE SET
        title = excluded.title,
        duration = excluded.duration,
        width = excluded.width,
        height = excluded.height,
        thumbnail_url = excluded.thumbnail_url,
        video_url = excluded.video_url,
        hls_url = excluded.hls_url
       RETURNING id`
    )
    .bind(
      body.original_id,
      body.title,
      body.duration || 0,
      body.width || 0,
      body.height || 0,
      body.thumbnail_url || "",
      body.video_url || "",
      body.hls_url || "",
      slug,
      randomInt31()
    )
    .first<{ id: number }>();

  if (!result) throw new Error("insert failed");

  const videoId = result.id;

  await syncVideoTaxonomiesForLang(
    db, videoId, "en",
    body.keyword || "",
    body.tags || [],
    body.categories || []
  );

  if (body.translations) {
    const stmt = db.prepare(
      `INSERT INTO title_translations (video_id, lang_id, title)
       VALUES (?, ${LANG_ID}, ?)
       ON CONFLICT(video_id, lang_id) DO UPDATE SET
        title = excluded.title`
    );
    const batch: ReturnType<typeof stmt.bind>[] = [];
    for (const [lang, tr] of Object.entries(body.translations)) {
      if (tr.title) {
        batch.push(stmt.bind(videoId, lang, tr.title));
      }
      await syncVideoTaxonomiesForLang(
        db, videoId, lang,
        tr.keyword || body.keyword || "",
        tr.tags || body.tags || [],
        tr.categories || body.categories || []
      );
    }
    if (batch.length) await db.batch(batch);
  }

  if (body.subtitle_tracks) {
    const stmt = db.prepare(
      `INSERT INTO subtitle_tracks (video_id, lang_id, url)
       VALUES (?, ${LANG_ID}, ?)
       ON CONFLICT(video_id, lang_id) DO UPDATE SET url = excluded.url`
    );
    const batch = body.subtitle_tracks.map((t) =>
      stmt.bind(videoId, t.lang, t.url)
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

export async function syncFromCrawler(db: D1Database, settings: Settings): Promise<{ synced: number }> {
  const crawlerUrl = settings.fetch_api_url;
  const crawlerKey = settings.fetch_api_key;

  if (!crawlerUrl || !crawlerKey) return { synced: 0 };

  await syncLanguages(db, crawlerUrl, crawlerKey);

  const maxRow = await db
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
      await ingestVideo(db, video, settings);
      synced++;
    }

    cursor = videos[videos.length - 1].original_id;
    if (videos.length < 50) break;
  }

  return { synced };
}

apiRoutes.post("/sync", async (c) => {
  try {
    const result = await syncFromCrawler(c.env.DB, c.get("settings"));
    return c.json(result);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

apiRoutes.get("/videos", async (c) => {
  const db = c.env.DB;
  const rows = await db
    .prepare("SELECT * FROM videos ORDER BY random_key DESC LIMIT 100")
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
    .prepare(
      `SELECT l.code AS lang, l.name AS label, st.url
       FROM subtitle_tracks st INNER JOIN languages l ON l.id = st.lang_id
       WHERE st.video_id = ?`
    )
    .bind(id)
    .all();
  const translations = await db
    .prepare(
      `SELECT l.code AS lang, tt.title
       FROM title_translations tt INNER JOIN languages l ON l.id = tt.lang_id
       WHERE tt.video_id = ?`
    )
    .bind(id)
    .all();

  return c.json({
    ...video,
    subtitle_tracks: subs.results,
    translations: Object.fromEntries(
      translations.results.map((r: any) => [r.lang, { title: r.title }])
    ),
  });
});
