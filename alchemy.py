#!/usr/bin/env python3
"""Foundry alchemy — transmute last SKUs + INTEL into a stronger next brief.

This is the foundry layer, not Dakota's private forge/Transmutation repos.
No network. No Gamut. Works after credits expire.

  python3 alchemy.py                  # print next brief + ticket floor
  python3 alchemy.py --write briefs/next.json
  python3 alchemy.py --learn "one line"   # append INTEL.md

Ticket rule: next_floor = min(49, max(29, last_price + 2)) unless last was hold/kill.
Never clones the last niche listed in INTEL.md or LEDGER.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "LEDGER.md"
INTEL = ROOT / "INTEL.md"

NICHES = [
    "wedding photography",
    "SaaS onboarding copy",
    "Etsy shop ops",
    "podcast booking",
    "Airbnb turnover",
    "yoga studio memberships",
    "independent bookstore events",
    "mobile detailing",
    "tutor session packs",
    "church volunteer ops",
    "food-truck prep lists",
    "tattoo aftercare kits",
]

MODULE_LADDER = [
    ["intake_form", "scope_recap", "change_order", "email_ladder"],
    ["intake_form", "change_order", "cited_rate_card", "quote_sheet", "worked_example"],
    ["intake_form", "cited_rate_card", "loss_bench", "quote_sheet", "offer_page", "preflight_qa"],
    ["onboarding_sop", "revision_sop", "welcome_3", "dunning_4", "cited_rate_card", "delivery_sop"],
]


def last_ledger_row() -> dict | None:
    if not LEDGER.exists():
        return None
    rows = [
        line
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.startswith("|") and not line.startswith("| date") and not re.match(r"^\|\s*---", line)
    ]
    if not rows:
        return None
    cells = [c.strip() for c in rows[-1].strip("|").split("|")]
    if len(cells) < 6:
        return None
    price = 0
    m = re.search(r"(\d+)", cells[3])
    if m:
        price = int(m.group(1))
    return {"date": cells[0], "sku": cells[1], "repo": cells[2], "price": price, "decision": cells[3] if False else cells[4], "reason": cells[5]}


def used_niches() -> set[str]:
    text = ""
    if INTEL.exists():
        text += INTEL.read_text(encoding="utf-8").lower()
    if LEDGER.exists():
        text += LEDGER.read_text(encoding="utf-8").lower()
    found = set()
    for n in NICHES:
        if n.lower() in text:
            found.add(n)
    return found


def next_floor(last_price: int, decision: str) -> int:
    if decision == "kill":
        return 29
    if decision == "hold":
        return max(29, last_price)
    return min(49, max(29, last_price + 2))


def propose() -> dict:
    last = last_ledger_row()
    last_price = last["price"] if last else 29
    decision = last["decision"] if last else "list"
    floor = next_floor(last_price, decision)
    used = used_niches()
    niche = next((n for n in NICHES if n not in used), NICHES[0])
    rung = min(3, max(0, (floor - 29) // 7))
    modules = MODULE_LADDER[rung]
    brief = {
        "buyer_handle": "foundry-hourly",
        "product_name": f"{niche.title()} Desk",
        "audience": f"Solo operators in {niche} who need files today",
        "niche": niche,
        "trades": [],
        "modules": modules,
        "tone": "plain",
        "include_worked_example": True,
    }
    return {
        "ticket_floor_usd": floor,
        "last_sku": last["sku"] if last else None,
        "last_price_usd": last_price,
        "alchemy": "foundry-public",
        "brief": brief,
    }


def append_intel(line: str) -> None:
    if not INTEL.exists():
        INTEL.write_text(
            "# Foundry INTEL\n\nAppend-only learnings. Each ship adds one line so the next hourly build is smarter.\n\n",
            encoding="utf-8",
        )
    day = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    with INTEL.open("a", encoding="utf-8") as f:
        f.write(f"- {day} — {line.strip()}\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--write", help="write proposed brief JSON")
    p.add_argument("--learn", help="append one INTEL.md line")
    args = p.parse_args()
    if args.learn:
        append_intel(args.learn)
        print("intel appended")
        return
    prop = propose()
    print(json.dumps(prop, indent=2))
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(prop["brief"], indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} floor=${prop['ticket_floor_usd']}", file=sys.stderr)


if __name__ == "__main__":
    main()
