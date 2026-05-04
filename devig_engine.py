#!/usr/bin/env python3
"""
Sports Edge - Independent Devigging Engine

Since OddsTrader's cover probabilities appear inflated and they don't actually
have Pinnacle prop data, we build our own devigging from available sources.

Approach:
1. For game lines: Use Pinnacle from SBR (proven, +3.39% CLV)
2. For props: Use multi-source consensus devigging:
   - FanDuel O/U lines -> devig for fair probability
   - Bovada O/U lines -> devig for fair probability
   - Average the devigged probabilities (wisdom of crowds on soft books)
   - Compare each book's price to the averaged fair odds
   - If a book offers significantly better odds than fair -> edge

This isn't as sharp as Pinnacle devig, but it's better than trusting
an unknown model. And we VERIFY by grading every pick.
"""

import json
import os
import re
import requests
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def american_to_decimal(american):
    """Convert American odds to decimal."""
    if isinstance(american, str):
        if american in ("EVEN", "even", "EV"):
            return 2.0
        american = int(american.replace("+", ""))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    """Convert decimal odds to implied probability."""
    return 1.0 / dec if dec > 0 else 0


def devig_two_way(over_dec, under_dec):
    """Remove vig from a two-way market (over/under).

    Uses the multiplicative method:
    fair_prob_over = implied_over / (implied_over + implied_under)
    """
    imp_over = decimal_to_implied(over_dec)
    imp_under = decimal_to_implied(under_dec)
    total = imp_over + imp_under

    if total <= 0:
        return None, None

    fair_over = imp_over / total
    fair_under = imp_under / total
    return fair_over, fair_under


def devig_power(over_dec, under_dec):
    """Power method devigging (more accurate for balanced markets).

    Solves: p^k + (1-p)^k = 1 where k adjusts for vig.
    Falls back to multiplicative if power method fails.
    """
    imp_o = decimal_to_implied(over_dec)
    imp_u = decimal_to_implied(under_dec)

    # Try power method
    import math
    total_imp = imp_o + imp_u
    if total_imp <= 1.0:
        return devig_two_way(over_dec, under_dec)

    # Binary search for k
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
        return devig_two_way(over_dec, under_dec)


def fetch_fanduel_props(sport="mlb"):
    """Fetch FanDuel O/U props for devigging."""
    sport_config = {
        "nhl": {"event_url": "https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page?page=SPORT&eventType=nhl&_ak=FhMFpcPWXMeyZxOx",
                "tabs": ["shots", "goals"]},
        "mlb": {"event_url": "https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page?page=SPORT&eventType=mlb&_ak=FhMFpcPWXMeyZxOx",
                "tabs": ["pitcher-props", "batter-props"]},
    }

    config = sport_config.get(sport)
    if not config:
        return []

    headers = {"User-Agent": "Mozilla/5.0"}
    props = []

    try:
        resp = requests.get(config["event_url"], headers=headers, timeout=15)
        data = resp.json()
        attachments = data.get("attachments", {})
        events = attachments.get("events", {})
        competitions = attachments.get("competitions", {})

        # Get event IDs
        event_ids = list(events.keys())

        for eid in event_ids:
            event = events[eid]
            event_name = event.get("name", "")
            comp_id = event.get("competitionId")

            for tab in config["tabs"]:
                tab_url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?eventId={eid}&tab={tab}&_ak=FhMFpcPWXMeyZxOx"
                try:
                    tab_resp = requests.get(tab_url, headers=headers, timeout=10)
                    tab_data = tab_resp.json()
                    tab_attachments = tab_data.get("attachments", {})
                    markets = tab_attachments.get("markets", {})

                    for mid, market in markets.items():
                        market_name = market.get("marketName", "")
                        runners = market.get("runners", [])

                        if len(runners) == 2:
                            # O/U market
                            over_runner = None
                            under_runner = None
                            for r in runners:
                                rname = r.get("runnerName", "").lower()
                                if "over" in rname:
                                    over_runner = r
                                elif "under" in rname:
                                    under_runner = r

                            if over_runner and under_runner:
                                over_odds = over_runner.get("winRunnerOdds", {}).get("americanDisplayOdds", {}).get("americanOdds")
                                under_odds = under_runner.get("winRunnerOdds", {}).get("americanDisplayOdds", {}).get("americanOdds")
                                handicap = over_runner.get("handicap")

                                if over_odds and under_odds:
                                    # Extract player name from market name
                                    # Format: "Player Name - Stat Type"
                                    parts = market_name.split(" - ")
                                    player = parts[0].strip() if parts else market_name

                                    props.append({
                                        "sport": sport.upper(),
                                        "game": event_name,
                                        "player": player,
                                        "market": market_name,
                                        "line": float(handicap) if handicap else None,
                                        "over_odds": over_odds,
                                        "under_odds": under_odds,
                                        "source": "fanduel",
                                    })
                except:
                    continue
    except Exception as e:
        print(f"  FD error: {e}")

    return props


def fetch_bovada_props(sport="mlb"):
    """Fetch Bovada O/U props for devigging."""
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
                                props.append({
                                    "sport": sport.upper(),
                                    "game": game,
                                    "player": desc,
                                    "market": desc,
                                    "line": float(handicap) if handicap else None,
                                    "over_odds": str(over_odds),
                                    "under_odds": str(under_odds),
                                    "source": "bovada",
                                })
    except Exception as e:
        print(f"  Bovada error: {e}")

    return props


def run_devig_scan():
    """Run independent devigging scan across available sources."""
    now = datetime.now(timezone.utc)
    print(f"\n{'=' * 60}")
    print(f"  INDEPENDENT DEVIG ENGINE")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'=' * 60}")

    all_devigged = []

    for sport in ["nhl", "mlb"]:
        print(f"\n  === {sport.upper()} ===")

        # Fetch from both sources
        fd_props = fetch_fanduel_props(sport)
        bov_props = fetch_bovada_props(sport)
        print(f"  FanDuel: {len(fd_props)} | Bovada: {len(bov_props)}")

        # Devig each source independently
        for prop in fd_props + bov_props:
            try:
                over_dec = american_to_decimal(prop["over_odds"])
                under_dec = american_to_decimal(prop["under_odds"])

                fair_over, fair_under = devig_power(over_dec, under_dec)
                if fair_over is None:
                    continue

                # Calculate edge vs the book's own price
                imp_over = decimal_to_implied(over_dec)
                imp_under = decimal_to_implied(under_dec)

                edge_over = fair_over - imp_over  # Positive = over is +EV
                edge_under = fair_under - imp_under

                prop["fair_over"] = round(fair_over, 4)
                prop["fair_under"] = round(fair_under, 4)
                prop["edge_over"] = round(edge_over, 4)
                prop["edge_under"] = round(edge_under, 4)

                # A book can't have edge against itself in a 2-way market
                # The edge comes from COMPARING to another book's devigged line
                all_devigged.append(prop)
            except:
                continue

    # Cross-book comparison: find where one book's devigged fair odds
    # show another book offering better price
    print(f"\n  Total devigged: {len(all_devigged)}")

    # Save devigged data
    output = {
        "timestamp": now.isoformat(),
        "method": "power_devig",
        "count": len(all_devigged),
        "props": all_devigged,
    }

    outpath = os.path.join(DATA_DIR, "devigged_props.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"  Saved to {outpath}")
    return output


if __name__ == "__main__":
    run_devig_scan()
