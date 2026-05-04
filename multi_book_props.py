#!/usr/bin/env python3
"""
Sports Edge - Multi-Book Player Prop Scanner

Compares player prop odds across Bovada and FanDuel to find edge.

Strategy:
1. Fetch props from Bovada (free API, no key needed)
2. Fetch props from FanDuel (free API, no key needed)
3. Match same player/market/line across books
4. Devig each book's line to get implied "true" probability
5. Find where one book offers significantly better odds than the other
6. Additional: compare both against a combined "consensus" fair price

Sports: NHL (shots on goal, blocked shots) + MLB (strikeouts, hits, total bases)
"""

import json
import os
import re
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Markets that are empirically unprofitable (-1061 on "Player to score", -280 on "2+ Goals")
# Only bet markets with proven positive or neutral track record
BLACKLISTED_MARKETS = {
    "Player to score",
    "Player to score 2+ Goals",
    "Player to Record an Assist",
    "Player to Record 2+ Points",
}

# FanDuel config
FD_BASE = "https://sbapi.mi.sportsbook.fanduel.com/api"
FD_AK = "FhMFpcPWXMeyZxOx"


def american_to_decimal(american):
    if isinstance(american, str):
        if american in ("EVEN", "even"):
            return 2.0
        american = int(american.replace("+", "").replace(" ", ""))
    if american == 0:
        return 2.0
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    return 1.0 / dec if dec > 0 else 0


def implied_to_american(imp):
    if imp <= 0 or imp >= 1:
        return 0
    dec = 1.0 / imp
    if dec >= 2.0:
        return round((dec - 1) * 100)
    else:
        return round(-100 / (dec - 1))


def devig_pair(over_american, under_american):
    """Remove vig from over/under pair. Returns (fair_over_prob, fair_under_prob)."""
    over_dec = american_to_decimal(over_american)
    under_dec = american_to_decimal(under_american)
    over_imp = decimal_to_implied(over_dec)
    under_imp = decimal_to_implied(under_dec)
    total = over_imp + under_imp
    if total <= 0:
        return 0.5, 0.5
    return over_imp / total, under_imp / total


def normalize_player_name(name):
    """Normalize player name for matching across books."""
    name = name.strip()
    # Remove team abbreviations in parens: "David Pastrnak (BOS)" -> "David Pastrnak"
    name = re.sub(r'\s*\([A-Z]{2,4}\)\s*$', '', name)
    # Remove suffixes like Jr., Sr., III
    name = re.sub(r'\s+(Jr\.?|Sr\.?|III|II|IV)$', '', name)
    # Normalize unicode/accents (basic)
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', 'ö': 'o', 'ä': 'a',
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    return name.lower().strip()


def normalize_team_name(name):
    """Normalize team name for matching."""
    name = name.strip().lower()
    # Common abbreviations
    abbrevs = {
        'tb': 'tampa bay lightning', 'tbl': 'tampa bay lightning',
        'bos': 'boston bruins', 'car': 'carolina hurricanes',
        'phi': 'philadelphia flyers', 'det': 'detroit red wings',
        'fla': 'florida panthers', 'nyr': 'new york rangers',
        'tor': 'toronto maple leafs', 'min': 'minnesota wild',
        'dal': 'dallas stars', 'stl': 'st. louis blues',
        'col': 'colorado avalanche', 'edm': 'edmonton oilers',
        'wpg': 'winnipeg jets', 'vgk': 'vegas golden knights',
        'lak': 'los angeles kings', 'nsh': 'nashville predators',
        'sea': 'seattle kraken', 'sjs': 'san jose sharks',
        'buf': 'buffalo sabres', 'chi': 'chicago blackhawks',
    }
    return name


# ============================================================
# BOVADA FETCHER
# ============================================================

