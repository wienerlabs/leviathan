# Committee economics

Issue leviathan-net#4. This document sizes the verifier committee: how many
verifiers, what quorum, what bounty, and what bond those choices force. Numbers
come from `sim/leviathan_sim/committee.py` and are reproducible (see the bottom).

The on-chain mechanism is already live: a bonded verifier submits a verdict, a
two thirds quorum fires the slash, and the forfeited bond pays the verifiers who
voted. This document answers the parameters that mechanism leaves open.

## Quorum and Byzantine tolerance

The committee uses a two thirds quorum, matching the witness quorum already in
the coordinator. Two bounds apply at once:

- safety: an attacker holding `quorum - 1` verifiers cannot convict anyone;
- liveness: honest verifiers must still reach quorum, so at most
  `committee_size - quorum` may be malicious or absent.

The binding bound is the smaller one, which lands on the classic one third:

| Committee size | Quorum | Tolerated malicious | Fraction |
|---|---|---|---|
| 3 | 2 | 1 | 33% |
| 6 | 4 | 2 | 33% |
| 9 | 6 | 3 | 33% |
| 21 | 14 | 7 | 33% |
| 100 | 67 | 33 | 33% |

## The finding: the bond is set by verifier pay, not by deterrence

The whitepaper sizes the bond so that cheating is expected negative:

```
deterrence bond = reward * (1 - p) / p
```

That is necessary but not sufficient. A verifier also has to be paid enough to
bother auditing. A verifier pays the replay cost on every audit but only earns
when it catches a cheat, and the bounty is split across the quorum:

```
verifier EV = fraud_rate * (slash * bounty_bps / 10000) / quorum - audit_cost
```

Setting that to zero gives a second, independent floor on the slash:

```
sustainable bond = audit_cost * quorum / (fraud_rate * bounty_bps / 10000)
```

The bond the network must actually require is the larger of the two. For the 1B
genesis preset at `p = 0.1` with a 50% bounty, the second constraint dominates
everywhere:

| Committee size | Quorum | Deterrence bond | Verifier-sustainable bond | Required bond | Binding constraint | Collusion capital |
|---|---|---|---|---|---|---|
| 3 | 2 | $2.91 | $10.55 | $10.55 | verifier pay | $21 |
| 6 | 4 | $2.91 | $21.10 | $21.10 | verifier pay | $84 |
| 9 | 6 | $2.91 | $31.65 | $31.65 | verifier pay | $190 |
| 21 | 14 | $2.91 | $73.85 | $73.85 | verifier pay | $1034 |

So the published break-even bond of $2.91 is roughly 3.6x too low for a
three-verifier committee. At that bond a rational verifier declines to audit, and
a security layer nobody runs is not a security layer.

## What this implies

1. **Committees are not free.** Every extra verifier multiplies the audit cost
   the network pays while the bounty pool stays fixed, so the required bond grows
   roughly linearly with quorum. Going from 3 to 21 verifiers raises the bond
   floor 7x.
2. **There is a real trade-off.** A larger committee buys more Byzantine
   tolerance and makes collusion far more expensive to buy (from $21 to $1034),
   but it raises the entry bond, which thins participation. Bigger is not free.
3. **A 3 to 6 verifier committee is the sensible starting point** for the genesis
   run: it keeps the bond in the tens of dollars, tolerates one to two malicious
   verifiers, and still forces an attacker to lock a quorum of bonds.
4. **The bounty rate is a lever on the bond.** Raising `slash_bounty_bps` lowers
   the sustainable bond proportionally, because more of the forfeit reaches the
   people doing the work. A 100% bounty halves the required bond versus 50%.

## What is deliberately not modelled

- **Losing-side penalty.** There is no on-chain cost yet for voting to convict
  someone who turns out to be honest. Framing an innocent target is therefore
  cheap, bounded only by the attacker needing a quorum. This is the open economic
  hole and it needs a dispute or challenge step before it can be priced.
- **Verifier bond at risk.** The model charges the verifier the audit cost but
  does not model its own bond being slashed, since nothing slashes verifiers yet.
- **Correlated collusion.** Verifier selection is a deterministic lottery from
  on-chain state; an attacker controlling a fraction of the whole worker pool
  gets a matching fraction of verifier seats over time. The table prices buying a
  quorum outright, not grinding into one over many rounds.
- **Fee-paying demand.** No inference revenue is assumed anywhere here. The whole
  table is funded by forfeited bonds.

## Reproduce

```
cd sim && uv run python -c "from leviathan_sim.committee import committee_table; [print(r) for r in committee_table([3,6,9,21])]"
```

Tests: `cd sim && uv run python -m pytest tests/test_committee.py`
