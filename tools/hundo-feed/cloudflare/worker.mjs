// PGS Hundo Feed: only authorized, exact-coordinate wild 100% IV spawns.
const interval = 300;
const stateKey = "pgs-feed-v1";
const backupKey = "pgs-feed-backup-v1";
const publicPaths=new Set(["/hundos.json","/sources.json","/status.json"]);
const providerName=s=>s.name==="iflowgo-pokemon"?"iflowgo":s.name;
const sourceKey=s=>s.name+" "+s.url;
// Twelve seconds matches the previous operator setting and is enough for a
// healthy upstream; the 256 KiB cap keeps memory bounded on Workers Free.
const timeoutMs=12000, maxBodyBytes=262144;
// Consecutive failures back off to at most 30 minutes. The old 2^steps curve
// reached more than 21 hours, which effectively silenced a source after a
// transient fault. Retry-After is honoured above this floor.
const maxFailures=6, backoffCapMs=1800*1000;
const ADAPTER_VERSION=2;
const MAX_MOONANI_PAGES=3, MOONANI_PAGE_SIZE=100;
const RATE_LIMIT_FLOOR_MS=1800*1000;
// iFlowGo exposes an IV index filter (min_iv=100) and paginates at 25 rows.
// Fetching every page is bounded here and stays well below provider quotas.
const maxIflowPages=5;
// Filter legacy category configuration as well as persisted KV snapshots. A removed
// raid source must not be queried even if dashboard variables still contain it.
const hundoOnly=s=>s && s.name!=="iflowgo-raids" && [undefined,"hundos","pokemon"].includes(s.category);
function configuredSources(env) {
  const configs=JSON.parse(env.SOURCES || "[]");
  if (!Array.isArray(configs)) throw Error("invalid_config");
  return configs.filter(hundoOnly);
}
function hundoState(state,configs,now=Date.now()) {
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
// Unambiguous numeric normalization: accepts numbers and trimmed numeric
// strings only; everything else becomes NaN and is rejected downstream.
const num=v=>typeof v==="number"?v:(typeof v==="string"&&/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(v.trim())?Number(v.trim()):NaN);

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
// Counts for diagnostics only. Mirrors rows() so operators see how many raw
// records arrived, how many were validated and how many were discarded.
function counted(body, now) {
  const clean=rows(body,now);
  const received=(Array.isArray(body?.hundos)?body.hundos.length:0)+(Array.isArray(body?.spots)?body.spots.length:0);
  const validated=clean.hundos.length+clean.spots.length;
  return {...clean,received,validated,discarded:Math.max(0,received-validated)};
}

const cityHosts=new Set(["nycpokemap.com","sgpokemap.com","londonpogomap.com","sydneypogomap.com","vanpokemap.com"]);
// Shared 15/15/15 spawn -> compact spot conversion for city instances and
// Moonani. `received` is the raw record count for diagnostics.
async function spotsFromSpawns(spawns,received,now) {
  const spots=[];
  for (const p of spawns) {
    if (!p || ![p.attack,p.defence,p.stamina].every(v=>num(v)===15)) continue;
    const lat=num(p.lat), lon=num(p.lng), dex=num(p.pokemon_id);
    const desp=num(p.despawn);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(desp) || desp<=0 || !Number.isSafeInteger(dex) || dex<=0) continue;
    const end=desp*1000;
    const seed=[dex,lat.toFixed(5),lon.toFixed(5),Math.floor(end/60000)].join(":");
    const hash=new Uint8Array(await crypto.subtle.digest("SHA-1",new TextEncoder().encode(seed)));
    const key="s"+Array.from(hash.slice(0,8),v=>v.toString(16).padStart(2,"0")).join("");
    const form=num(p.form ?? 0), cp=num(p.cp ?? 0), level=num(p.level ?? 0);
    spots.push([key,dex,Number.isSafeInteger(form)&&form>=0?form:0,lat,lon,end,
      Number.isSafeInteger(cp)&&cp>=0?cp:0,Number.isFinite(level)&&level>=0&&level<=55?level:0]);
  }
  const clean=rows({v:1,fetched_ms:now,hundos:[],spots},now);
  return {...clean,received,validated:clean.spots.length,discarded:Math.max(0,received-clean.spots.length)};
}
export async function cityRows(body,now) {
  if (!Array.isArray(body?.pokemons)) throw Error("city_schema");
  // The upstream contract sends numeric IVs and unix-seconds expiry. Numeric
  // strings are accepted only when unambiguous (see num()).
  const spawns=body.pokemons.filter(p=>p && (p.coordinate_precision==null || p.coordinate_precision==="exact") && (p.iv_percent==null || num(p.iv_percent)===100) && (p.defense==null || num(p.defense)===15)).map(p=>({attack:p?.attack,defence:p?.defence??p?.defense,stamina:p?.stamina,
    pokemon_id:p?.pokemon_id,lat:p?.lat,lng:p?.lng,despawn:p?.despawn,form:p?.form,cp:p?.cp,level:p?.level}));
  return spotsFromSpawns(spawns,body.pokemons.length,now);
}

