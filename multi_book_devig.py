#!/usr/bin/env python3
"""
Sports Edge - Multi-Book Prop Devigging Engine V2

Strategy: Devig Bovada O/U props (power method) to get fair probabilities,
then cross-reference against OddsTrader's picks. When BOTH sources agree
on a +EV bet, confidence is HIGH.

Data sources (all free, no API key):
- Bovada API: 800+ player props with O/U lines per sport
- OddsTrader scrape: 200+ "model-identified" +EV props
- FanDuel API: Player props (when available)

Cross-validation logic:
1. Devig every Bovada O/U prop -> get fair probability
2. Load OddsTrader picks
3. Match by player + market type
4. If Bovada devig agrees prop is +EV -> CONFIRMED edge
5. If Bovada devig disagrees -> OddsTrader model may be wrong
"""

import json
import os
import re
import requests
from datetime import datetime, timezone
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def american_to_decimal(american):
    if isinstance(american, str):
        if american in ("EVEN", "even", "EV"):
            return 2.0
        american = int(american.replace("+", ""))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_american(dec):
    if dec >= 2.0:
        return f"+{int((dec - 1) * 100)}"
    else:
        return f"{int(-100 / (dec - 1))}"


def devig_power(over_dec, under_dec):
    """Power method devigging - more accurate than multiplicative."""
    imp_o = 1.0 / over_dec if over_dec > 0 else 0
    imp_u = 1.0 / under_dec if under_dec > 0 else 0
    total = imp_o + imp_u

    if total <= 1.0:
        # No vig or negative vig - just normalize
        return imp_o / total if total > 0 else (None, None)

    # Binary search for k where imp_o^k + imp_u^k = 1
    lo, hi = 0.5, 2.0
    for _ in range(50):
        k = (lo + hi) / 2
        try:
            val = imp_o ** k + imp_u ** k
        except:
            break
        if val > 1.0:
            hi = k
        else:
            lo = k

    k = (lo + hi) / 2
    try:
        fair_over = imp_o ** k
        fair_under = imp_u ** k
        return fair_over, fair_under
    except:
        # Fallback to multiplicative
        return imp_o / total, imp_u / total


def normalize_player_name(name):
    """Normalize player name for matching."""
    name = name.lower().strip()
    # Remove team abbreviations in parens
    name = re.sub(r'\s*\([^)]+\)\s*', '', name)
    # Remove common prefixes
    name = re.sub(r'^(total\s+)?(shots on goal|goals|assists|points|hits|rbi|strikeouts|total bases|runs)\s*-?\s*', '', name)
    # Remove "player to" prefix
    name = re.sub(r'^player to\s+', '', name)
    name = name.strip(' -')
    return name


def normalize_market_type(market_str):
    """Normalize market type for cross-book matching."""
    m = market_str.lower()
    if 'shot' in m and 'goal' in m:
        return 'sog'
    if 'goal' in m and 'score' not in m:
        if 'total' in m:
            return 'goals'
        return 'goals'
    if 'score' in m or ('goal' in m and 'player' in m):
        return 'anytime_goal'
    if 'assist' in m:
        return 'assists'
    if 'point' in m:
        return 'points'
    if 'hits allowed' in m or 'pitching hits' in m:
        return 'hits_allowed'
    if 'hits, runs and rbi' in m:
        return 'hits_runs_rbi'  # Combo market, not standalone
    if 'hit' in m and 'rbi' not in m and 'allow' not in m and 'runs' not in m:
        return 'hits'
    if 'rbi' in m or 'runs batted' in m:
        return 'rbi'
    if 'strikeout' in m:
        return 'strikeouts'
    if 'total base' in m:
        return 'total_bases'
    if 'home run' in m or 'homer' in m:
        return 'home_runs'
    if 'stolen base' in m:
        return 'stolen_bases'
    return m


