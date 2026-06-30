const API = "";                                  // same origin
const adminKey = () => localStorage.getItem("adminKey") || "";
async function api(path, opts={}){
  opts.headers = Object.assign({"Content-Type":"application/json","X-Admin-Key":adminKey()}, opts.headers||{});
  const r = await fetch(API+path, opts);
  if(!r.ok){ throw new Error((await r.json().catch(()=>({}))).detail || r.statusText); }
  return r.status===204?null:r.json();
}
function el(tag, cls, html){ const e=document.createElement(tag); if(cls)e.className=cls; if(html!=null)e.innerHTML=html; return e; }
function statusClass(s){ return s==="Champion"?"s-Champion":s==="Eliminated"?"s-Eliminated":s==="Not started"?"s-none":"s-alive"; }
function fmtDate(iso){ if(!iso) return "TBD"; const d=new Date(iso);
  return d.toLocaleDateString(undefined,{month:"short",day:"numeric"})+" "+d.toLocaleTimeString(undefined,{hour:"numeric",minute:"2-digit"}); }

// ---- Eastern Time kickoff (auto-handles EST/EDT; labelled ET) ----
function etTime(iso){ if(!iso) return "TBD";
  if(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(iso) && !/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso)) iso+="Z"; // treat naive timestamps as UTC
  const d=new Date(iso);
  const day=d.toLocaleDateString("en-US",{timeZone:"America/New_York",weekday:"short",month:"short",day:"numeric"});
  const t=d.toLocaleTimeString("en-US",{timeZone:"America/New_York",hour:"numeric",minute:"2-digit"});
  return `${day} · ${t} ET`; }

// ---- country flags (flagcdn; works on every OS incl. Windows) ----
const FLAGS = {
 "Mexico":"mx","South Africa":"za","South Korea":"kr","Czechia":"cz",
 "Canada":"ca","Bosnia & Herzegovina":"ba","Qatar":"qa","Switzerland":"ch",
 "Brazil":"br","Morocco":"ma","Haiti":"ht","Scotland":"gb-sct",
 "United States":"us","Paraguay":"py","Australia":"au","Turkiye":"tr",
 "Germany":"de","Curacao":"cw","Ivory Coast":"ci","Ecuador":"ec",
 "Netherlands":"nl","Japan":"jp","Sweden":"se","Tunisia":"tn",
 "Belgium":"be","Egypt":"eg","Iran":"ir","New Zealand":"nz",
 "Spain":"es","Cape Verde":"cv","Saudi Arabia":"sa","Uruguay":"uy",
 "France":"fr","Senegal":"sn","Iraq":"iq","Norway":"no",
 "Argentina":"ar","Algeria":"dz","Austria":"at","Jordan":"jo",
 "Portugal":"pt","DR Congo":"cd","Uzbekistan":"uz","Colombia":"co",
 "England":"gb-eng","Croatia":"hr","Ghana":"gh","Panama":"pa"
};
function flag(team){ const c=FLAGS[team];
  if(!c) return `<span class="flag flag-tbd"></span>`;
  return `<img class="flag" src="https://flagcdn.com/24x18/${c}.png" srcset="https://flagcdn.com/48x36/${c}.png 2x" width="24" height="18" alt="" loading="lazy">`; }
// flag + country name (+ optional owner badge)
function teamLabel(team, owner){
  return `${flag(team)}<span class="cname">${team||"TBD"}</span>${owner?`<span class="owner">${owner}</span>`:""}`; }
function ownerBadge(owner){ return owner?`<span class="owner">${owner}</span>`:""; }
const TAB_ICONS={
  standings:'<svg viewBox="0 0 24 24"><path d="M7 4h10v4a5 5 0 0 1-10 0zM5 4a3 3 0 0 0 3 5M19 4a3 3 0 0 1-3 5M9 19h6M12 14v5"/></svg>',
  groups:'<svg viewBox="0 0 24 24"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></svg>',
  schedule:'<svg viewBox="0 0 24 24"><path d="M5 5h14v15H5zM5 9h14M9 3v4M15 3v4"/></svg>',
  bracket:'<svg viewBox="0 0 24 24"><path d="M3 5h5v5h4M3 19h5v-5M16 7h5M16 17h5M12 14h4v-4"/></svg>',
  admin:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/></svg>'
};
function navbar(active){
  const tabs=[["index.html","standings","Standings"],["groups.html","groups","Groups"],
              ["schedule.html","schedule","Schedule"],["bracket.html","bracket","Bracket"],["admin.html","admin","Admin"]];
  const top=tabs.map(([h,k,l])=>`<a href="${h}" class="${active===k?'active':''}">${l}</a>`).join("");
  const bottom=tabs.map(([h,k,l])=>`<a href="${h}" class="${active===k?'active':''}">${TAB_ICONS[k]}${l}</a>`).join("");
  return `<header><div class="wrap"><nav>
  <a href="index.html" class="brand">World Cup <span>Pool</span></a>
  ${top}
</nav></div></header><div id="ticker-mount"></div><nav class="tabbar">${bottom}</nav>`;
}

