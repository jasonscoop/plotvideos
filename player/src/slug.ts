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
