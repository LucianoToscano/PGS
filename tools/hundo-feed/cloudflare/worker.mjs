// PGS Hundo Feed. SOURCES is an operator-configured JSON array of authorized compact feeds.
const interval = 300;
const stateKey = "pgs-feed-v1";

function encounter(value) {
  if (typeof value !== "string" && !Number.isSafeInteger(value)) return null;
  const id = String(value).trim();
  if (!/^(?:-?\d{1,20}|0x[0-9a-f]{1,16})$/i.test(id)) return null;
  const n = BigInt(id);
  return n && n >= -(1n << 63n) && n < (1n << 64n) ? BigInt.asUintN(64, n).toString() : null;
}

export function rows(body, now) {
  if (body?.v !== 1 || !Number.isSafeInteger(body.fetched_ms) || body.fetched_ms < now-600000 ||
      body.fetched_ms > now+60000 || (body.coordinate_precision ?? "exact") !== "exact" ||
      !Array.isArray(body.hundos) || !Array.isArray(body.spots ?? []) ||
      !Array.isArray(body.approximate_encounters ?? [])) throw Error("invalid_feed");
  const approximate = new Set((body.approximate_encounters ?? []).map(encounter));
  function clean(list, spot) {
    const result = new Map();
    for (const row of list) {
      if (!Array.isArray(row) || row.length !== 8) continue;
      const [raw,dex,form,lat,lon,end,cp,level] = row;
      const key = spot ? (typeof raw === "string" && /^s[0-9a-f]{16}$/.test(raw) && raw) : encounter(raw);
      if (!key || (!spot && approximate.has(key)) || ![dex,form,end,cp].every(Number.isSafeInteger) ||
          dex<=0 || form<0 || cp<0 || ![lat,lon,level].every(Number.isFinite) ||
          Math.abs(lat)>90 || Math.abs(lon)>180 || end<now+60000 || level<0 || level>55) continue;
      if (!result.has(key)) result.set(key,[key,...row.slice(1)]);
    }
    return [...result.values()];
  }
  return {hundos:clean(body.hundos,false), spots:clean(body.spots ?? [],true)};
}

async function collect(source, now) {
  const url = new URL(source.url);
  if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash ||
      !url.pathname.endsWith("/hundos.json")) throw Error("source_url");
  const response = await fetch(url,{redirect:"error",signal:AbortSignal.timeout(12000),
    headers:{Accept:"application/json","User-Agent":"PGS-Hundo-Feed/1"}});
  if (!response.ok) {
    const error = Error("upstream_http");
    const retry = response.headers.get("Retry-After");
    if (retry) error.retryAt = /^\d+$/.test(retry) ? now + Number(retry)*1000 : Date.parse(retry);
    throw error;
  }
  const reader=response.body.getReader(), decoder=new TextDecoder("utf-8",{fatal:true});
  let bytes=0, data="";
  while (true) {
    const {done,value}=await reader.read();
    if (done) break;
    bytes+=value.length;
    if (bytes>262144) { await reader.cancel(); throw Error("size"); }
    data+=decoder.decode(value,{stream:true});
  }
  return rows(JSON.parse(data+decoder.decode()),now);
}

async function refresh(env) {
  const now=Date.now(), configs=JSON.parse(env.SOURCES || "[]");
  if (!configs.length) return;
  if (configs.length>8 || configs.some(s=>!s || !/^[a-z][a-z0-9-]{0,39}$/.test(s.name) ||
      !Number.isSafeInteger(s.interval_s) || s.interval_s<interval) ||
      new Set(configs.map(s=>s.name)).size!==configs.length) throw Error("invalid_config");
  const previous=await env.FEED.get(stateKey,"json") || {};
  const entries=await Promise.all(configs.map(async source=>{
    const old=previous.entries?.find(x=>x.name===source.name && x.url===source.url);
    if (old?.next>now) return old;
    const base={name:source.name,url:source.url,next:now+source.interval_s*1000};
    try { return {...base,...await collect(source,now),updated:now,status:"online",failures:0}; }
    catch(error) {
      console.warn("PGS upstream unavailable",source.name);
      const failures=Math.min((old?.failures||0)+1,8);
      return {...old,...base,status:"offline",failures,
        next:Math.max(base.next,now+interval*1000*2**failures,Number.isFinite(error.retryAt)?error.retryAt:0)};
    }
  }));
  await env.FEED.put(stateKey,JSON.stringify({entries,time:now}));
}

export function feed(state,now) {
  const hundos=new Map(), spots=[], nearby=new Map(), sources=Object.create(null);
  const radians=Math.PI/180;
  function register(row) {
    const group=nearby.get(row[1]) || [];
    group.push(row); nearby.set(row[1],group);
  }
  for (const s of state.entries) {
    const count=sources[s.name]={active:0,unique:0,status:s.status};
    for (const row of s.hundos || []) {
      if (row[5]<now+60000) continue;
      count.active++;
      if (!hundos.has(row[0])) { hundos.set(row[0],row); register(row); count.unique++; }
    }
  }
  for (const s of state.entries) for (const row of s.spots || []) {
    if (row[5]<now+60000) continue;
    sources[s.name].active++;
    const duplicate=(nearby.get(row[1]) || []).some(other=>{
      if (Math.abs(other[5]-row[5])>180000) return false;
      const a=Math.sin((row[3]-other[3])*radians/2)**2 +
        Math.cos(row[3]*radians)*Math.cos(other[3]*radians)*Math.sin((row[4]-other[4])*radians/2)**2;
      return a<=Math.sin(50/12742000)**2;
    });
    if (!duplicate) { register(row); spots.push(row); sources[s.name].unique++; }
  }
  return {v:1,fetched_ms:Math.max(...state.entries.map(s=>s.updated || 0)),interval_s:interval,
    coordinate_precision:"exact",hundos:[...hundos.values()],spots,sources};
}

export default {
  async scheduled(event,env) {
    const now=event.scheduledTime;
    const row=["18446744073709551615",25,0,0,0,now+900000,10,1];
    const sample=rows({v:1,fetched_ms:now,hundos:[row,row]},now);
    await env.FEED.put("pgs-simulation-v1",JSON.stringify({time:now,entries:[
      {name:"simulation",updated:now,status:"online",...sample}
    ]}));
    await refresh(env);
  },
  async fetch(request,env) {
    const path=new URL(request.url).pathname;
    const simulation=path==="/simulation/hundos.json";
    if (!simulation && path!=="/hundos.json") return new Response(null,{status:404});
    if (!["GET","HEAD"].includes(request.method)) return new Response(null,{status:405,headers:{Allow:"GET, HEAD"}});
    const active=new Set(JSON.parse(env.SOURCES || "[]").map(s=>s.name+" "+s.url));
    const state=await env.FEED.get(simulation?"pgs-simulation-v1":stateKey,"json");
    if (!simulation && state?.entries) state.entries=state.entries.filter(s=>active.has(s.name+" "+s.url));
    if (!state?.entries?.some(s=>s.updated)) return new Response(null,{status:503,headers:{"Retry-After":"300","Cache-Control":"no-store"}});
    const body=feed(state,Date.now());
    if (simulation) body.simulated=true;
    return new Response(request.method==="HEAD"?null:JSON.stringify(body),{headers:{
      "Content-Type":"application/json; charset=utf-8","Cache-Control":"public, max-age=15"}});
  }
};