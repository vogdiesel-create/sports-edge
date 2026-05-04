const fetch = require("node-fetch");

// ---------------------------------------------------------------------------
// DraftKings NBA Player Props aggregator
//
// Flow:
//   1. Fetch NBA event group (42648) to get list of today's events
//   2. For each event, fetch the offer catalog to find player prop categories
//   3. For each prop category, fetch the actual lines/odds
//   4. Return consolidated JSON
// ---------------------------------------------------------------------------

const DK_BASE = "https://sportsbook.draftkings.com/sites/US-SB/api/v5";
const NBA_EVENT_GROUP = "42648";

// Rate limit: stagger requests by 250ms to stay well under any soft limits
const STAGGER_MS = 250;

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
  };
}

async function fetchJSON(url) {
  const res = await fetch(url, { headers: browserHeaders(), timeout: 15000 });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} from ${url}`);
  }
  return res.json();
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ---------------------------------------------------------------------------
// Parse DK offer into a clean prop object
// ---------------------------------------------------------------------------
function parseOutcome(outcome, market, event) {
  return {
    player: outcome.label || outcome.participant || "Unknown",
    stat: market.label || market.name || "Unknown",
    line: outcome.line != null ? outcome.line : null,
    odds: outcome.oddsAmerican || outcome.odds || null,
    oddsDecimal: outcome.oddsDecimal || null,
    over_under: outcome.label && outcome.label.toLowerCase().includes("under") ? "under" : "over",
    event: event.name || "Unknown",
    eventId: event.eventId || event.id || null,
    book: "DraftKings",
  };
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------
exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return cors204();
  }

  const sport = (event.queryStringParameters && event.queryStringParameters.sport) || "nba";
  const groupId =
    (event.queryStringParameters && event.queryStringParameters.group_id) || NBA_EVENT_GROUP;

  try {
    // Step 1: Get event group
    const groupUrl = `${DK_BASE}/eventgroups/${groupId}`;
    const groupData = await fetchJSON(groupUrl);

    // Extract events -- DK nests them in different spots depending on version
    let events = [];
    if (groupData.eventGroup && groupData.eventGroup.events) {
      events = groupData.eventGroup.events;
    } else if (groupData.events) {
      events = groupData.events;
    } else if (groupData.eventGroup && groupData.eventGroup.offerCategories) {
      // Sometimes events are inside offer categories
      const cats = groupData.eventGroup.offerCategories || [];
      for (const cat of cats) {
        const subCats = cat.offerSubcategoryDescriptors || [];
        for (const sub of subCats) {
          if (sub.offerSubcategory && sub.offerSubcategory.offers) {
            for (const offerGroup of sub.offerSubcategory.offers) {
              for (const offer of offerGroup) {
                if (offer.eventId) {
                  events.push({ eventId: offer.eventId, name: offer.label || "Event" });
                }
              }
            }
          }
        }
      }
    }

    // Step 2: Extract player props from offer categories
    const allProps = [];
    const categories = groupData.eventGroup
      ? groupData.eventGroup.offerCategories || []
      : [];

    for (const category of categories) {
      const catName = category.name || "";
      // Player props are usually in categories with "player" in the name
      const isPlayerProp =
        catName.toLowerCase().includes("player") ||
        catName.toLowerCase().includes("prop") ||
        catName.toLowerCase().includes("performance");

      const subCats = category.offerSubcategoryDescriptors || [];

      for (const subCat of subCats) {
        const subName = subCat.name || "";
        const offers =
          subCat.offerSubcategory && subCat.offerSubcategory.offers
            ? subCat.offerSubcategory.offers
            : [];

        for (const offerGroup of offers) {
          if (!Array.isArray(offerGroup)) continue;
          for (const offer of offerGroup) {
            const outcomes = offer.outcomes || [];
            const marketLabel = offer.label || subName || catName;

            for (const outcome of outcomes) {
              allProps.push({
                player: outcome.participant || outcome.label || "Unknown",
                stat: marketLabel,
                category: catName,
                subcategory: subName,
                line: outcome.line != null ? outcome.line : null,
                odds: outcome.oddsAmerican || null,
                oddsDecimal: outcome.oddsDecimal || null,
                over_under: outcome.label
                  ? outcome.label.toLowerCase().includes("under")
                    ? "under"
                    : "over"
                  : null,
                eventId: offer.eventId || null,
                book: "DraftKings",
              });
            }
          }
        }
      }
    }

    // Step 3: If no props found from inline data, try subcategory endpoints
    if (allProps.length === 0 && categories.length > 0) {
      for (const category of categories) {
        const subCats = category.offerSubcategoryDescriptors || [];
        for (const subCat of subCats) {
          if (!subCat.subcategoryId) continue;
          try {
            await sleep(STAGGER_MS);
            const subUrl =
              `${DK_BASE}/eventgroups/${groupId}/categories/${category.offerCategoryId}` +
              `/subcategories/${subCat.subcategoryId}`;
            const subData = await fetchJSON(subUrl);

            const subOffers =
              subData.offerSubcategory && subData.offerSubcategory.offers
                ? subData.offerSubcategory.offers
                : [];

            for (const offerGroup of subOffers) {
              if (!Array.isArray(offerGroup)) continue;
              for (const offer of offerGroup) {
                const outcomes = offer.outcomes || [];
                for (const outcome of outcomes) {
                  allProps.push({
                    player: outcome.participant || outcome.label || "Unknown",
                    stat: offer.label || subCat.name || category.name || "Unknown",
                    category: category.name || "",
                    subcategory: subCat.name || "",
                    line: outcome.line != null ? outcome.line : null,
                    odds: outcome.oddsAmerican || null,
                    oddsDecimal: outcome.oddsDecimal || null,
                    over_under: outcome.label
                      ? outcome.label.toLowerCase().includes("under")
                        ? "under"
                        : "over"
                      : null,
                    eventId: offer.eventId || null,
                    book: "DraftKings",
                  });
                }
              }
            }
          } catch {
            // Skip failed subcategory fetches
          }
        }
      }
    }

    return respond(200, {
      sport,
      groupId,
      eventsFound: events.length,
      propsFound: allProps.length,
      props: allProps,
      fetchedAt: new Date().toISOString(),
    });
  } catch (err) {
    return respond(502, {
      error: "DraftKings fetch failed",
      message: err.message,
    });
  }
};

// ---------------------------------------------------------------------------
// Helpers
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

function cors204() {
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
