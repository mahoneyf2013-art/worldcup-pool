import os, datetime
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
import models
from models import Player, Pick, Match
import scoring, seed_data, football_api, espn_api

Base.metadata.create_all(bind=engine)

def _migrate():
    """Add columns introduced after the first deploy. create_all() won't alter an
    existing table, so add them by hand (idempotent: ignores 'already exists')."""
    from sqlalchemy import text
    for stmt in ("ALTER TABLE matches ADD COLUMN network VARCHAR",
                 "ALTER TABLE matches ADD COLUMN slot_a VARCHAR",
                 "ALTER TABLE matches ADD COLUMN slot_b VARCHAR"):
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception:
            pass
_migrate()

app = FastAPI(title="World Cup Pool")
ADMIN_KEY = os.environ.get("ADMIN_KEY")          # optional; if set, writes require it
KO_ORDER = {"group":0,"R32":1,"R16":2,"QF":3,"SF":4,"3rd":5,"Final":6}

def require_admin(x_admin_key: str = Header(default=None)):
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(401, "Admin key required")

def seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(Match).count() == 0:
            for d, g, a, b in seed_data.GROUP_FIXTURES:
                db.add(Match(round="group", grp=g, team_a=a, team_b=b,
                             kickoff=datetime.datetime.fromisoformat(d+"T12:00:00")))
            for d, r in seed_data.KO_SKELETON:
                db.add(Match(round=r, kickoff=datetime.datetime.fromisoformat(d+"T12:00:00")))
            db.commit()
    finally:
        db.close()
seed_if_empty()

def _repair_matches():
    """One-time cleanup. An earlier second sync source (football-data) created
    duplicate fixtures. The canonical set is exactly the 72 group fixtures + the
    32 knockout slots; trim anything beyond that, keeping the real rows."""
    import collections
    db = SessionLocal()
    try:
        # genuine group rows always carry a group letter; null-grp rows are strays
        db.query(Match).filter(Match.round == "group", Match.grp.is_(None)).delete(synchronize_session=False)
        want = collections.Counter(r for _, r in seed_data.KO_SKELETON)   # {R32:16, R16:8, ...}
        for rnd, n in want.items():
            rows = db.query(Match).filter(Match.round == rnd).all()
            if len(rows) > n:
                # keep the n most "real": manual edits > has teams > has TV > earliest id
                ranked = sorted(rows, key=lambda m: (bool(m.manual), bool(m.team_a), bool(m.network), -m.id), reverse=True)
                keep = {m.id for m in ranked[:n]}
                for m in rows:
                    if m.id not in keep:
                        db.delete(m)
        db.commit()
    finally:
        db.close()
_repair_matches()

# ---------- official knockout bracket: derive matchups from results ----------
# match id -> (feeder a, feeder b). IDs are FIFA match numbers (73-104), matching our rows.
KO_FEEDERS = {89:(74,77),90:(73,75),91:(76,78),92:(79,80),93:(83,84),94:(81,82),95:(86,88),96:(85,87),
              97:(89,90),98:(93,94),99:(91,92),100:(95,96),101:(97,98),102:(99,100),104:(101,102)}
KO_THIRD = (101,102)   # match 103 (3rd place) = the two semifinal losers

def _mwinner(m):
    if not m: return None
    if m.winner: return m.winner
    if m.status == "FINISHED" and m.score_a is not None and m.score_b is not None:
        if m.score_a > m.score_b: return m.team_a
        if m.score_b > m.score_a: return m.team_b
    return None

def _mloser(m):
    w = _mwinner(m)
    if not w or not m.team_a or not m.team_b: return None
    return m.team_b if w == m.team_a else m.team_a

