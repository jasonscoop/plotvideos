/**
 * B2 S3-compatible proxy with SigV4 signing (Backblaze B2).
 * @typedef {{ B2_BUCKET: string; B2_REGION: string; B2_KEY_ID: string; B2_APP_KEY: string; CORS_ALLOWS: string }} Env
 */

/** @param {Request} request @param {Env} env */
async function handleFetch(request, env) {
  const { B2_BUCKET, B2_REGION, B2_KEY_ID, B2_APP_KEY, CORS_ALLOWS } = env;
  const url = new URL(request.url);

  function getCorsOrigin(request) {
    const origin = request.headers.get("Origin");
    const allowed = CORS_ALLOWS ? CORS_ALLOWS.split("\n").map((s) => s.trim()).filter(Boolean) : [];
    if (origin && allowed.includes(origin)) {
      return origin;
    }
    return "";
  }
  const corsOrigin = getCorsOrigin(request);

  if (request.method === "OPTIONS") {
    const preflightHeaders = { Vary: "Origin" };
    if (corsOrigin) {
      preflightHeaders["Access-Control-Allow-Origin"] = corsOrigin;
      preflightHeaders["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS";
      preflightHeaders["Access-Control-Allow-Headers"] = "Range, Content-Type, Authorization";
      preflightHeaders["Access-Control-Expose-Headers"] = "Content-Length, Content-Range";
      preflightHeaders["Access-Control-Max-Age"] = "86400";
    }
    return new Response(null, { status: 204, headers: preflightHeaders });
  }

  const method = request.method;
  const service = "s3";
  const host = `${B2_BUCKET}.s3.${B2_REGION}.backblazeb2.com`;
  const canonicalUri = url.pathname;

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
    `${method}\n` +
    `${canonicalUri}\n` +
    `${canonicalQuerystring}\n` +
    `${canonicalHeaders}\n` +
    `${signedHeaders}\n` +
    `${payloadHash}`;

  const algorithm = "AWS4-HMAC-SHA256";
  const credentialScope = `${dateStamp}/${B2_REGION}/${service}/aws4_request`;

  const hashedCanonicalRequest = await hashSHA256(canonicalRequest);

  const stringToSign =
    `${algorithm}\n` +
    `${amzDate}\n` +
    `${credentialScope}\n` +
    `${hashedCanonicalRequest}`;

  const signingKey = await getSignatureKey(B2_APP_KEY, dateStamp, B2_REGION, service);
  const signature = await hmacHex(signingKey, stringToSign);

  const authorizationHeader =
    `${algorithm} ` +
    `Credential=${B2_KEY_ID}/${credentialScope}, ` +
    `SignedHeaders=${signedHeaders}, ` +
    `Signature=${signature}`;

  const headers = new Headers(request.headers);

  headers.set("Authorization", authorizationHeader);
  headers.set("x-amz-date", amzDate);
  headers.set("x-amz-content-sha256", payloadHash);
  headers.set("host", host);

  if (!headers.has("User-Agent")) {
    headers.set("User-Agent", "Cloudflare-Worker-B2-SigV4");
  }

  const fetchUrl = `https://${host}${canonicalUri}${canonicalQuerystring ? "?" + canonicalQuerystring : ""}`;

  const response = await fetch(fetchUrl, {
    method,
    headers,
    body: method === "GET" || method === "HEAD" ? undefined : request.body,
  });

  if (response.status === 404 && canonicalUri.includes("/thumbnail.webp") && canonicalUri !== "/thumbnail.webp") {
    const defaultUrl = new URL(request.url);
    defaultUrl.pathname = "/thumbnail.webp";
    const defaultRequest = new Request(defaultUrl.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
    return handleFetch(defaultRequest, env);
  }

  const responseHeaders = new Headers(response.headers);
  if (corsOrigin) {
    responseHeaders.set("Access-Control-Allow-Origin", corsOrigin);
    responseHeaders.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
    responseHeaders.set("Access-Control-Allow-Headers", "Range, Content-Type, Authorization");
    responseHeaders.set("Access-Control-Expose-Headers", "Content-Length, Content-Range");
  }

  const path = url.pathname.toLowerCase();
  // B2 may store wrong Content-Type (e.g. video/* or octet-stream). Override so Chrome doesn’t
  // open the URL in the video pipeline (second Range request, DevTools “media” type).
  let explicitType = "";
  if (path.endsWith(".webp")) {
    explicitType = "image/webp";
  } else if (path.endsWith(".png")) {
    explicitType = "image/png";
  } else if (path.endsWith(".jpg") || path.endsWith(".jpeg")) {
    explicitType = "image/jpeg";
  } else if (path.endsWith(".gif")) {
    explicitType = "image/gif";
  } else if (path.endsWith(".avif")) {
    explicitType = "image/avif";
  } else if (path.endsWith(".svg")) {
    explicitType = "image/svg+xml";
  } else if (path.endsWith(".ico")) {
    explicitType = "image/x-icon";
  } else if (path.endsWith(".vtt")) {
    explicitType = "text/vtt";
  } else if (path.endsWith(".m3u8")) {
    explicitType = "application/vnd.apple.mpegurl";
  } else if (path.endsWith(".m4s")) {
    explicitType = "video/iso.segment";
  } else if (path.endsWith(".ts")) {
    explicitType = "video/mp2t";
  } else if (path.endsWith(".mp4")) {
    explicitType = "video/mp4";
  } else if (path.endsWith(".webm")) {
    explicitType = "video/webm";
  }
  if (explicitType) {
    responseHeaders.delete("Content-Type");
    responseHeaders.set("Content-Type", explicitType);
    // Stops Chrome from MIME-sniffing navigation loads as video (avoids duplicate Range/media fetch).
    responseHeaders.set("X-Content-Type-Options", "nosniff");
  }
  responseHeaders.set("Accept-Ranges", "bytes");
  responseHeaders.set("Cache-Control", "public, max-age=31536000");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}

export default {
  /** @param {Request} request @param {Env} env */
  fetch(request, env) {
    return handleFetch(request, env);
  },
};

async function hashSHA256(str) {
  const buf = new TextEncoder().encode(str);
  const hashBuffer = await crypto.subtle.digest("SHA-256", buf);
  return toHex(new Uint8Array(hashBuffer));
}

async function hmac(key, str) {
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    key,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", cryptoKey, new TextEncoder().encode(str));
  return new Uint8Array(sig);
}

async function hmacHex(key, str) {
  const sig = await hmac(key, str);
  return toHex(sig);
}

async function getSignatureKey(key, dateStamp, regionName, serviceName) {
  const kDate = await hmac(new TextEncoder().encode("AWS4" + key), dateStamp);
  const kRegion = await hmac(kDate, regionName);
  const kService = await hmac(kRegion, serviceName);
  const kSigning = await hmac(kService, "aws4_request");
  return kSigning;
}

function toHex(arr) {
  return Array.from(arr).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function toAmzDate(date) {
  const iso = date.toISOString();
  return iso.slice(0, 19).replace(/[:-]/g, "") + "Z";
}

function toDateStamp(date) {
  return date.toISOString().slice(0, 10).replace(/-/g, "");
}
