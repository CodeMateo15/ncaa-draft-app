# NCAA Baseball Draft Predictor — web app

**Live: https://codemateo15-ncaa-draft-app.share.connect.posit.cloud/**

An interactive front end for a model of the MLB draft, built on public NCAA
college baseball statistics. One audience selector reshapes the whole interface,
so a scout, a player's family, a researcher and a fan each get a coherent view of
the same model rather than one kitchen-sink page.

**Board** — every draft-eligible player above a probability gate, ranked, for
2021–2026. Filter by season, role, team, draft result; sort by actual draft
order. Scout and researcher views add a projected-vs-actual scatter.

**Player** — search 61,000 player-seasons and read the model's probability,
grade and SHAP-backed strengths and concerns.

**Score a stat line** — type in a season, pick a team-season for context, and
the model scores it. Blank fields stay missing rather than being filled with a
median, which is how the model was trained.

**Stat glossary** — all 80 abbreviations, with what each means and whether it was
recorded at the game, computed from those counts, or produced by the model.

## Running it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
shiny run --reload app.py
```

Python 3.10 or newer. The first launch installs `ncaa_bbStats` from GitHub,
which carries the models and every statistic the app shows — this repository
contains no player data at all.

## Deploying

Built for [Posit Connect Cloud](https://connect.posit.cloud), which deploys
straight from this repository: point it at `app.py` and it reads
`requirements.txt`. Cold start is about a second; steady state is roughly 400 MB
of memory, most of it the scientific Python stack rather than the data.

`requirements.txt` pins the package to a release tag rather than a branch, so a
deployed site cannot change because the package repository moved.

## The model

`v7-public-2026.1`. It shares its design with the V7 model in Biggs & Gerber
(2026) but is a **separate lineage**, not a revision of it — different features,
labels, population and settings. The paper's published metrics do not describe
it, and the two agree on only about half of a top-100 board. `model_card()`
lists every difference, and the app shows it under "How it works".

Two stages ship: a classifier for whether a player is drafted, and a regressor
for where a drafted player falls within their college class. A third stage
predicting signing bonus as a share of slot value was attempted and is not
shipped — it scored a rank correlation of 0.003 on held-out data.

Trained on 2021–2025 and held out on 2026. On that held-out season Stage 1
reaches 0.703 PR-AUC against a 7.8% base rate, and Stage 2 a Spearman
correlation of 0.647.

## Known limits

The order model regresses toward the middle: it never projects anyone later than
about the 290th college pick, while players are taken as late as the 440th. Late
picks are therefore systematically projected earlier than they go. The app says
so beneath the chart rather than hiding it.

Draft probability is a population rate, not a promise about an individual. The
model sees box-score statistics and program strength — no scouting grades, no
velocity, no medicals, no makeup.

## A note on how this was built

The interface was built with AI assistance (Claude) as a way to visualise the
model's output. The model, the data pipeline and the research behind them are
the author's own work; the app around them is not hand-written and has not been
reviewed line by line. Read what it shows with that in mind.

## Licence

MIT for the code. Data licensing and provenance are documented in the
[`ncaa_bbStats`](https://github.com/CodeMateo15/CollegeBaseballStatsPackage)
repository. Not affiliated with or endorsed by MLB or the NCAA.
