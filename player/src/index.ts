import { Hono } from "hono";
import { apiRoutes, refreshRandomKeys, syncFromCrawler } from "./api";
import { pageRoutes } from "./pages";
import STYLES_CSS from "./styles.css";
import LANG_DROPDOWN_JS from "./lang-dropdown.client.js";
import WATCH_PAGE_JS from "./watch-page.client.js";
import LOGO_SVG from "./logo.svg";

export type Env = {
  Bindings: {
    DB: D1Database;
    VIDEO_FETCH_API_URL: string;
    VIDEO_FETCH_API_KEY: string;
    SITE_NAME?: string;
    GA_ID?: string;
    /** Added to each D1 `videos.id` for the public watch URL only (e.g. id 5 + offset 100 → `/video/105.html`). Not stored in D1. Defaults to 0 if unset. */
    SLUG_OFFSET_VALUE?: string;
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

app.get("/styles.css", (c) => {
  return c.body(STYLES_CSS, 200, {
    "Content-Type": "text/css; charset=utf-8",
    "Cache-Control": "public, max-age=3600",
  });
});

app.get("/lang-dropdown.js", (c) => {
  return c.body(LANG_DROPDOWN_JS, 200, {
    "Content-Type": "application/javascript; charset=utf-8",
    "Cache-Control": "public, max-age=3600",
  });
});

app.get("/watch-page.js", (c) => {
  return c.body(WATCH_PAGE_JS, 200, {
    "Content-Type": "application/javascript; charset=utf-8",
    "Cache-Control": "public, max-age=3600",
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

app.route("/api", apiRoutes);
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