export function iflowRows(body,now) {
  if (!Array.isArray(body?.items)) throw Error("iflow_schema");
  const spots=[];
  for (const p of body.items) {
    if (!p || (p.coordinate_precision!=null && p.coordinate_precision!=="exact") || ![p.attack_iv,p.defense_iv,p.stamina_iv].every(v=>num(v)===15) ||
        (p.percent_iv!=null && num(p.percent_iv)!==100)) continue;
    const end=Date.parse(p.expires_at);
    const idnum=num(p.pokemon_id);
    if (!Number.isFinite(end) || end<now+60000 || typeof p.id!=="string" || !/^\d{1,20}$/.test(p.id) ||
        !Number.isSafeInteger(idnum) || idnum<=0 ||
        !Number.isFinite(num(p.lat)) || Math.abs(num(p.lat))>90 || !Number.isFinite(num(p.lon)) || Math.abs(num(p.lon))>180 ||
        (num(p.lat)===0 && num(p.lon)===0)) continue;
    const id=BigInt(p.id);
    if (id===0n || id>=(1n<<64n)) continue;
    // The provider ID is not asserted to be a game encounter ID. Keep the
    // existing spot representation and use zero only for unknown optional fields.
    const form=Number.isSafeInteger(num(p.form)) && num(p.form)>=0?num(p.form):0;
    const cp=Number.isSafeInteger(num(p.cp)) && num(p.cp)>=0?num(p.cp):0;
    const level=Number.isFinite(num(p.level)) && num(p.level)>=0 && num(p.level)<=55?num(p.level):0;
    spots.push(["s"+id.toString(16).padStart(16,"0"),idnum,form,num(p.lat),num(p.lon),end,cp,level]);
  }
  const clean=rows({v:1,fetched_ms:now,hundos:[],spots},now);
  return {...clean,received:body.items.length,validated:clean.spots.length,discarded:Math.max(0,body.items.length-clean.spots.length)};
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
  return spotsFromSpawns(pokemons,body.data.length,now);
}