def fetch_bovada_props(sport="hockey/nhl"):
    """Fetch all player props from Bovada."""
    url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/{sport}?lang=en"
    req = urllib.request.Request(url, headers=HEADERS)

    try:
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"  [Bovada] Error fetching {sport}: {e}")
        return []

    props = []
    for item in data:
        for event in item.get("events", []):
            game = event.get("description", "")
            for dg in event.get("displayGroups", []):
                group = dg.get("description", "")
                for mkt in dg.get("markets", []):
                    mkt_desc = mkt.get("description", "")
                    outcomes = mkt.get("outcomes", [])

                    overs = [o for o in outcomes if o.get("description", "").lower() == "over"]
                    unders = [o for o in outcomes if o.get("description", "").lower() == "under"]

                    if overs and unders:
                        o_price = overs[0].get("price", {})
                        u_price = unders[0].get("price", {})
                        over_odds = o_price.get("american")
                        under_odds = u_price.get("american")
                        line = o_price.get("handicap")

                        if over_odds is None or under_odds is None or line is None:
                            continue

                        # Parse player name from market description
                        player = ""
                        if " - " in mkt_desc:
                            # "Total Strikeouts - Paul Skenes (PIT)"
                            parts = mkt_desc.split(" - ", 1)
                            player = parts[1].strip()
                            market_type = parts[0].strip()
                        else:
                            market_type = mkt_desc

                        # Parse odds to int
                        def parse_odds(o):
                            if isinstance(o, (int, float)):
                                return int(o) if o != 0 else 100
                            s = str(o).strip().replace("+", "")
                            if s.upper() in ("EVEN", "EV"):
                                return 100
                            return int(s)

                        try:
                            ov = parse_odds(over_odds)
                            un = parse_odds(under_odds)
                        except (ValueError, TypeError):
                            continue

                        props.append({
                            "book": "bovada",
                            "game": game,
                            "group": group,
                            "market_type": market_type,
                            "market_raw": mkt_desc,
                            "player": player,
                            "player_norm": normalize_player_name(player) if player else "",
                            "line": float(line),
                            "over_odds": ov,
                            "under_odds": un,
                        })

    return props


# ============================================================
# FANDUEL FETCHER (extended for NHL + MLB)
# ============================================================

FD_SPORT_CONFIGS = {
    "nhl": {
        "page_id": "nhl",
        "tabs": {
            # NHL uses 'shots' for SOG props and 'pitcher-props'/'batter-props' style tabs don't exist
            # The real prop tabs for NHL:
            "shots": "Shots on Goal",        # Threshold markets: "Player X+ SOG"
            "goals": "Goals",                # Threshold markets: "Player to score X+ goals"
        }
    },
    "mlb": {
        "page_id": "mlb",
        "tabs": {
            # MLB uses 'pitcher-props' and 'batter-props' tabs
            "pitcher-props": "Pitcher Props",
            "batter-props": "Batter Props",
        }
    },
}


