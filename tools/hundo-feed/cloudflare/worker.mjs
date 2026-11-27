// PGS Hundo Feed: only authorized, exact-coordinate wild 100% IV spawns.
const interval = 300;
const stateKey = "pgs-feed-v1";
const ADAPTER_VERSION=2, FETCH_TIMEOUT_MS=15000, MAX_SOURCE_BYTES=524288, MAX_BACKOFF_MS=3600000;
const MAX_UPSTREAM_REQUESTS=15;
const maxPages=s=>s.kind==="iflow"?5:s.kind==="moonani"?3:1;
const pages=s=>s.max_pages ?? 1;
const publicPaths=new Set(["/hundos.json","/sources.json","/status.json"]);
const providerName=s=>s.name==="iflowgo-pokemon"?"iflowgo":s.name;
const sourceKey=s=>s.name+" "+s.url;
// Filter legacy category configuration as well as persisted KV snapshots. A removed
// raid source must not be queried even if dashboard variables still contain it.
const hundoOnly=s=>s && s.name!=="iflowgo-raids" && [undefined,"hundos","pokemon"].includes(s.category);
function configuredSources(env) {
  const configs=JSON.parse(env.SOURCES || "[]");
  if (!Array.isArray(configs)) throw Error("invalid_config");
  return configs.filter(hundoOnly);
}
function hundoState(state,configs) {
  const active=new Set(configs.map(sourceKey)), names=new Set(configs.map(s=>s.name));
  const entries=(state?.entries || []).filter(s=>hundoOnly(s) && active.has(sourceKey(s))).map(s=>{
    const {records,...entry}=s; // Never retain the legacy arbitrary-IV/raid catalogue.
    return entry;
  });
  const history=(state?.history || []).map(h=>({...h,online:(h.online || []).filter(name=>names.has(name))}));
  return {...state,entries,history};
}

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
          Math.abs(lat)>90 || Math.abs(lon)>180 || (lat===0 && lon===0) || end<now+60000 || level<0 || level>55) continue;
      if (!result.has(key)) result.set(key,[key,...row.slice(1)]);
    }
    return [...result.values()];
  }
  return {hundos:clean(body.hundos,false), spots:clean(body.spots ?? [],true)};
}

function strictFinite(value) {
  if (typeof value==="number") return Number.isFinite(value)?value:NaN;
  if (typeof value!=="string" || !/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(value.trim())) return NaN;
  const n=Number(value.trim());
  return Number.isFinite(n)?n:NaN;
}
function strictInt(value) {
  if (typeof value==="string" && !/^-?\d+$/.test(value.trim())) return NaN;
  const n=strictFinite(value);
  return Number.isSafeInteger(n)?n:NaN;
}
const optionalInt=value=>{const n=strictInt(value);return Number.isSafeInteger(n)&&n>=0?n:0;};
const optionalLevel=value=>{const n=strictFinite(value);return Number.isFinite(n)&&n>=0&&n<=55?n:0;};

const cityHosts=new Set(["nycpokemap.com","sgpokemap.com","londonpogomap.com","sydneypogomap.com","vanpokemap.com"]);
async function cityRows(body,now) {
  if (!Array.isArray(body?.pokemons)) throw Error("city_schema");
  const spots=[];
  for (const p of body.pokemons) {
    if (!p || ![p.attack,p.defence??p.defense,p.stamina].every(v=>strictInt(v)===15) ||
        (p.defence!=null && p.defense!=null && strictInt(p.defense)!==15) ||
        (p.coordinate_precision!=null && p.coordinate_precision!=="exact") ||
        (p.iv_percent!=null && strictFinite(p.iv_percent)!==100)) continue;
    const lat=strictFinite(p.lat), lon=strictFinite(p.lng), dex=strictInt(p.pokemon_id), rawEnd=strictFinite(p.despawn);
    const end=Math.round(rawEnd>1e12?rawEnd:rawEnd*1000);
    if (!Number.isSafeInteger(dex) || dex<=0 || !Number.isFinite(lat) || !Number.isFinite(lon) ||
        Math.abs(lat)>90 || Math.abs(lon)>180 || (lat===0 && lon===0) ||
        !Number.isSafeInteger(end) || end<now+60000 || end>now+7200000) continue;
    const seed=[dex,lat.toFixed(5),lon.toFixed(5),Math.floor(end/60000)].join(":");
    const hash=new Uint8Array(await crypto.subtle.digest("SHA-1",new TextEncoder().encode(seed)));
    const key="s"+Array.from(hash.slice(0,8),v=>v.toString(16).padStart(2,"0")).join("");
    spots.push([key,dex,optionalInt(p.form),lat,lon,end,optionalInt(p.cp),optionalLevel(p.level)]);
  }
  return rows({v:1,fetched_ms:now,hundos:[],spots},now);
}