// GOCoords (https://gocoords.com/api/spawns) publishes a free public hundo feed
// (schema_version 2, max 10 rows, iv=100 == 15/15/15). Rows carrying a game
// encounter_id go to `hundos`; provider-keyed rows without one become
// synthetic-id `spots` (never invent encounter ids). Dormant until the
// operator adds the SOURCES entry and attests permission, like PGSharp.
export async function gocoordsRows(body,now) {
  if (!body || Number(body.schema_version)!==2 || !Array.isArray(body.rows)) throw Error("gocoords_schema");
  const generated=Date.parse(body.generated_at);
  if (!Number.isFinite(generated) || generated<now-600000 || generated>now+60000) throw Error("invalid_feed");
  if (body.rows.length>10 || body.count!==body.rows.length) throw Error("gocoords_schema");
  const hundos=[], spots=[];
  for (const p of body.rows) {
    if (!p) continue;
    if ((p.coordinate_precision!=null && p.coordinate_precision!=="exact") || (p.raw_iv!=null && p.raw_iv!=="15/15/15") || num(p.iv)!==100) continue; // IV 45/45 == 15/15/15
    const attrs=[p.atk_iv,p.def_iv,p.sta_iv].map(num);
    if ([p.atk_iv,p.def_iv,p.sta_iv].some(v=>v!=null) && !attrs.every(v=>v===15)) continue;
    const end=Date.parse(p.expires_at_utc), lat=num(p.lat), lon=num(p.lon), dex=num(p.pokemon_id);
    if (!Number.isFinite(end) || end<now+60000 || !Number.isFinite(lat) || Math.abs(lat)>90 ||
        !Number.isFinite(lon) || Math.abs(lon)>180 || (lat===0 && lon===0) ||
        !Number.isSafeInteger(dex) || dex<=0) continue;
    const form=Number.isSafeInteger(num(p.form))&&num(p.form)>=0?num(p.form):0;
    const cp=Number.isSafeInteger(num(p.cp))&&num(p.cp)>=0?num(p.cp):0;
    const level=Number.isFinite(num(p.lvl))&&num(p.lvl)>=0&&num(p.lvl)<=55?num(p.lvl):0;
    const enc=encounter(p.encounter_id);
    if (enc && enc!=="0") { hundos.push([enc,dex,form,lat,lon,end,cp,level]); continue; }
    const seed="gocoords:"+(typeof p.provider_unique_id==="string"&&p.provider_unique_id?p.provider_unique_id:[dex,lat.toFixed(5),lon.toFixed(5),Math.floor(end/60000)].join(":"));
    const hash=new Uint8Array(await crypto.subtle.digest("SHA-1",new TextEncoder().encode(seed)));
    const key="s"+Array.from(hash.slice(0,8),v=>v.toString(16).padStart(2,"0")).join("");
    spots.push([key,dex,form,lat,lon,end,cp,level]);
  }
  const clean=rows({v:1,fetched_ms:now,hundos,spots},now);
  return {...clean,received:body.rows.length,validated:clean.hundos.length+clean.spots.length,
    discarded:Math.max(0,body.rows.length-clean.hundos.length-clean.spots.length)};
}

// Shared bounded read + JSON decode. Strips a UTF-8 BOM, reports the upstream
// Content-Type for diagnostics and classifies hard failures precisely.
async function fetchJson(url,init,now,remaining) {
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),remaining);
  let observedStatus=null;
  try {
    const response=await fetch(url,{redirect:"manual",signal:controller.signal,...init});
    observedStatus=response.status;
    const contentType=(response.headers.get("content-type")||"").split(";")[0].trim().toLowerCase()||null;
    if (!response.ok) {
      const error = Error("upstream_http");
      error.httpStatus=response.status; error.contentType=contentType;
      const retry = response.headers.get("Retry-After");
      if (retry) error.retryAt = /^\d+$/.test(retry) ? Date.now() + Number(retry)*1000 : Date.parse(retry);
      throw error;
    }
    if (!response.body) throw Object.assign(Error("empty_response"),{contentType});
    const reader=response.body.getReader(), decoder=new TextDecoder("utf-8",{fatal:true});
    let bytes=0, data="";
    while (true) {
      const {done,value}=await reader.read();
      if (done) break;
      bytes+=value.length;
      if (bytes>maxBodyBytes) { await reader.cancel(); const e=Error("size"); e.contentType=contentType; throw e; }
      try { data+=decoder.decode(value,{stream:true}); } catch { throw Object.assign(Error("invalid_encoding"),{contentType}); }
    }
    try { data+=decoder.decode(); } catch { throw Object.assign(Error("invalid_encoding"),{contentType}); }
    // A leading BOM (EF BB BF) decodes to U+FEFF and breaks JSON.parse; remove it.
    if (data.charCodeAt(0)===0xFEFF) data=data.slice(1);
    data=data.trim();
    if (!data) throw Object.assign(Error("empty_response"),{contentType});
    try { return {body:JSON.parse(data),contentType}; }
    catch (error) { throw Object.assign(error,{contentType,message:"invalid_json"}); }
  } catch (error) {
    if (error.httpStatus==null && error.contentType===undefined && error.name==="AbortError") error.reason="timeout";
    error.observedStatus=observedStatus;
    if (error.contentType===undefined) error.contentType=null;
    throw error;
  } finally { clearTimeout(timer); }
}