def propagate_bracket(db):
    """Fill knockout matchups (R16 -> Final, plus 3rd place) from the official bracket tree
    and the winners so far, so Schedule/Bracket/scoring all agree. R32 rows are left as seeded.
    Manual edits (match.manual) are never overwritten."""
    ms = {m.id: m for m in db.query(Match).all()}
    changed = False
    for mid in (89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104):
        m = ms.get(mid)
        if not m or m.manual: continue
        if mid == 103:
            fa, fb = KO_THIRD; a, b = _mloser(ms.get(fa)), _mloser(ms.get(fb)); lbl = "Loser"
        else:
            fa, fb = KO_FEEDERS[mid]; a, b = _mwinner(ms.get(fa)), _mwinner(ms.get(fb)); lbl = "Winner"
        sa = None if a else f"{lbl} Match {fa}"
        sb = None if b else f"{lbl} Match {fb}"
        if (m.team_a, m.team_b, m.slot_a, m.slot_b) != (a, b, sa, sb):
            m.team_a, m.team_b, m.slot_a, m.slot_b = a, b, sa, sb
            changed = True
    if changed: db.commit()

def _startup_propagate():
    db = SessionLocal()
    try: propagate_bracket(db)
    finally: db.close()
_startup_propagate()

def _matches(db):
    return [dict(id=m.id, round=m.round, grp=m.grp, team_a=m.team_a, team_b=m.team_b,
                 score_a=m.score_a, score_b=m.score_b, winner=m.winner, status=m.status,
                 network=m.network,
                 kickoff=m.kickoff.isoformat() if m.kickoff else None) for m in db.query(Match).all()]

def _owners(db):
    """Map of team name -> player who drafted it."""
    owner = {}
    for p in db.query(Player).all():
        for pk in p.picks:
            owner[pk.team] = p.name
    return owner

def _team_scores(db):
    return scoring.compute_team_scores(_matches(db))

def _team_status(team, matches, ts):
    """Display status: Champion / Out / next round."""
    if ts.get(team, {}).get("champion"): return "Champion"
    future=[m for m in matches if team in (m["team_a"],m["team_b"]) and m["status"]!="FINISHED"]
    if future:
        nxt=min(future,key=lambda m:KO_ORDER.get(m["round"],9))
        return "Group stage" if nxt["round"]=="group" else f"In {nxt['round']}"
    played=[m for m in matches if team in (m["team_a"],m["team_b"]) and m["status"]=="FINISHED"]
    return "Eliminated" if played else "Not started"

# ---------- read endpoints ----------
@app.get("/api/standings")
def standings(db: Session = Depends(get_db)):
    ts = _team_scores(db)
    players = [dict(id=p.id, name=p.name, teams=[pk.team for pk in p.picks]) for p in db.query(Player).all()]
    return scoring.compute_standings(players, ts)

@app.get("/api/players/{pid}")
def player_detail(pid: int, db: Session = Depends(get_db)):
    p = db.query(Player).get(pid)
    if not p: raise HTTPException(404)
    ts = _team_scores(db); ms = _matches(db)
    teams=[]
    for pk in p.picks:
        s = ts.get(pk.team, dict(total=0, breakdown=[], reached=[], champion=False))
        teams.append(dict(team=pk.team, points=s["total"], breakdown=s["breakdown"],
                          status=_team_status(pk.team, ms, ts)))
    teams.sort(key=lambda x:-x["points"])
    return dict(id=p.id, name=p.name, total=sum(t["points"] for t in teams), teams=teams)

@app.get("/api/teams")
def teams(db: Session = Depends(get_db)):
    ts=_team_scores(db); ms=_matches(db)
    # which player owns each team
    owner={}
    for p in db.query(Player).all():
        for pk in p.picks: owner[pk.team]=p.name
    out=[]
    allnames=[t for g in seed_data.GROUPS.values() for t in g]
    for t in allnames:
        s=ts.get(t, dict(total=0,group_points=0,ko_points=0,breakdown=[],reached=[],champion=False))
        out.append(dict(team=t, group=next(g for g,xs in seed_data.GROUPS.items() if t in xs),
                        total=s["total"], status=_team_status(t,ms,ts),
                        owner=owner.get(t), breakdown=s["breakdown"]))
    out.sort(key=lambda x:-x["total"])
    return out