export function iflowRows(body,now) {
  if (!Array.isArray(body?.items)) throw Error("iflow_schema");
  const spots=[];
  for (const p of body.items) {
    if (!p || ![p.attack_iv,p.defense_iv,p.stamina_iv].every(v=>strictInt(v)===15) ||
        (p.percent_iv!=null && strictFinite(p.percent_iv)!==100) ||
        (p.coordinate_precision!=null && p.coordinate_precision!=="exact")) continue;
    const end=typeof p.expires_at==="string"?Date.parse(p.expires_at):NaN;
    const dex=strictInt(p.pokemon_id), lat=strictFinite(p.lat), lon=strictFinite(p.lon);
    if (!Number.isFinite(end) || end<now+60000 || end>now+7200000 || typeof p.id!=="string" || !/^\d{1,20}$/.test(p.id) ||
        !Number.isSafeInteger(dex) || dex<=0 ||
        !Number.isFinite(lat) || Math.abs(lat)>90 || !Number.isFinite(lon) || Math.abs(lon)>180 ||
        (lat===0 && lon===0)) continue;
    const id=BigInt(p.id);
    if (id===0n || id>=(1n<<64n)) continue;
    // The provider ID is not asserted to be a game encounter ID. Keep the
    // existing spot representation and use zero only for unknown optional fields.
    spots.push(["s"+id.toString(16).padStart(16,"0"),dex,optionalInt(p.form),lat,lon,end,optionalInt(p.cp),optionalLevel(p.level)]);
  }
  return rows({v:1,fetched_ms:now,hundos:[],spots},now);
}

async function moonaniRows(body,now) {
  if (!Array.isArray(body?.data)) throw Error("moonani_schema");
  const wall=value=>typeof value==="string" && /^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$/.test(value)? Date.parse(value.replace(" ","T")+"Z"):NaN;
  const starts=body.data.map(p=>wall(p?.["Start Time"])).filter(Number.isFinite);
  if (!starts.length && body.data.length) throw Error("moonani_schema");
  const newest=Math.max(...starts), hour=3600000;
  const offset=Math.round((newest-now)/hour)*hour, age=now-newest+offset;
  if (starts.length && (offset < -12*hour || offset>14*hour || age < -120000 || age>hour)) throw Error("invalid_feed");
  const pokemons=[];
  for (const p of body.data) {
    if (!p || !["Attack","Defense","HP"].every(k=>String(p[k])==="15")) continue;
    const point=String(p.Coords).match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
    const end=wall(p["End Time"])-offset;
    if (!point || !Number.isFinite(end) || end>now+2*hour || (+point[1]===0 && +point[2]===0)) continue;
    pokemons.push({attack:15,defence:15,stamina:15,pokemon_id:p.Number,lat:point[1],lng:point[2],
      despawn:end/1000,cp:p.CP,level:p.Level});
  }
  return cityRows({pokemons},now);
}

