"""Definitions for every statistic and model term the app puts on screen.

Each entry is (term, full name, definition, source). ``source`` says where a
number comes from, which matters more here than usual: some are recorded by the
NCAA, some are arithmetic this package does on read, and some are the model's
own output. Conflating the three is how a projection gets mistaken for a fact.
"""

RECORDED = "Recorded"      # counted at the game, stored as-is
COMPUTED = "Computed"      # arithmetic on recorded numbers, derived on read
COLLEGE = "College-calibrated"  # package-original, fitted to NCAA play
MODEL = "Model output"     # produced by the predictor, not observed

BATTING = [
    ("G", "Games", "Games in which the player appeared.", RECORDED),
    ("PA", "Plate appearances", "Every trip to the plate, including walks, "
     "hit-by-pitches and sacrifices.", RECORDED),
    ("AB", "At-bats", "Plate appearances excluding walks, hit-by-pitches, "
     "sacrifices and catcher's interference.", RECORDED),
    ("H", "Hits", "Times the batter reached base on a batted ball without an "
     "error or fielder's choice.", RECORDED),
    ("1B", "Singles", "Hits on which the batter reached first base. Derived as "
     "H − 2B − 3B − HR.", COMPUTED),
    ("2B", "Doubles", "Hits on which the batter reached second base.", RECORDED),
    ("3B", "Triples", "Hits on which the batter reached third base.", RECORDED),
    ("HR", "Home runs", "Hits on which the batter scored on the same play.",
     RECORDED),
    ("TB", "Total bases", "1B + 2×2B + 3×3B + 4×HR.", COMPUTED),
    ("R", "Runs", "Times the player scored.", RECORDED),
    ("RBI", "Runs batted in", "Runs that scored as a result of the batter's "
     "plate appearance.", RECORDED),
    ("BB", "Walks", "Bases on balls.", RECORDED),
    ("SO", "Strikeouts", "Times the batter struck out.", RECORDED),
    ("HBP", "Hit by pitch", "Times the batter was awarded first base after "
     "being struck by a pitch.", RECORDED),
    ("SF", "Sacrifice flies", "Fly outs that scored a runner.", RECORDED),
    ("SH", "Sacrifice hits", "Bunts that advanced a runner at the cost of an "
     "out.", RECORDED),
    ("GDP", "Grounded into double play", "Ground balls that produced two outs.",
     RECORDED),
    ("SB", "Stolen bases", "Bases taken without the aid of a hit or error.",
     RECORDED),
    ("CS", "Caught stealing", "Failed stolen-base attempts.", RECORDED),
    ("AVG", "Batting average", "H / AB. The oldest rate statistic, and the "
     "least informative: it treats a home run and a single as the same event "
     "and ignores walks entirely.", COMPUTED),
    ("OBP", "On-base percentage", "(H + BB + HBP) / (AB + BB + HBP + SF). How "
     "often the batter avoids making an out.", COMPUTED),
    ("SLG", "Slugging percentage", "TB / AB. Average bases per at-bat, so it "
     "measures power rather than frequency.", COMPUTED),
    ("OPS", "On-base plus slugging", "OBP + SLG. Crude — it adds two numbers "
     "with different denominators — but a good quick read.", COMPUTED),
    ("ISO", "Isolated power", "SLG − AVG. Extra bases per at-bat, stripping "
     "out singles.", COMPUTED),
    ("BB%", "Walk rate", "BB / PA.", COMPUTED),
    ("K%", "Strikeout rate", "SO / PA.", COMPUTED),
    ("BB/K", "Walk-to-strikeout ratio", "BB / SO. A plate-discipline read.",
     COMPUTED),
    ("BABIP", "Batting average on balls in play", "(H − HR) / (AB − SO − HR + "
     "SF). Often reverts toward the mean, so an extreme value can flag luck "
     "rather than skill.", COMPUTED),
    ("cwOBA", "College weighted on-base average", "On-base ability with each "
     "outcome weighted by the runs it actually produces, using run values "
     "fitted to NCAA play. Scaled like OBP.", COLLEGE),
    ("cwRAA", "College weighted runs above average", "Runs contributed above "
     "what an average hitter would produce in the same number of plate "
     "appearances.", COLLEGE),
    ("cwRC", "College weighted runs created", "Total runs the batter's offence "
     "is worth.", COLLEGE),
    ("cwRC+", "College weighted runs created plus", "cwRC indexed so 100 is "
     "league average and every 1 point above is 1% better. 150 means half "
     "again as productive as an average hitter that season.", COLLEGE),
    ("cwSB", "College weighted stolen-base runs", "Runs added or lost by "
     "base-stealing, netting steals against times caught.", COLLEGE),
    ("cSpd", "College speed score", "A speed estimate built from stolen-base "
     "attempts and success rate, triples and runs scored.", COLLEGE),
]