// animate a number from its previous value to a new target
function countUp(node, to, from){
  if(!node) return;
  from = (from==null||isNaN(from)) ? 0 : from;
  if(from===to || typeof requestAnimationFrame!=="function"){ node.textContent=to; return; }
  const dur=600, t0=performance.now();
  (function step(t){ const k=Math.min(1,(t-t0)/dur);
    node.textContent=String(Math.round(from+(to-from)*(1-Math.pow(1-k,3))));
    if(k<1) requestAnimationFrame(step); })(t0);
}

function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])); }

// ---- skeleton loaders ----
function skeletonCard(rows=5){ let r="";
  for(let i=0;i<rows;i++) r+=`<div class="skrow"><div class="sk sk-rank"></div><div class="sk sk-name"></div><div class="sk sk-pts"></div></div>`;
  return `<div class="card skwrap" aria-hidden="true">${r}</div>`; }
function skeletonGrid(cards=6){ let g="";
  for(let i=0;i<cards;i++) g+=`<div class="card skcard" aria-hidden="true"><div class="sk sk-title"></div>`+
    `<div class="sk sk-line"></div><div class="sk sk-line"></div><div class="sk sk-line"></div><div class="sk sk-line"></div></div>`;
  return `<div class="groups-grid">${g}</div>`; }

// ---- live ticker (shown on every page, under the nav) ----
let _tickerTimer=null;
function renderTicker(matches){
  const mount=document.getElementById("ticker-mount"); if(!mount) return;
  const live=(matches||[]).filter(m=>m.status==="LIVE");
  if(live.length){
    const items=live.map(m=>{
      const oa=m.owner_a?` <span class="tk-own">${esc(m.owner_a)}</span>`:"";
      const ob=m.owner_b?` <span class="tk-own">${esc(m.owner_b)}</span>`:"";
      return `<span class="tk-game">${flag(m.team_a)}<b>${esc(m.team_a)}</b>${oa}`+
             ` <span class="tk-score">${m.score_a??0}–${m.score_b??0}</span> `+
             `${flag(m.team_b)}<b>${esc(m.team_b)}</b>${ob}</span>`;
    }).join('<span class="tk-sep">•</span>');
    mount.innerHTML=`<a class="ticker live" href="schedule.html"><span class="tk-tag">● LIVE</span><div class="tk-scroll">${items}</div></a>`;
    return;
  }
  const next=(matches||[]).filter(m=>m.status!=="FINISHED"&&m.team_a&&m.team_b&&m.kickoff)
      .sort((a,b)=>(a.kickoff||"")<(b.kickoff||"")?-1:1)[0];
  mount.innerHTML = next
    ? `<a class="ticker next" href="schedule.html"><span class="tk-tag muted">NEXT</span>`+
      `<div class="tk-scroll"><span class="tk-game">${flag(next.team_a)}<b>${esc(next.team_a)}</b> vs ${flag(next.team_b)}<b>${esc(next.team_b)}</b>`+
      ` <span class="muted">${etTime(next.kickoff)}</span></span></div></a>`
    : "";
}
async function refreshTicker(){ try{ renderTicker(await api("/api/schedule")); }catch(e){} }

// auto-refresh: ticker on every page + the page's own load() (if it opts in via window.__reload)
document.addEventListener("DOMContentLoaded",()=>{
  refreshTicker();
  if(_tickerTimer) clearInterval(_tickerTimer);
  _tickerTimer=setInterval(()=>{ refreshTicker(); if(typeof window.__reload==="function") window.__reload(); }, 30000);
});

