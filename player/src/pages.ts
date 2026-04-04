import { Hono } from "hono";
import type { Env } from "./index";
import {
  indexPage,
  watchPage,
  taxonomyListingPage,
  taxonomyListingHref,
  compliancePage,
  dmcaPage,
  notFoundPage,
  type NavTaxonomyItem,
} from "./html";
import { DEFAULT_LANG, inferLangFromPath, isValidLang, langPrefix, t } from "./i18n";
import { fetchVttCues, orderedSubtitleUrls } from "./vtt";
import {
  parseTaxonomyPagedSuffix,
  parseTaxonomySlugParam,
  parseVideoSlugParam,
} from "./slug";
import { isSettingEnabled, type Settings } from "./settings";

export const pageRoutes = new Hono<Env>();

export function renderNotFoundHtml(c: any): string {
  const settings = c.get("settings");
  const siteName = settings.site_name?.trim() || "PlotVideos";
  const origin = new URL(c.req.url).origin;
  const lang = inferLangFromPath(c.req.path);
  return notFoundPage(lang, siteName, origin, c.req.path, {
    headCode: settings.head_code || "",
    footerCode: settings.footer_code || "",
    contactEmail: settings.contact_email?.trim() || "",
    contactTelegram: settings.contact_telegram?.trim() || "",
    contactWhatsapp: settings.contact_whatsapp?.trim() || "",
    compliance2257Title: settings.compliance_2257_title?.trim() || "18 U.S.C. 2257 Compliance Statement",
    compliance2257Enabled: isSettingEnabled(settings.compliance_2257_enabled),
    dmcaTitle: settings.dmca_title?.trim() || "DMCA / Copyright Policy",
    dmcaEnabled: isSettingEnabled(settings.dmca_enabled),
    siteUrl: origin,
    year: new Date().getFullYear(),
  });
}

async function resolveLangId(db: D1Database, code: string): Promise<number> {
  const row = await db.prepare("SELECT id FROM languages WHERE code = ?").bind(code).first<{ id: number }>();
  return row?.id ?? 0;
}

async function resolveTaxonomyListRowAndPage(
  c: any,
  db: D1Database,
  lang: string,
  kind: "tag" | "category",
  rawParam: string
): Promise<
  | { row: { id: number; name: string; slug: string }; page: number }
  | { redirect: string }
  | null
