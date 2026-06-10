"""
Scoring engine for the World Cup pool  — FLAT, NO GOALS.

Rules (the single source of truth for points):
  GROUP STAGE   Win = 3, Draw = 1, Loss = 0   (goals are ignored)
  KNOCKOUT      +4 for EACH round a team reaches, cumulative:
                  reach Round of 32 (qualify from group) +4
                  reach Round of 16                       +4
                  reach Quarter-final                     +4
                  reach Semi-final                        +4
                  reach Final                             +4
                  win the Final (Champion)                +4
  The 3rd-place playoff scores nothing (reaching the semis already paid).

A team "reaches" a knockout round when it appears as a participant in a match of
that round — so points accrue automatically as the bracket fills in. Champion is
the winner of the Final. A player's score = sum of their drafted teams' points.

These functions are pure (operate on plain dicts) so they are trivially testable
and independent of the database or web layer.
"""
from collections import defaultdict

GROUP_WIN, GROUP_DRAW, GROUP_LOSS = 3, 1, 0
ROUND_BONUS = 4
KO_ROUNDS = ["R32", "R16", "QF", "SF", "Final"]   # rounds that grant the reach bonus
ROUND_LABEL = {"R32": "Reached Round of 32", "R16": "Reached Round of 16",
               "QF": "Reached Quarter-final", "SF": "Reached Semi-final",
               "Final": "Reached Final"}


def _finished(m):
    return m.get("status") == "FINISHED" and m.get("score_a") is not None and m.get("score_b") is not None


def _winner(m):
    """Winner of a knockout match: explicit `winner` (e.g. penalties) wins, else higher score."""
    if m.get("winner"):
        return m["winner"]
    if not _finished(m):
        return None
    if m["score_a"] > m["score_b"]:
        return m["team_a"]
    if m["score_b"] > m["score_a"]:
        return m["team_b"]
    return None


def compute_team_scores(matches):
    """matches: list of dicts with round, team_a, team_b, score_a, score_b, status, winner.
    round in {'group','R32','R16','QF','SF','Final','3rd'}.
    Returns {team_name: {...points + breakdown...}}."""
    teams = {}

    def t(name):
        if name not in teams:
            teams[name] = dict(team=name, gw=0, gd=0, gl=0, group_points=0,
                               reached=[], champion=False, ko_points=0, total=0, breakdown=[])
        return teams[name]

    # --- group stage: tally W/D/L from finished group matches ---
    for m in matches:
        if m.get("round") != "group":
            continue
        a, b = m.get("team_a"), m.get("team_b")
        if not a or not b or not _finished(m):
            continue
        ta, tb = t(a), t(b)
        sa, sb = m["score_a"], m["score_b"]
        if sa > sb:
            ta["gw"] += 1; tb["gl"] += 1
        elif sb > sa:
            tb["gw"] += 1; ta["gl"] += 1
        else:
            ta["gd"] += 1; tb["gd"] += 1

    # --- knockout: a team reaches a round if it appears in a match of that round ---
    reached = defaultdict(set)
    for m in matches:
        r = m.get("round")
        if r in KO_ROUNDS:
            for name in (m.get("team_a"), m.get("team_b")):
                if name:
                    reached[name].add(r); t(name)
        if r == "Final" and _finished(m):
            w = _winner(m)
            if w:
                t(w)["champion"] = True

    # --- assemble points + UI breakdown ---
    for name, st in teams.items():
        st["group_points"] = st["gw"] * GROUP_WIN + st["gd"] * GROUP_DRAW + st["gl"] * GROUP_LOSS
        st["reached"] = [r for r in KO_ROUNDS if r in reached.get(name, set())]
        st["ko_points"] = ROUND_BONUS * len(st["reached"]) + (ROUND_BONUS if st["champion"] else 0)
        st["total"] = st["group_points"] + st["ko_points"]
        bd = []
        if st["gw"] or st["gd"] or st["gl"]:
            bd.append(dict(label=f"Group stage: {st['gw']}W {st['gd']}D {st['gl']}L", points=st["group_points"]))
        for r in st["reached"]:
            bd.append(dict(label=ROUND_LABEL[r], points=ROUND_BONUS))
        if st["champion"]:
            bd.append(dict(label="Champion", points=ROUND_BONUS))
        st["breakdown"] = bd
    return teams


def compute_standings(players, team_scores):
    """players: list of {id, name, teams:[country,...]}. Returns ranked standings with breakdowns."""
    rows = []
    for p in players:
        items, total = [], 0
        for tm in p["teams"]:
            ts = team_scores.get(tm)
            pts = ts["total"] if ts else 0
            total += pts
            items.append(dict(team=tm, points=pts,
                              breakdown=ts["breakdown"] if ts else [],
                              eliminated=_is_elim(ts) if ts else False))
        items.sort(key=lambda x: -x["points"])
        rows.append(dict(id=p["id"], name=p["name"], total=total, teams=items))
    rows.sort(key=lambda x: -x["total"])
    rank = 0
    last = None
    for i, r in enumerate(rows):
        if r["total"] != last:
            rank = i + 1; last = r["total"]
        r["rank"] = rank
    return rows


def _is_elim(ts):
    return False  # placeholder; elimination is derived in the API layer from match data
