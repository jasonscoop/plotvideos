export const DEFAULT_SITE_NAME = "PlotVideos";

export function siteNameFromEnv(env: { SITENAME?: string }): string {
  const v = env.SITENAME?.trim();
  return v || DEFAULT_SITE_NAME;
}