// Public GOCoords v2 response observed on 2026-11-25; opt-in only after
// operator confirms current data, precision and redistribution permission.
// Do not follow cursors or exceed the public ten-row limit.
export async function gocoordsRows(body,now) {
  const fetched=typeof body?.generated_at==="string" && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(body.generated_at)?Date.parse(body.generated_at):NaN;
  if (body?.schema_version!==2 || !Number.isFinite(fetched) || fetched<now-600000 || fetched>now+60000 ||
      !Array.isArray(body.rows) || body.rows.length>10 || body.count!==body.rows.length) throw Error("gocoords_schema");
  const pokemons=[];
  for (const p of body.rows) {
    if (!p || p.iv!==100 || ![p.atk_iv,p.def_iv,p.sta_iv].every(v=>v===15) ||
        !Number.isSafeInteger(p.pokemon_id) || p.pokemon_id<=0 ||
        !Number.isFinite(p.lat) || !Number.isFinite(p.lon) || Math.abs(p.lat)>90 || Math.abs(p.lon)>180 ||
        (p.lat===0 && p.lon===0) ||
        (p.coordinate_precision!=null && p.coordinate_precision!=="exact") ||
        (p.form!=null && !Number.isSafeInteger(p.form))) continue;
    const end=typeof p.expires_at_utc==="string" && p.expires_at_utc.endsWith("Z")?Date.parse(p.expires_at_utc):NaN;
    if (!Number.isFinite(end) || end<now+60000 || end>now+7200000) continue;
    // Conservative coordinate spot; do not assert a provider ID is a verified game encounter.
    pokemons.push({attack:15,defence:15,stamina:15,pokemon_id:p.pokemon_id,form:p.form??0,
      lat:p.lat,lng:p.lon,despawn:end/1000,
      cp:Number.isSafeInteger(p.cp) && p.cp>=0?p.cp:0,
      level:Number.isFinite(p.lvl) && p.lvl>=0 && p.lvl<=55?p.lvl:0});
  }
  return cityRows({pokemons},now);
}