@app.get("/api/schedule")
def schedule(db: Session = Depends(get_db)):
    owner = _owners(db)
    rows=[]
    for m in db.query(Match).all():
        rows.append(dict(id=m.id, round=m.round, grp=m.grp, team_a=m.team_a, team_b=m.team_b,
                         score_a=m.score_a, score_b=m.score_b, winner=m.winner, status=m.status,
                         network=m.network, slot_a=m.slot_a, slot_b=m.slot_b,
                         owner_a=owner.get(m.team_a), owner_b=owner.get(m.team_b),
                         kickoff=m.kickoff.isoformat() if m.kickoff else None))
    rows.sort(key=lambda r:(r["kickoff"] or "9999", KO_ORDER.get(r["round"],9)))
    return rows

@app.get("/api/groups")
def groups():
    return seed_data.GROUPS

# ---------- write endpoints (optionally admin-gated) ----------
class PlayerIn(BaseModel): name: str
class PicksIn(BaseModel): teams: list[str]
class MatchIn(BaseModel):
    team_a: str|None=None; team_b: str|None=None
    score_a: int|None=None; score_b: int|None=None
    winner: str|None=None; status: str|None=None

@app.post("/api/players", dependencies=[Depends(require_admin)])
def add_player(p: PlayerIn, db: Session = Depends(get_db)):
    if db.query(Player).filter(Player.name==p.name).first(): raise HTTPException(400,"Name exists")
    pl=Player(name=p.name); db.add(pl); db.commit(); db.refresh(pl); return {"id":pl.id,"name":pl.name}

@app.delete("/api/players/{pid}", dependencies=[Depends(require_admin)])
def del_player(pid:int, db: Session = Depends(get_db)):
    pl=db.query(Player).get(pid)
    if pl: db.delete(pl); db.commit()
    return {"ok":True}

@app.put("/api/players/{pid}/picks", dependencies=[Depends(require_admin)])
def set_picks(pid:int, body:PicksIn, db: Session = Depends(get_db)):
    pl=db.query(Player).get(pid)
    if not pl: raise HTTPException(404)
    pl.picks.clear()
    for t in body.teams: pl.picks.append(Pick(team=t))
    db.commit(); return {"ok":True,"teams":body.teams}

@app.put("/api/matches/{mid}", dependencies=[Depends(require_admin)])
def update_match(mid:int, body:MatchIn, db: Session = Depends(get_db)):
    m=db.query(Match).get(mid)
    if not m: raise HTTPException(404)
    for f in ("team_a","team_b","score_a","score_b","winner","status"):
        v=getattr(body,f)
        if v is not None: setattr(m,f,v)
    m.manual=True            # protect hand-entered result from API sync
    db.commit(); propagate_bracket(db); return {"ok":True}

@app.post("/api/sync", dependencies=[Depends(require_admin)])
def sync(db: Session = Depends(get_db)):
    # ESPN is the sole source: keyless, reliable, and provides scores, kickoff
    # times and TV networks. (football-data is intentionally not used — running a
    # second source created duplicate fixtures.)
    r = espn_api.sync(db)
    propagate_bracket(db)
    if r.get("ok"):
        return {"ok": True, "updated": r["updated"], "created": 0,
                "msg": f"ESPN {r['updated']} matches, {r['networks']} TV"}
    return {"ok": False, "updated": 0, "created": 0, "msg": r.get("msg", "ESPN unavailable")}

