import { Hono } from "hono";
import { apiRoutes, refreshRandomKeys, syncFromCrawler } from "./api";
import { pageRoutes } from "./pages";
import { registerSitemapRoutes } from "./sitemap";
import STYLES_CSS from "./styles.css";
import LANG_DROPDOWN_JS from "./lang-dropdown.client.js";
import WATCH_PAGE_JS from "./watch-page.client.js";
import LOGO_SVG from "./logo.svg";
import { ASSET_HASHES } from "./asset-hashes";

export type Env = {
  Bindings: {
    DB: D1Database;
    FETCH_API_URL: string;
    FETCH_API_KEY: string;
    SITENAME?: string;
    GA_ID?: string;
    ID_OFFSET?: string;
    CONTACT_EMAIL?: string;
  };
};

let synced = false;

const app = new Hono<Env>();

app.use("*", async (c, next) => {
  if (!synced) {
    synced = true;
    c.executionCtx.waitUntil(syncFromCrawler(c.env));
  }
  return next();
});

app.get(`/styles.${ASSET_HASHES.css}.css`, (c) => {
  return c.body(STYLES_CSS, 200, {
    "Content-Type": "text/css; charset=utf-8",
    "Cache-Control": "public, max-age=31536000, immutable",
  });
});

app.get(`/lang-dropdown.${ASSET_HASHES.langDropdown}.js`, (c) => {
  return c.body(LANG_DROPDOWN_JS, 200, {
    "Content-Type": "application/javascript; charset=utf-8",
    "Cache-Control": "public, max-age=31536000, immutable",
  });
});

app.get(`/watch-page.${ASSET_HASHES.watchPage}.js`, (c) => {
  return c.body(WATCH_PAGE_JS, 200, {
    "Content-Type": "application/javascript; charset=utf-8",
    "Cache-Control": "public, max-age=31536000, immutable",
  });
});

app.get("/favicon.ico", (c) => {
  return c.body(LOGO_SVG, 200, {
    "Content-Type": "image/svg+xml",
    "Cache-Control": "public, max-age=86400",
  });
});

app.get("/logo.svg", (c) => {
  return c.body(LOGO_SVG, 200, {
    "Content-Type": "image/svg+xml",
    "Cache-Control": "public, max-age=86400",
  });
});

app.get("/robots.txt", (c) => {
  const origin = new URL(c.req.url).origin;
  const body = `User-agent: *\nAllow: /\n\nSitemap: ${origin}/sitemap.xml\n`;
  return c.body(body, 200, {
    "Content-Type": "text/plain; charset=utf-8",
    "Cache-Control": "public, max-age=86400",
  });
});

app.route("/api", apiRoutes);
registerSitemapRoutes(app);
app.route("/", pageRoutes);

export default {
  fetch: app.fetch,
  async scheduled(event: ScheduledEvent, env: Env["Bindings"], ctx: ExecutionContext) {
    if (event.cron === "0 * * * *") {
      ctx.waitUntil(refreshRandomKeys(env.DB));
    } else {
      ctx.waitUntil(syncFromCrawler(env));
    }
  },
};
