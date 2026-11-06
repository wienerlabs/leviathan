"""Published figures must track the model that produces them.

The operating point is quoted by hand across the docs, so a change to the
economy constants can leave a stale number behind without failing anything.
"""

import re
from pathlib import Path

import pytest

from leviathan_sim.committee import committee_table
from leviathan_sim.economy import genesis_parameters

DOCS = Path(__file__).resolve().parents[2] / "docs"
README = DOCS.parent / "README.md"
BASE58_ID = re.compile(r"`([1-9A-HJ-NP-Za-km-z]{32,44})`")


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _genesis_committee_row(size: int) -> dict:
    preset = genesis_parameters()["preset"]
    rows = committee_table([size])
    return next(row for row in rows if row["preset"] == preset)


@pytest.mark.parametrize("doc", ["AUDIT_PREP.md", "TASKS.md", "TOKENOMICS.md"])
def test_audit_burn_share_matches_the_model(doc):
    share = genesis_parameters()["audit_burn_share_of_rewards"]
    assert f"{share * 100:.2f}%" in _read(doc)


@pytest.mark.parametrize("doc", ["REDTEAM_BOUNTY.md", "TOKENOMICS.md"])
def test_deterrence_bond_matches_the_model(doc):
    bond = genesis_parameters()["bond_usd"]
    assert f"${bond:.2f}" in _read(doc)


@pytest.mark.parametrize(
    "doc", ["REDTEAM_BOUNTY.md", "TOKENOMICS.md", "COMMITTEE_ECONOMICS.md"]
)
def test_committee_bond_matches_the_model(doc):
    bond = _genesis_committee_row(3)["bond_usd"]
    assert f"${bond:.2f}" in _read(doc)


def test_audit_scope_names_the_deployed_programs():
    section = README.read_text(encoding="utf-8").split("Current devnet program IDs:")[1]
    current = set(BASE58_ID.findall(section.split("##")[0]))
    assert len(current) == 3

    scope = _read("AUDIT_PREP.md").split("## In-scope programs")[1].split("##")[0]
    assert set(BASE58_ID.findall(scope)) == current