def fetch_bovada_all_props(sport="nhl"):
    """Fetch ALL Bovada player props with full details."""
    sport_map = {
        "nhl": "hockey/nhl",
        "mlb": "baseball/mlb",
    }
    sport_path = sport_map.get(sport)
    if not sport_path:
        return []

    url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/{sport_path}?lang=en"
    headers = {"User-Agent": "Mozilla/5.0"}

    props = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        events = data[0].get("events", []) if data else []

        for event in events:
            game = event.get("description", "")
            for dg in event.get("displayGroups", []):
                group_name = dg.get("description", "")
                for market in dg.get("markets", []):
                    desc = market.get("description", "")
                    outcomes = market.get("outcomes", [])

                    if len(outcomes) == 2:
                        over = under = None
                        for o in outcomes:
                            otype = o.get("type", "").lower()
                            if otype == "o":
                                over = o
                            elif otype == "u":
                                under = o

                        if over and under:
                            over_odds = over.get("price", {}).get("american")
                            under_odds = under.get("price", {}).get("american")
                            handicap = over.get("price", {}).get("handicap")

                            if over_odds and under_odds:
                                # Extract player name from description
                                player = desc
                                # Common patterns: "Total SOG - Player Name (TEAM)"
                                parts = desc.split(" - ")
                                if len(parts) >= 2:
                                    player = parts[-1].strip()

                                try:
                                    over_dec = american_to_decimal(str(over_odds))
                                    under_dec = american_to_decimal(str(under_odds))
                                    fair_over, fair_under = devig_power(over_dec, under_dec)

                                    if fair_over and fair_under:
                                        props.append({
                                            "sport": sport.upper(),
                                            "game": game,
                                            "group": group_name,
                                            "market_raw": desc,
                                            "market_type": normalize_market_type(desc),
                                            "player_raw": player,
                                            "player_norm": normalize_player_name(player),
                                            "line": float(handicap) if handicap else None,
                                            "over_odds": str(over_odds),
                                            "under_odds": str(under_odds),
                                            "over_dec": round(over_dec, 4),
                                            "under_dec": round(under_dec, 4),
                                            "fair_over": round(fair_over, 4),
                                            "fair_under": round(fair_under, 4),
                                            "vig": round((1/over_dec + 1/under_dec - 1) * 100, 2),
                                            "source": "bovada",
                                        })
                                except:
                                    continue
    except Exception as e:
        print(f"  Bovada {sport} error: {e}")

    return props


