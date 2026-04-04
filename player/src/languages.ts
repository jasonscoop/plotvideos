import { DEFAULT_LANG } from "./i18n";

export type LanguageRow = {
  code: string;
  name: string;
  locale: string;
  flag: string;
};

let cachedLanguages: LanguageRow[] | null = null;

export async function loadLanguages(db: D1Database): Promise<LanguageRow[]> {
  const r = await db
    .prepare("SELECT code, name, locale, flag FROM languages ORDER BY id ASC")
    .all<LanguageRow>();
  return r.results;
}

export async function getLanguages(db: D1Database): Promise<LanguageRow[]> {
  if (cachedLanguages) return cachedLanguages;
  cachedLanguages = await loadLanguages(db);
  return cachedLanguages;
}

export function isValidLangCode(code: string, languages: LanguageRow[]): boolean {
  return languages.some((l) => l.code === code);
}

export function inferLangFromPath(path: string, languages: LanguageRow[]): string {
  const seg = path.split("/").filter(Boolean)[0];
  if (seg && isValidLangCode(seg, languages)) return seg;
  return DEFAULT_LANG;
}

export function languageName(code: string, languages: LanguageRow[]): string {
  return languages.find((l) => l.code === code)?.name ?? code;
}

export function languageFlag(code: string, languages: LanguageRow[]): string {
  return languages.find((l) => l.code === code)?.flag ?? "";
}

export function pathWithoutLangPrefix(path: string, languages: LanguageRow[]): string {
  const parts = path.split("/").filter(Boolean);
  if (parts.length === 0) return "/";
  if (languages.some((l) => l.code === parts[0])) {
    const rest = parts.slice(1);
    return rest.length ? `/${rest.join("/")}` : "/";
  }
  return path.startsWith("/") ? path : `/${path}`;
}
