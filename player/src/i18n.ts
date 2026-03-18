export const LANGUAGES = [
  { code: "en", native: "English" },
  { code: "de", native: "Deutsch" },
  { code: "fr", native: "Français" },
  { code: "nl", native: "Nederlands" },
  { code: "ja", native: "日本語" },
  { code: "ko", native: "한국어" },
  { code: "pt", native: "Português" },
  { code: "ar", native: "العربية" },
  { code: "es", native: "Español" },
  { code: "zh", native: "简体中文" },
] as const;

export const LANG_CODES = LANGUAGES.map((l) => l.code);
export const DEFAULT_LANG = "en";

export type LangCode = (typeof LANGUAGES)[number]["code"];

export function isValidLang(code: string): code is LangCode {
  return LANG_CODES.includes(code as any);
}

export function langPrefix(lang: string): string {
  return lang === DEFAULT_LANG ? "" : `/${lang}`;
}

export function nativeName(code: string): string {
  return LANGUAGES.find((l) => l.code === code)?.native || code;
}

const translations: Record<string, Record<string, string>> = {
  en: {
    search: "Search",
    search_placeholder: "Search",
    latest_videos: "Latest videos",
    no_videos: "No videos found.",
    previous: "Previous",
    next: "Next",
    videos: "videos",
    original: "Original",
    host: "Host",
    duration: "Duration",
    subtitles: "subtitles",
    no_thumbnail: "No thumbnail",
  },
  de: {
    search: "Suchen",
    search_placeholder: "Suchen",
    latest_videos: "Neueste Videos",
    no_videos: "Keine Videos gefunden.",
    previous: "Zurück",
    next: "Weiter",
    videos: "Videos",
    original: "Original",
    host: "Host",
    duration: "Dauer",
    subtitles: "Untertitel",
    no_thumbnail: "Kein Thumbnail",
  },
  fr: {
    search: "Rechercher",
    search_placeholder: "Rechercher",
    latest_videos: "Dernières vidéos",
    no_videos: "Aucune vidéo trouvée.",
    previous: "Précédent",
    next: "Suivant",
    videos: "vidéos",
    original: "Original",
    host: "Source",
    duration: "Durée",
    subtitles: "sous-titres",
    no_thumbnail: "Pas de miniature",
  },
  nl: {
    search: "Zoeken",
    search_placeholder: "Zoeken",
    latest_videos: "Nieuwste video's",
    no_videos: "Geen video's gevonden.",
    previous: "Vorige",
    next: "Volgende",
    videos: "video's",
    original: "Origineel",
    host: "Bron",
    duration: "Duur",
    subtitles: "ondertitels",
    no_thumbnail: "Geen thumbnail",
  },
  ja: {
    search: "検索",
    search_placeholder: "検索",
    latest_videos: "最新の動画",
    no_videos: "動画が見つかりません。",
    previous: "前へ",
    next: "次へ",
    videos: "本の動画",
    original: "オリジナル",
    host: "ソース",
    duration: "再生時間",
    subtitles: "字幕",
    no_thumbnail: "サムネイルなし",
  },
  ko: {
    search: "검색",
    search_placeholder: "검색",
    latest_videos: "최신 동영상",
    no_videos: "동영상을 찾을 수 없습니다.",
    previous: "이전",
    next: "다음",
    videos: "개의 동영상",
    original: "원본",
    host: "소스",
    duration: "재생시간",
    subtitles: "자막",
    no_thumbnail: "썸네일 없음",
  },
  pt: {
    search: "Pesquisar",
    search_placeholder: "Pesquisar",
    latest_videos: "Vídeos recentes",
    no_videos: "Nenhum vídeo encontrado.",
    previous: "Anterior",
    next: "Próximo",
    videos: "vídeos",
    original: "Original",
    host: "Fonte",
    duration: "Duração",
    subtitles: "legendas",
    no_thumbnail: "Sem miniatura",
  },
  ar: {
    search: "بحث",
    search_placeholder: "بحث",
    latest_videos: "أحدث الفيديوهات",
    no_videos: "لم يتم العثور على فيديوهات.",
    previous: "السابق",
    next: "التالي",
    videos: "فيديوهات",
    original: "الأصلي",
    host: "المصدر",
    duration: "المدة",
    subtitles: "ترجمات",
    no_thumbnail: "لا توجد صورة مصغرة",
  },
  es: {
    search: "Buscar",
    search_placeholder: "Buscar",
    latest_videos: "Últimos videos",
    no_videos: "No se encontraron videos.",
    previous: "Anterior",
    next: "Siguiente",
    videos: "videos",
    original: "Original",
    host: "Fuente",
    duration: "Duración",
    subtitles: "subtítulos",
    no_thumbnail: "Sin miniatura",
  },
  zh: {
    search: "搜索",
    search_placeholder: "搜索",
    latest_videos: "最新视频",
    no_videos: "未找到视频。",
    previous: "上一页",
    next: "下一页",
    videos: "个视频",
    original: "原标题",
    host: "来源",
    duration: "时长",
    subtitles: "字幕",
    no_thumbnail: "无缩略图",
  },
};

export function t(lang: string, key: string): string {
  return translations[lang]?.[key] || translations.en[key] || key;
}

export function isRtl(lang: string): boolean {
  return lang === "ar";
}
