# Contributing

This repository holds the Phase 0 proof: the simulation and the documents. The network
substrate (Anchor programs, trainer, verifier daemon) lives in wienerlabs/leviathan-net; the
site lives in wienerlabs/leviathan-web.

## Setup

```
cd sim
uv venv && uv pip install torch numpy matplotlib pytest   # CPU torch is fine
```

The full sim needs the tinyshakespeare corpus at `sim/data/shakespeare.txt` (gitignored):

```
curl -sSL -o data/shakespeare.txt \
  https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt
```

## Tests

```
cd sim && python -m pytest tests -q
```

The suite runs on CPU with a synthetic corpus and no downloads; CI runs exactly this. Every
qualitative claim the README makes should have a test that would fail if the sim stopped
backing it — if you change aggregation, attacks, the verifier or the economy, extend the tests
with the claim your change adds.

## Experiments

```
python -m leviathan_sim.run --rounds 30        # the seven headline scenarios
python -m leviathan_sim.run --verify           # tolerance-band replay experiment
python -m leviathan_sim.run --sparse           # dense vs SparseLoCo transport
python -m leviathan_sim.run --band-sweep       # within-band adversary budget
```

Add `--smoke` for a 3-round sanity pass. Outputs land in `sim/out/` (gitignored); curated
results are promoted to `docs/assets/` by hand, together with the numbers quoted in README and
docs. If you regenerate an asset, update every number that quotes it in the same commit.

## Docs discipline

The honest-claims policy (docs/DECISIONS.md, D6) binds prose, not just marketing: no claim in
README, the whitepaper or ARCHITECTURE.md should outrun what the sim or the fork actually
demonstrates. If you find one that does, that is a bug — file it or fix it via docs/GAPS.md.

## Security findings

See SECURITY.md — exploitable findings go through private reporting, not public issues.
