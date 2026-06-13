"""Live data from ESPN's free, key-less World Cup feed: scores, exact kickoff
times and TV networks. No API key required. Manual edits (match.manual=True) are
never overwritten for scores/status — but kickoff time and TV network are always
refreshed from ESPN since those are schedule facts, not results."""
import datetime, httpx
import seed_data
from models import Match

SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

# ESPN season slug -> our round code
ROUND = {"group-stage": "group", "round-of-32": "R32", "round-of-16": "R16",
         "quarterfinals": "QF", "semifinals": "SF", "third-place": "3rd", "final": "Final"}
# ESPN display name -> our canonical name
NAME = {"Bosnia-Herzegovina": "Bosnia & Herzegovina", "Congo DR": "DR Congo",
        "Curaçao": "Curacao", "Türkiye": "Turkiye"}
# tidy ESPN's short broadcaster labels into readable network names
NET = {"Tele": "Telemundo", "Uni": "Universo"}

TEAMS = set(t for g in seed_data.GROUPS.values() for t in g)


def _n(name):
    return NAME.get(name, name) if name else name


def _date_range():
    """YYYYMMDD-YYYYMMDD spanning the whole tournament, derived from the seed."""
    ds = [d for d, _, _, _ in seed_data.GROUP_FIXTURES] + [d for d, _ in seed_data.KO_SKELETON]
    return min(ds).replace("-", "") + "-" + max(ds).replace("-", "")


def _parse_dt(s):
    if not s:
        return None
    try:
        dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def _networks(comp):
    """Readable TV network string, e.g. 'FOX · Telemundo'. Prefers TV (not
    streaming) entries; falls back to the generic broadcasts list."""
    tv = []
    for gb in comp.get("geoBroadcasts", []) or []:
        if (gb.get("type") or {}).get("shortName") == "TV":
            nm = (gb.get("media") or {}).get("shortName")
            if nm:
                tv.append(NET.get(nm, nm))
    if not tv:
        for b in comp.get("broadcasts", []) or []:
            for nm in b.get("names", []):
                tv.append(NET.get(nm, nm))
    seen, out = set(), []
    for n in tv:
        if n not in seen:
            seen.add(n); out.append(n)
    return " · ".join(out) if out else None


def _score(competitor):
    try:
        return int(competitor.get("score"))
    except (TypeError, ValueError):
        return None


def sync(db):
    try:
        r = httpx.get(SCOREBOARD, params={"dates": _date_range()}, timeout=20)
        r.raise_for_status()
        events = r.json().get("events", [])
    except Exception as e:
        return {"ok": False, "msg": f"ESPN error: {e}"}

    updated = 0
    nets = 0
    ko_pending = {}   # round -> [(kickoff, network)] for not-yet-resolved bracket slots

    for e in events:
        rnd = ROUND.get((e.get("season") or {}).get("slug"))
        if not rnd:
            continue
        comp = (e.get("competitions") or [{}])[0]
        kdt = _parse_dt(e.get("date"))
        state = ((comp.get("status") or {}).get("type") or {}).get("state")
        status = {"pre": "SCHEDULED", "in": "LIVE", "post": "FINISHED"}.get(state, "SCHEDULED")
        net = _networks(comp)
        cs = comp.get("competitors", [])
        home = next((c for c in cs if c.get("homeAway") == "home"), None)
        away = next((c for c in cs if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        a = _n((home.get("team") or {}).get("displayName"))
        b = _n((away.get("team") or {}).get("displayName"))

        if a in TEAMS and b in TEAMS:
            # resolved match (group, or a knockout whose teams are known): match by team set
            row = None
            for cand in db.query(Match).filter(Match.round == rnd).all():
                if cand.team_a and {cand.team_a, cand.team_b} == {a, b}:
                    row = cand; break
            if row is None:
                for cand in db.query(Match).all():
                    if cand.team_a and {cand.team_a, cand.team_b} == {a, b}:
                        row = cand; break
            if row is None:
                continue
            if kdt:
                row.kickoff = kdt                 # schedule fact — always refresh
            if net:
                row.network = net; nets += 1       # schedule fact — always refresh
            if not row.manual:                     # results never clobber manual entry
                if state in ("in", "post"):
                    sa, sb = _score(home), _score(away)
                    if sa is not None:
                        row.score_a = sa
                    if sb is not None:
                        row.score_b = sb
                row.status = status
                if rnd != "group" and status == "FINISHED":
                    w = home if home.get("winner") else (away if away.get("winner") else None)
                    if w:
                        row.winner = _n((w.get("team") or {}).get("displayName"))
            updated += 1
        else:
            # unresolved knockout slot (e.g. "Group A Winner") — keep its date + TV
            ko_pending.setdefault(rnd, []).append((kdt, net))

    # fill empty knockout skeleton rows with kickoff + TV, matched by round then date order
    for rnd, items in ko_pending.items():
        items = sorted([x for x in items if x[0]], key=lambda x: x[0])
        rows = [m for m in db.query(Match).filter(Match.round == rnd).all()
                if not m.team_a and not m.manual]
        rows.sort(key=lambda m: (m.kickoff or datetime.datetime.max, m.id))
        for (kdt, net), row in zip(items, rows):
            if kdt:
                row.kickoff = kdt
            if net:
                row.network = net; nets += 1

    db.commit()
    return {"ok": True, "updated": updated, "networks": nets}
