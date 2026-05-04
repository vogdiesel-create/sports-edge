const fetch = require("node-fetch");

// ---------------------------------------------------------------------------
// Domain allowlist -- only sportsbook APIs, never arbitrary URLs
// ---------------------------------------------------------------------------
const ALLOWED_DOMAINS = [
  "sportsbook.draftkings.com",
  "sports.mi.betmgm.com",
  "guest.api.arcadia.pinnacle.com",
  "www.bovada.lv",
  "api.pointsbet.com",
  "sbapi.mi.sportsbook.fanduel.com",
];

// ---------------------------------------------------------------------------
// Per-domain rate limiter -- max 1 request per second per domain
// Uses in-memory timestamps (resets on cold start, which is fine for Lambda)
// ---------------------------------------------------------------------------
const lastRequestTime = {};

function rateLimitOk(domain) {
  const now = Date.now();
  const last = lastRequestTime[domain] || 0;
  if (now - last < 1000) return false;
  lastRequestTime[domain] = now;
  return true;
}

// ---------------------------------------------------------------------------
// Shared browser-like headers so sportsbooks don't reject us immediately
// ---------------------------------------------------------------------------
function browserHeaders() {
  return {
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    Accept: "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    Referer: "https://sportsbook.draftkings.com/",
    Origin: "https://sportsbook.draftkings.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
  };
}

// ---------------------------------------------------------------------------
// CORS preflight + main handler
// ---------------------------------------------------------------------------
exports.handler = async (event) => {
  // Handle CORS preflight
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
      body: "",
    };
  }

  const targetUrl = event.queryStringParameters && event.queryStringParameters.url;

  if (!targetUrl) {
    return respond(400, { error: "Missing 'url' query parameter" });
  }

  // Validate URL format
  let parsed;
  try {
    parsed = new URL(targetUrl);
  } catch {
    return respond(400, { error: "Invalid URL format" });
  }

  // Enforce domain allowlist
  if (!ALLOWED_DOMAINS.includes(parsed.hostname)) {
    return respond(403, {
      error: `Domain '${parsed.hostname}' is not in the allowlist`,
      allowed: ALLOWED_DOMAINS,
    });
  }

  // Enforce rate limit
  if (!rateLimitOk(parsed.hostname)) {
    return respond(429, {
      error: `Rate limited -- max 1 req/s per domain (${parsed.hostname})`,
    });
  }

  try {
    const res = await fetch(targetUrl, {
      method: "GET",
      headers: browserHeaders(),
      timeout: 15000,
    });

    const contentType = res.headers.get("content-type") || "";
    let body;

    if (contentType.includes("application/json")) {
      body = await res.json();
    } else {
      body = await res.text();
    }

    return respond(res.status, {
      status: res.status,
      source: parsed.hostname,
      data: body,
      fetchedAt: new Date().toISOString(),
    });
  } catch (err) {
    return respond(502, {
      error: "Upstream fetch failed",
      message: err.message,
      source: parsed.hostname,
    });
  }
};

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
function respond(statusCode, body) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
    body: JSON.stringify(body, null, 2),
  };
}