async function collect(source, now) {
  const url = new URL(source.url);
  const city=source.kind==="city" && cityHosts.has(url.hostname) && url.pathname==="/query2.php";
  const moonani=source.kind==="moonani" && url.href==="https://moonani.com/PokeList/ajax.php";
  const iflow=source.kind==="iflow" && url.hostname==="pokecoords.iflowgo.com" &&
    source.category==="pokemon" && url.pathname==="/iflowgopokecoords/api/v1/pokemon-search";
  const gocoords=source.kind==="gocoords" && source.approved===true && url.href==="https://gocoords.com/api/spawns";
  const compact=(!source.kind || source.kind==="compact") && url.pathname.endsWith("/hundos.json");
  if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash ||
      !hundoOnly(source) || (!moonani && !iflow && !city && !compact && !gocoords)) throw Error("source_url");
  // Candidate pagination is explicitly configured for existing authorized
  // providers. One deadline and one byte budget cover the entire source.
  if (!Number.isSafeInteger(pages(source)) || pages(source)<1 || pages(source)>maxPages(source)) throw Error("source_url");
  if (city) url.search=new URLSearchParams({mons:Array.from({length:1025},(_,i)=>i+1).join(","),minIV:"100",since:"0",time:String(now)});
  if (moonani) url.search="page=pokemon&action=load";
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),FETCH_TIMEOUT_MS);
  let httpStatus=null, contentType=null, bytes=0, attemptedPages=0;
  const headers={Accept:city?"application/json, text/javascript;q=0.9":"application/json",
    "User-Agent":"PGS-Hundo-Feed/1 (+https://github.com/LucianoToscano/PGS)",
    ...(city?{"X-Requested-With":"XMLHttpRequest"}:{}),
    ...(moonani?{"Content-Type":"application/x-www-form-urlencoded"}:{})};
  async function fetchPage(pageUrl,options={}) {
    httpStatus=null;contentType=null;attemptedPages++;
    const response=await fetch(pageUrl,{...options,redirect:"manual",signal:controller.signal,headers});
    httpStatus=response.status;
    const type=(response.headers.get("Content-Type") || "").split(";")[0].trim().toLowerCase();
    contentType=/^[a-z0-9.+_-]+\/[a-z0-9.+_-]+$/.test(type)?type:null;
    if (!response.ok) {
      const error=Error("upstream_http");
      const retry=response.headers.get("Retry-After");
      if (retry) error.retryAt=/^\d+$/.test(retry.trim())?now+Number(retry.trim())*1000:Date.parse(retry);
      try {await response.body?.cancel();} catch {}
      throw error;
    }
    if (!response.body) throw Error("empty_response");
    const reader=response.body.getReader(),decoder=new TextDecoder("utf-8",{fatal:true});
    let data="";
    try {
      while (true) {
        const {done,value}=await reader.read();
        if (done) break;
        bytes+=value.length;
        if (bytes>MAX_SOURCE_BYTES) throw Error("size");
        try {data+=decoder.decode(value,{stream:true});} catch {throw Error("invalid_encoding");}
      }
      try {data+=decoder.decode();} catch {throw Error("invalid_encoding");}
    } catch(error) {
      try {await reader.cancel();} catch {}
      throw error;
    } finally {reader.releaseLock();}
    if (!data.trim()) throw Error("empty_response");
    return JSON.parse(data);
  }
  try {
    let body;
    if (iflow) {
      const requestPage=page=>{
        const u=new URL(url.href);
        u.search=new URLSearchParams(source.min_iv_100===true?{min_iv:"100",page:String(page)}:{page:String(page)});
        return fetchPage(u);
      };
      const first=await requestPage(1);
      if (!Array.isArray(first?.items) || first.items.length>100) throw Error("iflow_schema");
      const items=[...first.items],reported=strictInt(first.total_pages);
      const count=Number.isSafeInteger(reported)&&reported>0?Math.min(reported,pages(source)):1;
      for(let page=2;items.length>0&&page<=count;page++) {
        const next=await requestPage(page);
        if (!Array.isArray(next?.items)||next.items.length>100) throw Error("iflow_schema");
        if (!next.items.length) break;
        items.push(...next.items);
      }
      body={items};
    } else if (moonani) {
      const requestPage=page=>fetchPage(url,{method:"POST",body:new URLSearchParams({
        draw:String(page),start:String((page-1)*100),length:"100",pokemons:"",iv:"100",pvp:"0"}).toString()});
      const first=await requestPage(1);
      if (!Array.isArray(first?.data)||first.data.length>100) throw Error("moonani_schema");
      const data=[...first.data],total=strictInt(first.recordsFiltered);
      for(let page=2;data.length===(page-1)*100&&page<=pages(source)&&Number.isSafeInteger(total)&&data.length<total;page++) {
        const next=await requestPage(page);
        if (!Array.isArray(next?.data)||next.data.length>100) throw Error("moonani_schema");
        data.push(...next.data);
      }
      body={data};
    } else body=await fetchPage(url);
    const result=moonani?await moonaniRows(body,now):iflow?iflowRows(body,now):
      city?await cityRows(body,now):gocoords?await gocoordsRows(body,now):rows(body,now);
    const received=moonani?body.data.length:iflow?body.items.length:city?body.pokemons.length:
      gocoords?body.rows.length:body.hundos.length+(body.spots??[]).length;
    const validated=result.hundos.length+result.spots.length;
    return {...result,httpStatus,contentType,received,validated,discarded:received-validated,
      collectedPages:attemptedPages,attemptedPages};
  } catch(error) {
    if (error instanceof Error) {error.httpStatus=httpStatus;error.contentType=contentType;error.attemptedPages=attemptedPages;}
    throw error;
  } finally {clearTimeout(timer);}
}