async function collect(source, now, metrics) {
  const deadline=Date.now()+timeoutMs;
  let partialError;
  async function page(url,init) {
    metrics.attemptedPages++;
    const remaining=deadline-Date.now();
    if (remaining<=0) throw Error("timeout");
    const result=await fetchJson(url,init,now,remaining);
    metrics.collectedPages++;
    return result;
  }
  const url = new URL(source.url);
  const city=source.kind==="city" && cityHosts.has(url.hostname) && url.pathname==="/query2.php";
  const moonani=source.kind==="moonani" && url.href==="https://moonani.com/PokeList/ajax.php";
  const iflow=source.kind==="iflow" && url.hostname==="pokecoords.iflowgo.com" &&
    source.category==="pokemon" && url.pathname==="/iflowgopokecoords/api/v1/pokemon-search";
  const gocoords=source.kind==="gocoords" && url.href==="https://gocoords.com/api/spawns";
  const poke100=source.kind==="poke100iv" && url.href==="https://poke100iv.com/api/pokemon";
  const compact=(!source.kind || source.kind==="compact") && url.pathname.endsWith("/hundos.json");
  if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash ||
      !hundoOnly(source) || (!moonani && !iflow && !city && !compact && !gocoords && !poke100)) throw Error("source_url");
  // iFlowGo officially answers the provider's IV index when min_iv=100 is set;
  // each page is still verified row-by-row before persistence.
  if (poke100) url.search=new URLSearchParams({minLevel:"0",limit:"101",latMin:"40.6",latMax:"40.9",
    lonMin:"-74.1",lonMax:"-73.8",ivFilters:"15-15-15"});
  if (iflow) url.search=new URLSearchParams({page:"1",min_iv:"100"}).toString();
  // The city query contract expects unix seconds in `time`; the server meta
  // block reports seconds as well. mons covers species 1..1025 with minIV=100.
  if (city) url.search=new URLSearchParams({mons:Array.from({length:1025},(_,i)=>i+1).join(","),minIV:"100",since:"0",time:String(Math.floor(now/1000))}).toString();
  if (moonani) {
    // The IV100 table holds roughly 203 15/15/15 rows while the site frontend
    // pages at 100 rows per XHR. Follow the same contract, bounded to 3 pages.
    const u = new URL(url.href); u.search="page=pokemon&action=load";
    const mHeaders={Accept:"application/json","User-Agent":"PGS-Hundo-Feed/1.1 (+https://github.com/LucianoToscano/PGS)",
      "Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest",Referer:"https://moonani.com/PokeList/"};
    const postPage=(draw,start)=>page(u,{method:"POST",
      body:`draw=${draw}&start=${start}&length=${MOONANI_PAGE_SIZE}&pokemons=&iv=100&pvp=0`,headers:mHeaders},now);
    const first=await postPage(1,0);
    if (!Array.isArray(first.body?.data)) throw Object.assign(Error("moonani_schema"),{contentType:first.contentType});
    const all=[...first.body.data];
    const total=Number.isSafeInteger(Number(first.body?.recordsFiltered)) ? Number(first.body.recordsFiltered)
      : (Number.isSafeInteger(Number(first.body?.recordsTotal)) ? Number(first.body.recordsTotal) : null);
    for (let page=2; page<=MAX_MOONANI_PAGES; page++) {
      if (all.length < MOONANI_PAGE_SIZE) break;
      if (total!=null && all.length>=total) break;
      try {
        const next=await postPage(page,(page-1)*MOONANI_PAGE_SIZE);
        if (!Array.isArray(next.body?.data) || !next.body.data.length) break;
        all.push(...next.body.data);
        if (next.body.data.length < MOONANI_PAGE_SIZE) break;
      } catch (error) { partialError=error; break; }
    }
    return {partialError,...await moonaniRows({data:all},now),contentType:first.contentType};
  }
  // Honest AJAX-contract headers for the map sites whose own frontend queries these
  // endpoints as XHR JSON. Identity stays truthful (no browser fingerprint, no cookies);
  // the city instances serve their own public map data. If an instance requires more
  // than the contract headers, its status will read invalid_response with content_type.
  const acceptAjax="application/json, text/javascript, */*; q=0.01";
  const headers={"User-Agent":"PGS-Hundo-Feed/1.1 (+https://github.com/LucianoToscano/PGS)",
    ...(city?{Accept:acceptAjax,"X-Requested-With":"XMLHttpRequest",Referer:`https://${url.hostname}/`}
      :{Accept:"application/json"})};
  const init={method:"GET",headers};
  if (iflow) {
    const first=await page(url,init);
    if (!Array.isArray(first.body?.items)) throw Error("iflow_schema");
    const items=[...(Array.isArray(first.body?.items)?first.body.items:[])];
    const pages=Number.isSafeInteger(first.body?.total_pages)?Math.min(Math.max(first.body.total_pages,1),maxIflowPages):1;
    for (let n=2;n<=pages;n++) {
      const next=new URL(url);
      next.searchParams.set("page",String(n));
      try {
        const response=await page(next,init);
        if (!Array.isArray(response.body?.items)) throw Error("iflow_schema");
        items.push(...response.body.items);
      } catch (error) { partialError=error; break; }
    }
    const seen=new Set(), unique=[];
    for (const item of items) { const key=item&&typeof item.id==="string"?item.id:null; if (key && seen.has(key)) continue; if (key) seen.add(key); unique.push(item); }
    const result=iflowRows({items:unique},now);
    // received counts raw rows including any cross-page duplicates.
    return {partialError,...result,received:items.length,discarded:Math.max(0,items.length-result.validated),contentType:first.contentType};
  }
  const {body,contentType}=await page(url,init);
  if (poke100) {
    if (body?.success!==true || !Array.isArray(body.data) || body.data.length>101) throw Error("invalid_feed");
    const spawns=body.data.filter(p=>p && num(p.iv)===100 && (p.coordinate_precision??"exact")==="exact")
      .map(p=>({attack:p.atk,defence:p.def,stamina:p.sta,pokemon_id:p.pokemon_id,lat:p.latitude,
        lng:p.longitude,despawn:Date.parse(p.expires_at)/1000,cp:p.cp,level:p.level,form:p.form}));
    return {...await spotsFromSpawns(spawns,body.data.length,now),contentType};
  }
  if (gocoords) return {...await gocoordsRows(body,now),contentType};
  if (moonani) return {...await moonaniRows(body,now),contentType};
  if (city) return {...await cityRows(body,now),contentType};
  const clean=counted(body,now);
  return {...clean,contentType};
}

