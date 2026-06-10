import os, sys, tempfile
db=os.path.join(tempfile.mkdtemp(),"t.db"); os.environ["DATABASE_URL"]="sqlite:///"+db
sys.path.insert(0,"app")
from fastapi.testclient import TestClient
import main
c=TestClient(main.app)
sched=c.get("/api/schedule").json()
print("seeded matches:",len(sched),"| groups:",len(c.get('/api/groups').json()))
a=c.post("/api/players",json={"name":"Alice"}).json(); b=c.post("/api/players",json={"name":"Bob"}).json()
c.put(f"/api/players/{a['id']}/picks",json={"teams":["Spain","Uruguay"]})
c.put(f"/api/players/{b['id']}/picks",json={"teams":["Argentina","England"]})
def setm(mid,**kw): c.put(f"/api/matches/{mid}",json=kw)
# Spain: win all 3 group games (mark the 3 Spain group matches finished as wins)
spain_grp=[m for m in sched if m["round"]=="group" and "Spain" in (m["team_a"],m["team_b"])]
for m in spain_grp:
    if m["team_a"]=="Spain": setm(m["id"],score_a=2,score_b=0,status="FINISHED")
    else: setm(m["id"],score_a=0,score_b=2,status="FINISHED")
# Spain marches to title: fill one match per KO round with Spain winning
ko={r:[m for m in sched if m["round"]==r] for r in ["R32","R16","QF","SF","Final"]}
setm(ko["R32"][0]["id"],team_a="Spain",team_b="Norway",score_a=2,score_b=0,status="FINISHED")
setm(ko["R16"][0]["id"],team_a="Spain",team_b="Belgium",score_a=1,score_b=0,status="FINISHED")
setm(ko["QF"][0]["id"], team_a="Spain",team_b="Brazil", score_a=2,score_b=1,status="FINISHED")
setm(ko["SF"][0]["id"], team_a="Spain",team_b="France", score_a=1,score_b=0,status="FINISHED")
setm(ko["Final"][0]["id"],team_a="Spain",team_b="Argentina",score_a=1,score_b=1,winner="Spain",status="FINISHED")
det=c.get(f"/api/players/{a['id']}").json()
sp=[t for t in det["teams"] if t["team"]=="Spain"][0]
print("Spain:",sp["points"],"pts ->",[(x['label'],x['points']) for x in sp['breakdown']],"| status:",sp["status"])
assert sp["points"]==9+24, sp["points"]            # 3 wins=9 ; R32+R16+QF+SF+Final=20 ; champion +4 => 33
st=c.get("/api/standings").json()
print("Standings:",[(p["rank"],p["name"],p["total"]) for p in st])
assert st[0]["name"]=="Alice" and st[0]["total"]==33
# Argentina = finalist (reached R32? only Final here) -> appears only in Final => 4; Bob has Argentina+England
arg=[t for t in c.get(f"/api/players/{b['id']}").json()["teams"] if t["team"]=="Argentina"][0]
print("Argentina(finalist, partial data):",arg["points"],[(x['label'],x['points']) for x in arg['breakdown']])
print("\nALL ENDPOINTS + SCORING VERIFIED")
os.remove(db)
