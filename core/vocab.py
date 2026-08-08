"""Per-audience wording and tab sets.

The same numbers mean different things to a scout and to a player's family, and
the difference is mostly vocabulary. One table, so a phrase can be audited in
one place rather than hunted through render functions.
"""

MODES = {
    "scout": "Scout / analyst",
    "player": "Player / family",
    "researcher": "Researcher",
    "fan": "Fan",
}

# Which tabs each mode sees, in order. The first is the landing tab.
TABS = {
    "scout": ["board", "player", "custom", "glossary", "methods"],
    "player": ["custom", "player", "glossary", "methods"],
    "researcher": ["methods", "board", "player", "custom", "glossary"],
    "fan": ["board", "player", "glossary"],
}

_STRINGS = {
    "board.title": {
        "scout": "Draft board",
        "player": "Draft board",
        "researcher": "Model board",
        "fan": "The Big Board",
    },
    "board.blurb": {
        "scout": "Every player the model gives a real chance of being drafted, "
                 "ranked by projected college draft order.",
        "player": "Where the model ranks this year's draft-eligible players.",
        "researcher": "Stage 1 gates on modelled draft probability; Stage 2 "
                      "orders the survivors. Ranks are the rank of the Stage 2 "
                      "output within the gated pool, not a predicted pick.",
        "fan": "Who the model likes in this year's class.",
    },
    "prob": {
        "scout": "Draft probability",
        "player": "Chance of being drafted",
        "researcher": "P(drafted) — Stage 1",
        "fan": "Draft chance",
    },
    "order": {
        "scout": "Projected college draft order",
        "player": "Roughly where you'd go",
        "researcher": "Stage 2 predicted college draft order",
        "fan": "Projected slot",
    },
    "grade": {
        "scout": "Draft grade",
        "player": "Grade",
        "researcher": "Percentile grade vs training population",
        "fan": "Grade",
    },
    "custom.title": {
        "scout": "Score a stat line",
        "player": "Get my projection",
        "researcher": "Ad-hoc inference",
        "fan": "Try a stat line",
    },
    "custom.blurb": {
        "scout": "Enter a line and the model scores it against the selected "
                 "team-season context. Blank fields stay missing rather than "
                 "being filled with a median.",
        "player": "Put in your season and see what the model makes of it. "
                  "Leave anything you don't know blank.",
        "researcher": "Builds a feature row over the model's full column set, "
                      "fills what you supply, derives what is exactly "
                      "derivable, and leaves the rest missing for XGBoost to "
                      "handle natively.",
        "fan": "Make up a season and see what the model says.",
    },
    "explain": {
        "scout": "Feature contributions",
        "player": "What's helping and hurting",
        "researcher": "SHAP contributions",
        "fan": "Why",
    },
}


def t(mode: str, key: str) -> str:
    """Look up one phrase for one audience."""
    entry = _STRINGS.get(key, {})
    return entry.get(mode, entry.get("scout", key))


PAPER_NOTE_TITLE = "How this relates to the published model"

# Written to be reassuring where that is warranted and specific where it is
# not. The aggregate metrics really are close; the individual boards are not,
# and a note that glossed over the second would be misleading in exactly the
# way a reader would most likely act on.
PAPER_NOTE = [
    "The model behind this site is a public rebuild of the one in the research "
    "paper. Some of the statistics the published model trains on come from a "
    "commercial provider whose terms do not allow the data to be "
    "redistributed, so it cannot be put on a website as it stands.",

    "Rather than drop those inputs, they were rebuilt: the run-value metrics "
    "were re-derived from public NCAA play, and everything else comes from "
    "counting statistics that are records of what happened on the field. "
    "Removing the rebuilt metrics entirely changes accuracy by less than the "
    "run-to-run variation of the model itself, so little is lost by the "
    "substitution — the approach and the results carry over.",

    "Headline accuracy is close to the published figures. Individual rankings "
    "are not: the two models agree on about half of a top-100 board. That gap "
    "is mostly down to the two being fitted on different populations — this "
    "one scores every player it can find, the published one a smaller "
    "screened set — along with different settings and a different held-out "
    "season. It is not a correction of the published model, which uses its "
    "own, separately built data.",

    "So this is the same idea, freely usable and reproducible by anyone, but "
    "it is a separate model rather than a copy of the paper's. Cite the paper "
    "for the published results, and this site for what you see here. The "
    "model card lists every difference.",
]

DISCLAIMER = (
    "This is a statistical projection built from public college statistics and "
    "team context. It has no scouting grades, velocity readings, medical "
    "information or makeup assessment in it, and it is not advice. Players are "
    "drafted for reasons this model cannot see."
)