// Granular outcome for status.json / sources.json. Never throws.
const STATE_LABELS={pending:"Aguardando primeira coleta",online_with_results:"Online com resultados",online_without_hundos:"Online sem Hundos",
  offline_connection:"Offline por falha de conexão",invalid_response:"Resposta inválida",access_denied:"Acesso recusado",
  rate_limited:"Limite de consultas",upstream_http:"Erro HTTP do fornecedor",offline_error:"Offline"};
function stateOf(entry) {
  if (!entry) return "offline_error";
  // Legacy snapshots lack the counters; derive a best-effort count from rows.
  const validated=Number.isSafeInteger(entry.validated) ? entry.validated
    : (entry.hundos?.length||0)+(entry.spots?.length||0);
  if (entry.status==="online") return validated>0 ? "online_with_results" : "online_without_hundos";
  if (entry.httpStatus===401 || entry.httpStatus===403) return "access_denied";
  if (entry.httpStatus===429) return "rate_limited";
  if (entry.reason==="timeout" || entry.reason==="connection_error") return "offline_connection";
  if (["invalid_json","empty_response","invalid_encoding","invalid_content_type","invalid_feed","size",
       "city_schema","iflow_schema","moonani_schema","gocoords_schema","source_url","invalid_config"].includes(entry.reason))
    return "invalid_response";
  if (entry.reason==="upstream_http") return "upstream_http";
  return "offline_error";
}

