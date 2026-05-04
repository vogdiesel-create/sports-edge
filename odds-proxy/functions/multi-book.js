const fetch = require("node-fetch");

// ---------------------------------------------------------------------------
// Multi-Book Odds Aggregator
//
// Hits DraftKings, BetMGM, Pinnacle, FanDuel, Bovada in PARALLEL.
// Consolidates odds by (player, stat, line).
// Calculates devigged fair probabilities.
// Flags +EV opportunities.
// ---------------------------------------------------------------------------

const STAGGER_MS = 250;

function browserHeaders(referer) {
  return {
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    Accept: "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    Referer: referer || "https://www.google.com/",
  };
}

async function fetchJSON(url, referer) {
  const res = await fetch(url, {
    headers: browserHeaders(referer),
    timeout: 15000,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${url}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// American odds -> implied probability (no vig)
// ---------------------------------------------------------------------------
function americanToImplied(odds) {
  if (odds == null || isNaN(odds)) return null;
  const o = Number(odds);
  if (o > 0) return 100 / (o + 100);
  if (o < 0) return Math.abs(o) / (Math.abs(o) + 100);
  return null;
}

// ---------------------------------------------------------------------------
// Devig: multiplicative method
// Given over_prob and under_prob (implied, with vig), return fair probs
// ---------------------------------------------------------------------------
function devigMultiplicative(overImplied, underImplied) {
  if (!overImplied || !underImplied) return { fairOver: null, fairUnder: null };
  const total = overImplied + underImplied;
  return {
    fairOver: overImplied / total,
    fairUnder: underImplied / total,
  };
}

// ---------------------------------------------------------------------------
// Implied probability -> American odds
// ---------------------------------------------------------------------------
function impliedToAmerican(prob) {
  if (!prob || prob <= 0 || prob >= 1) return null;
  if (prob >= 0.5) return Math.round((-prob / (1 - prob)) * 100);
  return Math.round(((1 - prob) / prob) * 100);
}

// ---------------------------------------------------------------------------
// Book-specific fetchers -- each returns array of normalized prop objects
// ---------------------------------------------------------------------------

async function fetchDraftKings(sport) {
  const groupId = sport === "nba" ? "42648" : sport === "nfl" ? "88808" : "42648";
  const url = `https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/${groupId}`;

  try {
    const data = await fetchJSON(url, "https://sportsbook.draftkings.com/");
    const props = [];
    const categories = data.eventGroup ? data.eventGroup.offerCategories || [] : [];

    for (const cat of categories) {
      for (const sub of cat.offerSubcategoryDescriptors || []) {
        const offers =
          sub.offerSubcategory && sub.offerSubcategory.offers
            ? sub.offerSubcategory.offers
            : [];
        for (const group of offers) {
          if (!Array.isArray(group)) continue;
          for (const offer of group) {
            for (const outcome of offer.outcomes || []) {
              props.push({
                player: (outcome.participant || outcome.label || "").trim(),
                stat: (offer.label || sub.name || cat.name || "").trim(),
                line: outcome.line != null ? Number(outcome.line) : null,
                odds: outcome.oddsAmerican ? Number(outcome.oddsAmerican) : null,
                oddsDecimal: outcome.oddsDecimal ? Number(outcome.oddsDecimal) : null,
                over_under: outcome.label
                  ? outcome.label.toLowerCase().includes("under")
                    ? "under"
                    : "over"
                  : null,
                book: "DraftKings",
              });
            }
          }
        }
      }
    }
    return props;
  } catch (err) {
    return [{ book: "DraftKings", error: err.message }];
  }
}

async function fetchBetMGM() {
  // BetMGM uses a different API structure
  // Try the main NBA offerings endpoint
  const url =
    "https://sports.mi.betmgm.com/cds-api/bettingoffer/fixtures?" +
    "x-bwin-accessid=NmFjOTEwMjQtOTAzYi00OTFjLWE2ZGMtNzI1MzNlMjdjMDcy&" +
    "lang=en-us&country=US&userCountry=US&fixtureTypes=Standard&" +
    "state=Latest&offerMapping=Ede&sportIds=7&regionIds=9&competitionIds=264";

  try {
    const data = await fetchJSON(url, "https://sports.mi.betmgm.com/");
    const props = [];
    const fixtures = data.fixtures || [];

    for (const fixture of fixtures) {
      const games = fixture.games || [];
      for (const game of games) {
        const results = game.results || [];
        for (const result of results) {
          if (result.name && result.americanOdds != null) {
            props.push({
              player: (result.name.value || result.name || "").toString().trim(),
              stat: (game.name && game.name.value ? game.name.value : "").trim(),
              line: result.attr != null ? Number(result.attr) : null,
              odds: result.americanOdds ? Number(result.americanOdds) : null,
              oddsDecimal: result.odds ? Number(result.odds) : null,
              over_under: result.name && result.name.value
                ? result.name.value.toLowerCase().includes("under")
                  ? "under"
                  : "over"
                : null,
              book: "BetMGM",
            });
          }
        }
      }
    }
    return props;
  } catch (err) {
    return [{ book: "BetMGM", error: err.message }];
  }
}

async function fetchPinnacle() {
  // Pinnacle guest API for NBA lines
  const url =
    "https://guest.api.arcadia.pinnacle.com/0.1/leagues/487/matchups?" +
    "brandId=0&withSpecials=true";

  try {
    const data = await fetchJSON(url, "https://www.pinnacle.com/");
    const props = [];

    if (!Array.isArray(data)) return props;

    for (const matchup of data) {
      if (!matchup.special) continue;
      const special = matchup.special;
      const desc = special.description || "";

      for (const market of matchup.prices || []) {
        props.push({
          player: desc.trim(),
          stat: (special.category || "").trim(),
          line: market.points != null ? Number(market.points) : null,
          odds: market.price ? Number(market.price) : null,
          oddsDecimal: market.price ? Number(market.price) : null,
          over_under: market.designation
            ? market.designation.toLowerCase() === "under"
              ? "under"
              : "over"
            : null,
          book: "Pinnacle",
        });
      }
    }
    return props;
  } catch (err) {
    return [{ book: "Pinnacle", error: err.message }];
  }
}

async function fetchFanDuel() {
  // FanDuel NBA player props - iterate events and prop tabs
  const BASE = "https://sbapi.mi.sportsbook.fanduel.com/api";
  const AK = "FhMFpcPWXMeyZxOx";
  const TABS = ["player-points", "player-rebounds", "player-assists", "player-threes"];

  try {
    // Step 1: Get NBA events
    const landing = await fetchJSON(
      `${BASE}/content-managed-page?page=CUSTOM&customPageId=nba&pbHorizontal=true&_ak=${AK}`,
      "https://sportsbook.fanduel.com/"
    );
    const events = landing.attachments ? landing.attachments.events || {} : {};
    const gameEvents = Object.entries(events)
      .filter(([, ev]) => {
        const name = (ev.name || "").toLowerCase();
        return name.includes("v") || name.includes("@");
      })
      .map(([id, ev]) => ({ id, name: ev.name }));

    const props = [];

    // Step 2: For each game, fetch each prop tab
    for (const game of gameEvents.slice(0, 15)) {
      for (const tab of TABS) {
        try {
          const tabData = await fetchJSON(
            `${BASE}/event-page?eventId=${game.id}&tab=${tab}&_ak=${AK}`,
            "https://sportsbook.fanduel.com/"
          );
          const markets = (tabData.attachments || {}).markets || {};
          for (const [, market] of Object.entries(markets)) {
            for (const runner of market.runners || []) {
              const name = (runner.runnerName || "").trim();
              if (!name || ["Over","Under","Yes","No","Odd","Even"].includes(name)) continue;
              const odds = runner.winRunnerOdds;
              if (!odds) continue;
              const american = odds.americanDisplayOdds
                ? Number(odds.americanDisplayOdds.americanOdds)
                : null;
              if (american == null) continue;
              props.push({
                player: name,
                stat: tab.replace("player-", ""),
                line: runner.handicap != null ? Number(runner.handicap) : 0,
                odds: american,
                oddsDecimal: american > 0 ? 1 + american/100 : 1 + 100/Math.abs(american),
                over_under: "over",
                book: "FanDuel",
              });
            }
          }
        } catch (_) { /* skip failed tabs */ }
      }
    }
    return props;
  } catch (err) {
    return [{ book: "FanDuel", error: err.message }];
  }
}

async function fetchBovada() {
  // Bovada NBA props
  const url =
    "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba";

  try {
    const data = await fetchJSON(url, "https://www.bovada.lv/");
    const props = [];

    if (!Array.isArray(data)) return props;

    for (const group of data) {
      const events = group.events || [];
      for (const evt of events) {
        const markets = evt.displayGroups || [];
        for (const dg of markets) {
          for (const market of dg.markets || []) {
            const desc = market.description || "";
            for (const outcome of market.outcomes || []) {
              const price = outcome.price || {};
              props.push({
                player: (outcome.description || "").trim(),
                stat: desc.trim(),
                line: price.handicap != null ? Number(price.handicap) : null,
                odds: price.american ? Number(price.american.replace("+", "")) : null,
                oddsDecimal: price.decimal ? Number(price.decimal) : null,
                over_under: outcome.type
                  ? outcome.type.toLowerCase() === "u"
                    ? "under"
                    : "over"
                  : null,
                book: "Bovada",
              });
            }
          }
        }
      }
    }
    return props;
  } catch (err) {
    return [{ book: "Bovada", error: err.message }];
  }
}

// ---------------------------------------------------------------------------
// Consolidate + find +EV
// ---------------------------------------------------------------------------
function consolidateAndFindEV(allProps) {
  // Filter out error entries and entries without required fields
  const valid = allProps.filter((p) => p.player && p.stat && !p.error);

  // Group by normalized key: player|stat|line
  const groups = {};
  for (const prop of valid) {
    const key = `${prop.player.toLowerCase()}|${prop.stat.toLowerCase()}|${prop.line || ""}`;
    if (!groups[key]) {
      groups[key] = {
        player: prop.player,
        stat: prop.stat,
        line: prop.line,
        books: [],
      };
    }
    groups[key].books.push({
      book: prop.book,
      odds: prop.odds,
      oddsDecimal: prop.oddsDecimal,
      over_under: prop.over_under,
    });
  }

  // For groups with multiple books, calculate devigged fair value
  const opportunities = [];

  for (const [key, group] of Object.entries(groups)) {
    if (group.books.length < 2) continue;

    // Find sharpest book (Pinnacle preferred, then average)
    const pinnacle = group.books.find((b) => b.book === "Pinnacle");

    // Get over/under pairs for devigging
    const overBooks = group.books.filter((b) => b.over_under === "over");
    const underBooks = group.books.filter((b) => b.over_under === "under");

    // Use Pinnacle as the fair-value anchor if available
    let fairOverProb = null;
    let fairUnderProb = null;

    if (pinnacle) {
      const pinnOver = overBooks.find((b) => b.book === "Pinnacle");
      const pinnUnder = underBooks.find((b) => b.book === "Pinnacle");
      if (pinnOver && pinnUnder) {
        const dv = devigMultiplicative(
          americanToImplied(pinnOver.odds),
          americanToImplied(pinnUnder.odds)
        );
        fairOverProb = dv.fairOver;
        fairUnderProb = dv.fairUnder;
      }
    }

    // If no Pinnacle, try to devig from any book that has both sides
    if (!fairOverProb) {
      for (const book of ["DraftKings", "FanDuel", "BetMGM", "Bovada"]) {
        const ov = overBooks.find((b) => b.book === book);
        const un = underBooks.find((b) => b.book === book);
        if (ov && un) {
          const dv = devigMultiplicative(
            americanToImplied(ov.odds),
            americanToImplied(un.odds)
          );
          fairOverProb = dv.fairOver;
          fairUnderProb = dv.fairUnder;
          break;
        }
      }
    }

    // Flag +EV: any book offering odds better than fair value
    for (const entry of group.books) {
      const impliedProb = americanToImplied(entry.odds);
      if (!impliedProb) continue;

      let fairProb =
        entry.over_under === "under" ? fairUnderProb : fairOverProb;
      if (!fairProb) continue;

      const ev = (1 / impliedProb - 1) * fairProb - (1 - fairProb);

      if (ev > 0) {
        opportunities.push({
          player: group.player,
          stat: group.stat,
          line: group.line,
          book: entry.book,
          odds: entry.odds,
          over_under: entry.over_under,
          fairProb: Math.round(fairProb * 1000) / 1000,
          fairOdds: impliedToAmerican(fairProb),
          impliedProb: Math.round(impliedProb * 1000) / 1000,
          ev: Math.round(ev * 10000) / 100, // as percentage
          booksCompared: group.books.length,
        });
      }
    }

    group.fairOverProb = fairOverProb;
    group.fairUnderProb = fairUnderProb;
    group.fairOverOdds = impliedToAmerican(fairOverProb);
    group.fairUnderOdds = impliedToAmerican(fairUnderProb);
  }

  // Sort by EV descending
  opportunities.sort((a, b) => b.ev - a.ev);

  return { groups: Object.values(groups), opportunities };
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------
exports.handler = async (event) => {
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

  const sport =
    (event.queryStringParameters && event.queryStringParameters.sport) || "nba";

  const startTime = Date.now();

  // Fetch ALL books in parallel
  const [dk, mgm, pinnacle, fanduel, bovada] = await Promise.allSettled([
    fetchDraftKings(sport),
    fetchBetMGM(),
    fetchPinnacle(),
    fetchFanDuel(),
    fetchBovada(),
  ]);

  // Collect results and errors
  const allProps = [];
  const bookStatus = {};

  const results = [
    { name: "DraftKings", result: dk },
    { name: "BetMGM", result: mgm },
    { name: "Pinnacle", result: pinnacle },
    { name: "FanDuel", result: fanduel },
    { name: "Bovada", result: bovada },
  ];

  for (const { name, result } of results) {
    if (result.status === "fulfilled") {
      const data = result.value;
      const errors = data.filter((d) => d.error);
      const valid = data.filter((d) => !d.error);
      allProps.push(...data);
      bookStatus[name] = {
        status: errors.length > 0 ? "error" : "ok",
        propsFound: valid.length,
        error: errors.length > 0 ? errors[0].error : null,
      };
    } else {
      bookStatus[name] = {
        status: "failed",
        propsFound: 0,
        error: result.reason ? result.reason.message : "Unknown error",
      };
    }
  }

  // Consolidate and find +EV
  const { groups, opportunities } = consolidateAndFindEV(allProps);

  const elapsed = Date.now() - startTime;

  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
    body: JSON.stringify(
      {
        sport,
        bookStatus,
        totalProps: allProps.filter((p) => !p.error).length,
        consolidatedGroups: groups.length,
        plusEVCount: opportunities.length,
        plusEV: opportunities.slice(0, 50), // top 50
        allGroups: groups.slice(0, 200), // top 200 groups for display
        elapsedMs: elapsed,
        fetchedAt: new Date().toISOString(),
      },
      null,
      2
    ),
  };
};
