export interface VttCue {
  start: number;
  end: number;
  text: string;
}

function toSec(t: string): number {
  const p = t.replace(".", ":").split(":");
  if (p.length === 3) return +p[0] * 60 + +p[1] + +p[2] / 1000;
  return +p[0] * 3600 + +p[1] * 60 + +p[2] + +(p[3] || 0) / 1000;
}

/** Parse WebVTT body (WEBVTT header optional). */
export function parseVtt(text: string): VttCue[] {
  const cues: VttCue[] = [];
  const body = text.replace(/^WEBVTT[^\n]*\n*/i, "").trim();
  const blocks = body.split(/\n\n+/);
  for (const block of blocks) {
    const lines = block.trim().split("\n");
    for (let j = 0; j < lines.length; j++) {
      const m = lines[j].match(
        /(\d{2}:\d{2}[.:]\d{2,3})\s*-->\s*(\d{2}:\d{2}[.:]\d{2,3})/
      );
      if (m) {
        const txt = lines
          .slice(j + 1)
          .join(" ")
          .replace(/<[^>]+>/g, "")
          .trim();
        if (txt) cues.push({ start: toSec(m[1]), end: toSec(m[2]), text: txt });
        break;
      }
    }
  }
  return cues;
}

/** Same ordering as client `loadTranscript` (page lang first, then others). */
export function orderedSubtitleUrls(
  tracks: { lang: string; url: string }[],
  pageLang: string
): string[] {
  const urls: string[] = [];
  const byLang: Record<string, string> = {};
  for (const tr of tracks) {
    if (tr.url) byLang[tr.lang] = tr.url;
  }
  if (byLang[pageLang]) urls.push(byLang[pageLang]);
  for (const lang of Object.keys(byLang)) {
    if (lang !== pageLang && byLang[lang]) urls.push(byLang[lang]);
  }
  return urls;
}

async function fetchWithTimeout(url: string, ms: number): Promise<Response> {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), ms);
  try {
    return await fetch(url, {
      signal: ac.signal,
      headers: { Accept: "text/vtt,text/plain,*/*" },
    });
  } finally {
    clearTimeout(t);
  }
}

export async function fetchVttCues(urls: string[], ms = 8000): Promise<VttCue[] | null> {
  for (const url of urls) {
    try {
      const r = await fetchWithTimeout(url, ms);
      if (!r.ok) continue;
      const text = await r.text();
      const cues = parseVtt(text);
      if (cues.length) return cues;
    } catch {
      continue;
    }
  }
  return null;
}