> {
  const stripped = rawParam.replace(/\.html$/i, "").trim().toLowerCase();
  if (!stripped) return null;

  const table = kind === "tag" ? "tags" : "categories";
  const prefix = langPrefix(lang);

  const rowFull = await db
    .prepare(`SELECT id, name, slug FROM ${table} WHERE slug = ?`)
    .bind(stripped)
    .first<{ id: number; name: string; slug: string }>();

  if (rowFull) {
    const qp = c.req.query("page");
    const page = qp ? Math.max(1, parseInt(qp, 10) || 1) : 1;
    if (page > 1) {
      return { redirect: taxonomyListingHref(prefix, kind, rowFull.slug, page) };
    }
    return { row: rowFull, page: 1 };
  }

  const paged = parseTaxonomyPagedSuffix(stripped);
  if (paged) {
    const row = await db
      .prepare(`SELECT id, name, slug FROM ${table} WHERE slug = ?`)
      .bind(paged.baseSlug)
      .first<{ id: number; name: string; slug: string }>();
    if (!row) return null;
    return { row, page: paged.page };
  }

  if (!parseTaxonomySlugParam(rawParam)) return null;
  return null;
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

function pageContext(c: any) {
  const settings: Settings = c.get("settings");
  const siteName = settings.site_name?.trim() || "PlotVideos";
  const siteSlogan = settings.site_slogan?.trim() || "";
  const siteDescription = settings.site_description?.trim() || "";
  const origin = new URL(c.req.url).origin;
  return {
    siteName,
    siteSlogan,
    siteDescription,
    headCode: settings.head_code || "",
    footerCode: settings.footer_code || "",
    origin,
    siteUrl: origin,
    year: new Date().getFullYear(),
    contactEmail: settings.contact_email?.trim() || "",
    contactTelegram: settings.contact_telegram?.trim() || "",
    contactWhatsapp: settings.contact_whatsapp?.trim() || "",
    compliance2257Title: settings.compliance_2257_title?.trim() || "18 U.S.C. 2257 Compliance Statement",
    compliance2257Enabled: isSettingEnabled(settings.compliance_2257_enabled),
    dmcaTitle: settings.dmca_title?.trim() || "DMCA / Copyright Policy",
    dmcaEnabled: isSettingEnabled(settings.dmca_enabled),
    adHomeSidebar: settings.ad_home_sidebar?.trim() || "",
    adHomeListTop: settings.ad_home_list_top?.trim() || "",
    adHomeListBottom: settings.ad_home_list_bottom?.trim() || "",
    adListingSidebar: settings.ad_listing_sidebar?.trim() || "",
    adListingListTop: settings.ad_listing_list_top?.trim() || "",
    adListingListBottom: settings.ad_listing_list_bottom?.trim() || "",
    adWatchTop: settings.ad_watch_top?.trim() || "",
    adWatchRelatedAbove: settings.ad_watch_related_above?.trim() || "",
    adWatchRelatedBelow: settings.ad_watch_related_below?.trim() || "",
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

function parseHomePageSize(raw: string | undefined): number {
  const n = parseInt(raw?.trim() || "16", 10);
  if (!Number.isFinite(n) || n < 1) return 16;
  return Math.min(n, 100);
}

async function resolveIndex(c: any, lang: string) {
  const db = c.env.DB;
  const {
    siteName,
    siteSlogan,
    siteDescription,
    headCode,
    footerCode,
    origin,
    siteUrl,
    year,
    contactEmail,
    contactTelegram,
    contactWhatsapp,
    compliance2257Title,
    compliance2257Enabled,
    dmcaTitle,
    dmcaEnabled,
    adHomeSidebar,
    adHomeListTop,
    adHomeListBottom,
  } = pageContext(c);
  const page = Math.max(parseInt(c.req.query("page") || "1"), 1);
  const pageSize = parseHomePageSize(c.get("settings").home_page_size);
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
      siteSlogan ? `${siteName} - ${siteSlogan}` : siteName,
      origin,
      {
        contactEmail,
        contactTelegram,
        contactWhatsapp,
        compliance2257Title,
        compliance2257Enabled,
        dmcaTitle,
        dmcaEnabled,
        headCode,
        footerCode,
        siteUrl,
        year,
        siteDescription,
        adHomeSidebar,
        adHomeListTop,
        adHomeListBottom,
      }
    )
  );
}

async function resolveTagListing(c: any, lang: string) {
  const db = c.env.DB;
  const resolved = await resolveTaxonomyListRowAndPage(c, db, lang, "tag", c.req.param("slug"));
  if (!resolved) return c.html(renderNotFoundHtml(c), 404);
  if ("redirect" in resolved) return c.redirect(resolved.redirect, 301);
  const { row, page } = resolved;

  const {
    siteName,
    headCode,
    footerCode,
    origin,
    siteUrl,
    year,
    contactEmail,
    contactTelegram,
    contactWhatsapp,
    compliance2257Title,
    compliance2257Enabled,
    dmcaTitle,
    dmcaEnabled,
    siteDescription,
    adListingSidebar,
    adListingListTop,
    adListingListBottom,
  } = pageContext(c);
  const langId = await resolveLangId(db, lang);
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
  const browserTitle = t(lang, "taxonomy_seo_title").replace("{name}", row.name);

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
      siteName,
      origin,
      {
        contactEmail,
        contactTelegram,
        contactWhatsapp,
        compliance2257Title,
        compliance2257Enabled,
        dmcaTitle,
        dmcaEnabled,
        headCode,
        footerCode,
        siteUrl,
        year,
        siteDescription,
        adListingSidebar,
        adListingListTop,
        adListingListBottom,
      }
    )
  );
}

async function resolveCategoryListing(c: any, lang: string) {
  const db = c.env.DB;
  const resolved = await resolveTaxonomyListRowAndPage(c, db, lang, "category", c.req.param("slug"));
  if (!resolved) return c.html(renderNotFoundHtml(c), 404);
  if ("redirect" in resolved) return c.redirect(resolved.redirect, 301);
  const { row, page } = resolved;

  const {
    siteName,
    headCode,
    footerCode,
    origin,
    siteUrl,
    year,
    contactEmail,
    contactTelegram,
    contactWhatsapp,
    compliance2257Title,
    compliance2257Enabled,
    dmcaTitle,
    dmcaEnabled,
    siteDescription,
    adListingSidebar,
    adListingListTop,
    adListingListBottom,
  } = pageContext(c);
  const langId = await resolveLangId(db, lang);
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
  const browserTitle = t(lang, "taxonomy_seo_title").replace("{name}", row.name);

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
      siteName,
      origin,
      {
        contactEmail,
        contactTelegram,
        contactWhatsapp,
        compliance2257Title,
        compliance2257Enabled,
        dmcaTitle,
        dmcaEnabled,
        headCode,
        footerCode,
        siteUrl,
        year,
        siteDescription,
        adListingSidebar,
        adListingListTop,
        adListingListBottom,
      }
    )
  );
}

async function resolveWatchBySlug(c: any, lang: string) {
  const db = c.env.DB;
  const slug = parseVideoSlugParam(c.req.param("slug"));
  if (!slug) return c.html(renderNotFoundHtml(c), 404);

  const video = await db.prepare("SELECT * FROM videos WHERE slug = ?").bind(slug).first<any>();
  if (!video) return c.html(renderNotFoundHtml(c), 404);
  return _renderWatch(c, lang, video);
}

