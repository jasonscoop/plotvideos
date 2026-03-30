#!/usr/bin/env node
const { readFileSync, writeFileSync, existsSync } = require("fs");
const { resolve } = require("path");

const root = resolve(__dirname, "..");
const envPath = resolve(root, ".env");

const fileVars = {};
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const i = trimmed.indexOf("=");
    if (i > 0) fileVars[trimmed.slice(0, i)] = trimmed.slice(i + 1);
  }
}

function get(key) {
  return process.env[key] || fileVars[key] || "";
}

const dbId = get("D1_DATABASE_ID");
if (!dbId) {
  console.error("D1_DATABASE_ID is required (set as env var or in .env)");
  process.exit(1);
}

const name = get("WORKER_NAME") || "player";
const dbName = get("D1_DATABASE_NAME") || `${name}-db`;

const toml = `name = "${name}"
main = "src/index.ts"
compatibility_date = "2025-01-01"

[[rules]]
type = "Text"
globs = ["**/*.css"]
fallthrough = true

[[rules]]
type = "Text"
globs = ["**/*.client.js"]
fallthrough = true

[[rules]]
type = "Text"
globs = ["**/*.svg"]
fallthrough = true

[dev]
port = 8000

[[d1_databases]]
binding = "DB"
database_name = "${dbName}"
database_id = "${dbId}"

[triggers]
crons = ["*/10 * * * *", "0 * * * *"]

[vars]
SLUG_OFFSET_VALUE = "${get("SLUG_OFFSET_VALUE") || "0"}"
SITE_NAME = "${get("SITE_NAME")}"
GA_ID = "${get("GA_ID")}"
`;

writeFileSync(resolve(root, "wrangler.toml"), toml);

const secrets = {
  VIDEO_FETCH_API_URL: get("VIDEO_FETCH_API_URL"),
  VIDEO_FETCH_API_KEY: get("VIDEO_FETCH_API_KEY"),
};
writeFileSync(resolve(root, ".secrets.json"), JSON.stringify(secrets));

console.log("wrangler.toml generated");
