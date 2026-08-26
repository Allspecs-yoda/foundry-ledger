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

4. To ship a SKU by hand: write a file pack (templates / checklist) in a new public repo, append one row to `LEDGER.md`, price $9–$19 if Reinvest is $0.
5. Never commit Stripe secrets. Never touch private repos. Never touch the public repo named like a Stripe key store.

## Next-cycle policy (automatic)

- Reinvest = $0 → thin $9–$19 file pack
- Reinvest ≥ $50 → may ship a $29–$49 pack
- Never spend Reserve
- Do not create payouts or charges from this repo