async function resolveWatch(c: any, lang: string) {
  const db = c.env.DB;
  const id = Math.trunc(Number(c.req.param("id")));
  if (!Number.isFinite(id) || id < 1) return c.html(renderNotFoundHtml(c), 404);

  const video = await db
    .prepare("SELECT slug FROM videos WHERE id = ?")
    .bind(id)
    .first<{ slug: string }>();

  if (!video) return c.html(renderNotFoundHtml(c), 404);
  return c.redirect(`${langPrefix(lang)}/video/${video.slug}.html`, 302);
}

async function _renderWatch(c: any, lang: string, video: any) {
  const db = c.env.DB;
  const {
    siteName,
    headCode,
    footerCode,
    origin,
    siteUrl,
    year,
    contactEmail,
    contactTelegram,
    contactWhatsapp,
    compliance2257Title,
    compliance2257Enabled,
    dmcaTitle,
    dmcaEnabled,
    adListingSidebar,
    adWatchTop,
    adWatchRelatedAbove,
    adWatchRelatedBelow,
  } = pageContext(c);
  const id = video.id;
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
      .prepare("SELECT id, slug, title, duration, thumbnail_url FROM videos WHERE id != ? ORDER BY random_key DESC LIMIT 10")
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
        slug: video.slug,
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
      siteName,
      origin,
      {
        contactEmail,
        contactTelegram,
        contactWhatsapp,
        compliance2257Title,
        compliance2257Enabled,
        dmcaTitle,
        dmcaEnabled,
        headCode,
        footerCode,
        siteUrl,
        year,
        adListingSidebar,
        adWatchTop,
        adWatchRelatedAbove,
        adWatchRelatedBelow,
      }
    )
  );
}

function resolveStaticPage(c: any, lang: string, page: "2257" | "dmca") {
  const ctx = pageContext(c);
  const { siteName, origin, siteUrl, year, contactEmail, contactTelegram, contactWhatsapp } = ctx;
  const settings = c.get("settings");
  const enabled =
    page === "2257"
      ? isSettingEnabled(settings.compliance_2257_enabled)
      : isSettingEnabled(settings.dmca_enabled);
  if (!enabled) return c.html(renderNotFoundHtml(c), 404);
  const render = page === "2257" ? compliancePage : dmcaPage;
  const pageTitle =
    page === "2257"
      ? settings.compliance_2257_title?.trim() || "18 U.S.C. 2257 Compliance Statement"
      : settings.dmca_title?.trim() || "DMCA / Copyright Policy";
  const pageContent = page === "2257" ? settings.compliance_2257_content : settings.dmca_content;
  const footerNav = {
    compliance2257Title: ctx.compliance2257Title,
    compliance2257Enabled: ctx.compliance2257Enabled,
    dmcaTitle: ctx.dmcaTitle,
    dmcaEnabled: ctx.dmcaEnabled,
  };
  return c.html(
    render(
      lang,
      siteName,
      pageTitle,
      pageContent,
      contactEmail,
      contactTelegram,
      contactWhatsapp,
      origin,
      siteUrl,
      year,
      footerNav
    )
  );
}

pageRoutes.get("/", (c) => resolveIndex(c, DEFAULT_LANG));
pageRoutes.get("/2257.html", (c) => resolveStaticPage(c, DEFAULT_LANG, "2257"));
pageRoutes.get("/dmca.html", (c) => resolveStaticPage(c, DEFAULT_LANG, "dmca"));
pageRoutes.get("/videos/:id", (c) => resolveWatch(c, DEFAULT_LANG));
pageRoutes.get("/video/:slug", (c) => resolveWatchBySlug(c, DEFAULT_LANG));
pageRoutes.get("/tag/:slug", (c) => resolveTagListing(c, DEFAULT_LANG));
pageRoutes.get("/category/:slug", (c) => resolveCategoryListing(c, DEFAULT_LANG));

pageRoutes.get("/:lang/", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveIndex(c, lang);
});

pageRoutes.get("/:lang/2257.html", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveStaticPage(c, lang, "2257");
});

pageRoutes.get("/:lang/dmca.html", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveStaticPage(c, lang, "dmca");
});

pageRoutes.get("/:lang/videos/:id", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveWatch(c, lang);
});

pageRoutes.get("/:lang/video/:slug", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveWatchBySlug(c, lang);
});

pageRoutes.get("/:lang/tag/:slug", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveTagListing(c, lang);
});

pageRoutes.get("/:lang/category/:slug", (c) => {
  const lang = c.req.param("lang");
  if (!isValidLang(lang)) return c.html(renderNotFoundHtml(c), 404);
  return resolveCategoryListing(c, lang);
});
