# Foundry runbook (works when Gamut credits are gone)

Night Shift Foundry is optional. The catalog, checkout links, and this allocator are not.

## If the agent cannot start

1. Do **not** invent a shipped SKU in chat.
2. Keep existing Stripe Payment Links live. Buyers do not need Gamut.
3. On your laptop:

```bash
git clone https://github.com/Allspecs-yoda/foundry-ledger.git
cd foundry-ledger
# export charges from Stripe Dashboard → Payments, or use a restricted key
python3 allocate.py --charges charges.json --capital CAPITAL.md
# or
STRIPE_SECRET_KEY=rk_live_... python3 allocate.py --stripe --capital CAPITAL.md
git add CAPITAL.md && git commit -m "capital: offline cycle" && git push
```

4. To keep **building after Gamut credits expire** (foundry still runs on your laptop):

```bash
git clone https://github.com/Allspecs-yoda/custom-brief-desk.git
git clone https://github.com/Allspecs-yoda/foundry-ledger.git
cd foundry-ledger
python3 alchemy.py --write ../custom-brief-desk/briefs/next.json
cd ../custom-brief-desk
python3 desk/build.py build briefs/next.json --out ../next-pack
# push next-pack as a new public repo, then:
cd ../foundry-ledger
python3 alchemy.py --learn "shipped next-pack; note what worked"
# append LEDGER.md by hand, run allocate.py, git push
```

A local hourly cron can call the same two scripts. No agent required.

5. To ship a SKU by hand without alchemy: write a file pack, append `LEDGER.md`.
6. Never commit Stripe secrets. Never touch private repos (including Transmutation / any forge). Never touch the public repo named like a Stripe key store. This is the **foundry**.

## Next-cycle policy (automatic)

- Reinvest = $0 → thin $9–$19 file pack
- Reinvest ≥ $50 → may ship a $29–$49 pack
- Never spend Reserve
- Do not create payouts or charges from this repo

## Checkout (already live)

Every listed SKU has a Stripe Payment Link. Files stay public; payment is the license + CLAIM record.

After a paid Checkout Session, the foundry clerk (webhook or this agent) should open `PAID:` on this repo and append `CAPITAL.md`. Buyers open `CLAIM:` with receipt last-4 (issue template in `.github/ISSUE_TEMPLATE/claim.yml`).

## Payouts (Dakota Dashboard — OAuth cannot do this)

Stripe account `Veritas` / Dakota VanNauker: **charges_enabled=true**, **payouts_enabled=true**, but:

- Payout schedule is **manual** (not daily).
- Available balance is **negative ~$97.92**. Stripe already failed three automatic bank *debits* (`insufficient_funds`) trying to cover that hole. Statement descriptor on those pulls: `Iipi`.
- A **Tax Product Subscription** Stripe fee (~$90) is on the ledger. There are **zero succeeded customer charges**.
- This agent cannot POST `/v1/account` payout schedule (403 Platform Controls) and cannot create payouts via API (`cannot_create_connect_standard_payouts_through_api`).

Do this in Stripe Dashboard (you, not the agent):

1. **Balance** — add funds or wait until foundry sales exceed ~$98 so the balance is positive. Until then **nothing can pay out**.
2. **Settings → Payouts** — set interval to **Automatic / Daily** (delay 2 days is already on the account). Confirm the bank `ba_…` is the account you want.
3. **Developers → Webhooks** — add an endpoint for `checkout.session.completed` (and optionally `charge.succeeded`) pointing at the foundry checkout-paid hook. Signing secret goes on the agent webhook, never in this repo.
4. Do **not** reuse donation Payment Links for SKUs.

Never commit Stripe secrets here. Never create payouts from `allocate.py`.
