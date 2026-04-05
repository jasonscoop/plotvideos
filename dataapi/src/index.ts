import postgres from "postgres";

interface Env {
  HYPERDRIVE: Hyperdrive;
  CRAWLER_API_KEY: string;
  B2_CDN_DOMAIN: string;
}

interface Hyperdrive {
  connectionString: string;
}

const LANGUAGES = [
  { code: "en", name: "English", locale: "en-US", flag: "🇺🇸" },
  { code: "de", name: "Deutsch", locale: "de-DE", flag: "🇩🇪" },
  { code: "fr", name: "Français", locale: "fr-FR", flag: "🇫🇷" },
  { code: "nl", name: "Nederlands", locale: "nl-NL", flag: "🇳🇱" },
  { code: "ja", name: "日本語", locale: "ja-JP", flag: "🇯🇵" },
  { code: "ko", name: "한국어", locale: "ko-KR", flag: "🇰🇷" },
  { code: "pt", name: "Português", locale: "pt-PT", flag: "🇵🇹" },
  { code: "ar", name: "العربية", locale: "ar-SA", flag: "🇸🇦" },
  { code: "es", name: "Español", locale: "es-ES", flag: "🇪🇸" },
  { code: "zh", name: "简体中文", locale: "zh-CN", flag: "🇨🇳" },
] as const;

function storePrefix(videoId: number): string {
  const vid = Math.floor(videoId);
  const shard = String(vid % 100).padStart(2, "0");
  return `${shard}/${vid}`;
}

function videoCdnKeys(videoId: number) {
  const p = storePrefix(videoId);
  const hlsP = `${p}/hls`;
  return {
    prefix: p,
    translatedS3Key: `${p}/subtitles/`,
    thumbnailS3Key: `${p}/thumbnail.webp`,
    videoS3Key: `${p}/video.mp4`,
    hlsMasterS3Key: `${hlsP}/master.m3u8`,
  };
}

function b2CdnObjectUrl(base: string, objectKey: string): string {
  const b = base.replace(/\/$/, "");
  const k = objectKey.replace(/^\//, "");
  return `${b}/${k}`;
}

function parseJsonArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.map((x) => String(x));
  if (typeof v === "string") {
    try {
      const j = JSON.parse(v) as unknown;
      return Array.isArray(j) ? j.map((x) => String(x)) : [];
    } catch {
      return [];
    }
  }
  return [];
}

type LangRow = (typeof LANGUAGES)[number];

interface VideoRow {
  id: string | number;
  title: string;
  duration: number;
  width: number;
  height: number;
  tags: unknown;
  categories: unknown;
  keyword_name: string | null;
}

interface TermRow {
  text: string;
  lang: string;
  translation: string;
}

interface TitleRow {
  video_id: string | number;
  lang: string;
  translated_title: string;
}

function termsToNestedMap(rows: TermRow[]): Map<string, Map<string, string>> {
  const m = new Map<string, Map<string, string>>();
  for (const r of rows) {
    let inner = m.get(r.lang);
    if (!inner) {
      inner = new Map();
      m.set(r.lang, inner);
    }
    inner.set(r.text, r.translation);
  }
  return m;
}

