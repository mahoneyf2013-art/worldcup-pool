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
function etTime(iso){ if(!iso) return "TBD"; const d=new Date(iso);
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
function navbar(active){ return `<header><div class="wrap"><nav>
  <div class="brand">World Cup <span>Pool</span></div>
  <a href="index.html" class="${active==='standings'?'active':''}">Standings</a>
  <a href="groups.html" class="${active==='groups'?'active':''}">Groups</a>
  <a href="schedule.html" class="${active==='schedule'?'active':''}">Schedule</a>
  <a href="admin.html" class="${active==='admin'?'active':''}">Admin</a>
</nav></div></header>`; }