def load_oddstrader_picks():
    """Load the most recent OddsTrader picks."""
    path = os.path.join(DATA_DIR, "oddstrader_ev_props.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("props", [])


def cross_validate(bovada_props, ot_picks):
    """Cross-validate OddsTrader picks against Bovada devigged lines.

    For each OT pick, find matching Bovada prop and check if
    Bovada's devigged fair odds also show the bet as +EV.
    """
    results = {
        "confirmed": [],    # Both sources agree: +EV
        "disagreed": [],    # Bovada devig says NOT +EV
        "unmatched": [],    # No Bovada match found
    }

    # Index Bovada props by normalized player name
    bov_index = defaultdict(list)
    for bp in bovada_props:
        key = bp["player_norm"]
        bov_index[key].append(bp)

    for ot in ot_picks:
        ot_player = normalize_player_name(ot.get("player", ""))
        ot_market = normalize_market_type(ot.get("market", ""))
        ot_ev = ot.get("ev_pct", 0)
        ot_odds_str = ot.get("best_odds", "")
        ot_fair_prob = ot.get("fair_prob", 0)

        # Try to find matching Bovada prop
        matches = bov_index.get(ot_player, [])

        # Filter by market type
        market_matches = [m for m in matches if m["market_type"] == ot_market]

        if not market_matches:
            # Try fuzzy: check if player name is substring
            for key, bov_list in bov_index.items():
                if ot_player in key or key in ot_player:
                    for bp in bov_list:
                        if bp["market_type"] == ot_market:
                            market_matches.append(bp)

        if not market_matches:
            results["unmatched"].append({
                "player": ot.get("player", ""),
                "market": ot.get("market", ""),
                "ot_ev": ot_ev,
                "reason": "no_bovada_match",
            })
            continue

        # Take the best matching Bovada line
        bov = market_matches[0]

        # Determine if OT pick is over or under
        line_str = ot.get("line", "").lower()
        is_over = line_str.startswith("o") if line_str else True

        if is_over:
            bov_fair = bov["fair_over"]
        else:
            bov_fair = bov["fair_under"]

        # Calculate what odds would be fair based on Bovada devig
        if bov_fair > 0 and bov_fair < 1:
            fair_dec = 1.0 / bov_fair
            fair_american = decimal_to_american(fair_dec)
        else:
            fair_american = "N/A"
            fair_dec = 0

        # Check if OT's best odds beat Bovada's fair line
        try:
            ot_dec = american_to_decimal(ot_odds_str)
            if fair_dec > 0:
                edge_vs_bovada = (1.0 / fair_dec) - (1.0 / ot_dec)
                edge_pct = round(edge_vs_bovada * 100, 2)
            else:
                edge_pct = 0
        except:
            ot_dec = 0
            edge_pct = 0

        entry = {
            "player": ot.get("player", ""),
            "game": ot.get("game", ""),
            "sport": ot.get("sport", ""),
            "market": ot.get("market", ""),
            "line": ot.get("line", ""),
            "ot_ev_pct": ot_ev,
            "ot_fair_prob": ot_fair_prob,
            "ot_best_odds": ot_odds_str,
            "bovada_over_odds": bov["over_odds"],
            "bovada_under_odds": bov["under_odds"],
            "bovada_fair_over": bov["fair_over"],
            "bovada_fair_under": bov["fair_under"],
            "bovada_fair_american": fair_american,
            "bovada_line": bov["line"],
            "bovada_vig": bov["vig"],
            "edge_vs_bovada_devig": edge_pct,
        }

        if edge_pct > 1.0:  # At least 1% edge vs Bovada devig
            entry["status"] = "CONFIRMED"
            entry["confidence"] = "HIGH" if edge_pct > 3.0 else "MEDIUM"
            results["confirmed"].append(entry)
        else:
            entry["status"] = "DISAGREED"
            entry["bovada_says"] = f"Fair odds = {fair_american}, OT offering {ot_odds_str} is NOT +EV"
            results["disagreed"].append(entry)

    return results


def find_bovada_only_edges(bovada_props, min_vig_diff=3.0):
    """Find props where Bovada's own vig structure reveals edges.

    When one side of a Bovada O/U has much less vig than expected,
    it suggests the book is less confident in that line.

    Also find props where the fair probability is far from 50%
    (heavily skewed = stronger opinion = potential mispricing on other books).
    """
    edges = []
    for bp in bovada_props:
        fair_o = bp["fair_over"]
        fair_u = bp["fair_under"]

        # Skip game-level totals (not player props)
        if bp["market_raw"] in ("Total",) or "team" in bp["market_type"]:
            continue

        # Look for heavily skewed lines (fair prob > 65% one side)
        if fair_o > 0.65 or fair_u > 0.65:
            # This is a strong opinion - the other side might be mispriced elsewhere
            skewed_side = "over" if fair_o > fair_u else "under"
            edges.append({
                "player": bp["player_raw"],
                "game": bp["game"],
                "sport": bp["sport"],
                "market": bp["market_raw"],
                "market_type": bp["market_type"],
                "line": bp["line"],
                "fair_over": bp["fair_over"],
                "fair_under": bp["fair_under"],
                "over_odds": bp["over_odds"],
                "under_odds": bp["under_odds"],
                "vig": bp["vig"],
                "skewed_toward": skewed_side,
                "skew_strength": round(max(fair_o, fair_u) * 100, 1),
            })

    # Sort by skew strength (strongest opinions first)
    edges.sort(key=lambda x: x["skew_strength"], reverse=True)
    return edges


def run_multi_book_devig():
    """Run the full multi-book devigging analysis."""
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  MULTI-BOOK DEVIGGING ENGINE V2")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    all_bovada = []
    for sport in ["mlb"]:  # NHL disabled Apr 29 per Braxton
        print(f"\n  Fetching Bovada {sport.upper()} props...")
        props = fetch_bovada_all_props(sport)
        print(f"    {len(props)} O/U props devigged")
        all_bovada.extend(props)

    # Show market type breakdown
    by_type = defaultdict(int)
    for bp in all_bovada:
        by_type[f"{bp['sport']}|{bp['market_type']}"] += 1
    print(f"\n  Market breakdown:")
    for k, v in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    # Cross-validate with OddsTrader
    ot_picks = load_oddstrader_picks()
    print(f"\n  OddsTrader picks loaded: {len(ot_picks)}")

    if ot_picks:
        print(f"\n  Cross-validating...")
        xv = cross_validate(all_bovada, ot_picks)
        print(f"    CONFIRMED (both agree +EV): {len(xv['confirmed'])}")
        print(f"    DISAGREED (Bovada says no):  {len(xv['disagreed'])}")
        print(f"    UNMATCHED (no Bovada prop):  {len(xv['unmatched'])}")

        if xv["confirmed"]:
            print(f"\n  TOP CONFIRMED PICKS:")
            for i, c in enumerate(sorted(xv["confirmed"], key=lambda x: -x["edge_vs_bovada_devig"])[:15], 1):
                print(f"    {i:2d}. {c['sport']} {c['player']:25s} {c['market']:20s}"
                      f" OT_EV:+{c['ot_ev_pct']:.1f}% Bov_edge:+{c['edge_vs_bovada_devig']:.1f}%"
                      f" [{c['confidence']}]")
    else:
        xv = None

    # Find Bovada-only edges (skewed lines)
    print(f"\n  Bovada skewed lines (strong opinions)...")
    skewed = find_bovada_only_edges(all_bovada)
    print(f"    {len(skewed)} heavily skewed props found")
    if skewed:
        print(f"\n  TOP SKEWED (potential cross-book edges):")
        for i, s in enumerate(skewed[:10], 1):
            print(f"    {i:2d}. {s['sport']} {s['player']:30s} {s['market_type']:10s}"
                  f" line:{s['line']} fair:{s['skew_strength']:.0f}% toward {s['skewed_toward']}"
                  f" O:{s['over_odds']} U:{s['under_odds']}")

    # Save everything
    output = {
        "timestamp": now.isoformat(),
        "bovada_props_count": len(all_bovada),
        "bovada_props": all_bovada,
        "cross_validation": {
            "confirmed": xv["confirmed"] if xv else [],
            "disagreed": xv["disagreed"] if xv else [],
            "unmatched": xv["unmatched"] if xv else [],
        } if xv else None,
        "skewed_lines": skewed[:50],
    }

    outpath = os.path.join(DATA_DIR, "multi_book_devig.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Saved to {outpath}")

    return output


if __name__ == "__main__":
    run_multi_book_devig()