// ---- alive / eliminated status from schedule + group tables ----
function buildStatus(schedule, groupData){
  const status={}, teams=new Set();
  (schedule||[]).forEach(m=>[m.team_a,m.team_b].forEach(t=>{ if(t) teams.add(t); }));
  const groups=(groupData&&groupData.groups)||{};
  const advancing=new Set(), groupOf={}, complete={};
  Object.entries(groups).forEach(([g,t])=>{ complete[g]=t.complete;
    (t.rows||[]).forEach(r=>{ groupOf[r.team]=g; teams.add(r.team); if(r.advancing) advancing.add(r.team); }); });
  ((groupData&&groupData.thirds)||[]).forEach(r=>{ if(r.qualified) advancing.add(r.team); });
  const fin=(schedule||[]).find(m=>m.round==="Final"&&m.status==="FINISHED");
  const champ=fin?(fin.winner||(fin.score_a>fin.score_b?fin.team_a:fin.team_b)):null;
  const KO=["R32","R16","QF","SF","Final"];
  const koWin=m=>m.winner||(m.score_a>m.score_b?m.team_a:(m.score_b>m.score_a?m.team_b:null));
  teams.forEach(t=>{
    if(t===champ){ status[t]="Champion"; return; }
    const ko=(schedule||[]).filter(m=>KO.includes(m.round)&&(m.team_a===t||m.team_b===t));
    if(ko.some(m=>m.status!=="FINISHED")){ status[t]="alive"; return; }   // playing or awaiting a knockout game
    if(ko.length){                                                        // all its knockout games are finished
      const lost=ko.some(m=>m.status==="FINISHED"&&koWin(m)&&koWin(m)!==t);
      status[t]=lost?"Eliminated":"alive";   // won its last game; next round just isn't drawn yet
      return;
    }
    const g=groupOf[t];
    status[t]=(g && complete[g]) ? (advancing.has(t)?"alive":"Eliminated") : "alive";
  });
  return status;
}

// ---- group games remaining + projected-to-advance (top 2 + current best-8 thirds) ----
function groupInfo(groupData){
  const remaining={}, advancing=new Set();
  const groups=(groupData&&groupData.groups)||{};
  Object.values(groups).forEach(t=>(t.rows||[]).forEach(r=>{
    remaining[r.team]=Math.max(0, 3-(r.played||0));
    if(r.advancing) advancing.add(r.team);
  }));
  ((groupData&&groupData.thirds)||[]).forEach(r=>{ if(r.qualified) advancing.add(r.team); });
  return { remaining, advancing };
}

// ---- shareable results card (canvas -> native share or PNG download) ----
async function shareStandings(standings, statusMap){
  const W=720, pad=36, rowH=46, headH=150, rows=standings.slice(0,12);
  const H=headH + rows.length*rowH + 60, scale=2;
  const c=document.createElement("canvas"); c.width=W*scale; c.height=H*scale;
  const x=c.getContext("2d"); x.scale(scale,scale);
  x.fillStyle="#0f1720"; x.fillRect(0,0,W,H);
  x.fillStyle="#16212e"; x.fillRect(pad,headH-12,W-2*pad,rows.length*rowH+24);
  x.fillStyle="#e8eef5"; x.font="700 30px -apple-system,Segoe UI,Roboto,sans-serif";
  x.fillText("World Cup Pool — Standings", pad, 56);
  x.fillStyle="#22c55e"; x.font="600 16px -apple-system,Segoe UI,Roboto,sans-serif";
  x.fillText(new Date().toLocaleString(undefined,{month:"short",day:"numeric",hour:"numeric",minute:"2-digit"}), pad, 84);
  x.fillStyle="#a8bcd0"; x.font="700 12px -apple-system,Segoe UI,Roboto,sans-serif";
  x.fillText("RANK", pad+6, headH+4); x.fillText("PLAYER", pad+64, headH+4);
  x.textAlign="right"; x.fillText("TEAMS IN", W-pad-92, headH+4); x.fillText("PTS", W-pad-10, headH+4); x.textAlign="left";
  rows.forEach((p,i)=>{ const y=headH+30+i*rowH;
    if(i%2){ x.fillStyle="#1c2a3a"; x.fillRect(pad,y-rowH+14,W-2*pad,rowH); }
    x.fillStyle=p.rank===1?"#f5c542":"#a8bcd0"; x.font="800 18px -apple-system,Segoe UI,Roboto,sans-serif"; x.fillText(String(p.rank), pad+10, y);
    x.fillStyle="#e8eef5"; x.font="600 18px -apple-system,Segoe UI,Roboto,sans-serif"; x.fillText(p.name, pad+64, y);
    const alive=(p.teams||[]).filter(t=>statusMap&&statusMap[t.team]!=="Eliminated").length;
    x.textAlign="right"; x.fillStyle="#a8bcd0"; x.font="600 15px -apple-system,Segoe UI,Roboto,sans-serif"; x.fillText(`${alive}/${(p.teams||[]).length}`, W-pad-92, y);
    x.fillStyle="#e8eef5"; x.font="800 20px -apple-system,Segoe UI,Roboto,sans-serif"; x.fillText(String(p.total), W-pad-10, y); x.textAlign="left"; });
  const blob=await new Promise(res=>c.toBlob(res,"image/png"));
  const file=new File([blob],"wc-pool-standings.png",{type:"image/png"});
  if(navigator.canShare && navigator.canShare({files:[file]})){
    try{ await navigator.share({files:[file], title:"World Cup Pool Standings"}); return; }catch(e){}
  }
  const url=URL.createObjectURL(blob), a=document.createElement("a");
  a.href=url; a.download="wc-pool-standings.png"; a.click(); URL.revokeObjectURL(url);
}