def compute_group_tables(db):
    ms = _matches(db)
    owner = _owners(db)
    tables = {}
    for g, teams in seed_data.GROUPS.items():
        rec = {t: dict(team=t, owner=owner.get(t), played=0, w=0, d=0, l=0, gf=0, ga=0, gd=0, pts=0) for t in teams}
        finished = 0
        for m in ms:
            if m["round"] != "group" or m["grp"] != g: continue
            if m["status"] != "FINISHED" or m["score_a"] is None or m["score_b"] is None: continue
            a, b, sa, sb = m["team_a"], m["team_b"], m["score_a"], m["score_b"]
            if a not in rec or b not in rec: continue
            finished += 1
            for tm, gf, ga in ((a, sa, sb), (b, sb, sa)):
                r = rec[tm]; r["played"] += 1; r["gf"] += gf; r["ga"] += ga; r["gd"] += gf - ga
            if sa > sb: rec[a]["w"] += 1; rec[a]["pts"] += 3; rec[b]["l"] += 1
            elif sb > sa: rec[b]["w"] += 1; rec[b]["pts"] += 3; rec[a]["l"] += 1
            else: rec[a]["d"] += 1; rec[b]["d"] += 1; rec[a]["pts"] += 1; rec[b]["pts"] += 1
        rows = sorted(rec.values(), key=lambda r: (r["pts"], r["gd"], r["gf"]), reverse=True)
        for i, r in enumerate(rows): r["pos"] = i + 1; r["advancing"] = i < 2
        tables[g] = dict(rows=rows, complete=(finished == 6))
    thirds = []
    for g, t in tables.items():
        if len(t["rows"]) >= 3:
            r = dict(t["rows"][2]); r["group"] = g; thirds.append(r)
    thirds.sort(key=lambda r: (r["pts"], r["gd"], r["gf"]), reverse=True)
    for i, r in enumerate(thirds): r["third_rank"] = i + 1; r["qualified"] = i < 8
    return dict(groups=tables, thirds=thirds)

@app.get("/api/group-standings")
def group_standings(db: Session = Depends(get_db)):
    return compute_group_tables(db)

# ---------- automatic, match-aware background sync ----------
import threading, time

def _active_window(db):
    """True if any match is live, or within (-2h .. +3h) of kickoff -> poll fast."""
    now = datetime.datetime.utcnow()
    for m in db.query(Match).all():
        if m.status == "LIVE":
            return True
        if m.kickoff and m.status != "FINISHED":
            ko = m.kickoff.replace(tzinfo=None) if m.kickoff.tzinfo else m.kickoff
            if ko - datetime.timedelta(hours=2) <= now <= ko + datetime.timedelta(hours=3):
                return True
    return False

def _seconds_until_window(db):
    """Seconds until the next match window opens (kickoff - 2h). None if no future matches."""
    now = datetime.datetime.utcnow()
    best = None
    for m in db.query(Match).all():
        if m.kickoff and m.status != "FINISHED":
            ko = m.kickoff.replace(tzinfo=None) if m.kickoff.tzinfo else m.kickoff
            start = ko - datetime.timedelta(hours=2)
            if start > now:
                d = (start - now).total_seconds()
                best = d if best is None else min(best, d)
    return best

def _run_sync(db):
    espn_api.sync(db)                                          # keyless — sole source
    propagate_bracket(db)                                      # derive KO matchups from the official tree

def _auto_sync_loop():
    poll_min = int(os.environ.get("WINDOW_POLL_MIN", "30"))   # during match windows
    try:
        db = SessionLocal(); _run_sync(db); db.close()         # initial: fill times, TV, live scores
    except Exception:
        pass
    while True:
        wait = 3600
        try:
            db = SessionLocal()
            if _active_window(db):
                _run_sync(db)
                wait = poll_min * 60
            else:
                nxt = _seconds_until_window(db)
                wait = min(nxt, 3600) if nxt is not None else 3600
            db.close()
        except Exception:
            wait = 600
        time.sleep(max(60, wait))

@app.on_event("startup")
def _start_auto_sync():
    # ESPN needs no key, so the auto-updater runs by default (set AUTO_SYNC=0 to disable)
    if os.environ.get("AUTO_SYNC", "1") != "0":
        threading.Thread(target=_auto_sync_loop, daemon=True).start()

# ---------- serve the static frontend (single Railway service) ----------
WEB = os.path.join(os.path.dirname(__file__), "..", "web")
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
