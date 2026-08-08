"""NCAA baseball draft predictor -- interactive front end.

    shiny run --reload app.py

One audience selector drives which tabs exist and how the numbers are worded;
everything else is shared. Model and data come from the ncaa_bbStats package,
so this app ships no player data of its own.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from shiny import App, reactive, render, ui
from shiny.types import SilentException

from core import backend as be
from core import glossary as G
from core import vocab as V

PITCHER_FIELDS = [
    ("ip", "IP", 80.0), ("so", "SO", 95.0), ("bb", "BB", 28.0),
    ("h", "H", 65.0), ("er", "ER", 28.0), ("hr", "HR", 6.0),
    ("g", "G", 16.0), ("gs", "GS", 15.0), ("hbp", "HBP", 7.0),
    ("tbf", "TBF", 330.0),
]
BATTER_FIELDS = [
    ("pa", "PA", 250.0), ("ab", "AB", 215.0), ("h", "H", 68.0),
    ("2b", "2B", 15.0), ("3b", "3B", 2.0), ("hr", "HR", 12.0),
    ("bb", "BB", 28.0), ("so", "SO", 40.0), ("sb", "SB", 8.0),
    ("g", "G", 56.0), ("hbp", "HBP", 6.0), ("sf", "SF", 3.0),
]

# Resolved from this file, not the working directory: the deploy target
# does not necessarily launch the app from its own folder.
APP_DIR = Path(__file__).parent

# The dark-mode component tracks the operating system and keeps nothing, so a
# chosen theme was lost on every reload. This stores the choice and restores it,
# and starts from light rather than the system setting -- the site should look
# the same to everyone until they say otherwise.
#
# Applied in <head> so the restored theme is set before first paint. The
# component overwrites the attribute when it upgrades, so the value is applied
# again on load, and only then is persistence armed -- otherwise the component's
# own default would be saved over the user's choice.
THEME_SCRIPT = """
(function () {
  var KEY = "ncaa-draft-theme";
  var root = document.documentElement;
  var read = function () {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  };
  var stored = read();
  var initial = (stored === "dark" || stored === "light") ? stored : "light";
  root.setAttribute("data-bs-theme", initial);

  window.addEventListener("load", function () {
    if (root.getAttribute("data-bs-theme") !== initial) {
      root.setAttribute("data-bs-theme", initial);
    }
    new MutationObserver(function () {
      var mode = root.getAttribute("data-bs-theme");
      if (mode !== "dark" && mode !== "light") return;
      try { window.localStorage.setItem(KEY, mode); } catch (e) {}
    }).observe(root, { attributes: true, attributeFilter: ["data-bs-theme"] });
  });
})();
"""

GRADE_STATUS = {
    "A+": "good", "A": "good", "A-": "good",
    "B+": "good", "B": "good", "B-": "warning",
    "C+": "warning", "C": "warning", "C-": "warning",
    "D+": "serious", "D": "serious", "D-": "serious",
}


def grade_pill(grade: str | None):
    """A letter grade. The letter is the label, so colour never carries it alone."""
    if not grade:
        return ui.span("—", class_="pill pill-none")
    status = GRADE_STATUS.get(str(grade).strip(), "critical")
    return ui.span(str(grade), class_=f"pill pill-{status}")


def tile(label: str, value, sub: str | None = None):
    return ui.div(
        ui.div(label, class_="tile-label"),
        ui.div(value, class_="tile-value"),
        ui.div(sub or "", class_="tile-sub"),
        class_="tile",
    )


# --- UI ---------------------------------------------------------------------

app_ui = ui.page_fluid(
    ui.head_content(
        ui.include_css(APP_DIR / "www" / "styles.css"),
        ui.tags.script(THEME_SCRIPT),
    ),
    ui.div(
        ui.div(
            ui.h1("NCAA Baseball Draft Predictor", class_="brand"),
            ui.p("A three-stage XGBoost model of the MLB draft, "
                 "built on public college statistics.", class_="brand-sub"),
            class_="brand-block",
        ),
        ui.div(
            ui.input_select("audience", "I am a…", V.MODES, selected="scout"),
            ui.div(
                ui.tags.label("Theme", class_="theme-label"),
                ui.input_dark_mode(id="theme", mode="light"),
                class_="theme-block",
            ),
            class_="audience-block",
        ),
        class_="topbar",
    ),
    ui.output_ui("tabs"),
    ui.div(
        ui.h4(V.PAPER_NOTE_TITLE),
        *[ui.p(paragraph) for paragraph in V.PAPER_NOTE],
        class_="paper-note",
    ),
    ui.div(
        ui.span(f"Model {be.MODEL_VERSION}", class_="version-chip"),
        V.DISCLAIMER,
        class_="disclaimer",
    ),
)


# --- server -----------------------------------------------------------------

def server(input, output, session):

    @reactive.calc
    def mode() -> str:
        return input.audience() or "scout"

    # ---- tab shell ----------------------------------------------------
    @render.ui
    def tabs():
        panels = {
            "board": ui.nav_panel("Board", ui.output_ui("board_tab"), value="board"),
            "player": ui.nav_panel("Player", ui.output_ui("player_tab"), value="player"),
            "custom": ui.nav_panel(V.t(mode(), "custom.title"),
                                   ui.output_ui("custom_tab"), value="custom"),
            "methods": ui.nav_panel("How it works", ui.output_ui("methods_tab"),
                                    value="methods"),
            "glossary": ui.nav_panel("Stat glossary",
                                     ui.output_ui("glossary_tab"),
                                     value="glossary"),
        }
        wanted = V.TABS[mode()]
        return ui.navset_card_tab(*[panels[name] for name in wanted],
                                  id="nav", selected=wanted[0])

    # ---- board --------------------------------------------------------
    @reactive.calc
    def board_df() -> pd.DataFrame:
        gate = (be.REAL_CHANCE if (input.board_scope() or "real") == "real"
                else 0.0)
        return be.board(int(input.board_season() or be.CURRENT_SEASON), gate)

    @reactive.calc
    def board_view() -> pd.DataFrame:
        df = board_df()
        if df.empty:
            return df
        role = input.board_role() or "All"
        if role != "All":
            df = df[df["role"] == role]
        team = input.board_team() or ""
        if team:
            df = df[df["team"] == team]
        result = input.board_result() or "all"
        if result == "drafted":
            df = df[df["actual_pick"].notna()]
        elif result == "undrafted":
            df = df[df["actual_pick"].isna()]
        df = _sorted_by_draft_order(df, input.board_sort() or "off")
        name = (input.board_name() or "").strip().lower()
        if name:
            df = df[df["name"].str.lower().str.contains(name, regex=False)]
        return df

    @render.ui
    def board_tab():
        m = mode()
        controls = [
            ui.input_radio_buttons(
                "board_scope", "Show",
                {"real": f"Real chance ({be.REAL_CHANCE:.0%}+)",
                 "all": "All available players"},
                selected="real", inline=True),
            ui.input_select("board_season", "Season",
                            {str(s): str(s) for s in be.SEASONS},
                            selected=str(be.CURRENT_SEASON)),
            ui.input_select("board_role", "Role",
                            ["All", "Pitcher", "Batter", "Two-way"]),
            ui.input_selectize("board_team", "Team",
                               {"": "All teams"} | be.TEAM_CHOICES,
                               selected=""),
            ui.input_select("board_result", "Draft result",
                            {"all": "Everyone",
                             "drafted": "Drafted only",
                             "undrafted": "Undrafted only"},
                            selected="all"),
            ui.input_select("board_sort", "Sort by draft order",
                            {"off": "Off — model rank",
                             "low": "Earliest picked first (undrafted last)",
                             "high": "Latest picked first (undrafted last)",
                             "undrafted": "Undrafted first, then earliest"},
                            selected="off"),
            ui.input_text("board_name", "Player name", placeholder="e.g. Carlon"),
        ]
        blocks = [
            ui.h2(V.t(m, "board.title")),
            ui.p(V.t(m, "board.blurb"), class_="blurb"),
            ui.div(*controls, class_="controls"),
            ui.output_ui("board_summary"),
            ui.output_data_frame("board_table"),
        ]
        if m in ("scout", "researcher"):
            blocks.append(ui.output_ui("board_scatter"))
        return ui.div(*blocks)

    @render.ui
    def board_summary():
        df = board_view()
        if df.empty:
            return ui.div()
        season = int(input.board_season() or be.CURRENT_SEASON)
        matched = int(df["actual_pick"].notna().sum()) if "actual_pick" in df else 0
        total = be.college_class_size(season)
        tiles = [
            tile("Players shown", f"{len(df):,}"),
            tile("Median draft probability",
                 f"{df['draft_probability'].median():.0%}"),
        ]
        if matched:
            # Both halves of the trade, so widening the gate visibly buys
            # coverage at the cost of precision rather than looking free.
            tiles.append(tile("Actually drafted", f"{matched:,}",
                              f"{matched / len(df):.0%} of those shown"))
            if total:
                tiles.append(tile("Draft class covered",
                                  f"{matched / total:.0%}",
                                  f"of {total:,} college draftees"))
        return ui.div(*tiles, class_="tiles")

    @render.data_frame
    def board_table():
        df = board_view()
        if df.empty:
            team = input.board_team() or ""
            reason = (f"No {be.TEAM_CHOICES.get(team, team)} players made this "
                      "season's board." if team else "No players match.")
            return render.DataGrid(pd.DataFrame({"": [reason]}))
        m = mode()
        out = pd.DataFrame({
            "#": df["rank"],
            "Player": df["name"],
            "Team": df["team name"].fillna(df["team"]),
            "Role": df["role"],
        })
        out[V.t(m, "grade")] = df["draft_grade"]
        if m != "fan":
            out[V.t(m, "prob")] = (df["draft_probability"] * 100).round(1)
        if m in ("scout", "researcher"):
            out[V.t(m, "order")] = df["predicted_order"].map(
                lambda v: "Not projected" if pd.isna(v) else f"{v:,.1f}")
        out["Tier"] = df["tier"].astype(str)
        if "actual_college_order" in df:
            # Numeric, so the column sorts by draft position rather than
            # alphabetically. "Drafted" carries the undrafted state instead, so
            # an empty cell is never the only thing saying a player went
            # unpicked -- and undrafted rows group together at one end of any
            # sort rather than landing under "U".
            out["Actual college order"] = be.as_draft_position(
                df["actual_college_order"])
            if m in ("scout", "researcher"):
                out["Actual overall pick"] = be.as_draft_position(df["actual_pick"])
        return render.DataGrid(out, height="460px", filters=False)

    @render.ui
    def board_scatter():
        df = board_view()
        if df.empty or "actual_college_order" not in df:
            return ui.div()
        # A point needs both coordinates. Stage 2 only projects an order for
        # players it is asked about, so most of the wider board has none.
        drafted = df[df["actual_college_order"].notna()]
        pts = drafted[drafted["predicted_order"].notna()]
        if pts.empty:
            return ui.div(ui.p("No drafted players in view have a projected "
                               "order to compare against.", class_="blurb"))
        season = int(input.board_season() or be.CURRENT_SEASON)
        total = be.college_class_size(season)
        omitted = len(drafted) - len(pts)
        note = (f" {omitted} more were drafted but have no projected order, so "
                "they cannot be plotted." if omitted else "")

        projected_max = float(pts["predicted_order"].max())
        actual_max = float(pts["actual_college_order"].max())
        late = int((pts["actual_college_order"] > projected_max).sum())
        return ui.div(
            ui.h3("Projected order vs. actual college draft order"),
            ui.p(f"{len(pts):,} drafted players are plotted. Both axes count "
                 f"college players only — {total:,} of them in {season} — so a "
                 "point on the diagonal is a player the model placed exactly "
                 f"right. Below the diagonal went earlier than projected.{note}",
                 class_="blurb"),
            ui.HTML(_scatter_svg(pts)),
            # The blank upper range of the horizontal axis is a property of the
            # model, not of the rendering, so it is explained rather than
            # cropped away.
            ui.p(f"The upper right of the chart is empty because the model never "
                 f"projects anyone later than about {projected_max:.0f}, while "
                 f"players were actually taken as late as {actual_max:.0f}. The "
                 "order model minimises squared error, and nothing in a college "
                 "stat line reliably separates a 320th pick from a 440th, so it "
                 "settles toward the middle rather than guessing at the tail. "
                 f"The practical effect is a known bias: all {late} players "
                 f"taken later than {projected_max:.0f} were projected earlier "
                 "than they went.",
                 class_="note"),
            class_="chart-block",
        )

    # ---- player -------------------------------------------------------
    @reactive.calc
    def matches() -> pd.DataFrame:
        return be.search_players(input.player_query(),
                                 int(input.player_season() or be.CURRENT_SEASON))

    @render.ui
    def player_tab():
        m = mode()
        heading = "Look yourself up" if m == "player" else "Player lookup"
        return ui.div(
            ui.h2(heading),
            ui.p("Search 2021-2026 Division I players.", class_="blurb"),
            ui.div(
                ui.input_select("player_season", "Season",
                                {str(s): str(s) for s in be.SEASONS},
                                selected=str(be.CURRENT_SEASON)),
                ui.input_text("player_query", "Name",
                              placeholder="start typing a name"),
                class_="controls",
            ),
            ui.output_ui("player_picker"),
            ui.output_ui("player_card"),
        )

    @render.ui
    def player_picker():
        hits = matches()
        if not (input.player_query() or "").strip():
            return ui.div()
        if hits.empty:
            return ui.div(ui.p("No player by that name in this season.",
                               class_="blurb"))
        choices = {
            f"{row['name']}||{row['team']}":
                f"{row['name']} — {row['team name']} ({row['role']})"
            for _, row in hits.iterrows()
        }
        return ui.input_select("player_pick", "Matches", choices,
                               selected=next(iter(choices)))

    @render.ui
    def player_card():
        # Unset before the picker renders; SilentException blanks the card,
        # which is what should happen before a player is chosen.
        try:
            picked = input.player_pick()
        except SilentException:
            return ui.div()
        if not picked:
            return ui.div()
        name = picked.split("||")[0]
        season = int(input.player_season() or be.CURRENT_SEASON)
        m = mode()

        pred = be.prediction(name, season)
        if pred["probability"] is None:
            return ui.div(ui.p("The model has no row for that player-season.",
                               class_="blurb"))

        probability = pred["probability"]
        tiles = [tile(V.t(m, "prob"), f"{probability:.0%}")]
        if probability >= be.MIN_PROB_FOR_PICK_DETAIL and pred["order"]:
            low, high = _order_band(pred["order"])
            tiles.append(tile(V.t(m, "order"), f"{low}–{high}",
                              "a range, not a pick number"))
        if pred["eligible"] is not None:
            tiles.append(tile("Draft-eligible",
                              "Yes" if pred["eligible"] else "No",
                              str(pred["eligibility_basis"] or "")))

        blocks = [ui.h3(name), ui.div(*tiles, class_="tiles")]
        if probability < be.MIN_PROB_FOR_PICK_DETAIL:
            blocks.append(ui.p(
                "The model puts this player below the threshold where a "
                "projected pick means anything, so only the probability is "
                "shown.", class_="note"))
        text = be.report(name, season)
        if text and m != "fan":
            blocks.append(ui.h4(V.t(m, "explain")))
            blocks.append(ui.tags.pre(text, class_="report"))
        return ui.div(*blocks, class_="card")

    # ---- custom -------------------------------------------------------
    @render.ui
    def custom_tab():
        m = mode()
        return ui.div(
            ui.h2(V.t(m, "custom.title")),
            ui.p(V.t(m, "custom.blurb"), class_="blurb"),
            ui.div(
                ui.input_radio_buttons("c_role", "Role",
                                       {"pitcher": "Pitcher", "batter": "Batter"},
                                       selected="pitcher", inline=True),
                ui.input_numeric("c_age", "Age", 21, min=17, max=26),
                ui.input_select("c_team", "Team context",
                                {"": "League average"} | be.TEAM_CHOICES),
                ui.input_select("c_season", "Season context",
                                {str(s): str(s) for s in be.SEASONS},
                                selected=str(be.CURRENT_SEASON)),
                class_="controls",
            ),
            ui.output_ui("custom_fields"),
            ui.input_action_button("c_go", "Score this line", class_="go"),
            ui.output_ui("custom_result"),
        )

    @render.ui
    def custom_fields():
        fields = PITCHER_FIELDS if input.c_role() == "pitcher" else BATTER_FIELDS
        return ui.div(
            *[ui.input_numeric(f"c_{key}", label, value, min=0)
              for key, label, value in fields],
            class_="stat-grid",
        )

    @reactive.calc
    @reactive.event(input.c_go)
    def custom_result_data():
        role = input.c_role()
        fields = PITCHER_FIELDS if role == "pitcher" else BATTER_FIELDS
        stats = {}
        for key, _, _ in fields:
            # A field the user cleared, or one belonging to the other role, is
            # left out entirely rather than sent as a zero.
            try:
                value = input[f"c_{key}"]()
            except SilentException:
                continue
            if value is not None:
                stats[key] = float(value)
        return be.custom_prediction(
            role, float(input.c_age() or 21), stats,
            input.c_team() or None, int(input.c_season() or be.CURRENT_SEASON),
        )

    @render.ui
    def custom_result():
        try:
            result = custom_result_data()
        except Exception:
            return ui.div()
        if not result:
            return ui.div()
        m = mode()
        probability = result.get("draft_probability")
        tiles = [
            tile(V.t(m, "prob"), f"{probability:.0%}" if probability else "—"),
            tile(V.t(m, "grade"), grade_pill(result.get("draft_grade"))),
        ]
        order = result.get("predicted_order")
        if probability and probability >= be.MIN_PROB_FOR_PICK_DETAIL and order:
            low, high = _order_band(order)
            tiles.append(tile(V.t(m, "order"), f"{low}–{high}"))
        blocks = [ui.div(*tiles, class_="tiles")]

        supplied = result.get("supplied_features") or []
        confidence = result.get("confidence")
        if m in ("scout", "researcher"):
            blocks.append(ui.p(
                f"Supplied {len(supplied)} statistics. "
                f"Model confidence in this line: {confidence}.",
                class_="note"))
        elif confidence == "low":
            blocks.append(ui.p(
                "That's not many statistics to go on, so treat this as a rough "
                "read rather than a projection.", class_="note"))
        return ui.div(*blocks, class_="card")

    # ---- glossary -----------------------------------------------------
    @render.ui
    def glossary_tab():
        categories = {"all": "Everything"} | {
            name.lower(): name for name, _ in G.SECTIONS}
        return ui.div(
            ui.h2("Stat glossary"),
            ui.p("Every abbreviation the app uses, what it means, and where the "
                 "number comes from — whether it was counted at the game, "
                 "calculated from those counts, or produced by the model.",
                 class_="blurb"),
            ui.div(
                ui.input_select("gloss_cat", "Section", categories,
                                selected="all"),
                ui.input_text("gloss_query", "Search",
                              placeholder="e.g. OPS, strikeout, SHAP"),
                class_="controls",
            ),
            ui.output_ui("glossary_notes"),
            ui.output_ui("glossary_body"),
        )

    @render.ui
    def glossary_notes():
        # Only when browsing the whole thing; they are context, not answers to
        # a specific lookup.
        if (input.gloss_query() or "").strip() or (input.gloss_cat() or "all") != "all":
            return ui.div()
        return ui.div(
            *[ui.div(ui.h4(title), ui.p(body, class_="blurb"), class_="note-card")
              for title, body in G.NOTES],
            class_="note-grid",
        )

    @render.ui
    def glossary_body():
        query = (input.gloss_query() or "").strip().lower()
        chosen = input.gloss_cat() or "all"
        blocks, total = [], 0
        for name, entries in G.SECTIONS:
            if chosen != "all" and name.lower() != chosen:
                continue
            rows = [e for e in entries
                    if not query
                    or query in e[0].lower() or query in e[1].lower()
                    or query in e[2].lower()]
            if not rows:
                continue
            total += len(rows)
            blocks.append(ui.h3(name))
            blocks.append(ui.tags.table(
                ui.tags.thead(ui.tags.tr(
                    ui.tags.th("Term"), ui.tags.th("Name"),
                    ui.tags.th("Definition"), ui.tags.th("Source"))),
                ui.tags.tbody(*[
                    ui.tags.tr(
                        ui.tags.td(ui.tags.code(term), class_="gloss-term"),
                        ui.tags.td(full),
                        ui.tags.td(definition),
                        ui.tags.td(ui.span(source,
                                           class_=f"src src-{_slug(source)}")),
                    ) for term, full, definition, source in rows]),
                class_="gloss-table",
            ))
        if not blocks:
            return ui.div(ui.p(f"Nothing matches “{query}”.", class_="blurb"))
        return ui.div(ui.p(f"{total} entries.", class_="note"), *blocks)

    # ---- methods ------------------------------------------------------
    @render.ui
    def methods_tab():
        m = mode()
        if m == "player":
            return ui.div(
                ui.h2("How this works"),
                ui.p("The model learned from every Division I player-season "
                     "from 2021 to 2026 and who actually got drafted. It asks "
                     "two questions in order: how likely is this player to be "
                     "drafted at all, and if so, roughly how early?",
                     class_="blurb"),
                ui.p("It only sees box-score statistics and the strength of "
                     "the program around you. It has never seen you play.",
                     class_="blurb"),
                class_="card",
            )
        card = be.model_card()
        lineage = card.get("lineage", {})
        reference = card.get("reference_implementation", {})
        return ui.div(
            ui.h2("Model card"),
            ui.div(
                tile("Model version", card.get("model_version", "—")),
                tile("Trained on", ", ".join(str(y) for y in
                                             card.get("train_years", []))),
                tile("Held-out season", str(card.get("test_year", "—"))),
                class_="tiles",
            ),
            ui.div(
                ui.h4(f"Derived from {reference.get('name', 'the research model')}"),
                ui.p(reference.get("note", ""), class_="blurb"),
                ui.h4("What differs"),
                ui.tags.ul(*[ui.tags.li(d)
                             for d in lineage.get("differences", [])]),
                class_="note-card",
            ),
            ui.h3("Full card"),
            ui.tags.pre(_format_card(card), class_="report"),
            class_="card",
        )


# --- helpers ----------------------------------------------------------------

def _order_band(order: float) -> tuple[int, int]:
    """A band around a Stage 2 point estimate.

    The regression output is continuous and can even go negative; presenting it
    as a pick number implies a precision the model does not have.
    """
    order = max(float(order), 1.0)
    width = max(8.0, order * 0.25)
    return max(1, int(order - width)), int(order + width)


def _format_card(card: dict) -> str:
    lines = []
    for key, value in card.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k2, v2 in value.items():
                lines.append(f"    {k2}: {v2}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _slug(text: str) -> str:
    """CSS-safe class suffix for a source label."""
    return text.lower().replace(" ", "-")


def _sorted_by_draft_order(df: pd.DataFrame, how: str) -> pd.DataFrame:
    """Order the board by actual college draft order.

    Sorted here rather than by clicking the column header, because the column
    reads "Undrafted" rather than sitting empty -- and a header sort would put
    that string among the U's instead of at the end. Where undrafted players
    land is a choice, so it is offered as one.
    """
    if how == "off" or "actual_college_order" not in df:
        return df
    if how == "undrafted":
        # Undrafted first, then the drafted in order.
        return df.sort_values("actual_college_order", ascending=True,
                              na_position="first", kind="stable")
    return df.sort_values("actual_college_order", ascending=(how == "low"),
                          na_position="last", kind="stable")


def _esc(text) -> str:
    """Escape for SVG text. Names carry apostrophes and ampersands."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _delta(projected: float, actual: float) -> str:
    """Which way the model was wrong, in plain words."""
    if pd.isna(projected) or pd.isna(actual):
        return "No projected order for this player"
    gap = round(actual - projected)
    if gap == 0:
        return "Exactly as projected"
    spots = "spot" if abs(gap) == 1 else "spots"
    direction = "earlier" if gap < 0 else "later"
    return f"Went {abs(gap)} {spots} {direction} than projected"


