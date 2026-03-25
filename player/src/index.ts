import { Hono } from "hono";
import { apiRoutes, syncFromCrawler } from "./api";
import { pageRoutes } from "./pages";
import STYLES_CSS from "./styles.css";
import LANG_DROPDOWN_JS from "./lang-dropdown.client.js";
import WATCH_PAGE_JS from "./watch-page.client.js";

export type Env = {
  Bindings: {
    DB: D1Database;
    VIDEO_FETCH_API_URL: string;
    VIDEO_FETCH_API_KEY: string;
    /** Added to each crawler `original_id` to form the public numeric slug (e.g. 5 + 100 → `/video/105.html`). */
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

app.route("/api", apiRoutes);
app.route("/", pageRoutes);

export default app;

export const scheduled: ExportedHandlerScheduledHandler<Env["Bindings"]> = async (
  _event,
  env,
  ctx
) => {
  ctx.waitUntil(syncFromCrawler(env));
};