function buildPayload(
  video: VideoRow,
  languages: readonly LangRow[],
  titleByVideo: Map<number, Map<string, string>>,
  globalTermMap: Map<string, Map<string, string>>,
  cdnBase: string
) {
  const vid = Number(video.id);
  const sp = videoCdnKeys(vid);
  const titleMap = titleByVideo.get(vid) ?? new Map<string, string>();
  const keyword = video.keyword_name ?? "";
  const tags = parseJsonArray(video.tags);
  const categories = parseJsonArray(video.categories);
  const allTerms = new Set<string>();
  if (keyword) allTerms.add(keyword);
  for (const t of tags) allTerms.add(t);
  for (const c of categories) allTerms.add(c);

  const translations: Record<
    string,
    { title: string; keyword: string; tags: string[]; categories: string[] }
  > = {};
  for (const lang of languages) {
    const langTerms = globalTermMap.get(lang.code);
    const title = titleMap.get(lang.code) ?? "";
    translations[lang.code] = {
      title,
      keyword: keyword ? (langTerms?.get(keyword) ?? keyword) : "",
      tags: tags.map((t) => langTerms?.get(t) ?? t),
      categories: categories.map((c) => langTerms?.get(c) ?? c),
    };
  }

  const subtitle_tracks = languages.map((lang) => ({
    lang: lang.code,
    label: lang.name,
    url: b2CdnObjectUrl(cdnBase, `${sp.translatedS3Key}${lang.code}.vtt`),
  }));

  return {
    original_id: vid,
    title: video.title,
    duration: video.duration,
    width: video.width,
    height: video.height,
    thumbnail_url: b2CdnObjectUrl(cdnBase, sp.thumbnailS3Key),
    video_url: b2CdnObjectUrl(cdnBase, sp.videoS3Key),
    hls_url: b2CdnObjectUrl(cdnBase, sp.hlsMasterS3Key),
    keyword,
    tags,
    categories,
    translations,
    subtitle_tracks,
  };
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "GET") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    const apiKey = request.headers.get("X-API-Key");
    if (!env.CRAWLER_API_KEY || apiKey !== env.CRAWLER_API_KEY) {
      return jsonResponse({ detail: "Invalid API key" }, 403);
    }

    const url = new URL(request.url);
    const pathname = url.pathname.replace(/\/$/, "") || "/";

    if (pathname === "/languages") {
      return jsonResponse([...LANGUAGES]);
    }

    if (pathname !== "/videos") {
      return new Response("Not Found", { status: 404 });
    }

    const limitRaw = url.searchParams.get("limit");
    const limit = Math.min(
      100,
      Math.max(1, limitRaw === null || limitRaw === "" ? 20 : parseInt(limitRaw, 10) || 20)
    );

    const afterRaw = url.searchParams.get("after_id");
    let afterId: number | null = null;
    if (afterRaw !== null && afterRaw !== "") {
      const parsed = parseInt(afterRaw, 10);
      if (Number.isNaN(parsed) || parsed < 0) {
        return jsonResponse({ detail: "Invalid after_id" }, 422);
      }
      afterId = parsed;
    }

    const cdnBase = env.B2_CDN_DOMAIN || "https://play.luckvideos.com";

    const sql = postgres(env.HYPERDRIVE.connectionString, {
      max: 1,
      fetch_types: false,
    });

    try {
      const rows: VideoRow[] =
        afterId === null
          ? await sql`
              SELECT v.id, v.title, v.duration, v.width, v.height, v.tags, v.categories, k.name AS keyword_name
              FROM videos v
              LEFT JOIN keywords k ON k.id = v.keyword_id
              WHERE v.status = 'uploaded'
              ORDER BY v.id ASC
              LIMIT ${limit}
            `
          : await sql`
              SELECT v.id, v.title, v.duration, v.width, v.height, v.tags, v.categories, k.name AS keyword_name
              FROM videos v
              LEFT JOIN keywords k ON k.id = v.keyword_id
              WHERE v.status = 'uploaded' AND v.id > ${afterId}
              ORDER BY v.id ASC
              LIMIT ${limit}
            `;

      if (rows.length === 0) {
        return jsonResponse([]);
      }

      const videoIds = rows.map((r) => Number(r.id));

      const titleRows: TitleRow[] = await sql`
        SELECT video_id, lang, translated_title
        FROM title_translations
        WHERE video_id IN ${sql(videoIds)}
      `;

      const titleByVideo = new Map<number, Map<string, string>>();
      for (const tr of titleRows) {
        const vid = Number(tr.video_id);
        let m = titleByVideo.get(vid);
        if (!m) {
          m = new Map();
          titleByVideo.set(vid, m);
        }
        m.set(tr.lang, tr.translated_title);
      }

      const uniqueTexts = new Set<string>();
      for (const v of rows) {
        const kw = v.keyword_name ?? "";
        if (kw) uniqueTexts.add(kw);
        for (const t of parseJsonArray(v.tags)) uniqueTexts.add(t);
        for (const c of parseJsonArray(v.categories)) uniqueTexts.add(c);
      }

      const textList = [...uniqueTexts];
      let termRows: TermRow[] = [];
      if (textList.length > 0) {
        termRows = await sql`
          SELECT text, lang, translation
          FROM terms
          WHERE text IN ${sql(textList)}
        `;
      }

      const termNested = termsToNestedMap(termRows);

      const payloads = rows.map((row) =>
        buildPayload(row, LANGUAGES, titleByVideo, termNested, cdnBase)
      );

      return jsonResponse(payloads);
    } catch {
      return jsonResponse({ detail: "Internal Server Error" }, 500);
    } finally {
      await sql.end({ timeout: 0 });
    }
  },
};
