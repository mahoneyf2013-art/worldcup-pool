import os, datetime
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
import models
from models import Player, Pick, Match
import scoring, seed_data, football_api

Base.metadata.create_all(bind=engine)
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

def _matches(db):
    return [dict(id=m.id, round=m.round, grp=m.grp, team_a=m.team_a, team_b=m.team_b,
                 score_a=m.score_a, score_b=m.score_b, winner=m.winner, status=m.status,
                 kickoff=m.kickoff.isoformat() if m.kickoff else None) for m in db.query(Match).all()]

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
    rows=[]
    for m in db.query(Match).all():
        rows.append(dict(id=m.id, round=m.round, grp=m.grp, team_a=m.team_a, team_b=m.team_b,
                         score_a=m.score_a, score_b=m.score_b, winner=m.winner, status=m.status,
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
    db.commit(); return {"ok":True}

@app.post("/api/sync", dependencies=[Depends(require_admin)])
def sync(db: Session = Depends(get_db)):
    return football_api.sync(db)

def compute_group_tables(db):
    ms = _matches(db)
    tables = {}
    for g, teams in seed_data.GROUPS.items():
        rec = {t: dict(team=t, played=0, w=0, d=0, l=0, gf=0, ga=0, gd=0, pts=0) for t in teams}
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

# ---------- serve the static frontend (single Railway service) ----------
WEB = os.path.join(os.path.dirname(__file__), "..", "web")
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
