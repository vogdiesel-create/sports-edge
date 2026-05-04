#!/usr/bin/env python3
"""
CLV (Closing Line Value) Capture

Runs ~30 min before first pitch. Scrapes current OddsTrader lines for every
player/market combo we have an open bet on today. Stores closing odds alongside
the opening odds so we can compute CLV at grade time.

CLV = (closing_implied_prob - opening_implied_prob)
Positive CLV = we got a better number than the market closed at = real edge signal.

Usage:
    python3 clv_capture.py          # Capture closing lines for today's bets
    python3 clv_capture.py summary  # Show CLV stats across all graded bets

Cron (30 min before typical first pitch):
    25 17 * * 1-5 cd /home/aiciv/sports-edge && python3 clv_capture.py >> data/daily_runs/clv.log 2>&1
    # 17:25 UTC = 1:25 PM ET (most MLB games start ~1:35 PM or 7:05 PM ET)
    # Run again for evening games:
    55 22 * * 1-5 cd /home/aiciv/sports-edge && python3 clv_capture.py >> data/daily_runs/clv.log 2>&1
    # 22:55 UTC = 6:55 PM ET
"""

import json
import os
import re
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SIM_LEDGER = os.path.join(DATA_DIR, "oddstrader_sim_ledger.json")


def american_to_implied(odds_str):
    """Convert American odds to implied probability."""
    if not odds_str:
        return None
    try:
        odds = int(odds_str.replace("+", ""))
    except (ValueError, AttributeError):
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def scrape_current_lines(players_needed):
    """Scrape OddsTrader for current lines on specific players/markets.

    players_needed: set of (player_lower, market_lower) tuples
    Returns: dict of (player_lower, market_lower) -> {"odds": str, "ev_pct": float, "line": str}
    """
    if not players_needed:
        return {}

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.oddstrader.com/mlb/player-props/", timeout=30000)
        page.wait_for_timeout(12000)

        # Click LOAD MORE to get all props
        for _ in range(10):
            try:
                page.click('text=LOAD MORE', timeout=3000)
                page.wait_for_timeout(2000)
            except:
                break

        rows = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[class*="betWithBottomRow"]')).map(r => ({
                text: r.innerText.trim()
            }));
        }''')

        browser.close()

    # Parse each row looking for our players
    for item in rows:
        lines = [l.strip() for l in item['text'].split('\n') if l.strip()]
        if len(lines) < 5:
            continue

        player = market = odds = line_value = ev_pct = ""
        for i, l in enumerate(lines):
            if '@' in l and len(l) < 20:
                if i + 1 < len(lines):
                    player = lines[i + 1]
                if i + 2 < len(lines):
                    market = lines[i + 2]

        for l in lines:
            if l.startswith('+') and l.endswith('%'):
                ev_pct = l
            elif re.match(r'^[+-]\d+$', l):
                odds = l
            elif re.match(r'^\([+-]\d+\)$', l):
                odds = l.strip('()')
            elif re.match(r'^[ou]\d*½?$', l):
                line_value = l

        if player and market:
            key = (player.lower(), market.lower())
            if key in players_needed:
                ev_val = 0
                if ev_pct:
                    try:
                        ev_val = float(ev_pct.replace('+', '').replace('%', ''))
                    except:
                        pass
                results[key] = {
                    "close_odds": odds,
                    "close_ev_pct": ev_val,
                    "close_line": line_value,
                }

    return results


def capture_closing_lines():
    """Main CLV capture: find today's ungraded bets, scrape closing lines, update ledger."""
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    print(f"\n{'=' * 60}")
    print(f"  CLV CAPTURE")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'=' * 60}")

    # Load ledger
    with open(SIM_LEDGER) as f:
        ledger = json.load(f)

    # Find today's bets that don't have closing lines yet
    todays_bets = []
    players_needed = set()
    for bet in ledger["bets"]:
        if bet.get("date") != today:
            continue
        if bet.get("close_odds"):
            continue  # Already captured
        player = bet.get("player", "")
        market = bet.get("market", "")
        if player and market:
            todays_bets.append(bet)
            players_needed.add((player.lower(), market.lower()))

    print(f"\n  Today's bets needing closing lines: {len(todays_bets)}")
    print(f"  Unique player/market combos: {len(players_needed)}")

    if not players_needed:
        print("  Nothing to capture.")
        return

    # Scrape current lines
    print(f"\n  Scraping OddsTrader for closing lines...")
    closing_lines = scrape_current_lines(players_needed)
    print(f"  Found closing lines for {len(closing_lines)} of {len(players_needed)} combos")

    # Update bets with closing lines
    matched = 0
    for bet in todays_bets:
        key = (bet["player"].lower(), bet["market"].lower())
        if key in closing_lines:
            cl = closing_lines[key]
            bet["close_odds"] = cl["close_odds"]
            bet["close_ev_pct"] = cl["close_ev_pct"]
            bet["close_line"] = cl["close_line"]

            # Calculate CLV
            open_implied = american_to_implied(bet.get("odds", ""))
            close_implied = american_to_implied(cl["close_odds"])
            if open_implied and close_implied:
                # CLV = close_implied - open_implied
                # Positive = we got better odds than close (edge)
                bet["clv"] = round((close_implied - open_implied) * 100, 2)
            else:
                bet["clv"] = None

            matched += 1
            clv_str = f"{bet['clv']:+.1f}pp" if bet.get('clv') is not None else "N/A"
            print(f"    {bet['player']:25s} {bet['market']:25s} open={bet.get('odds','?'):>6s} close={cl['close_odds']:>6s} CLV={clv_str}")

    # Save
    with open(SIM_LEDGER, "w") as f:
        json.dump(ledger, f, indent=2)

    print(f"\n  Updated {matched} bets with closing lines")
    print(f"  Saved to {SIM_LEDGER}")


def show_clv_summary():
    """Show CLV stats across all bets that have closing line data."""
    with open(SIM_LEDGER) as f:
        ledger = json.load(f)

    bets_with_clv = [b for b in ledger["bets"] if b.get("clv") is not None]

    if not bets_with_clv:
        print("No bets with CLV data yet. Run clv_capture.py before games start.")
        return

    print(f"\n{'=' * 60}")
    print(f"  CLV SUMMARY")
    print(f"{'=' * 60}")
    print(f"\n  Total bets with CLV: {len(bets_with_clv)}")

    clvs = [b["clv"] for b in bets_with_clv]
    positive = [c for c in clvs if c > 0]
    negative = [c for c in clvs if c < 0]
    zero = [c for c in clvs if c == 0]

    print(f"  Positive CLV (got better number): {len(positive)} ({len(positive)/len(clvs)*100:.0f}%)")
    print(f"  Negative CLV (got worse number): {len(negative)} ({len(negative)/len(clvs)*100:.0f}%)")
    print(f"  Zero CLV: {len(zero)}")
    print(f"  Median CLV: {sorted(clvs)[len(clvs)//2]:+.2f}pp")
    print(f"  Mean CLV: {sum(clvs)/len(clvs):+.2f}pp")

    # By market
    by_market = {}
    for b in bets_with_clv:
        m = b.get("market", "Unknown")
        by_market.setdefault(m, []).append(b["clv"])

    print(f"\n  By market:")
    for m, vals in sorted(by_market.items(), key=lambda x: -len(x[1])):
        med = sorted(vals)[len(vals)//2]
        pos = len([v for v in vals if v > 0])
        print(f"    {m:30s} n={len(vals):3d}  median={med:+.2f}pp  positive={pos}/{len(vals)}")

    # CLV vs actual wins
    graded_clv = [b for b in bets_with_clv if b.get("graded")]
    if graded_clv:
        print(f"\n  CLV vs Outcomes (n={len(graded_clv)}):")
        pos_clv_bets = [b for b in graded_clv if b["clv"] > 0]
        neg_clv_bets = [b for b in graded_clv if b["clv"] < 0]

        if pos_clv_bets:
            pos_wr = sum(1 for b in pos_clv_bets if b.get("won")) / len(pos_clv_bets) * 100
            pos_pnl = sum(b.get("pnl", 0) for b in pos_clv_bets)
            print(f"    Positive CLV: {len(pos_clv_bets)} bets, {pos_wr:.0f}% WR, ${pos_pnl:+.2f} P&L")

        if neg_clv_bets:
            neg_wr = sum(1 for b in neg_clv_bets if b.get("won")) / len(neg_clv_bets) * 100
            neg_pnl = sum(b.get("pnl", 0) for b in neg_clv_bets)
            print(f"    Negative CLV: {len(neg_clv_bets)} bets, {neg_wr:.0f}% WR, ${neg_pnl:+.2f} P&L")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        show_clv_summary()
    else:
        capture_closing_lines()