async function refresh(env) {
  const now=Date.now(), configs=configuredSources(env);
  if (!configs.length) return;
  if (configs.length>9 || configs.some(s=>!s || !/^[a-z][a-z0-9-]{0,39}$/.test(s.name) ||
      !Number.isSafeInteger(s.interval_s) || s.interval_s<interval ||
      !Number.isSafeInteger(pages(s)) || pages(s)<1 || pages(s)>maxPages(s) ||
      (s.min_iv_100!==undefined && (s.kind!=="iflow" || typeof s.min_iv_100!=="boolean"))) ||
      configs.reduce((sum,s)=>sum+pages(s),0)>MAX_UPSTREAM_REQUESTS ||
      new Set(configs.map(s=>s.name)).size!==configs.length) throw Error("invalid_config");
  const previous=hundoState(await env.FEED.get(stateKey,"json") || {},configs);
  async function poll(source) {
    const old=previous.entries?.find(x=>x.name===source.name && x.url===source.url);
    // Retry a legacy malformed/empty city response once after upgrading.
    // Never reset a refusal, redirect, rate limit or Retry-After deadline.
    const recover=source.kind==="city" && old?.adapter_v!==ADAPTER_VERSION &&
      ["invalid_json","empty_response"].includes(old?.reason) &&
      (old.httpStatus==null||old.httpStatus===200) && !(old.retryAt>now);
    if (old?.next>now && !recover) return old;
    const base={name:source.name,url:source.url,adapter_v:ADAPTER_VERSION,next:now+source.interval_s*1000,lastAttempt:now};
    try { return {...base,...await collect(source,now),updated:now,status:"online",failures:0,reason:null,retryAt:null}; }
    catch(error) {
      console.warn("PGS upstream unavailable",source.name);
      const failures=Math.min((old?.failures||0)+1,8);
      const reason=["invalid_feed","source_url","city_schema","iflow_schema","moonani_schema","gocoords_schema","upstream_http","size","empty_response","invalid_encoding"].includes(error.message)
        ? error.message : (error.name==="SyntaxError"?"invalid_json":error.name==="AbortError"?"timeout":error.name==="TypeError"?"connection_error":"runtime_"+String(error.name).slice(0,24));
      const http=error.httpStatus || null;
      const restricted=[401,403,429].includes(http)||(http>=300&&http<400);
      const backoff=restricted?interval*1000*2**failures:Math.min(MAX_BACKOFF_MS,source.interval_s*1000*2**failures);
      const retryAt=Number.isFinite(error.retryAt)?error.retryAt:null;
      return {...old,...base,status:"offline",httpStatus:http,contentType:error.contentType || null,
        reason,failures,retryAt,attemptedPages:error.attemptedPages ?? 0,
        next:Math.max(base.next,now+backoff,http===429?now+1800000:0,retryAt||0)};
    }
  }
  // Keep simultaneous upstream connections bounded; preserve config order for dedup.
  const entries=[];
  for(let i=0;i<configs.length;i+=4) entries.push(...await Promise.all(configs.slice(i,i+4).map(poll)));
  const history=[...(previous.history || []),{time:now,online:entries.filter(e=>e.status==="online").map(e=>e.name)}].slice(-288);
  if (previous.entries?.some(e=>e.updated)) await env.FEED.put("pgs-feed-backup-v1",JSON.stringify(previous));
  await env.FEED.put(stateKey,JSON.stringify({entries,time:now,history}));
}

