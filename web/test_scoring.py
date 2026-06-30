from scoring import compute_team_scores, compute_standings

def F(rnd,a,b,sa,sb,winner=None,status="FINISHED"):
    return dict(round=rnd,team_a=a,team_b=b,score_a=sa,score_b=sb,winner=winner,status=status)

def build():
    M=[]
    # Group H (Spain group): Spain wins all 3, Uruguay 1-1-1, etc.
    M+=[F("group","Spain","Cape Verde",3,0),F("group","Spain","Saudi Arabia",2,0),F("group","Spain","Uruguay",1,0)]
    M+=[F("group","Uruguay","Saudi Arabia",2,1),F("group","Uruguay","Cape Verde",1,1)]
    # Knockout participation: Spain reaches everything and wins; Uruguay reaches R32 then out
    M+=[F("R32","Spain","Norway",2,1)]
    M+=[F("R32","Uruguay","Croatia",0,1)]          # Uruguay reached R32 only
    M+=[F("R16","Spain","Belgium",2,0)]
    M+=[F("QF","Spain","Brazil",1,0)]
    M+=[F("SF","Spain","France",2,1)]
    M+=[F("Final","Spain","Argentina",1,1,winner="Spain")]   # Spain champion on pens
    M+=[F("3rd","France","Brazil",2,0)]            # 3rd place: no points
    return M

def test():
    ts=compute_team_scores(build())
    # Spain: group 3W=9; reached R32,R16,QF,SF,Final=5*4=20; champion +4 => 33
    assert ts["Spain"]["group_points"]==9, ts["Spain"]
    assert ts["Spain"]["reached"]==["R32","R16","QF","SF","Final"], ts["Spain"]["reached"]
    assert ts["Spain"]["champion"] is True
    assert ts["Spain"]["total"]==33, ts["Spain"]["total"]
    # Argentina: finalist (reached Final via that match) - but only Final match lists Argentina here,
    # so it reached only Final in this toy data => 4 (not realistic, just tests participation logic)
    assert ts["Argentina"]["reached"]==["Final"], ts["Argentina"]["reached"]
    assert ts["Argentina"]["champion"] is False
    # Uruguay: group 1W1D1L = 3+1+0=4; reached R32 only +4 => 8
    assert ts["Uruguay"]["group_points"]==4, ts["Uruguay"]
    assert ts["Uruguay"]["reached"]==["R32"]
    assert ts["Uruguay"]["total"]==8, ts["Uruguay"]["total"]
    # Cape Verde: 0W1D1L group only = 1
    assert ts["Cape Verde"]["total"]==1, ts["Cape Verde"]
    # standings
    players=[dict(id=1,name="Alice",teams=["Spain","Uruguay"]),
             dict(id=2,name="Bob",teams=["Argentina","Cape Verde"])]
    s=compute_standings(players,ts)
    assert s[0]["name"]=="Alice" and s[0]["total"]==41, s
    assert s[1]["name"]=="Bob" and s[1]["total"]==5, s
    assert s[0]["rank"]==1 and s[1]["rank"]==2
    # breakdown sanity
    alice_spain=[x for x in s[0]["teams"] if x["team"]=="Spain"][0]
    assert alice_spain["points"]==33
    print("ALL SCORING TESTS PASSED")
    print("Spain breakdown:", [ (b['label'],b['points']) for b in ts['Spain']['breakdown'] ])

if __name__=="__main__":
    test()