def fetch_fanduel_props(sport="nhl"):
    """Fetch FanDuel player props for a sport.

    Handles two FD market formats:
    1. Over/Under: runners named "Over"/"Under" with handicap (MLB pitcher Ks)
    2. Threshold: runners named "Player X+ Stat" (NHL SOG, MLB batter hits)
       - We convert threshold to equivalent O/U: "X+" = "Over X-0.5"
    """
    config = FD_SPORT_CONFIGS.get(sport, {})
    if not config:
        return []

    import requests
    session = requests.Session()
    session.headers.update(HEADERS)

    props = []

    try:
        resp = session.get(f"{FD_BASE}/content-managed-page",
            params={"page": "CUSTOM", "customPageId": config["page_id"],
                    "pbHorizontal": "true", "_ak": FD_AK}, timeout=15)
        if resp.status_code != 200:
            print(f"  [FD-{sport}] Event list error: {resp.status_code}")
            return props

        data = resp.json()
        events = data.get("attachments", {}).get("events", {})
        games = []
        for eid, ev in events.items():
            name = ev.get("name", "")
            if "v" in name.lower() or "@" in name.lower():
                games.append({"id": eid, "name": name})

        print(f"  [FD-{sport}] {len(games)} games found")

        for game in games:
            for tab_url, market_label in config["tabs"].items():
                try:
                    resp = session.get(f"{FD_BASE}/event-page",
                        params={"eventId": game["id"], "tab": tab_url, "_ak": FD_AK},
                        timeout=15)
                    if resp.status_code != 200:
                        continue

                    markets = resp.json().get("attachments", {}).get("markets", {})

                    for mid, mkt in markets.items():
                        mkt_name = mkt.get("marketName", "")
                        runners = mkt.get("runners", [])

                        # --- Format 1: Over/Under pairs ---
                        # Market name like "Player Name - Strikeouts"
                        by_handicap = defaultdict(dict)
                        for runner in runners:
                            rname = runner.get("runnerName", "")
                            handicap = runner.get("handicap", 0)
                            odds_data = runner.get("winRunnerOdds", {})
                            american = odds_data.get("americanDisplayOdds", {}).get("americanOdds")
                            if american is None:
                                continue
                            try:
                                american = int(american)
                            except (ValueError, TypeError):
                                continue

                            if rname.lower().strip() in ("over", "under"):
                                by_handicap[handicap][rname.lower().strip()] = american
                                by_handicap[handicap]["player"] = mkt_name

                        for handicap, pair in by_handicap.items():
                            if "over" in pair and "under" in pair and "player" in pair:
                                player = pair["player"]
                                market_type = market_label
                                if " - " in player:
                                    parts = player.split(" - ", 1)
                                    player = parts[0].strip()
                                    market_type = parts[1].strip()

                                props.append({
                                    "book": "fanduel",
                                    "game": game["name"],
                                    "group": market_label,
                                    "market_type": market_type,
                                    "market_raw": mkt_name,
                                    "player": player,
                                    "player_norm": normalize_player_name(player),
                                    "line": float(handicap),
                                    "over_odds": pair["over"],
                                    "under_odds": pair["under"],
                                })

                        # --- Format 2: Threshold markets ---
                        # Two sub-formats:
                        # A) Runner name contains threshold: "Player Name X+ Stat"
                        #    (seen in MLB alt strikeouts)
                        # B) Market name contains threshold: "Player X+ Shots on Goal"
                        #    and runner names are just player names (NHL SOG)
                        if not by_handicap:
                            threshold_runner_re = re.compile(r'^(.+?)\s+(\d+)\+\s+(.+)$')
                            # Check market name for "X+ Stat" pattern
                            # e.g. "Player 3+ Shots on Goal", "1st Period Player 2+ Shots on Goal"
                            mkt_threshold_re = re.compile(r'(?:Player\s+)?(\d+)\+\s+(.+)$', re.IGNORECASE)
                            mkt_match = mkt_threshold_re.search(mkt_name)

                            # Skip period-specific markets (1st/2nd/3rd Period)
                            if mkt_match and not re.search(r'\d+(st|nd|rd) Period', mkt_name):
                                threshold = int(mkt_match.group(1))
                                stat = mkt_match.group(2).strip()
                                line = threshold - 0.5

                                for runner in runners:
                                    rname = runner.get("runnerName", "")
                                    odds_data = runner.get("winRunnerOdds", {})
                                    american = odds_data.get("americanDisplayOdds", {}).get("americanOdds")
                                    if american is None:
                                        continue
                                    try:
                                        american = int(american)
                                    except (ValueError, TypeError):
                                        continue

                                    player = rname.strip()
                                    if not player or player.lower() in ("over", "under", "yes", "no"):
                                        continue

                                    # Estimate under odds from over probability
                                    over_imp = decimal_to_implied(american_to_decimal(american))
                                    under_imp = 1.045 - over_imp
                                    if under_imp <= 0.01 or under_imp >= 0.99:
                                        continue
                                    under_odds = implied_to_american(under_imp)

                                    props.append({
                                        "book": "fanduel",
                                        "game": game["name"],
                                        "group": market_label,
                                        "market_type": stat,
                                        "market_raw": mkt_name,
                                        "player": player,
                                        "player_norm": normalize_player_name(player),
                                        "line": line,
                                        "over_odds": american,
                                        "under_odds": under_odds,
                                        "threshold_derived": True,
                                    })
                            else:
                                # Format A: threshold in runner name
                                for runner in runners:
                                    rname = runner.get("runnerName", "")
                                    odds_data = runner.get("winRunnerOdds", {})
                                    american = odds_data.get("americanDisplayOdds", {}).get("americanOdds")
                                    if american is None:
                                        continue
                                    try:
                                        american = int(american)
                                    except (ValueError, TypeError):
                                        continue

                                    m = threshold_runner_re.match(rname)
                                    if m:
                                        player = m.group(1).strip()
                                        threshold = int(m.group(2))
                                        stat = m.group(3).strip()
                                        line = threshold - 0.5

                                        over_imp = decimal_to_implied(american_to_decimal(american))
                                        under_imp = 1.045 - over_imp
                                        if under_imp <= 0.01 or under_imp >= 0.99:
                                            continue
                                        under_odds = implied_to_american(under_imp)

                                        props.append({
                                            "book": "fanduel",
                                            "game": game["name"],
                                            "group": market_label,
                                            "market_type": stat,
                                            "market_raw": mkt_name,
                                            "player": player,
                                            "player_norm": normalize_player_name(player),
                                            "line": line,
                                            "over_odds": american,
                                            "under_odds": under_odds,
                                            "threshold_derived": True,
                                        })

                    time.sleep(0.15)
                except Exception as e:
                    continue

    except Exception as e:
        print(f"  [FD-{sport}] Error: {e}")

    print(f"  [FD-{sport}] {len(props)} prop lines fetched")
    return props


