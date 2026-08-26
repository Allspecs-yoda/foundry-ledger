# foundry-ledger

Append-only public ledger for Night Shift Foundry (Dakota / @Allspecs-yoda).

- `LEDGER.md` — one SKU row per cycle (list / hold / kill)
- `CAPITAL.md` — sales → Reserve / Reinvest / Experiment
- `allocate.py` — run the capital split **without Gamut**
- `RUNBOOK.md` — what to do when agent credits are gone
- `OFFERS.md` / `catalog.json` / `feed.xml` — opt-in tail-buyer notify (Watch this repo)
- `INTEL.md` — append-only learnings so each hourly ship is smarter
- `alchemy.py` — propose the next higher-ticket brief after credits expire
- `.github/ISSUE_TEMPLATE/brief.yml` — buyer specifies the exact pack

This repo does not move money. It only accounts for Stripe charges you already have.

## Offline capital pass

```bash
# Option A: charges JSON you exported
python3 allocate.py --charges charges.json --capital CAPITAL.md

# Option B: live Stripe (secret stays on your machine, never commit it)
STRIPE_SECRET_KEY=sk_live_... python3 allocate.py --stripe --capital CAPITAL.md
```

## Credit outage

If Night Shift Foundry cannot start: keep selling via existing Payment Links, run `allocate.py` locally, and follow `RUNBOOK.md` to publish a file-only pack by hand.
