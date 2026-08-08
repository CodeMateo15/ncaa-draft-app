"""Data and model access for the app.

Everything is loaded once at import and shared across sessions. The package
caches are process-global and read-only, so there is nothing per-session to
build -- and the first request must not be the one that pays for the load.
"""

from __future__ import annotations

import functools
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from ncaa_bbStats import scouting
from ncaa_bbStats._paths import data_path
from ncaa_bbStats.player_utils import load_player_frame

# The seasons the player caches cover. 2026 is the current draft class.
SEASONS = [2026, 2025, 2024, 2023, 2022, 2021]
CURRENT_SEASON = 2026

# Suppress pick/bonus detail below this modelled probability, matching the
# notebook. Below it the rank model is being asked about a player the
# classifier does not think will be drafted at all.
MIN_PROB_FOR_PICK_DETAIL = 0.25


def _frames():
    batting = load_player_frame("batting", "noMin")
    pitching = load_player_frame("pitching", "noMin")
    return batting, pitching


BATTING, PITCHING = _frames()


def _people() -> pd.DataFrame:
    """One row per player-season: identity only, for search and filters."""
    columns = ["player_id", "name", "team", "team name", "year"]
    both = pd.concat([BATTING[columns], PITCHING[columns]], ignore_index=True)
    roles = (
        pd.concat([
            BATTING[["player_id", "year"]].assign(bats=True),
            PITCHING[["player_id", "year"]].assign(pitches=True),
        ], ignore_index=True)
        .groupby(["player_id", "year"], as_index=False)
        .agg({"bats": "any", "pitches": "any"})
        .fillna(False)
    )
    out = (both.drop_duplicates(["player_id", "year"])
                .merge(roles, on=["player_id", "year"], how="left"))
    out["role"] = [
        "Two-way" if b and p else "Pitcher" if p else "Batter"
        for b, p in zip(out["bats"].fillna(False), out["pitches"].fillna(False))
    ]
    return out.sort_values(["name", "year"]).reset_index(drop=True)


PEOPLE = _people()

TEAMS = (PEOPLE[["team", "team name"]]
         .drop_duplicates()
         .sort_values("team name")
         .reset_index(drop=True))

TEAM_CHOICES = dict(zip(TEAMS["team"],
                        TEAMS["team name"] + " (" + TEAMS["team"] + ")"))


@functools.lru_cache(maxsize=1)
def _college_picks() -> dict:
    """Sorted overall pick numbers of the college draftees in each season.

    The model predicts a college draft order -- rank among college players only
    -- while the draft record gives an overall pick number that counts high
    school selections too. Comparing the two directly overstates the model's
    error for every player taken after the first high schooler. Ranking the
    actual pick within this list puts both on the college scale.
    """
    registry = pd.read_csv(data_path("player_registry", "player_registry.csv"))
    drafted = registry[registry["draft_pick"].notna()]
    return {
        int(year): np.sort(group["draft_pick"].astype(float).values)
        for year, group in drafted.groupby("draft_year")
    }


def college_order(season: int, picks: pd.Series) -> pd.Series:
    """Convert overall pick numbers to college draft order for one season."""

    reference = _college_picks().get(int(season))
    if reference is None or reference.size == 0:
        return pd.Series([pd.NA] * len(picks), index=picks.index, dtype="Int64")
    values = picks.astype("Float64")
    order = np.searchsorted(reference, values.fillna(-1).astype(float),
                            side="left") + 1
    # A draft order is a count of players, so it is an integer. Int64 rather
    # than int64 because undrafted players have no order at all.
    out = pd.Series(order, index=picks.index, dtype="Int64")
    return out.where(values.notna())


# A player the model gives better-than-even odds of being drafted. At this gate
# the 2026 board is 376 players, 67% of whom were drafted, and it contains 56%
# of all college draftees; opening it to everyone reaches 98% of them at 8%
# precision. Neither is the right answer for every user, so both are offered.
REAL_CHANCE = 0.50


@functools.lru_cache(maxsize=32)
def board(season: int, min_probability: float = REAL_CHANCE) -> pd.DataFrame:
    """Every available player above a probability gate, model-ranked."""
    rows = scouting.draft_board(season, n=1_000_000,
                                min_probability=min_probability)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.merge(PEOPLE[PEOPLE["year"] == season][["name", "team", "team name", "role"]],
                  on=["name", "team"], how="left")
    df["tier"] = pd.cut(df["rank"], bins=[0, 50, 150, 10 ** 6],
                        labels=["Early", "Middle", "Late"])
    df["actual_college_order"] = college_order(season, df["actual_pick"])
    df["actual_pick"] = df["actual_pick"].astype("Int64")
    return df


UNDRAFTED = "Undrafted"


def as_draft_position(values: pd.Series) -> pd.Series:
    """Render a draft position column: a whole number, or "Undrafted".

    An empty cell reads as missing data rather than as a fact about the player,
    and these players were not drafted -- which is the single most useful thing
    the column can say about them.
    """
    return values.apply(lambda v: UNDRAFTED if pd.isna(v) else f"{int(v):,}")


def college_class_size(season: int) -> int:
    """How many college players were drafted in one season."""
    reference = _college_picks().get(int(season))
    return 0 if reference is None else int(reference.size)


@functools.lru_cache(maxsize=4096)
def report(name: str, season: int) -> str | None:
    """The text scouting report for one player-season."""
    return scouting.scouting_report(name, season)


@functools.lru_cache(maxsize=4096)
def prediction(name: str, season: int) -> dict:
    """Probability, grade and projected order for one player-season."""
    probability = scouting.predict_draft_probability(name, season)
    order = scouting.predict_draft_order(name, season)
    eligible, basis = (None, None)
    try:
        eligible, basis = scouting.is_draft_eligible(name, season)
    except Exception:
        pass
    return {
        "probability": probability,
        "order": order,
        "eligible": eligible,
        "eligibility_basis": basis,
    }


def search_players(query: str, season: int | None, limit: int = 40) -> pd.DataFrame:
    """Case-insensitive substring search over the player index."""
    people = PEOPLE
    if season is not None:
        people = people[people["year"] == season]
    query = (query or "").strip().lower()
    if not query:
        return people.head(0)
    hit = people[people["name"].str.lower().str.contains(query, regex=False)]
    return hit.head(limit)


def custom_prediction(role: str, age: float, stats: dict,
                      team: str | None, season: int) -> dict:
    """Score a stat line the user typed in."""
    return scouting.predict_from_stats(
        role, age, stats, team=team or None, season=season,
    )


def model_card() -> dict:
    return scouting.model_card()


# Stamped on the page so a screenshot always says which model produced it.
MODEL_VERSION = model_card().get("model_version", "unknown")
