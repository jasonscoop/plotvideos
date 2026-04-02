export const DEFAULT_ID_OFFSET = 0;

export function parseIdOffset(raw: string | undefined): number {
  const s = raw?.trim();
  if (s == null || s === "") return DEFAULT_ID_OFFSET;
  const n = parseInt(s, 10);
  return Number.isFinite(n) ? n : DEFAULT_ID_OFFSET;
}

export function generateVideoSlug(originalId: number, title: string, slugFrom: string, idOffset: number): string {
  if (slugFrom === "title_original_id") {
    return `${slugify(title)}-${originalId}`;
  }
  return String(originalId + idOffset);
}

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

export function parseVideoSlugParam(param: string): string | null {
  let raw = param.replace(/\.html$/i, "").trim().toLowerCase();
  raw = raw.replace(/\.0+$/, "");
  if (!raw || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(raw)) return null;
  return raw;
}

export function parseTaxonomySlugParam(param: string): string | null {
  const raw = param.replace(/\.html$/i, "").trim().toLowerCase();
  if (!raw || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(raw)) return null;
  return raw;
}
