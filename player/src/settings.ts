export interface Settings {
  fetch_api_url: string;
  fetch_api_key: string;
  id_offset: string;
  site_name: string;
  site_slogan: string;
  head_code: string;
  footer_code: string;
  contact_email: string;
  contact_telegram: string;
  contact_whatsapp: string;
  compliance_2257_title: string;
  compliance_2257_enabled: string;
  compliance_2257_content: string;
  dmca_title: string;
  dmca_enabled: string;
  dmca_content: string;
}

const DEFAULT_SETTINGS: Settings = {
  fetch_api_url: "",
  fetch_api_key: "",
  id_offset: "0",
  site_name: "PlotVideos",
  site_slogan: "",
  head_code: "",
  footer_code: "",
  contact_email: "",
  contact_telegram: "",
  contact_whatsapp: "",
  compliance_2257_title: "18 U.S.C. 2257 Compliance Statement",
  compliance_2257_enabled: "1",
  compliance_2257_content: "",
  dmca_title: "DMCA / Copyright Policy",
  dmca_enabled: "1",
  dmca_content: "",
};

let cachedSettings: Settings | null = null;

export async function loadSettings(db: D1Database): Promise<Settings> {
  const rows = await db.prepare("SELECT key, value FROM settings").all<{ key: string; value: string }>();
  const settings = { ...DEFAULT_SETTINGS };
  for (const row of rows.results) {
    if (row.key in settings) {
      settings[row.key as keyof Settings] = row.value;
    }
  }
  return settings;
}

export async function getSettings(db: D1Database): Promise<Settings> {
  if (cachedSettings) return cachedSettings;
  cachedSettings = await loadSettings(db);
  return cachedSettings;
}
