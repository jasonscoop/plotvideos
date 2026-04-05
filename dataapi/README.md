# Data API (Cloudflare Worker)

Read-only HTTP API for the player sync: same routes and JSON shape as the former crawler `api` service (`GET /languages`, `GET /videos`).

## Setup

1. In the Cloudflare dashboard, create a [Hyperdrive](https://developers.cloudflare.com/hyperdrive/) config pointing at the same Postgres database as the crawler (`DB_URL`).
2. Set `[[hyperdrive]]` `id` in `wrangler.toml` to that config’s ID (replace `replace-with-hyperdrive-config-id`).
3. Set the API key (must match player `fetch_api_key`):

   ```bash
   npx wrangler secret put CRAWLER_API_KEY
   ```

4. Optional: override `B2_CDN_DOMAIN` in `wrangler.toml` `[vars]` if it differs from the default.

## Local dev

Create `dataapi/.dev.vars` with `CRAWLER_API_KEY=...`. Run `npx wrangler dev` (Hyperdrive must be configured; use dashboard connection string or Hyperdrive local dev as in Cloudflare docs).

## Deploy

```bash
npm install
npx wrangler deploy
```

Point the player site setting **`fetch_api_url`** at the worker’s origin (no path suffix), e.g. `https://luckvideos-dataapi.<subdomain>.workers.dev`.
