"""Best-effort sync from football-data.org (free tier). Manual edits (match.manual=True)
are never overwritten. Set FOOTBALL_API_KEY in the environment to enable."""
import os, datetime, httpx
from models import Match

BASE = "https://api.football-data.org/v4/competitions/WC/matches"
STAGE = {"GROUP_STAGE":"group","ROUND_OF_32":"R32","LAST_32":"R32","ROUND_OF_16":"R16",
         "LAST_16":"R16","QUARTER_FINALS":"QF","QUARTER_FINAL":"QF","SEMI_FINALS":"SF",
         "SEMI_FINAL":"SF","THIRD_PLACE":"3rd","3RD_PLACE":"3rd","FINAL":"Final"}
# football-data name -> our canonical name
NAME = {"Turkey":"Turkiye","Türkiye":"Turkiye","Korea Republic":"South Korea","South Korea":"South Korea",
        "USA":"United States","United States":"United States","Côte d'Ivoire":"Ivory Coast","Ivory Coast":"Ivory Coast",
        "Curaçao":"Curacao","Cape Verde Islands":"Cape Verde","Bosnia and Herzegovina":"Bosnia & Herzegovina",
        "Czech Republic":"Czechia","Czechia":"Czechia","DR Congo":"DR Congo","Congo DR":"DR Congo"}

def _n(name):
    return NAME.get(name, name) if name else name

def sync(db):
    key = os.environ.get("FOOTBALL_API_KEY")
    if not key:
        return {"ok": False, "msg": "FOOTBALL_API_KEY not set; use manual entry."}
    try:
        r = httpx.get(BASE, headers={"X-Auth-Token": key}, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"ok": False, "msg": f"API error: {e}"}
    updated = created = 0
    for m in data.get("matches", []):
        rnd = STAGE.get(m.get("stage"), None)
        if rnd is None:
            continue
        a = _n((m.get("homeTeam") or {}).get("name"))
        b = _n((m.get("awayTeam") or {}).get("name"))
        sc = m.get("score", {}).get("fullTime", {})
        sa, sb = sc.get("home"), sc.get("away")
        st = {"FINISHED":"FINISHED","IN_PLAY":"LIVE","PAUSED":"LIVE"}.get(m.get("status"), "SCHEDULED")
        ko = m.get("utcDate")
        kdt = None
        if ko:
            try:
                kdt = datetime.datetime.fromisoformat(ko.replace("Z","+00:00"))
                kdt = kdt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            except Exception: pass
        ext = str(m.get("id"))
        row = db.query(Match).filter(Match.ext_id == ext).first()
        if row is None and a and b:
            # try to match a seeded fixture by round + team set
            q = db.query(Match).filter(Match.round == rnd)
            for cand in q.all():
                if cand.team_a and {cand.team_a, cand.team_b} == {a, b}:
                    row = cand; break
            if row is None:  # fill an empty placeholder of this round
                row = db.query(Match).filter(Match.round==rnd, Match.team_a.is_(None)).first()
        if row is None:
            row = Match(round=rnd); db.add(row); created += 1
        else:
            updated += 1
        if row.manual:      # never clobber manual edits
            continue
        row.ext_id = ext
        if a: row.team_a = a
        if b: row.team_b = b
        row.score_a, row.score_b, row.status = sa, sb, st
        if kdt: row.kickoff = kdt
        if rnd != "group" and st == "FINISHED" and sa is not None and sb is not None and sa != sb:
            row.winner = a if sa > sb else b
    db.commit()
    return {"ok": True, "updated": updated, "created": created}
