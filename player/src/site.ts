/**
 * Default site / product name (header logo and `<title>` suffix).
 * Production: set `SITE_NAME` in the Cloudflare dashboard only — not in wrangler.toml `[vars]` or `.dev.vars`,
 * so deploys and local dev do not override the portal value.
 */
export const DEFAULT_SITE_NAME = "PlotVideos";

export function siteNameFromEnv(env: { SITE_NAME?: string }): string {
  const v = env.SITE_NAME?.trim();
  return v || DEFAULT_SITE_NAME;
}
