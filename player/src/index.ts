import { Hono } from "hono";
import { apiRoutes } from "./api";
import { pageRoutes } from "./pages";
import { mediaRoutes } from "./b2";

export type Env = {
  Bindings: {
    DB: D1Database;
    B2_BUCKET: string;
    B2_REGION: string;
    B2_KEY_ID: string;
    B2_APP_KEY: string;
  };
};

const app = new Hono<Env>();

app.route("/api", apiRoutes);
app.route("/media", mediaRoutes);
app.route("/", pageRoutes);

export default app;
