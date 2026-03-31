export const DEFAULT_ID_OFFSET = 0;

export function parseIdOffset(raw: string | undefined): number {
  const s = raw?.trim();
  if (s == null || s === "") return DEFAULT_ID_OFFSET;
  const n = parseInt(s, 10);
  return Number.isFinite(n) ? n : DEFAULT_ID_OFFSET;
}

/** Public `/video/{n}.html` path segment = D1 `videos.id` + offset. */
export function publicWatchSegmentFromVideoId(videoId: number, slugOffset: number): number {
  return videoId + slugOffset;
}

/** Resolve `videos.id` from the numeric URL segment (inverse of publicWatchSegmentFromVideoId). */
export function videoIdFromPublicWatchSegment(segment: number, slugOffset: number): number {
  return segment - slugOffset;
}

/** URL segment for /tag/… and /category/… (stored in D1). */
export function slugify(name: string): string {
  const s = name
    .trim()
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return s || "item";
}

/** Strip optional `.html` from route param; allow `[a-z0-9-]+`. */
export function parseTaxonomySlugParam(param: string): string | null {
  const raw = param.replace(/\.html$/i, "").trim().toLowerCase();
  if (!raw || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(raw)) return null;
  return raw;
}