# ============================================================
# CROSS-BOOK COMPARISON ENGINE
# ============================================================

MARKET_TYPE_MAP = {
    # Bovada market_type -> normalized category
    "Total Strikeouts": "strikeouts",
    "Total Hits": "hits",
    "Total Bases": "total_bases",
    "Total Stolen Bases": "stolen_bases",
    "Total Runs O/U": "runs",
    "Total Pitcher Outs": "pitcher_outs",
    "Total Hits Allowed": "hits_allowed",
    "Total Hits, Runs and RBI's": "hits_runs_rbis",
    "Total Doubles": "doubles",
    "Total Shots On Goal": "shots_on_goal",
    "Total Shots on Goal": "shots_on_goal",
    # FD market_type -> normalized category
    "Strikeouts": "strikeouts",
    "Shots on Goal": "shots_on_goal",
    "Goals": "goals",
    "Blocked Shots": "blocked_shots",
}


def match_props(bovada_props, fd_props):
    """Match props across books by player name, market category, and line."""
    matches = []

    # Index FD props by (normalized player, normalized market, line)
    fd_index = defaultdict(list)
    for p in fd_props:
        if not p["player_norm"]:
            continue
        cat = MARKET_TYPE_MAP.get(p["market_type"], p["market_type"].lower())
        key = (p["player_norm"], cat, p["line"])
        fd_index[key].append(p)

    for bov in bovada_props:
        if not bov["player_norm"]:
            continue

        bov_cat = MARKET_TYPE_MAP.get(bov["market_type"], bov["market_type"].lower())
        key = (bov["player_norm"], bov_cat, bov["line"])
        fd_matches = fd_index.get(key, [])

        if fd_matches:
            best_fd = fd_matches[0]
            matches.append({
                "player": bov["player"],
                "player_norm": bov["player_norm"],
                "game_bov": bov["game"],
                "game_fd": best_fd["game"],
                "market": bov["market_type"],
                "market_category": bov_cat,
                "line": bov["line"],
                "bov_over": bov["over_odds"],
                "bov_under": bov["under_odds"],
                "fd_over": best_fd["over_odds"],
                "fd_under": best_fd["under_odds"],
                "fd_threshold_derived": best_fd.get("threshold_derived", False),
            })

    return matches


def find_edges(matches, min_edge=0.02):
    """Find profitable edges from cross-book matches.

    For each match:
    1. Devig each book to get their fair probability
    2. Average the fair probs for a consensus line
    3. Check if either book offers better odds than consensus
    4. Edge = consensus_prob - implied_prob_at_offered_odds
    """
    opportunities = []

    for m in matches:
        # Skip blacklisted markets
        if m.get("market", "") in BLACKLISTED_MARKETS:
            continue

        # Devig each book
        bov_fair_over, bov_fair_under = devig_pair(m["bov_over"], m["bov_under"])
        fd_fair_over, fd_fair_under = devig_pair(m["fd_over"], m["fd_under"])

        # Consensus = average of fair probs
        consensus_over = (bov_fair_over + fd_fair_over) / 2
        consensus_under = (bov_fair_under + fd_fair_under) / 2

        # Check each side at each book
        for side, book, odds in [
            ("over", "bovada", m["bov_over"]),
            ("under", "bovada", m["bov_under"]),
            ("over", "fanduel", m["fd_over"]),
            ("under", "fanduel", m["fd_under"]),
        ]:
            fair_prob = consensus_over if side == "over" else consensus_under
            offered_dec = american_to_decimal(odds)
            offered_imp = decimal_to_implied(offered_dec)

            edge = fair_prob - offered_imp

            if edge >= min_edge:
                # Kelly criterion (quarter kelly)
                b = offered_dec - 1  # net payout ratio
                p = fair_prob
                q = 1 - p
                kelly = (b * p - q) / b if b > 0 else 0
                quarter_kelly = max(0, kelly * 0.25)

                # EV per dollar
                ev = (p * b - q)

                opportunities.append({
                    "player": m["player"],
                    "game": m["game_bov"],
                    "market": m["market"],
                    "line": m["line"],
                    "side": side,
                    "book": book,
                    "odds": odds,
                    "fair_prob": round(fair_prob, 4),
                    "offered_imp": round(offered_imp, 4),
                    "edge": round(edge, 4),
                    "ev": round(ev, 4),
                    "kelly_pct": round(quarter_kelly * 100, 2),
                    "confidence": "HIGH" if edge >= 0.04 else "MEDIUM",
                    # Cross-book details
                    "bov_over": m["bov_over"],
                    "bov_under": m["bov_under"],
                    "fd_over": m["fd_over"],
                    "fd_under": m["fd_under"],
                    "bov_fair": round(bov_fair_over if side == "over" else bov_fair_under, 4),
                    "fd_fair": round(fd_fair_over if side == "over" else fd_fair_under, 4),
                })

    # Sort by edge descending
    opportunities.sort(key=lambda x: -x["edge"])
    return opportunities


