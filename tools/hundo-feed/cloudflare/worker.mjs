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

const cityHosts=new Set(["nycpokemap.com","sgpokemap.com","londonpogomap.com","sydneypogomap.com","vanpokemap.com"]);
async function cityRows(body,now) {
  if (!Array.isArray(body?.pokemons)) throw Error("city_schema");
  const spots=[];
  for (const p of body.pokemons) {
    if (!p || ![p.attack,p.defence,p.stamina].every(v=>v===15) ||
        [p.lat,p.lng,p.despawn,p.pokemon_id].some(v=>v==null || String(v).trim()==="")) continue;
    const lat=Number(p.lat), lon=Number(p.lng), dex=Number(p.pokemon_id), end=Number(p.despawn)*1000;
    const seed=[dex,lat.toFixed(5),lon.toFixed(5),Math.floor(end/60000)].join(":");
    const hash=new Uint8Array(await crypto.subtle.digest("SHA-1",new TextEncoder().encode(seed)));
    const key="s"+Array.from(hash.slice(0,8),v=>v.toString(16).padStart(2,"0")).join("");
    spots.push([key,dex,Number(p.form||0),lat,lon,end,Number(p.cp||0),Number(p.level||0)]);
  }
  return rows({v:1,fetched_ms:now,hundos:[],spots},now);
}

function iflowRows(body,category,now) {
  const raid=category==="raids", list=raid?body.raids:body.items;
  if (!Array.isArray(list)) throw Error("iflow_schema");
  const records=new Map(), spots=[];
  for (const p of list) {
    const end=Date.parse(raid?p?.raid_end_at:p?.expires_at);
    if (!Number.isFinite(end) || end<now+60000 || typeof p.id!=="string" || !/^\d{1,20}$/.test(p.id) ||
        !Number.isFinite(p.lat) || Math.abs(p.lat)>90 || !Number.isFinite(p.lon) || Math.abs(p.lon)>180) continue;
    if (!raid && !(Number.isSafeInteger(p.pokemon_id) && p.pokemon_id>0)) continue;
    const record={id:p.id,source:"iflowgo",lat:p.lat,lon:p.lon,expires_ms:end};
    if (raid) {record.boss=p.raid_pokemon_id; record.level=p.raid_level;}
    else {
      record.dex=p.pokemon_id;
      if ([p.attack_iv,p.defense_iv,p.stamina_iv].every(v=>v===15) && BigInt(p.id)<(1n<<64n))
        spots.push(["s"+BigInt(p.id).toString(16).padStart(16,"0"),p.pokemon_id,0,p.lat,p.lon,end,p.cp,p.level]);
    }
    records.set(p.id,record);
  }
  return {...rows({v:1,fetched_ms:now,hundos:[],spots},now),category,records:[...records.values()]};
}

async function collect(source, now) {
  const url = new URL(source.url);
  const city=source.kind==="city" && cityHosts.has(url.hostname) && url.pathname==="/query2.php";
  const iflow=source.kind==="iflow" && url.hostname==="pokecoords.iflowgo.com" &&
    ["pokemon","raids"].includes(source.category) && url.pathname==="/iflowgopokecoords/api/v1/"+(source.category==="raids"?"nearby":"pokemon-search");
  if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash ||
      (!iflow && !city && !url.pathname.endsWith("/hundos.json"))) throw Error("source_url");
  if (iflow) url.search=new URLSearchParams(source.category==="raids"
    ? {lat:"40.758",lon:"-73.9855",radius_km:"2",layers:"raids",limit:"200"} : {page:"1"});
  if (city) url.search=new URLSearchParams({mons:Array.from({length:1025},(_,i)=>i+1).join(","),minIV:"100",since:"0",time:String(now)});
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),12000);
  try {
  const response = await fetch(url,{redirect:"manual",signal:controller.signal,
    headers:{Accept:"application/json","User-Agent":"PGS-Hundo-Feed/1"}});
  if (!response.ok) {
    const error = Error("upstream_http");
    error.httpStatus=response.status;
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
  const body=JSON.parse(data+decoder.decode());
  if (iflow) return iflowRows(body,source.category,now);
  return city ? cityRows(body,now) : rows(body,now);
  } finally {clearTimeout(timer);}
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
      return {...old,...base,status:"offline",httpStatus:error.httpStatus || null,
        reason:["invalid_feed","source_url","city_schema","iflow_schema","upstream_http","size"].includes(error.message)
          ? error.message : (error.name==="SyntaxError"?"invalid_json":error.name==="AbortError"?"timeout":"runtime_"+String(error.name).slice(0,24)),failures,
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
    if (s.category==="raids") continue;
    const name=s.category==="pokemon"?"iflowgo":s.name;
    const count=sources[name]={active:0,unique:0,status:s.status,http_status:s.httpStatus || null};
    for (const row of s.hundos || []) {
      if (row[5]<now+60000) continue;
      count.active++;
      if (!hundos.has(row[0])) { hundos.set(row[0],row); register(row); count.unique++; }
    }
  }
  for (const s of state.entries) for (const row of s.spots || []) {
    if (row[5]<now+60000) continue;
    sources[s.category==="pokemon"?"iflowgo":s.name].active++;
    const duplicate=(nearby.get(row[1]) || []).some(other=>{
      if (Math.abs(other[5]-row[5])>180000) return false;
      const a=Math.sin((row[3]-other[3])*radians/2)**2 +
        Math.cos(row[3]*radians)*Math.cos(other[3]*radians)*Math.sin((row[4]-other[4])*radians/2)**2;
      return a<=Math.sin(50/12742000)**2;
    });
    if (!duplicate) { register(row); spots.push(row); sources[s.category==="pokemon"?"iflowgo":s.name].unique++; }
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
    const category=({"/pokemon.json":"pokemon","/raids.json":"raids"})[path];
    if (!category && !simulation && path!=="/hundos.json") return new Response(null,{status:404});
    if (!["GET","HEAD"].includes(request.method)) return new Response(null,{status:405,headers:{Allow:"GET, HEAD"}});
    const active=new Set(JSON.parse(env.SOURCES || "[]").map(s=>s.name+" "+s.url));
    const state=await env.FEED.get(simulation?"pgs-simulation-v1":stateKey,"json");
    if (!simulation && state?.entries) state.entries=state.entries.filter(s=>active.has(s.name+" "+s.url));
    if (!state?.entries?.some(s=>s.updated)) return new Response(null,{status:503,headers:{"Retry-After":"300","Cache-Control":"no-store"}});
    let body;
    if (category) {
      const entry=state.entries.find(s=>s.category===category);
      const records=(entry?.records || []).filter(r=>r.expires_ms>Date.now());
      if (!records.length) return new Response(null,{status:404,headers:{"Cache-Control":"no-store"}});
      body={v:1,category,source:"iflowgo",fetched_ms:entry.updated,coverage:category==="raids"?"Times Square, 2 km":"global, page 1",records};
    } else body=feed(state,Date.now());
    if (simulation) body.simulated=true;
    return new Response(request.method==="HEAD"?null:JSON.stringify(body),{headers:{
      "Content-Type":"application/json; charset=utf-8","Cache-Control":"public, max-age=15"}});
  }
};
