#!/usr/bin/env node
const { transformSync } = require("esbuild");
const { readFileSync, writeFileSync, readdirSync } = require("fs");
const { resolve, extname } = require("path");

const dir = resolve(__dirname, "..", "src", "static");

const loaders = { ".css": "css", ".js": "js" };

for (const file of readdirSync(dir)) {
  const ext = extname(file);
  const loader = loaders[ext];
  if (!loader) continue;

  const filePath = resolve(dir, file);
  const src = readFileSync(filePath, "utf8");
  const { code } = transformSync(src, { loader, minify: true });
  writeFileSync(filePath, code);
  const saved = src.length - code.length;
  console.log(`${file}: ${src.length} → ${code.length} (−${saved})`);
}