def find_vig_outliers(bovada_props, fd_props, max_vig_diff=0.03):
    """Find props where one book has much more vig than the other.

    High vig on one side often means that book has moved the line
    but hasn't fully adjusted odds - creating value on the other side.
    """
    alerts = []

    # Match props
    fd_index = defaultdict(list)
    for p in fd_props:
        key = (p["player_norm"], p["line"])
        fd_index[key].append(p)

    for bov in bovada_props:
        if not bov["player_norm"]:
            continue
        key = (bov["player_norm"], bov["line"])
        fd_matches = fd_index.get(key, [])
        if not fd_matches:
            continue

        fd = fd_matches[0]

        # Calculate vig for each book
        bov_over_imp = decimal_to_implied(american_to_decimal(bov["over_odds"]))
        bov_under_imp = decimal_to_implied(american_to_decimal(bov["under_odds"]))
        bov_vig = bov_over_imp + bov_under_imp - 1

        fd_over_imp = decimal_to_implied(american_to_decimal(fd["over_odds"]))
        fd_under_imp = decimal_to_implied(american_to_decimal(fd["under_odds"]))
        fd_vig = fd_over_imp + fd_under_imp - 1

        vig_diff = abs(bov_vig - fd_vig)

        if vig_diff >= max_vig_diff:
            alerts.append({
                "player": bov["player"],
                "market": bov["market_type"],
                "line": bov["line"],
                "bov_vig": round(bov_vig * 100, 1),
                "fd_vig": round(fd_vig * 100, 1),
                "vig_diff": round(vig_diff * 100, 1),
                "signal": "Bovada higher vig" if bov_vig > fd_vig else "FanDuel higher vig",
            })

    alerts.sort(key=lambda x: -x["vig_diff"])
    return alerts


# ============================================================
# MAIN SCANNER
# ============================================================

def scan_sport(sport_key, bovada_sport):
    """Scan a sport for cross-book prop edges."""
    print(f"\n  === {sport_key.upper()} Props ===")

    # Fetch from both books
    print(f"  Fetching Bovada {sport_key}...")
    bov_props = fetch_bovada_props(bovada_sport)
    print(f"  [Bovada] {len(bov_props)} props")

    print(f"  Fetching FanDuel {sport_key}...")
    fd_props = fetch_fanduel_props(sport_key)

    if not bov_props and not fd_props:
        print(f"  No prop data available")
        return {"matches": 0, "opportunities": [], "vig_alerts": []}

    # Match across books
    matches = match_props(bov_props, fd_props)
    print(f"  Cross-book matches: {len(matches)}")

    # Find edges
    opportunities = find_edges(matches, min_edge=0.02)
    print(f"  Edges found (2%+): {len(opportunities)}")

    # Find vig outliers
    vig_alerts = find_vig_outliers(bov_props, fd_props)
    print(f"  Vig outliers: {len(vig_alerts)}")

    # Also look for single-book value using devigged lines
    single_book_opps = find_single_book_value(bov_props, fd_props)

    return {
        "bovada_count": len(bov_props),
        "fanduel_count": len(fd_props),
        "matches": len(matches),
        "opportunities": opportunities,
        "vig_alerts": vig_alerts,
        "single_book": single_book_opps,
    }