export function feed(state,now) {
  const hundos=new Map(), spots=[], nearby=new Map(), sources=Object.create(null);
  const radians=Math.PI/180;
  // Revalidate cached compact rows too; older snapshots must not bypass expiry,
  // coordinate or category checks. Preserve the real last-success timestamp.
  const entries=(state.entries || []).filter(hundoOnly).map(s=>{
    const clean=rows({v:1,fetched_ms:now,hundos:s.hundos || [],spots:s.spots || []},now);
    return {...s,...clean};
  });
  function register(row) {
    const group=nearby.get(row[1]) || [];
    group.push(row); nearby.set(row[1],group);
  }
  for (const s of entries) {
    const name=providerName(s);
    const count=sources[name]={active:0,unique:0,status:s.status,http_status:s.httpStatus || null};
    for (const row of s.hundos || []) {
      if (row[5]<now+60000) continue;
      count.active++;
      if (!hundos.has(row[0])) { hundos.set(row[0],row); register(row); count.unique++; }
    }
  }
  for (const s of entries) for (const row of s.spots || []) {
    if (row[5]<now+60000) continue;
    sources[providerName(s)].active++;
    const duplicate=(nearby.get(row[1]) || []).some(other=>{
      if (Math.abs(other[5]-row[5])>180000) return false;
      const a=Math.sin((row[3]-other[3])*radians/2)**2 +
        Math.cos(row[3]*radians)*Math.cos(other[3]*radians)*Math.sin((row[4]-other[4])*radians/2)**2;
      return a<=Math.sin(50/12742000)**2;
    });
    if (!duplicate) { register(row); spots.push(row); sources[providerName(s)].unique++; }
  }
  return {v:1,fetched_ms:Math.max(0,...entries.map(s=>s.updated || 0)),interval_s:interval,
    coordinate_precision:"exact",hundos:[...hundos.values()],spots,sources};
}

export default {
  async scheduled(event,env) {
    // Synthetic snapshots are exercised offline only. Save KV quota for production.
    await refresh(env);
  },
  async fetch(request,env,ctx) {
    const path=new URL(request.url).pathname;
    // Reject removed routes before consulting a possibly stale edge cache.
    if (path!=="/admin" && !publicPaths.has(path)) return new Response(null,{status:404});
    if (env.PUBLIC_LIMIT && !(await env.PUBLIC_LIMIT.limit({key:path==="/admin"?"admin":"public"})).success)
      return new Response(null,{status:429,headers:{"Retry-After":"60","Cache-Control":"no-store"}});
    if (path==="/admin") return admin(request,env);
    const cache=ctx && globalThis.caches?.default;
    const key=new Request(new URL(path,request.url).href);
    if (cache && request.method==="GET") {const hit=await cache.match(key); if (hit) return hit;}
    const response=await readFeed(request,env);
    if (cache && request.method==="GET" && response.ok) ctx.waitUntil(cache.put(key,response.clone()));
    return response;
  }
};

function detailStatus(entry,active) {
  if (!entry) return "pending";
  if (entry.status==="online") return active>0?"online_with_results":"online_zero_hundos";
  if (entry.httpStatus===429) return "rate_limited";
  if ([401,403].includes(entry.httpStatus)) return "access_denied";
  if (entry.httpStatus>=300 && entry.httpStatus<400) return "redirected";
  if (["invalid_json","invalid_feed","city_schema","iflow_schema","moonani_schema","gocoords_schema","size","empty_response","invalid_encoding"].includes(entry.reason)) return "invalid_response";
  if (entry.reason==="source_url") return "invalid_configuration";
  if (entry.reason==="timeout" || !entry.httpStatus) return "offline_connection";
  return "offline_upstream";
}

