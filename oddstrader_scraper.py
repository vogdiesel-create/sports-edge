#!/usr/bin/env python3
"""
Sports Edge - OddsTrader +EV Prop Scraper

Scrapes OddsTrader's player props pages which aggregate odds from 10+ books
including Pinnacle (the sharpest). OddsTrader calculates EV% using their
no-vig fair odds derived from Pinnacle's lines.

We scrape the rendered +EV props and use them as sharp-benchmarked picks.
This gives us Pinnacle-quality prop data for FREE.

Output: data/oddstrader_ev_props.json
"""

import json
import os
import re
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def extract_all_props(page, sport):
    """Extract all +EV props from the current OddsTrader page."""
    # Click LOAD MORE repeatedly to get all props
    for _ in range(10):
        try:
            page.click('text=LOAD MORE', timeout=3000)
            page.wait_for_timeout(2000)
        except:
            break

    rows = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a[class*="betWithBottomRow"]')).map(r => ({
            text: r.innerText.trim(),
            href: r.getAttribute('href') || ''
        }));
    }''')

    results = []
    for item in rows:
        lines = [l.strip() for l in item['text'].split('\n') if l.strip()]
        if len(lines) < 5:
            continue

        game = player = market = ev_pct = fair_prob = odds = date_time = ""
        for i, l in enumerate(lines):
            if '@' in l and len(l) < 20:
                game = l
                if i > 0:
                    date_time = lines[i - 1]
                if i + 1 < len(lines):
                    player = lines[i + 1]
                if i + 2 < len(lines):
                    market = lines[i + 2]

        line_value = ""  # e.g., "u½", "o2½", "u1½"
        for l in lines:
            if l.startswith('+') and l.endswith('%'):
                ev_pct = l
            elif l.endswith('%') and not l.startswith(('+', '-')) and l != 'EV':
                fair_prob = l
            elif re.match(r'^[+-]\d+$', l):
                odds = l
            elif re.match(r'^\([+-]\d+\)$', l):
                odds = l.strip('()')
            elif re.match(r'^[ou]\d*½?$', l):
                line_value = l

        if player and ev_pct:
            ev_val = float(ev_pct.replace('+', '').replace('%', ''))
            fp_val = float(fair_prob.replace('%', '')) / 100 if fair_prob else 0

            results.append({
                "sport": sport,
                "game": game,
                "date_time": date_time,
                "player": player,
                "market": market,
                "line": line_value,
                "ev_pct": ev_val,
                "fair_prob": fp_val,
                "best_odds": odds,
                "href": item['href'],
            })
    return results


def american_to_decimal(american_str):
    """Convert American odds string to decimal odds."""
    if not american_str:
        return None
    american = int(american_str.replace('+', ''))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def calculate_kelly(cover_prob, odds_str, quarter=True):
    """Calculate Kelly criterion bet size.

    OddsTrader EV% = cover_prob - implied_prob (probability edge, not monetary EV).
    cover_prob: OddsTrader's model probability (e.g., 0.39)
    odds_str: American odds string (e.g., "+650")

    NOTE: cover_prob is from OddsTrader's model, NOT Pinnacle devig.
    Treat with caution until empirically verified.
    """
    if not cover_prob or cover_prob <= 0 or cover_prob >= 1:
        return 0
    if not odds_str:
        return 0

    try:
        dec = american_to_decimal(odds_str)
    except:
        return 0

    b = dec - 1  # net odds (profit per unit)
    p = cover_prob
    q = 1 - p

    if b <= 0:
        return 0

    kelly = (b * p - q) / b
    if kelly <= 0:
        return 0

    if quarter:
        kelly *= 0.25

    return min(kelly, 0.03)  # Cap at 3% bankroll (raised from 2% per TB performance data Apr 29)


def run_scrape():
    """Run full OddsTrader scrape for NHL and MLB props."""
    now = datetime.now(timezone.utc)
    print(f"\n{'=' * 60}")
    print(f"  ODDSTRADER +EV PROP SCRAPER")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'=' * 60}")

    all_props = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for sport, url in [# ("NHL", "https://www.oddstrader.com/nhl/player-props/"),  # DISABLED: Braxton directive Apr 29
                           ("MLB", "https://www.oddstrader.com/mlb/player-props/")]:
            print(f"\n  Scraping {sport}...")
            page.goto(url, timeout=30000)
            page.wait_for_timeout(12000)
            props = extract_all_props(page, sport)
            all_props.extend(props)
            print(f"  {sport}: {len(props)} +EV props")

        browser.close()

    # Enrich with Kelly sizing and true monetary EV
    for prop in all_props:
        prop["kelly_pct"] = round(calculate_kelly(prop["fair_prob"], prop.get("best_odds")) * 100, 2)
        # Calculate true monetary EV (not OT's probability-edge EV%)
        if prop["fair_prob"] > 0 and prop.get("best_odds"):
            try:
                dec = american_to_decimal(prop["best_odds"])
                true_ev = prop["fair_prob"] * (dec - 1) - (1 - prop["fair_prob"])
                prop["true_ev_pct"] = round(true_ev * 100, 1)
            except:
                prop["true_ev_pct"] = 0
        else:
            prop["true_ev_pct"] = 0

    # Sort by EV
    all_props.sort(key=lambda x: x['ev_pct'], reverse=True)

    # Apply filters for actionable picks
    actionable = []
    for prop in all_props:
        # Filter: EV between 10% and 35% (raised from 5% after 872 graded bets)
        # 5-10% tier was -$439 ROI, only 10%+ is profitable
        if prop["ev_pct"] < 10 or prop["ev_pct"] > 35:
            continue
        # Filter: Must have fair probability (quality check)
        if prop["fair_prob"] <= 0:
            continue
        # Filter: Disable NHL goal-scoring props (15% WR on 259 bets, 1.9% on 52 bets)
        market = prop.get("market", "").lower()
        if "player to score" in market:
            continue
        # Filter: Disable RBI props (29.6% WR on 27 OT sim bets, -10.8% ROI)
        if "rbi" in market:
            continue
        actionable.append(prop)

    # Tier the picks
    for prop in actionable:
        ev = prop["ev_pct"]
        if ev >= 15:
            prop["tier"] = "A"
            prop["confidence"] = "HIGH"
        elif ev >= 10:
            prop["tier"] = "B"
            prop["confidence"] = "HIGH"
        elif ev >= 5:
            prop["tier"] = "C"
            prop["confidence"] = "MEDIUM"

    output = {
        "timestamp": now.isoformat(),
        "source": "oddstrader",
        "benchmark": "pinnacle_novig",
        "total_scraped": len(all_props),
        "actionable": len(actionable),
        "props": actionable,
    }

    outpath = os.path.join(DATA_DIR, "oddstrader_ev_props.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2)

    # Summary
    print(f"\n  Total scraped: {len(all_props)}")
    print(f"  Actionable (5-35% EV): {len(actionable)}")

    by_market = {}
    for p2 in actionable:
        k = f"{p2['sport']}|{p2['market']}"
        by_market[k] = by_market.get(k, 0) + 1
    print(f"\n  By market:")
    for k, v in sorted(by_market.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    tier_a = [p2 for p2 in actionable if p2.get("tier") == "A"]
    tier_b = [p2 for p2 in actionable if p2.get("tier") == "B"]
    print(f"\n  Tier A (15%+ EV): {len(tier_a)}")
    print(f"  Tier B (10-15% EV): {len(tier_b)}")

    print(f"\n  TOP PICKS:")
    for i, p2 in enumerate(actionable[:15], 1):
        print(f"  {i:2d}. [{p2['tier']}] {p2['sport']} {p2['player']:25s} {p2['market']:25s} "
              f"EV:+{p2['ev_pct']:.1f}% kelly:{p2['kelly_pct']:.2f}% {p2['best_odds']:>6s} {p2['game']}")

    print(f"\n  Saved to {outpath}")

    # Log picks to simulation ledger with Kelly sizing
    sim_ledger_path = os.path.join(DATA_DIR, "oddstrader_sim_ledger.json")
    bankroll = 5000  # Simulation bankroll
    try:
        with open(sim_ledger_path) as f:
            sim_ledger = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        sim_ledger = {"bankroll": bankroll, "bets": []}

    # Track existing picks to avoid duplicates (player+market+game+date)
    existing = set()
    for b in sim_ledger["bets"]:
        key = f"{b.get('player')}|{b.get('market')}|{b.get('game')}|{b.get('date','')[:10]}"
        existing.add(key)

    new_count = 0
    today = now.strftime("%Y-%m-%d")
    max_exposure = sim_ledger["bankroll"] * 0.15  # 15% max daily exposure
    today_wagered = sum(b.get("wager", 0) for b in sim_ledger["bets"]
                        if b.get("date", "")[:10] == today)

    # Prioritize by market performance: TB first (70.5% WR), then pitching HA, then ER.
    # DISABLED MARKETS: RBI (28.2% WR, -$956), Strikeouts (47.8% WR, -$171). Data through Apr 30.
    DISABLED_MARKETS = {"Player to hit a RBI", "Total Strikeouts"}
    MARKET_PRIORITY = {"Total Bases": 0, "Total Pitching Hits Allowed": 1, "Total Earned Runs": 2}
    actionable_sorted = sorted(
        [p for p in actionable if p.get("market", "") not in DISABLED_MARKETS],
        key=lambda p: (MARKET_PRIORITY.get(p.get("market", ""), 5), -p.get("ev_pct", 0)))

    # JUICE CAP: TB bets worse than -160 have 66.7% WR but only 3.8% ROI.
    # Bets -160 or better: 74.4% WR, 29.4% ROI. Data through Apr 30, N=104.
    TB_JUICE_CAP = -160  # Reject TB bets with juice worse than this

    for prop in actionable_sorted:
        key = f"{prop['player']}|{prop['market']}|{prop['game']}|{today}"
        if key in existing:
            continue
        # Apply juice cap for Total Bases
        if prop.get("market") == "Total Bases":
            try:
                odds_val = int(prop.get("best_odds", "0").replace("+", ""))
                if odds_val < 0 and odds_val < TB_JUICE_CAP:
                    continue  # Skip heavy juice TB bets
            except (ValueError, AttributeError):
                pass
        # HA LINE FILTER: u4½ or tighter only. u5½+ is 50% WR (coin flip).
        # u4½: 8W-3L (73%, +$281). u5½: 7W-7L (50%, -$126). Data through May 3, N=28.
        if prop.get("market") == "Total Pitching Hits Allowed":
            line_str = prop.get("line", "")
            if line_str.startswith("u"):
                try:
                    line_val = float(line_str[1:].replace("½", ".5"))
                    if line_val > 4.5:
                        continue  # Skip loose HA unders (u5½+)
                except ValueError:
                    pass
        kelly_pct = prop.get("kelly_pct", 0) / 100
        wager = round(sim_ledger["bankroll"] * kelly_pct, 2)
        if wager < 5:
            wager = 5
        # Enforce 15% daily exposure cap
        if today_wagered + wager > max_exposure:
            wager = max(0, round(max_exposure - today_wagered, 2))
        if wager < 5:
            continue  # Skip bet if remaining exposure is less than minimum bet
        today_wagered += wager
        sim_ledger["bets"].append({
            "timestamp": now.isoformat(),
            "date": today,
            "player": prop["player"],
            "market": prop["market"],
            "game": prop["game"],
            "side": prop.get("side", ""),
            "line": prop.get("line", ""),
            "ev_pct": prop["ev_pct"],
            "odds": prop.get("best_odds", ""),
            "fair_prob": prop.get("fair_prob", 0),
            "kelly_pct": prop.get("kelly_pct", 0),
            "wager": wager,
            "tier": prop.get("tier", "C"),
            "graded": False,
            "won": None,
            "pnl": 0,
        })
        new_count += 1
        existing.add(key)

    with open(sim_ledger_path, "w") as f:
        json.dump(sim_ledger, f, indent=2)

    if new_count:
        print(f"  Logged {new_count} new picks to simulation ledger (Kelly-sized)")

    return output


if __name__ == "__main__":
    run_scrape()
