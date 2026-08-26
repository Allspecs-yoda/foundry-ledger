#!/usr/bin/env python3
"""Allocate foundry Stripe gains into Reserve / Reinvest / Experiment.

Works offline. Does not charge anyone. Does not need Gamut.

Usage:
  python3 allocate.py --charges charges.json --capital CAPITAL.md
  STRIPE_SECRET_KEY=sk_... python3 allocate.py --stripe --capital CAPITAL.md

charges.json: [{"id", "amount_cents", "refunded_cents", "fee_cents"?, "status", "created"}]
Amounts are integer cents. status should be "succeeded" to count.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RESERVE_PCT = 0.50
REINVEST_PCT = 0.30
EXPERIMENT_PCT = 0.20
FEE_RATE = 0.029
FEE_FIXED_CENTS = 30


def parse_last_balances(capital_path: Path) -> tuple[int, int, int]:
    text = capital_path.read_text(encoding="utf-8") if capital_path.exists() else ""
    rows = [
        line
        for line in text.splitlines()
        if line.startswith("|") and not line.startswith("| date") and not re.match(r"^\|\s*---", line)
    ]
    if not rows:
        return 0, 0, 0
    cells = [c.strip() for c in rows[-1].strip("|").split("|")]
    # date source new_gross refunds fees new_net to_r to_i to_e reserve reinvest experiment notes
    if len(cells) < 13:
        return 0, 0, 0

    def dollars_to_cents(s: str) -> int:
        s = s.replace("$", "").replace(",", "").strip()
        if not s or s == "—":
            return 0
        return int(round(float(s) * 100))

    return dollars_to_cents(cells[9]), dollars_to_cents(cells[10]), dollars_to_cents(cells[11])


def usd(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def estimate_fee(amount_cents: int, fee_cents: int | None) -> int:
    if fee_cents is not None:
        return fee_cents
    return int(round(amount_cents * FEE_RATE)) + FEE_FIXED_CENTS


def load_charges_file(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    if not isinstance(data, list):
        raise SystemExit("charges file must be a list or {data: [...]}")
    return data


def fetch_stripe_charges() -> list[dict]:
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise SystemExit("STRIPE_SECRET_KEY is empty")
    url = "https://api.stripe.com/v1/charges?limit=100"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Stripe error {e.code}: {e.read().decode()[:400]}") from e
    out = []
    for c in payload.get("data", []):
        fee = None
        bal = c.get("balance_transaction")
        # expanded objects only; otherwise leave fee unknown
        if isinstance(bal, dict) and "fee" in bal:
            fee = int(bal["fee"])
        out.append(
            {
                "id": c.get("id"),
                "amount_cents": int(c.get("amount") or 0),
                "refunded_cents": int(c.get("amount_refunded") or 0),
                "fee_cents": fee,
                "status": c.get("status"),
                "created": c.get("created"),
            }
        )
    return out


def known_charge_ids(capital_path: Path) -> set[str]:
    if not capital_path.exists():
        return set()
    return set(re.findall(r"ch_[A-Za-z0-9]+", capital_path.read_text(encoding="utf-8")))


def allocate(charges: list[dict], seen: set[str]) -> dict:
    gross = refunds = fees = 0
    ids = []
    fees_est = False
    for c in charges:
        if (c.get("status") or "succeeded") != "succeeded":
            continue
        cid = str(c.get("id") or "")
        if cid and cid in seen:
            continue
        amount = int(c.get("amount_cents") or c.get("amount") or 0)
        refunded = int(c.get("refunded_cents") or c.get("amount_refunded") or 0)
        fee_raw = c.get("fee_cents")
        fee = estimate_fee(amount, None if fee_raw is None else int(fee_raw))
        if fee_raw is None:
            fees_est = True
        if amount <= 0:
            continue
        gross += amount
        refunds += refunded
        fees += fee
        if cid:
            ids.append(cid)
    net = gross - refunds - fees
    if net < 0:
        net = 0
    to_r = int(round(net * RESERVE_PCT))
    to_i = int(round(net * REINVEST_PCT))
    to_e = net - to_r - to_i
    return {
        "gross": gross,
        "refunds": refunds,
        "fees": fees,
        "net": net,
        "to_r": to_r,
        "to_i": to_i,
        "to_e": to_e,
        "ids": ids,
        "fees_est": fees_est,
    }


def append_row(capital_path: Path, source: str, result: dict) -> None:
    r0, i0, e0 = parse_last_balances(capital_path)
    r1, i1, e1 = r0 + result["to_r"], i0 + result["to_i"], e0 + result["to_e"]
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    notes = []
    if result["fees_est"]:
        notes.append("fees_est")
    if result["ids"]:
        notes.append("charges=" + ",".join(result["ids"][:12]))
    else:
        notes.append("zero-sales" if result["gross"] == 0 else "unattributed")
    row = (
        f"| {day} | {source} | {usd(result['gross'])} | {usd(result['refunds'])} | "
        f"{usd(result['fees'])} | {usd(result['net'])} | {usd(result['to_r'])} | "
        f"{usd(result['to_i'])} | {usd(result['to_e'])} | {usd(r1)} | {usd(i1)} | "
        f"{usd(e1)} | {'; '.join(notes)} |"
    )
    text = capital_path.read_text(encoding="utf-8") if capital_path.exists() else ""
    if not text.endswith("\n"):
        text += "\n"
    capital_path.write_text(text + row + "\n", encoding="utf-8")
    print(row)
    print(
        f"balances reserve={usd(r1)} reinvest={usd(i1)} experiment={usd(e1)}",
        file=sys.stderr,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Foundry capital allocator")
    p.add_argument("--capital", default="CAPITAL.md")
    p.add_argument("--charges", help="JSON file of charges")
    p.add_argument("--stripe", action="store_true", help="Pull charges with STRIPE_SECRET_KEY")
    p.add_argument("--source", default="foundry")
    args = p.parse_args()
    capital = Path(args.capital)
    if args.stripe:
        charges = fetch_stripe_charges()
        source = "stripe"
    elif args.charges:
        charges = load_charges_file(Path(args.charges))
        source = args.source
    else:
        charges = []
        source = "zero"
    result = allocate(charges, known_charge_ids(capital))
    append_row(capital, source, result)


if __name__ == "__main__":
    main()
