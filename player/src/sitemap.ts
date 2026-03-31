import type { Hono } from "hono";
import type { Env } from "./index";
import { publicWatchSegmentFromVideoId, parseIdOffset } from "./slug";
import { DEFAULT_LANG } from "./i18n";

const PAGE_SIZE = 5000;

function xmlRes(c: any, xml: string) {
  return c.body(xml, 200, {
    "Content-Type": "application/xml; charset=utf-8",
    "Cache-Control": "public, max-age=3600",
  });
}

async function defaultLangId(db: D1Database): Promise<number> {
  const row = await db
    .prepare("SELECT id FROM languages WHERE code = ?")
    .bind(DEFAULT_LANG)
    .first<{ id: number }>();
  return row?.id ?? 0;
}

async function handleVideosSitemap(c: any, page: number) {
  const db = c.env.DB;
  const origin = new URL(c.req.url).origin;
  const slugOffset = parseIdOffset(c.env.ID_OFFSET);
  const offset = (page - 1) * PAGE_SIZE;

  const result = await db
    .prepare("SELECT id, created_at FROM videos ORDER BY id ASC LIMIT ? OFFSET ?")
    .bind(PAGE_SIZE, offset)
    .all<{ id: number; created_at: string }>();

  if (!result.results.length) return c.text("Not found", 404);

  const urls = result.results.map((r) => {
    const seg = publicWatchSegmentFromVideoId(r.id, slugOffset);
    const day = r.created_at?.substring(0, 10) || "";
    return day
      ? `<url><loc>${origin}/video/${seg}.html</loc><lastmod>${day}</lastmod></url>`
      : `<url><loc>${origin}/video/${seg}.html</loc></url>`;
  });

  return xmlRes(c, [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls,
    "</urlset>",
  ].join("\n"));
}

async function handleTagsSitemap(c: any) {
  const db = c.env.DB;
  const origin = new URL(c.req.url).origin;
  const langId = await defaultLangId(db);

  const result = await db
    .prepare("SELECT slug FROM tags WHERE lang_id = ? AND video_count > 0 ORDER BY video_count DESC")
    .bind(langId)
    .all<{ slug: string }>();

  const urls = result.results.map(
    (r) => `<url><loc>${origin}/tag/${r.slug}.html</loc></url>`
  );

  return xmlRes(c, [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls,
    "</urlset>",
  ].join("\n"));
}

async function handleCategoriesSitemap(c: any) {
  const db = c.env.DB;
  const origin = new URL(c.req.url).origin;
  const langId = await defaultLangId(db);

  const result = await db
    .prepare("SELECT slug FROM categories WHERE lang_id = ? AND video_count > 0 ORDER BY video_count DESC")
    .bind(langId)
    .all<{ slug: string }>();

  const urls = result.results.map(
    (r) => `<url><loc>${origin}/category/${r.slug}.html</loc></url>`
  );

  return xmlRes(c, [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls,
    "</urlset>",
  ].join("\n"));
}

export function registerSitemapRoutes(app: Hono<Env>) {
  app.get("/sitemap.xml", async (c) => {
    const db = c.env.DB;
    const origin = new URL(c.req.url).origin;

    const row = await db
      .prepare("SELECT COUNT(*) AS cnt FROM videos")
      .first<{ cnt: number }>();
    const totalPages = Math.max(1, Math.ceil((row?.cnt ?? 0) / PAGE_SIZE));

    const entries: string[] = [];
    for (let i = 1; i <= totalPages; i++) {
      entries.push(`<sitemap><loc>${origin}/sitemap/videos-${i}.xml</loc></sitemap>`);
    }
    entries.push(`<sitemap><loc>${origin}/sitemap/tags.xml</loc></sitemap>`);
    entries.push(`<sitemap><loc>${origin}/sitemap/categories.xml</loc></sitemap>`);

    return xmlRes(c, [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      ...entries,
      "</sitemapindex>",
    ].join("\n"));
  });

  app.get("/sitemap/*", async (c) => {
    const file = c.req.path.replace(/^\/sitemap\//, "");

    if (file === "tags.xml") return handleTagsSitemap(c);
    if (file === "categories.xml") return handleCategoriesSitemap(c);

    const videoMatch = file.match(/^videos-(\d+)\.xml$/);
    if (videoMatch) return handleVideosSitemap(c, parseInt(videoMatch[1]));

    return c.text("Not found", 404);
  });
}
