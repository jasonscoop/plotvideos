export const DEFAULT_SITE_NAME = "PlotVideos";

export function siteNameFromEnv(env: { SITE_NAME?: string }): string {
  const v = env.SITE_NAME?.trim();
  return v || DEFAULT_SITE_NAME;
}