async function readFeed(request,env) {
    const path=new URL(request.url).pathname;
    const catalog=path==="/sources.json";
    const health=path==="/status.json";
    if (!publicPaths.has(path)) return new Response(null,{status:404});
    if (!["GET","HEAD"].includes(request.method)) return new Response(null,{status:405,headers:{Allow:"GET, HEAD"}});
    const configs=configuredSources(env);
    const state=hundoState(await env.FEED.get(stateKey,"json") || await env.FEED.get("pgs-feed-backup-v1","json") || {},configs);
    if (catalog) {
      const byProvider=new Map();
      for (const s of state?.entries || []) {
        const provider=providerName(s);
        const item=byProvider.get(provider) || {provider,status:"IMPLEMENTADA",categories:[]};
        const data=[...(s.hundos || []),...(s.spots || [])];
        if (s.status==="online" && data.some(r=>r[5]>Date.now())) item.status="OPERACIONAL CONFIRMADA";
        else if (item.status!=="OPERACIONAL CONFIRMADA") {
          const detail=detailStatus(s,0);
          item.status=({"online_zero_hundos":"ONLINE SEM HUNDOS","access_denied":"ACESSO RECUSADO",
            "rate_limited":"LIMITE DE CONSULTAS","invalid_response":"RESPOSTA INVÁLIDA",
            "offline_connection":"FALHA DE CONEXÃO","redirected":"REDIRECIONADO",
            "invalid_configuration":"CONFIGURAÇÃO INVÁLIDA","offline_upstream":"FALHA NO PROVEDOR"})[detail] || "IMPLEMENTADA";
        }
        item.categories.push("hundos"); byProvider.set(provider,item);
      }
      for (const provider of ["pogocoordinates","livepokemap"]) byProvider.set(provider,{provider,status:"REQUER AUTENTICAÇÃO"});
      for (const provider of ["pgsharp-free-100iv","pgsharp-standard","rocketmap-instance"]) byProvider.set(provider,{provider,status:"AGUARDANDO CONTRATO"});
      const data={time:state?.time || null,providers:[...byProvider.values()]};
      return new Response(request.method==="HEAD"?null:JSON.stringify(data),{headers:{"Content-Type":"application/json","Cache-Control":"public, max-age=15"}});
    }
    if (health) {
      const now=Date.now(), counts=feed(state,now).sources;
      const status={time:state?.time || null,history:state?.history || [],connections:configs.map(source=>{
        const e=(state.entries || []).find(entry=>sourceKey(entry)===sourceKey(source));
        const active=counts[providerName(source)]?.active || 0;
        return {provider:providerName(source),category:"hundos",status:e?.status || "pending",
          detail_status:detailStatus(e,active),last_attempt:e?.lastAttempt || null,last_success:e?.updated || null,
          next_attempt:e?.next || null,failures:e?.failures || 0,http_status:e?.httpStatus || null,
          content_type:e?.contentType || null,reason:e?.reason || null,active,
          received:e?.received ?? null,validated:e?.validated ?? null,discarded:e?.discarded ?? null,
          collected_pages:e?.collectedPages ?? null,attempted_pages:e?.attemptedPages ?? null};
      })};
      return new Response(request.method==="HEAD"?null:JSON.stringify(status),{headers:{"Content-Type":"application/json","Cache-Control":"public, max-age=15"}});
    }
    if (!state?.entries?.some(s=>s.updated)) return new Response(null,{status:503,headers:{"Retry-After":"300","Cache-Control":"no-store"}});
    const body=feed(state,Date.now());
    return new Response(request.method==="HEAD"?null:JSON.stringify(body),{headers:{
      "Content-Type":"application/json; charset=utf-8","Cache-Control":"public, max-age=15"}});
}

async function admin(request,env) {
  const headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"};
  if (!env.ADMIN_PASSWORD) return new Response(null,{status:503,headers});
  if (request.method!=="GET") return new Response(null,{status:405,headers});
  const encoder=new TextEncoder();
  const digest=s=>crypto.subtle.digest("SHA-256",encoder.encode(s));
  const expected="Basic "+btoa("admin:"+env.ADMIN_PASSWORD);
  const [a,b]=await Promise.all([digest(request.headers.get("Authorization") || ""),digest(expected)]);
  if (!crypto.subtle.timingSafeEqual(a,b)) return new Response(null,{status:401,headers:{...headers,"WWW-Authenticate":'Basic realm="PGS Hundo Feed"'}});
  const state=hundoState(await env.FEED.get(stateKey,"json") || {},configuredSources(env));
  const summary=feed(state,Date.now());
  const report={updated:state?.time || null,hundos:summary.hundos.length,spots:summary.spots.length,
    by_source:summary.sources,history:state?.history || []};
  return new Response(JSON.stringify(report,null,2),{headers:{...headers,"Content-Type":"application/json; charset=utf-8"}});
}