def find_single_book_value(bov_props, fd_props):
    """Find value within a single book by looking for mispriced lines.

    When a book offers -105/-105, the vig is minimal.
    When a book offers -150/+120, they're heavily pricing one side.
    The +EV side is often the heavily juiced side's opposite at the OTHER book.
    """
    opps = []

    # Look for Bovada props with low vig on one side
    for p in bov_props:
        if not p["player_norm"]:
            continue
        over_dec = american_to_decimal(p["over_odds"])
        under_dec = american_to_decimal(p["under_odds"])
        over_imp = decimal_to_implied(over_dec)
        under_imp = decimal_to_implied(under_dec)
        total_imp = over_imp + under_imp
        vig = total_imp - 1

        # Low vig lines are well-priced - compare to FD
        if vig < 0.03:  # Less than 3% vig = sharp line
            opps.append({
                "book": "bovada",
                "player": p["player"],
                "market": p["market_type"],
                "line": p["line"],
                "over_odds": p["over_odds"],
                "under_odds": p["under_odds"],
                "vig_pct": round(vig * 100, 1),
                "signal": "low_vig_sharp_line",
            })

    for p in fd_props:
        if not p["player_norm"]:
            continue
        over_dec = american_to_decimal(p["over_odds"])
        under_dec = american_to_decimal(p["under_odds"])
        over_imp = decimal_to_implied(over_dec)
        under_imp = decimal_to_implied(under_dec)
        vig = over_imp + under_imp - 1

        if vig < 0.03:
            opps.append({
                "book": "fanduel",
                "player": p["player"],
                "market": p["market_type"],
                "line": p["line"],
                "over_odds": p["over_odds"],
                "under_odds": p["under_odds"],
                "vig_pct": round(vig * 100, 1),
                "signal": "low_vig_sharp_line",
            })

    return opps


def run_full_scan():
    """Run the full multi-book prop scanner."""
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  MULTI-BOOK PROP SCANNER")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Sources: Bovada + FanDuel")
    print(f"{'='*60}")

    results = {
        "timestamp": now.isoformat(),
        "version": "1.0",
        "sports": {},
        "all_opportunities": [],
    }

    # NHL disabled Apr 29 per Braxton
    # nhl = scan_sport("nhl", "hockey/nhl")
    # results["sports"]["nhl"] = { ... }
    # results["all_opportunities"].extend(nhl["opportunities"])

    # Scan MLB
    mlb = scan_sport("mlb", "baseball/mlb")
    results["sports"]["mlb"] = {
        "bovada_props": mlb["bovada_count"],
        "fanduel_props": mlb["fanduel_count"],
        "matches": mlb["matches"],
        "edges": len(mlb["opportunities"]),
    }
    results["all_opportunities"].extend(mlb["opportunities"])

    # Sort all opportunities by edge
    results["all_opportunities"].sort(key=lambda x: -x["edge"])

    # Print summary
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")

    total_opps = len(results["all_opportunities"])
    high_conf = sum(1 for o in results["all_opportunities"] if o["confidence"] == "HIGH")

    print(f"  Total opportunities: {total_opps}")
    print(f"  HIGH confidence (4%+): {high_conf}")
    print(f"  MEDIUM confidence (2-4%): {total_opps - high_conf}")

    if results["all_opportunities"]:
        print(f"\n  TOP PICKS:")
        for i, opp in enumerate(results["all_opportunities"][:10], 1):
            print(f"\n  {i}. [{opp['confidence']}] {opp['player']}")
            print(f"     {opp['market']} {opp['side'].upper()} {opp['line']} @ {opp['book']}")
            print(f"     Odds: {opp['odds']:+d} | Fair: {opp['fair_prob']:.1%} | Edge: {opp['edge']:.1%} | EV: {opp['ev']:.1%}")
            print(f"     Kelly: {opp['kelly_pct']:.1f}% | Bov: {opp['bov_over']:+d}/{opp['bov_under']:+d} | FD: {opp['fd_over']:+d}/{opp['fd_under']:+d}")

    # Save results
    outpath = os.path.join(DATA_DIR, "multi_book_props.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Saved to {outpath}")

    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        print(f"  Continuous mode: every {interval} min")
        cycle = 0
        while True:
            cycle += 1
            print(f"\n  === Cycle {cycle} ===")
            try:
                run_full_scan()
            except Exception as e:
                print(f"  Error: {e}")
            time.sleep(interval * 60)
    else:
        run_full_scan()