PITCHING = [
    ("W", "Wins", "Credited by the official scorer; depends heavily on run "
     "support, so it says little about the pitcher.", RECORDED),
    ("L", "Losses", "See wins.", RECORDED),
    ("G", "Games", "Appearances.", RECORDED),
    ("GS", "Games started", "Appearances as the starting pitcher.", RECORDED),
    ("CG", "Complete games", "Starts the pitcher finished.", RECORDED),
    ("ShO", "Shutouts", "Complete games allowing no runs.", RECORDED),
    ("SV", "Saves", "Games finished under the save rules.", RECORDED),
    ("IP", "Innings pitched", "Innings, in NCAA notation — see the note above "
     "the table, because this one is not a decimal.", RECORDED),
    ("TBF", "Total batters faced", "The pitcher's equivalent of plate "
     "appearances, and the correct denominator for rate statistics.", RECORDED),
    ("H", "Hits allowed", "Hits surrendered.", RECORDED),
    ("R", "Runs allowed", "All runs, earned or not.", RECORDED),
    ("ER", "Earned runs", "Runs that scored without the aid of an error.",
     RECORDED),
    ("HR", "Home runs allowed", "Home runs surrendered.", RECORDED),
    ("BB", "Walks allowed", "Bases on balls issued.", RECORDED),
    ("HBP", "Hit batters", "Batters struck by a pitch.", RECORDED),
    ("WP", "Wild pitches", "Pitches too errant for the catcher to handle, "
     "allowing a runner to advance.", RECORDED),
    ("BK", "Balks", "Illegal motions with runners on base.", RECORDED),
    ("SO", "Strikeouts", "Batters struck out.", RECORDED),
    ("ERA", "Earned run average", "9 × ER / IP. Earned runs per nine innings.",
     COMPUTED),
    ("WHIP", "Walks and hits per inning pitched", "(BB + H) / IP. How many "
     "runners the pitcher puts on.", COMPUTED),
    ("K/9", "Strikeouts per nine", "9 × SO / IP.", COMPUTED),
    ("BB/9", "Walks per nine", "9 × BB / IP.", COMPUTED),
    ("HR/9", "Home runs per nine", "9 × HR / IP.", COMPUTED),
    ("K/BB", "Strikeout-to-walk ratio", "SO / BB.", COMPUTED),
    ("K%", "Strikeout rate", "SO / TBF. Better than K/9, because it is not "
     "distorted by how many balls in play become outs.", COMPUTED),
    ("BB%", "Walk rate", "BB / TBF.", COMPUTED),
    ("K-BB%", "Strikeout minus walk rate", "K% − BB%. One of the most "
     "predictive single numbers for a pitcher.", COMPUTED),
    ("BABIP", "Batting average on balls in play", "(H − HR) / (TBF − SO − HR − "
     "BB − HBP). Largely outside a pitcher's control.", COMPUTED),
    ("cFIP", "College fielding independent pitching", "What the pitcher's ERA "
     "would be if only strikeouts, walks, hit batters and home runs counted — "
     "the outcomes that do not depend on the fielders behind him. Scaled to "
     "look like ERA.", COLLEGE),
    ("cLOB%", "College left-on-base percentage", "The share of baserunners the "
     "pitcher stranded.", COLLEGE),
    ("E-cF", "ERA minus cFIP", "The gap between results and the fielding-"
     "independent estimate. Strongly positive suggests bad luck or bad "
     "defence; strongly negative suggests the reverse.", COMPUTED),
]

