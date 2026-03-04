export default {
  async fetch(request, env) {
    const { B2_BUCKET, B2_REGION, B2_KEY_ID, B2_APP_KEY } = env;
    const url = new URL(request.url);

    function getCorsOrigin(request) {
      const origin = request.headers.get("Origin");
      const allowed = [
        "http://localhost",
        "http://localhost:8000",
        "https://wp.garymeng.com",
        "https://luckvideos.com",
        "https://hopevideos.com",
        "https://muchvideos.com",
        "https://weekvideos.com",
        "https://toovideos.com",
        "https://flatvideos.com",
      ];
      if (origin && allowed.includes(origin)) {
        return origin;  // return just the matched origin
      }
      return "";
    }
    const corsOrigin = getCorsOrigin(request);

    // --- Handle CORS Preflight ---
    if (request.method === "OPTIONS") {
      const preflightHeaders = { "Vary": "Origin" };
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

    // Dates for signing
    const now = new Date();
    const amzDate = toAmzDate(now);
    const dateStamp = toDateStamp(now);

    // ************* TASK 1: Create canonical request *************
    // Headers
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

    // ************* TASK 2: Create string to sign *************
    const algorithm = "AWS4-HMAC-SHA256";
    const credentialScope = `${dateStamp}/${B2_REGION}/${service}/aws4_request`;

    const hashedCanonicalRequest = await hashSHA256(canonicalRequest);

    const stringToSign =
      `${algorithm}\n` +
      `${amzDate}\n` +
      `${credentialScope}\n` +
      `${hashedCanonicalRequest}`;

    // ************* TASK 3: Calculate signature *************
    const signingKey = await getSignatureKey(B2_APP_KEY, dateStamp, B2_REGION, service);
    const signature = await hmacHex(signingKey, stringToSign);

    // ************* TASK 4: Build authorization header *************
    const authorizationHeader = 
      `${algorithm} ` +
      `Credential=${B2_KEY_ID}/${credentialScope}, ` +
      `SignedHeaders=${signedHeaders}, ` +
      `Signature=${signature}`;

    // ************* TASK 5: Prepare headers for fetch *************
    const headers = new Headers(request.headers);

    headers.set("Authorization", authorizationHeader);
    headers.set("x-amz-date", amzDate);
    headers.set("x-amz-content-sha256", payloadHash);
    headers.set("host", host);

    // Backblaze requires User-Agent (optional but good)
    if (!headers.has("User-Agent")) {
      headers.set("User-Agent", "Cloudflare-Worker-B2-SigV4");
    }

    const fetchUrl = `https://${host}${canonicalUri}${canonicalQuerystring ? "?" + canonicalQuerystring : ""}`;

    // ************* TASK 6: Fetch from B2 *************
    const response = await fetch(fetchUrl, {
      method,
      headers,
      body: method === "GET" || method === "HEAD" ? undefined : request.body,
    });

    // ************* TASK 6.5: Handle thumbnail fallback *************
    // If the request is for a thumbnail and we get 404, try the default thumbnail
    if (response.status === 404 && canonicalUri.includes('/thumbnail.webp') && canonicalUri !== '/thumbnail.webp') {
      // Create a new request for the default thumbnail by modifying the original URL
      const defaultUrl = new URL(request.url);
      defaultUrl.pathname = '/thumbnail.webp';
      
      // Recursively call this same function with the default thumbnail URL
      const defaultRequest = new Request(defaultUrl.toString(), {
        method: request.method,
        headers: request.headers,
        body: request.body
      });
      
      return await this.fetch(defaultRequest, env);
    }

    // ************* TASK 7: Setup response headers *************
    const responseHeaders = new Headers(response.headers);
    if (corsOrigin) {
      responseHeaders.set("Access-Control-Allow-Origin", corsOrigin);
      responseHeaders.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
      responseHeaders.set("Access-Control-Allow-Headers", "Range, Content-Type, Authorization");
      responseHeaders.set("Access-Control-Expose-Headers", "Content-Length, Content-Range");
    }

    const path = url.pathname.toLowerCase();
    if (path.endsWith(".vtt")) {
      responseHeaders.set("Content-Type", "text/vtt");
    } else if (path.endsWith(".m3u8")) {
      responseHeaders.set("Content-Type", "application/vnd.apple.mpegurl");
    } else if (path.endsWith(".m4s")) {
      responseHeaders.set("Content-Type", "video/iso.segment");
    } else if (path.endsWith(".ts")) {
      responseHeaders.set("Content-Type", "video/mp2t");
    }
    responseHeaders.set("Accept-Ranges", "bytes");
    // Make sure to allow seeking and caching on Cloudflare edge
    responseHeaders.set("Cache-Control", "public, max-age=31536000");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  }
};

// --- Helper functions ---

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
  return Array.from(arr).map(b => b.toString(16).padStart(2, "0")).join("");
}

function toAmzDate(date) {
  const iso = date.toISOString();
  return iso.slice(0, 19).replace(/[:-]/g, "") + "Z";
}


function toDateStamp(date) {
  return date.toISOString().slice(0, 10).replace(/-/g, "");
}
