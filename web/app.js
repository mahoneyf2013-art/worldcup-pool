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
function navbar(active){ return `<header><div class="wrap"><nav>
  <div class="brand">World Cup <span>Pool</span></div>
  <a href="index.html" class="${active==='standings'?'active':''}">Standings</a>
  <a href="groups.html" class="${active==='groups'?'active':''}">Groups</a>
  <a href="schedule.html" class="${active==='schedule'?'active':''}">Schedule</a>
  <a href="admin.html" class="${active==='admin'?'active':''}">Admin</a>
</nav></div></header>`; }