def _scatter_svg(points: pd.DataFrame) -> str:
    """Predicted order against actual pick, as a single-series scatter."""
    width, height, pad = 680, 380, 44
    xs = points["predicted_order"].astype(float)
    ys = points["actual_college_order"].astype(float)
    hi = max(xs.max(), ys.max()) * 1.05 or 1.0

    def sx(v):
        return pad + (v / hi) * (width - pad - 12)

    def sy(v):
        return height - pad - (v / hi) * (height - pad - 12)

    ticks = [t for t in (0, 100, 200, 300, 400, 500, 600) if t <= hi]
    grid = "".join(
        f'<line x1="{sx(t):.1f}" y1="{sy(0):.1f}" x2="{sx(t):.1f}" y2="{sy(hi):.1f}" '
        f'class="grid"/>'
        f'<line x1="{sx(0):.1f}" y1="{sy(t):.1f}" x2="{sx(hi):.1f}" y2="{sy(t):.1f}" '
        f'class="grid"/>' for t in ticks)
    xlabels = "".join(
        f'<text x="{sx(t):.1f}" y="{height - pad + 18:.1f}" class="tick" '
        f'text-anchor="middle">{t}</text>' for t in ticks)
    ylabels = "".join(
        f'<text x="{pad - 8:.1f}" y="{sy(t) + 4:.1f}" class="tick" '
        f'text-anchor="end">{t}</text>' for t in ticks)
    teams = points["team name"].fillna(points["team"])
    marks = "".join(
        f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="4.5" class="mark">'
        f'<title>{_esc(n)} — {_esc(t)}\n'
        f'Projected college order: {x:.0f}\n'
        f'Actual college order: {y:.0f}\n'
        f'{_delta(x, y)}</title></circle>'
        for x, y, n, t in zip(xs, ys, points["name"], teams))

    return f"""
<svg viewBox="0 0 {width} {height}" class="scatter" role="img"
     aria-label="Projected draft order against actual pick">
  {grid}
  <line x1="{sx(0):.1f}" y1="{sy(0):.1f}" x2="{sx(hi):.1f}" y2="{sy(hi):.1f}"
        class="diagonal"/>
  {marks}
  {xlabels}{ylabels}
  <text x="{width / 2:.0f}" y="{height - 6}" class="axis" text-anchor="middle">
    Projected college draft order</text>
  <text x="14" y="{height / 2:.0f}" class="axis" text-anchor="middle"
        transform="rotate(-90 14 {height / 2:.0f})">Actual college draft order</text>
</svg>"""


app = App(app_ui, server, static_assets=None)
