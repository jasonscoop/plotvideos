export interface Settings {
  fetch_api_url: string;
  fetch_api_key: string;
  id_offset: string;
  slug_from: string;
  home_page_size: string;
  site_name: string;
  site_slogan: string;
  site_description: string;
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
  ad_home_sidebar: string;
  ad_home_list_top: string;
  ad_home_list_bottom: string;
  ad_listing_sidebar: string;
  ad_listing_list_top: string;
  ad_listing_list_bottom: string;
  ad_watch_top: string;
  ad_watch_related_above: string;
  ad_watch_related_below: string;
}

const DEFAULT_SETTINGS: Settings = {
  fetch_api_url: "",
  fetch_api_key: "",
  id_offset: "0",
  slug_from: "original_id_plus_offset",
  home_page_size: "16",
  site_name: "PlotVideos",
  site_slogan: "",
  site_description: "",
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
  ad_home_sidebar: "",
  ad_home_list_top: "",
  ad_home_list_bottom: "",
  ad_listing_sidebar: "",
  ad_listing_list_top: "",
  ad_listing_list_bottom: "",
  ad_watch_top: "",
  ad_watch_related_above: "",
  ad_watch_related_below: "",
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