TEAM = [
    ("RPI", "Ratings percentage index", "The NCAA's strength rating, built "
     "from winning percentage and the quality of opponents.", RECORDED),
    ("SOS", "Strength of schedule", "How difficult the team's opponents were.",
     RECORDED),
    ("Q1–Q4", "Quadrant records", "Win-loss records split by opponent quality, "
     "Q1 being the toughest games.", RECORDED),
    ("(team)", "Team-context feature", "A suffix in the scouting report. The "
     "number describes the player's team or programme that season, not the "
     "player. \"HBP (team)\" is how many batters the whole pitching staff hit.",
     RECORDED),
    ("Conference", "Conference", "The league the school plays in. Enters the "
     "model only through the numbers attached to it, never as a name.",
     RECORDED),
]

MODEL_TERMS = [
    ("Draft probability", "Stage 1 output", "The model's estimated chance the "
     "player is drafted at all. It is a population rate, not a promise: of a "
     "hundred players at 70%, roughly seventy are drafted.", MODEL),
    ("Draft grade", "Letter grade", "The draft probability expressed as a "
     "letter, graded against the distribution of every player the model was "
     "trained on.", MODEL),
    ("Projected college draft order", "Stage 2 output", "Where the model "
     "expects the player to come off the board *among college players only*. "
     "High schoolers are not counted.", MODEL),
    ("Actual college order", "Observed", "Where the player actually came off "
     "the board among college players — the like-for-like comparison to the "
     "projection.", RECORDED),
    ("Actual overall pick", "Observed", "The real MLB pick number, counting "
     "high school selections. Always a larger number than college order.",
     RECORDED),
    ("Tier", "Board grouping", "Early, Middle or Late, from the player's "
     "position on the board.", MODEL),
    ("Draft-eligible", "Eligibility", "Whether the player may be drafted this "
     "year: three completed college seasons, or age 21 by the draft. "
     "\"Basis\" says which of the two qualified them.", RECORDED),
    ("Impact", "SHAP contribution", "How much one statistic moved this "
     "player's draft probability, in percentage points. Positive pushed the "
     "projection up, negative pulled it down. The contributions are specific "
     "to this player, not a global ranking of what matters.", MODEL),
    ("Value / median", "Comparison", "The player's number beside the median "
     "for the population the model trained on, so the impact figure can be "
     "read in context.", MODEL),
    ("Confidence", "Input completeness", "On a custom stat line, how much of "
     "the model's input was actually supplied. Low means most fields were "
     "left missing.", MODEL),
]

SECTIONS = [
    ("Batting", BATTING),
    ("Pitching", PITCHING),
    ("Team context", TEAM),
    ("Model terms", MODEL_TERMS),
]

# Things that surprise people, and that a definition list alone will not fix.
NOTES = [
    ("Innings pitched are not a decimal",
     "NCAA innings are written with outs after the point: 97.1 means 97 "
     "innings and one out, 97.2 means two outs. There is no 97.3. Reading it "
     "as 97.1 innings understates the outs recorded and inflates every rate "
     "built on it, so this app converts to true innings (97⅓) before "
     "calculating ERA, WHIP and the per-nine rates."),
    ("Why some statistics start with a small c",
     "cwOBA, cwRC+, cFIP, cLOB%, cwRAA, cwRC, cwSB and cSpd are calculated by "
     "this project using run values fitted to NCAA play, not taken from a "
     "commercial provider. They are built the same way as the familiar "
     "versions but with college league constants, so they are not "
     "interchangeable with a same-named number quoted elsewhere. The leading "
     "c is there so the two are never confused."),
    ("Rate statistics are recomputed, not stored",
     "Only counting statistics are stored. Every rate — AVG, ERA, K%, WHIP and "
     "the rest — is recalculated from those counts when the data loads. "
     "Storing a rate beside the numbers it comes from is how the two quietly "
     "drift apart."),
    ("A blank is not a zero",
     "Where a statistic is missing the model is told it is missing, rather "
     "than being given a zero or a league average. A pitcher has no batting "
     "line, and inventing one changes what the model sees."),
]
