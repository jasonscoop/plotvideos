import { Hono } from "hono";
import type { Env } from "./index";

export const mediaRoutes = new Hono<Env>();

mediaRoutes.all("/*", async (c) => {
  const { B2_BUCKET, B2_REGION, B2_KEY_ID, B2_APP_KEY } = c.env;
  const request = c.req.raw;
  const url = new URL(request.url);

  const method = request.method;
  const service = "s3";
  const host = `${B2_BUCKET}.s3.${B2_REGION}.backblazeb2.com`;
  const canonicalUri = url.pathname.replace(/^\/media/, "") || "/";

  if (method === "OPTIONS") {
    return new Response(null, { status: 204 });
  }

  const now = new Date();
  const amzDate = toAmzDate(now);
  const dateStamp = toDateStamp(now);

  const canonicalHeaders =
    `host:${host}\n` +
    `x-amz-content-sha256:UNSIGNED-PAYLOAD\n` +
    `x-amz-date:${amzDate}\n`;
  const signedHeaders = "host;x-amz-content-sha256;x-amz-date";
  const payloadHash = "UNSIGNED-PAYLOAD";
  const canonicalQuerystring = url.searchParams.toString();

  const canonicalRequest =
    `${method}\n${canonicalUri}\n${canonicalQuerystring}\n${canonicalHeaders}\n${signedHeaders}\n${payloadHash}`;

  const algorithm = "AWS4-HMAC-SHA256";
  const credentialScope = `${dateStamp}/${B2_REGION}/${service}/aws4_request`;
  const hashedCanonicalRequest = await hashSHA256(canonicalRequest);
  const stringToSign = `${algorithm}\n${amzDate}\n${credentialScope}\n${hashedCanonicalRequest}`;

  const signingKey = await getSignatureKey(B2_APP_KEY, dateStamp, B2_REGION, service);
  const signature = await hmacHex(signingKey, stringToSign);

  const authorization =
    `${algorithm} Credential=${B2_KEY_ID}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

  const headers: Record<string, string> = {
    "Authorization": authorization,
    "x-amz-date": amzDate,
    "x-amz-content-sha256": payloadHash,
    "host": host,
    "User-Agent": "Cloudflare-Worker-B2-SigV4",
  };
  const range = request.headers.get("Range");
  if (range) headers["Range"] = range;

  const fetchUrl = `https://${host}${canonicalUri}${canonicalQuerystring ? "?" + canonicalQuerystring : ""}`;
  let response: Response;
  try {
    response = await fetch(fetchUrl, { method, headers });
  } catch (e: any) {
    return c.text(`B2 fetch error: ${e.message}\nURL: ${fetchUrl}`, 502);
  }

  if (response.status === 404 && canonicalUri.endsWith("/thumbnail.webp")) {
    const fallbackUri = "/thumbnail.webp";
    const fbCanonicalRequest =
      `${method}\n${fallbackUri}\n${canonicalQuerystring}\n${canonicalHeaders}\n${signedHeaders}\n${payloadHash}`;
    const fbHashed = await hashSHA256(fbCanonicalRequest);
    const fbStringToSign = `${algorithm}\n${amzDate}\n${credentialScope}\n${fbHashed}`;
    const fbSignature = await hmacHex(signingKey, fbStringToSign);
    const fbAuth =
      `${algorithm} Credential=${B2_KEY_ID}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${fbSignature}`;

    const fbHeaders = { ...headers, "Authorization": fbAuth };
    const fbUrl = `https://${host}${fallbackUri}`;
    response = await fetch(fbUrl, { method, headers: fbHeaders });
  }

  const respHeaders = new Headers(response.headers);
  const path = canonicalUri.toLowerCase();
  if (path.endsWith(".vtt")) respHeaders.set("Content-Type", "text/vtt");
  else if (path.endsWith(".m3u8")) respHeaders.set("Content-Type", "application/vnd.apple.mpegurl");
  else if (path.endsWith(".m4s")) respHeaders.set("Content-Type", "video/iso.segment");
  else if (path.endsWith(".ts")) respHeaders.set("Content-Type", "video/mp2t");
  respHeaders.set("Accept-Ranges", "bytes");
  respHeaders.set("Cache-Control", "public, max-age=31536000");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: respHeaders,
  });
});

async function hashSHA256(str: string): Promise<string> {
  const buf = new TextEncoder().encode(str);
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return toHex(new Uint8Array(hash));
}

async function hmac(key: ArrayBuffer | Uint8Array, str: string): Promise<Uint8Array> {
  const cryptoKey = await crypto.subtle.importKey(
    "raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", cryptoKey, new TextEncoder().encode(str));
  return new Uint8Array(sig);
}

async function hmacHex(key: ArrayBuffer | Uint8Array, str: string): Promise<string> {
  return toHex(await hmac(key, str));
}

async function getSignatureKey(
  key: string, dateStamp: string, region: string, service: string
): Promise<Uint8Array> {
  const kDate = await hmac(new TextEncoder().encode("AWS4" + key), dateStamp);
  const kRegion = await hmac(kDate, region);
  const kService = await hmac(kRegion, service);
  return await hmac(kService, "aws4_request");
}

function toHex(arr: Uint8Array): string {
  return Array.from(arr).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function toAmzDate(date: Date): string {
  return date.toISOString().slice(0, 19).replace(/[:-]/g, "") + "Z";
}

function toDateStamp(date: Date): string {
  return date.toISOString().slice(0, 10).replace(/-/g, "");
}
