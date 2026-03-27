const GA4_MEASUREMENT_ID = /^G-[A-Z0-9]+$/i;

export function gaMeasurementIdFromEnv(env: { GA_ID?: string }): string | undefined {
  const v = env.GA_ID?.trim();
  if (!v || !GA4_MEASUREMENT_ID.test(v)) return undefined;
  return v;
}