async function refresh(env) {
  const now=Date.now(), configs=configuredSources(env);
  if (!configs.length) return;
  if (configs.length>10 || configs.some(s=>!s || !/^[a-z][a-z0-9-]{0,39}$/.test(s.name) ||
      !Number.isSafeInteger(s.interval_s) || s.interval_s<interval) ||
      new Set(configs.map(s=>s.name)).size!==configs.length) throw Error("invalid_config");
  const previous=hundoState(await env.FEED.get(stateKey,"json") || {},configs,now);
  const budget=Number(env.MAX_UPSTREAM_REQUESTS ?? 16);
  const required=configs.reduce((n,s)=>n+(s.kind==="iflow"?maxIflowPages:s.kind==="moonani"?MAX_MOONANI_PAGES:1),0);
  if (!Number.isSafeInteger(budget)||budget>16||required>budget) throw Error("invalid_config");
  async function poll(source) {
    const old=previous.entries?.find(x=>x.name===source.name && x.url===source.url);
    const recover=old?.adapter_v!==ADAPTER_VERSION && old?.status==="offline" &&
      ["empty_response","invalid_json","connection_error","timeout"].includes(old.reason) &&
      (!old.httpStatus || old.httpStatus===200) && !old.retryAt;
    if (old?.next>now && !recover) return old;
    const metrics={attemptedPages:0,collectedPages:0};
    let partial;
    const base={name:source.name,url:source.url,adapter_v:ADAPTER_VERSION,lastAttempt:now,next:now+source.interval_s*1000};
    try {
      const {partialError,...result}=await collect(source,now,metrics);
      if (partialError) {
        const cached=rows({v:1,fetched_ms:now,hundos:[...result.hundos,...(old?.hundos??[])],
          spots:[...result.spots,...(old?.spots??[])]},now);
        partial={...result,...cached};
        throw partialError;
      }
      return {...base,...metrics,...result,updated:now,status:"online",failures:0,reason:null,httpStatus:200};
    }
    catch(error) {
      console.warn("PGS upstream unavailable",source.name);
      const failures=Math.min((old?.failures||0)+1,maxFailures);
      const reason=classifyError(error);
      return {...(old||{}),...base,...partial,...metrics,updated:partial?now:old?.updated,retryAt:error.retryAt??null,status:"offline",httpStatus:error.httpStatus ?? error.observedStatus ?? null,contentType:error.contentType ?? old?.contentType ?? null,
        reason,failures,
        next:Math.max(base.next,now+Math.min(backoffCapMs,interval*1000*2**failures),
          error.httpStatus===429?now+RATE_LIMIT_FLOOR_MS:0,Number.isFinite(error.retryAt)?error.retryAt:0)};
    }
  }
  const entries=[];
  for (let i=0;i<configs.length;i+=4) entries.push(...await Promise.all(configs.slice(i,i+4).map(poll)));
  const history=[...(previous.history || []),{time:now,online:entries.filter(e=>e.status==="online").map(e=>e.name)}].slice(-288);
  if (previous.entries?.some(e=>e.updated)) await env.FEED.put(backupKey,JSON.stringify(previous));
  await env.FEED.put(stateKey,JSON.stringify({entries:entries.map(e=>({...e})),time:now,history}));
}
function classifyError(error) {
  if (error?.httpStatus) return "upstream_http";
  const name=error?.name, message=error?.message;
  if (name==="AbortError" || message==="timeout") return "timeout";
  if (name==="SyntaxError" || message==="invalid_json") return "invalid_json";
  if (name==="TypeError" || message==="connection_error") return "connection_error";
  if (["invalid_feed","source_url","city_schema","iflow_schema","moonani_schema","gocoords_schema","size","empty_response","invalid_encoding"].includes(message)) return message;
  return "runtime_"+String(name||"Error").slice(0,24);
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

async function readFeed(request,env) {
    const path=new URL(request.url).pathname;
    const catalog=path==="/sources.json";
    const health=path==="/status.json";
    if (!publicPaths.has(path)) return new Response(null,{status:404});
    if (!["GET","HEAD"].includes(request.method)) return new Response(null,{status:405,headers:{Allow:"GET, HEAD"}});
    const configs=configuredSources(env);
    const state=hundoState(await env.FEED.get(stateKey,"json") || await env.FEED.get(backupKey,"json") || {},configs);
    if (catalog) {
      const byProvider=new Map();
      for (const s of state?.entries || []) {
        const provider=providerName(s);
        const item=byProvider.get(provider) || {provider,status:"IMPLEMENTADA",categories:[]};
        const data=[...(s.hundos || []),...(s.spots || [])];
        const live=s.status==="online" && data.some(r=>r[5]>Date.now());
        if (live) item.status="OPERACIONAL CONFIRMADA";
        else if (s.httpStatus===401 || s.httpStatus===403) item.status="ACESSO RECUSADO";
        else if (s.httpStatus===429) item.status="LIMITE DE CONSULTAS";
        else if (s.status==="online") item.status="ONLINE SEM HUNDOS";
        else if (stateOf(s)==="invalid_response") item.status="RESPOSTA INVÁLIDA";
        else if (item.status!=="OPERACIONAL CONFIRMADA") item.status="OFFLINE";
        item.categories.push("hundos"); byProvider.set(provider,item);
      }
      for (const provider of ["pogocoordinates","livepokemap"]) byProvider.set(provider,{provider,status:"REQUER AUTENTICAÇÃO"});
      for (const provider of ["pgsharp-free-100iv","pgsharp-standard","rocketmap-instance","gocoords"])
        if (!byProvider.has(provider)) byProvider.set(provider,{provider,status:"AGUARDANDO AUTORIZAÇÃO DO FORNECEDOR"});
      const data={time:state?.time || null,providers:[...byProvider.values()]};
      return new Response(request.method==="HEAD"?null:JSON.stringify(data),{headers:{"Content-Type":"application/json","Cache-Control":"public, max-age=15"}});
    }
    if (health) {
      const summary=Object.create(null);
      const counts=feed(state,Date.now()).sources;
      const connections=configs.map(source=>{
        const e=state.entries.find(item=>sourceKey(item)===sourceKey(source)) || {...source,status:"pending"};
        const active=counts[providerName(e)]?.active??0;
        const stateName=e.status==="pending"?"pending":e.status==="online"?
          (active?"online_with_results":"online_without_hundos"):stateOf(e);
        const detail=stateName==="invalid_response"?e.reason:stateName;
        const labels={empty_response:"Resposta vazia",invalid_json:"JSON inválido",source_url:"Configuração inválida",invalid_config:"Configuração inválida"};
        summary[stateName]=(summary[stateName]||0)+1;
        return {provider:providerName(e),category:"hundos",
          active:counts[providerName(e)]?.active??0,unique:counts[providerName(e)]?.unique??0,
          detail_status:detail,last_attempt:e.lastAttempt??null,
          next_attempt:e.next??null,attempted_pages:e.attemptedPages??null,collected_pages:e.collectedPages??null,
          status:e.status,state:stateName,state_label:labels[detail]||STATE_LABELS[stateName]||"Desconhecido",
          last_success:e.updated || null,next_retry:Number.isSafeInteger(e.next)?e.next:null,
          http_status:e.httpStatus || null,reason:e.reason || null,content_type:e.contentType ?? null,
          received:Number.isSafeInteger(e.received)?e.received:null,
          validated:Number.isSafeInteger(e.validated)?e.validated:null,
          discarded:Number.isSafeInteger(e.discarded)?e.discarded:null,
          failures:Number.isSafeInteger(e.failures)?e.failures:0};
      });
      const status={time:state?.time || null,summary,connections,history:state?.history || []};
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
