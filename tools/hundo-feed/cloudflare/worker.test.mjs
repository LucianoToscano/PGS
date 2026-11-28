import test from "node:test";
import assert from "node:assert/strict";
import worker,{rows,feed,iflowRows,cityRows,gocoordsRows} from "./worker.mjs";
const now=Date.now();
const row=["18446744073709551615",25,0,-3.1234567,38.7654321,now+300000,10,1];
const spot=["s0123456789abcdef",...row.slice(1)];
const payload={v:1,fetched_ms:now,hundos:[row,row],spots:[spot]};
test("exact coordinates, aliases, approximate IDs and expiry",()=>{
  assert.deepEqual(rows(payload,now).hundos,[row]);
  assert.deepEqual(rows({...payload,approximate_encounters:["-1"]},now).hundos,[]);
  assert.deepEqual(rows({...payload,hundos:[[...row.slice(0,3),91,...row.slice(4)]]},now).hundos,[]);
  assert.deepEqual(rows(payload,now+250000).hundos,[]);
  assert.throws(()=>rows({...payload,fetched_ms:now-600001},now));
});
test("cross-source encounter and nearby spot deduplication",()=>{
  const entry={updated:now,status:"online",...rows(payload,now)};
  const result=feed({entries:[{name:"a",...entry},{name:"b",...entry}]},now);
  assert.deepEqual(result.hundos,[row]); assert.deepEqual(result.spots,[]);
  assert.equal(result.sources.a.unique,1); assert.equal(result.sources.b.unique,0);
});
test("empty configuration writes no simulation or production snapshot",async()=>{
  const db=new Map();
  const env={FEED:{put:(key,data)=>db.set(key,data),get:key=>JSON.parse(db.get(key)||"null")}};
  await worker.scheduled({scheduledTime:now},env);
  const get=path=>worker.fetch(new Request("https://example.org"+path),env);
  assert.equal(db.size,0);
  assert.equal((await get("/hundos.json")).status,503);
  for (const path of ["/pokemon.json","/raids.json","/simulation/hundos.json"])
    assert.equal((await get(path)).status,404);
});

const iflow={name:"iflowgo-pokemon",kind:"iflow",category:"pokemon",interval_s:600,
  url:"https://pokecoords.iflowgo.com/iflowgopokecoords/api/v1/pokemon-search"};
const raid={name:"iflowgo-raids",kind:"iflow",category:"raids",interval_s:600,
  url:"https://pokecoords.iflowgo.com/iflowgopokecoords/api/v1/nearby"};
const perfect={id:"1234",pokemon_id:25,lat:12.3456789,lon:0,expires_at:new Date(now+600000).toISOString(),
  attack_iv:15,defense_iv:15,stamina_iv:15,percent_iv:100,cp:10,level:1};
test("iFlowGo requires perfect IV components, exact valid coordinates and future expiry",()=>{
  const invalid=[
    {...perfect,id:"2",attack_iv:14},
    {...perfect,id:"3",stamina_iv:undefined},
    {...perfect,id:"4",percent_iv:99},
    {...perfect,id:"5",lat:null},
    {...perfect,id:"6",lat:91},
    {...perfect,id:"7",lat:0,lon:0},
    {...perfect,id:"8",expires_at:new Date(0).toISOString()},
    {...perfect,id:"0"},
    {...perfect,id:"9",lon:181}
  ];
  const result=iflowRows({items:[perfect,perfect,...invalid,{...perfect,id:"1235",lat:13,cp:undefined,level:undefined}]},now);
  assert.equal(result.spots.length,2);
  assert.equal(result.spots[0][3],perfect.lat);
  assert.deepEqual(result.spots[1].slice(6),[0,0]);
  assert.equal(result.hundos.length,0);
  assert.equal("records" in result,false);
});
test("production never queries raids, persists only hundos and disables old routes",async t=>{
  const calls=[];
  t.mock.method(globalThis,"fetch",async url=>{
    calls.push(String(url));
    return Response.json({items:[perfect,{...perfect,id:"2",attack_iv:14}]});
  });
  const db=new Map();
  const env={SOURCES:JSON.stringify([iflow,raid]),FEED:{put:(k,v)=>db.set(k,v),get:k=>JSON.parse(db.get(k)||"null")}};
  await worker.scheduled({scheduledTime:now},env);
  const read=path=>worker.fetch(new Request("https://example.org"+path),env);
  assert.equal(calls.length,1); assert.ok(calls[0].includes("/pokemon-search?"));
  assert.equal(db.has("pgs-simulation-v1"),false);
  const state=JSON.parse(db.get("pgs-feed-v1"));
  assert.equal(state.entries.length,1);
  assert.equal("records" in state.entries[0],false);
  const result=await (await read("/hundos.json")).json();
  assert.equal(result.spots.length,1);
  assert.equal(result.spots[0][3],perfect.lat);
  assert.equal(result.sources.iflowgo.unique,1);
  for (const path of ["/pokemon.json","/raids.json","/simulation/hundos.json"])
    assert.equal((await read(path)).status,404);
  const catalog=await (await read("/sources.json")).json();
  assert.deepEqual(catalog.providers.find(p=>p.provider==="iflowgo").categories,["hundos"]);
  // A legacy cached entry may have arbitrary-IV records and a separate raid
  // entry. A refresh must clean those even if no source is due for another poll.
  state.entries[0].records=[{id:"old",percent_iv:20}];
  state.entries.push({...raid,updated:now,status:"online",records:[{id:"raid"}],spots:[spot]});
  state.history.push({time:now,online:[iflow.name,raid.name]});
  db.set("pgs-feed-v1",JSON.stringify(state));
  await worker.scheduled({scheduledTime:now},env);
  for (const key of ["pgs-feed-v1","pgs-feed-backup-v1"]) {
    const snapshot=JSON.parse(db.get(key));
    assert.equal(snapshot.entries.length,1);
    assert.equal("records" in snapshot.entries[0],false);
    assert.equal(snapshot.history.some(h=>h.online.includes(raid.name)),false);
  }
  assert.equal(calls.length,1);
  env.SOURCES="[]"; assert.equal((await read("/hundos.json")).status,503);
});
test("legacy non-hundo categories and invalid cached coordinates cannot enter feed",()=>{
  const good={name:"a",updated:now,status:"online",hundos:[row],spots:[]};
  const result=feed({entries:[good,
    {...good,name:"iflowgo-raids",category:"raids",hundos:[["2",...row.slice(1)]]},
    {...good,name:"bad",hundos:[["3",25,0,0,0,now+300000,10,1],["4",25,0,91,0,now+300000,10,1]]}
  ]},now);
  assert.deepEqual(result.hundos,[row]);
  assert.equal(result.sources.bad.active,0);
  assert.equal("iflowgo-raids" in result.sources,false);
});

const cityDespawn=Math.floor((Date.now()+900000)/1000);
const cityPerfect={pokemon_id:358,lat:40.67196281,lng:-73.84379014,despawn:cityDespawn,
  cp:577,attack:15,defence:15,stamina:15,move1:263,move2:60,form:1592,level:9,weather:5};
const cityUrl="https://nycpokemap.com/query2.php";
const iflowSource={name:"iflowgo-pokemon",kind:"iflow",category:"pokemon",interval_s:600,
  url:"https://pokecoords.iflowgo.com/iflowgopokecoords/api/v1/pokemon-search"};
const citySource={name:"nycpokemap",kind:"city",interval_s:600,url:cityUrl};
function makeEnv(sources){ const db=new Map(); return {db,env:{SOURCES:JSON.stringify(sources),
  FEED:{put:(k,v)=>db.set(k,v),get:k=>JSON.parse(db.get(k)||"null")}}}; }

test("iFlowGo uses the provider IV index and paginates atomically",async t=>{
  const calls=[];
  const page=(n,items)=>({json:true,body:{source:"redis",scope:"global",total:120,page:n,page_size:25,
    candidate_count:120,candidate_pool_limited:false,candidate_source:"iv_index",total_pages:2,items}});
  const p=(id,over={})=>({id:String(id),pokemon_id:25,lat:12.3,lon:45.6,cp:100,level:5,
    percent_iv:100,attack_iv:15,defense_iv:15,stamina_iv:15,expires_at:new Date(Date.now()+600000).toISOString(),...over});
  t.mock.method(globalThis,"fetch",async url=>{
    const u=String(url); calls.push(u);
    const pageNo=Number(new URL(u).searchParams.get("page"));
    assert.equal(new URL(u).searchParams.get("min_iv"),"100");
    return Response.json(page(pageNo, pageNo===1?[p("111"),p("222")]:[p("333"),p("111")]).body);
  });
  const {db,env}=makeEnv([iflowSource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  assert.deepEqual(calls.map(u=>new URL(u).searchParams.get("page")),["1","2"]);
  const state=JSON.parse(db.get("pgs-feed-v1"));
  assert.equal(state.entries[0].status,"online");
  assert.equal(state.entries[0].spots.length,3); // cross-page duplicate id collapsed
  assert.equal(state.entries[0].received,4);
  assert.equal(state.entries[0].validated,3);
  assert.equal(state.entries[0].discarded,1);
});

test("city adapter accepts unambiguous numeric strings and reports counts",async t=>{
  const textRow={...cityPerfect,attack:"15",defence:"15",stamina:"15",lat:"40.67196281",lng:"-73.84379014",despawn:String(cityDespawn)};
  t.mock.method(globalThis,"fetch",async url=>{
    assert.ok(String(url).startsWith(cityUrl+"?"));
    assert.equal(new URL(String(url)).searchParams.get("time")?.length,10); // unix seconds
    return Response.json({pokemons:[textRow,{...cityPerfect,attack:14},{...cityPerfect,pokemon_id:"abc"}],
      meta:{inserted:1,time:2},weathers:[]});
  });
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  const state=JSON.parse(db.get("pgs-feed-v1"));
  assert.equal(state.entries[0].status,"online");
  assert.equal(state.entries[0].spots.length,1);
  assert.equal(state.entries[0].received,3);
  assert.equal(state.entries[0].validated,1);
  assert.equal(state.entries[0].discarded,2);
  const status=await worker.fetch(new Request("https://example.org/status.json"),env);
  const body=await status.json();
  assert.equal(body.connections[0].state,"online_with_results");
  assert.equal(body.summary.online_with_results,1);
});

test("successful collection with zero hundos stays online and is labelled",async t=>{
  t.mock.method(globalThis,"fetch",async()=>Response.json({pokemons:[],meta:{inserted:1,time:2},weathers:[]}));
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  const status=await worker.fetch(new Request("https://example.org/status.json"),env);
  const body=await status.json();
  assert.equal(body.connections[0].status,"online");
  assert.equal(body.connections[0].state,"online_without_hundos");
  assert.equal(body.connections[0].validated,0);
  assert.equal(body.connections[0].reason,null);
  assert.equal(body.summary.online_without_hundos,1);
});

test("BOM-prefixed JSON is accepted; HTML challenge reports invalid_response with content type",async t=>{
  const payload=JSON.stringify({pokemons:[cityPerfect],meta:{inserted:1,time:2},weathers:[]});
  let call=0;
  t.mock.method(globalThis,"fetch",async()=>{
    call++;
    return call===1 ? new Response("\uFEFF"+payload,{status:200,headers:{"content-type":"application/json; charset=utf-8"}})
                    : new Response("<html><body>challenge</body></html>",{status:200,headers:{"content-type":"text/html"}});
  });
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  assert.equal(JSON.parse(db.get("pgs-feed-v1")).entries[0].status,"online");
  // Force an immediate retry and serve the HTML page this time.
  const stored=JSON.parse(db.get("pgs-feed-v1")); stored.entries[0].next=0; db.set("pgs-feed-v1",JSON.stringify(stored));
  await worker.scheduled({scheduledTime:Date.now()},env);
  const status=await worker.fetch(new Request("https://example.org/status.json"),env);
  const body=await status.json();
  assert.equal(body.connections[0].status,"offline");
  assert.equal(body.connections[0].state,"invalid_response");
  assert.equal(body.connections[0].reason,"invalid_json");
  assert.equal(body.connections[0].content_type,"text/html");
});

test("access denied and rate limited responses are distinguished",async t=>{
  let mode=403;
  t.mock.method(globalThis,"fetch",async()=>new Response("forbidden",{status:mode,headers:{"content-type":"text/html","retry-after":"0"}}));
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  let body=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(body.connections[0].state,"access_denied");
  mode=429;
  const stored=JSON.parse(db.get("pgs-feed-v1")); stored.entries[0].next=0; db.set("pgs-feed-v1",JSON.stringify(stored));
  await worker.scheduled({scheduledTime:Date.now()},env);
  body=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(body.connections[0].state,"rate_limited");
  assert.equal(body.connections[0].http_status,429);
});

test("empty response body is reported precisely",async t=>{
  t.mock.method(globalThis,"fetch",async()=>new Response("",{status:200,headers:{"content-type":"application/json"}}));
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  const body=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(body.connections[0].reason,"empty_response");
  assert.equal(body.connections[0].state,"invalid_response");
});

test("failure backoff is capped and legacy far-future next values are clamped",async t=>{
  t.mock.method(globalThis,"fetch",async()=>{ throw new TypeError("fetch failed"); });
  const {db,env}=makeEnv([citySource]);
  const legacy={entries:[{name:"nycpokemap",url:cityUrl,kind:"city",interval_s:600,
    reason:"connection_error",status:"offline",failures:8,next:Date.now()+100*3600*1000,updated:null}],history:[]};
  db.set("pgs-feed-v1",JSON.stringify(legacy));
  const before=Date.now();
  await worker.scheduled({scheduledTime:before},env);
  const state=JSON.parse(db.get("pgs-feed-v1"));
  assert.equal(state.entries[0].status,"offline");
  assert.equal(state.entries[0].reason,"connection_error");
  assert.equal(state.entries[0].failures,6);
  assert.ok(state.entries[0].next-before <= 1800*1000+1000, "backoff must be capped at 30 minutes");
  const body=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(body.connections[0].state,"offline_connection");
  assert.ok(Number.isSafeInteger(body.connections[0].next_retry));
});

test("network failure keeps previous successful rows available",async t=>{
  const good=JSON.stringify({pokemons:[cityPerfect],meta:{inserted:1,time:2},weathers:[]});
  let up=true;
  t.mock.method(globalThis,"fetch",async()=>up ? Response.json({pokemons:[cityPerfect],meta:{inserted:1,time:2},weathers:[]})
                                                  : new Response("",{status:200}));
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  up=false;
  const stored=JSON.parse(db.get("pgs-feed-v1")); stored.entries[0].next=0; db.set("pgs-feed-v1",JSON.stringify(stored));
  await worker.scheduled({scheduledTime:Date.now()},env);
  const body=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(body.connections[0].status,"offline");
  assert.equal(body.connections[0].last_success!==null,true);
  const feed=await (await worker.fetch(new Request("https://example.org/hundos.json"),env)).json();
  assert.equal(feed.spots.length,1);
});

const gocoordsSource={name:"gocoords",kind:"gocoords",interval_s:300,url:"https://gocoords.com/api/spawns"};
const gRow=(id,over={})=>({encounter_id:id,provider_unique_id:"golbat:"+id,pokemon_name:"Staryu",pokemon_id:120,
  form:null,cp:892,lvl:27,iv:100,raw_iv:"15/15/15",atk_iv:15,def_iv:15,sta_iv:15,
  lat:41.641259,lon:-87.883012,expires_at_utc:new Date(Date.now()+720000).toISOString(),...over});
const gPayload=(rows)=>({schema_version:2,generated_at:new Date().toISOString(),count:rows.length,rows,next_cursor:null});

test("gocoords adapter: real encounter ids to hundos, keyed rows to spots, strict IV rules",async()=>{
  const result=await gocoordsRows(gPayload([
    gRow("143989166818287050"),
    {...gRow(null),encounter_id:null,provider_unique_id:"pokexperience:abc123",pokemon_id:358,raw_iv:null,atk_iv:null,def_iv:null,sta_iv:null},
    gRow("10564209155694614093",{atk_iv:14}),            // iv 100 but attribute 14 -> rejected
    gRow("10564209155694614094",{iv:99}),                 // not 100 -> rejected
    gRow("10564209155694614095",{expires_at_utc:new Date(Date.now()-60000).toISOString()}), // expired
    gRow("10564209155694614096",{lat:91}),                // invalid coordinate
  ]),Date.now());
  assert.equal(result.hundos.length,1);
  assert.equal(result.hundos[0][0],"143989166818287050"); // real encounter id preserved, not synthetic
  assert.equal(result.spots.length,1);
  assert.ok(/^s[0-9a-f]{16}$/.test(result.spots[0][0]));
  assert.equal(result.received,6);
  assert.equal(result.validated,2);
  assert.equal(result.discarded,4);
  await assert.rejects(()=>gocoordsRows({schema_version:2,generated_at:new Date(Date.now()-3600000).toISOString(),rows:[]},Date.now()),/invalid_feed/);
});

test("city sources send AJAX-contract headers with an honest UA",async t=>{
  let seen;
  t.mock.method(globalThis,"fetch",async(url,init)=>{
    seen={url:String(url),headers:init?.headers||{}};
    return Response.json({pokemons:[],meta:{inserted:1,time:2},weathers:[]});
  });
  const {env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  assert.equal(seen.headers["X-Requested-With"],"XMLHttpRequest");
  assert.equal(seen.headers.Referer,"https://nycpokemap.com/");
  assert.ok(String(seen.headers["User-Agent"]).startsWith("PGS-Hundo-Feed/"));
  assert.ok(!/mozilla|chrome|safari|firefox/i.test(String(seen.headers["User-Agent"])));
});

test("gocoords participates only when explicitly configured, with real encounter ids in hundos.json",async t=>{
  const row=gRow("143989166818287050");
  t.mock.method(globalThis,"fetch",async()=>Response.json(gPayload([row])));
  const {db,env}=makeEnv([gocoordsSource]);
  await worker.scheduled({scheduledTime:Date.now()},env);
  const status=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(status.connections[0].status,"online");
  assert.equal(status.connections[0].state,"online_with_results");
  const feed=await (await worker.fetch(new Request("https://example.org/hundos.json"),env)).json();
  assert.deepEqual(feed.hundos.map(r=>r[0]),["143989166818287050"]);
  const catalog=await (await worker.fetch(new Request("https://example.org/sources.json"),env)).json();
  assert.equal(catalog.providers.find(p=>p.provider==="gocoords").status,"OPERACIONAL CONFIRMADA");
});

test("gocoords is absent from production defaults and from the built-in dormant list when disabled",async()=>{
  const {env}=makeEnv([]);
  const catalog=await (await worker.fetch(new Request("https://example.org/sources.json"),env)).json();
  const dormant=catalog.providers.find(p=>p.provider==="gocoords");
  assert.ok(dormant && dormant.status.startsWith("AGUARDANDO"));
});

const mkMoonaniRow=(i,now)=>{
  const fmt=t=>new Date(t).toISOString().slice(0,19).replace("T"," ");
  return {Number:String(1+(i%150)),Coords:`${(10+i*0.01).toFixed(5)}, ${(20+i*0.01).toFixed(5)}`,
    Attack:"15",Defense:"15",HP:"15",CP:"500",Level:"20",Form:"",
    "Start Time":fmt(now-60000),"End Time":fmt(now+600000)};
};

test("moonani paginates beyond the first 100 rows and validates them",async t=>{
  const now=Date.now();
  const calls=[];
  t.mock.method(globalThis,"fetch",async(url,init)=>{
    calls.push(init.body);
    const start=Number(new URLSearchParams(init.body).get("start"));
    if (start===0) return Response.json({recordsFiltered:105,data:Array.from({length:100},(_,i)=>mkMoonaniRow(i,now))});
    if (start===100) return Response.json({recordsFiltered:105,data:Array.from({length:5},(_,i)=>mkMoonaniRow(100+i,now))});
    throw new Error("unexpected page");
  });
  const {db,env}=makeEnv([{name:"moonani",kind:"moonani",interval_s:900,url:"https://moonani.com/PokeList/ajax.php"}]);
  await worker.scheduled({scheduledTime:now},env);
  assert.deepEqual(calls.map(b=>new URLSearchParams(b).get("start")),["0","100"]);
  const state=JSON.parse(db.get("pgs-feed-v1"));
  assert.equal(state.entries[0].status,"online");
  assert.equal(state.entries[0].spots.length,105);
  assert.equal(state.entries[0].received,105);
});

test("moonani keeps zero-hundo page-1-only responses online without extra requests",async t=>{
  const now=Date.now();
  const calls=[];
  t.mock.method(globalThis,"fetch",async(url,init)=>{
    calls.push(init.body);
    return Response.json({recordsFiltered:2,data:[mkMoonaniRow(0,now),{...mkMoonaniRow(1,now),Attack:"14"}]});
  });
  const {db,env}=makeEnv([{name:"moonani",kind:"moonani",interval_s:900,url:"https://moonani.com/PokeList/ajax.php"}]);
  await worker.scheduled({scheduledTime:now},env);
  assert.equal(calls.length,1);
  const status=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(status.connections[0].state,"online_with_results");
  assert.equal(status.connections[0].state_label,"Online com resultados");
  assert.equal(status.connections[0].validated,1);
});

test("HTTP 429 without Retry-After waits at least 30 minutes",async t=>{
  const now=Date.now();
  t.mock.method(globalThis,"fetch",async()=>new Response("",{status:429,headers:{"content-type":"text/html"}}));
  const {db,env}=makeEnv([citySource]);
  await worker.scheduled({scheduledTime:now},env);
  const status=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(status.connections[0].state,"rate_limited");
  assert.ok(status.connections[0].next_retry>=now+1799000);
});

test("state_label is present and backoff stays at/below 30 minutes",async t=>{
  const now=Date.now();
  t.mock.method(globalThis,"fetch",async()=>{ throw new TypeError("network failed"); });
  const legacy={entries:[{name:"nycpokemap",url:cityUrl,kind:"city",interval_s:600,adapter_v:2,
    status:"offline",failures:6,next:now-1000}],history:[]};
  const {db,env}=makeEnv([citySource]);
  db.set("pgs-feed-v1",JSON.stringify(legacy));
  await worker.scheduled({scheduledTime:now},env);
  const status=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(status.connections[0].state_label,"Offline por falha de conexão");
  assert.ok(status.connections[0].next_retry<=Date.now()+1800000+1000);
});

test("adapter version change forces immediate recollection despite legacy next",async t=>{
  const now=Date.now();
  const calls=[];
  t.mock.method(globalThis,"fetch",async()=>{
    calls.push("hit");
    return Response.json({pokemons:[],meta:{inserted:1,time:2},weathers:[]});
  });
  const legacy={entries:[{name:"nycpokemap",url:cityUrl,kind:"city",interval_s:600,
    reason:"invalid_json",status:"offline",failures:3,next:now+7*24*3600*1000}],history:[]}; // no adapter_v: stale writer
  const {db,env}=makeEnv([citySource]);
  db.set("pgs-feed-v1",JSON.stringify(legacy));
  await worker.scheduled({scheduledTime:now},env);
  assert.equal(calls.length,1);
  assert.equal(JSON.parse(db.get("pgs-feed-v1")).entries[0].adapter_v,2);
});

test("legacy restrictions survive migrations and repeated cron calls",async t=>{
  t.mock.method(globalThis,"fetch",async()=>assert.fail("early retry"));
  for (const httpStatus of [403,429,503]) {
    const {db,env}=makeEnv([citySource]);
    const next=Date.now()+86400000;
    db.set("pgs-feed-v1",JSON.stringify({entries:[{...citySource,httpStatus,next,status:"offline",reason:"upstream_http"}]}));
    await worker.scheduled({},env);
    assert.equal(JSON.parse(db.get("pgs-feed-v1")).entries[0].next,next);
  }
});

test("partial iFlowGo pages keep valid spots and stop at the first rate limit",async t=>{
  const calls=[];
  t.mock.method(globalThis,"fetch",async url=>{
    const n=new URL(url).searchParams.get("page");
    calls.push(n);
    return n==="1"?Response.json({total_pages:5,items:[perfect]}):
      new Response(null,{status:429,headers:{"Retry-After":"86400"}});
  });
  const {db,env}=makeEnv([iflowSource]);
  const before=Date.now();
  await worker.scheduled({},env);
  await worker.scheduled({},env);
  assert.deepEqual(calls,["1","2"]);
  const [entry]=JSON.parse(db.get("pgs-feed-v1")).entries;
  assert.equal(entry.spots.length,1);
  assert.equal(entry.httpStatus,429);
  assert.equal(entry.attemptedPages,2);
  assert.equal(entry.collectedPages,1);
  assert.ok(entry.next>=before+86400000);
});

test("Poke100IV verifies all IV components and publishes internal IDs only as spots",async t=>{
  const row={id:1,pokemon_id:25,iv:100,atk:15,def:15,sta:15,latitude:"40.7",longitude:"-74.0",
    expires_at:new Date(Date.now()+600000).toISOString()};
  t.mock.method(globalThis,"fetch",async url=>{
    assert.equal(new URL(url).searchParams.get("ivFilters"),"15-15-15");
    return Response.json({success:true,data:[row,{...row,sta:14},{...row,coordinate_precision:"approximate"}]});
  });
  const {db,env}=makeEnv([{name:"poke100iv",kind:"poke100iv",url:"https://poke100iv.com/api/pokemon",interval_s:600}]);
  await worker.scheduled({},env);
  const [entry]=JSON.parse(db.get("pgs-feed-v1")).entries;
  assert.equal(entry.discarded,2);
  assert.equal(entry.hundos.length,0);
  assert.equal(entry.spots.length,1);
});

test("one serialized publication per minute and only revealed perfect encounters",async()=>{
  const {FeedPublisher}=await import("./worker.mjs");
  const data=new Map(), requests=[];
  const env={POGO_TOKEN:"fixture",SOURCES:"[]",FEED:{get:async()=>null,put:async()=>{}}};
  const publisher=new FeedPublisher({storage:{get:k=>data.get(k),put:(k,v)=>data.set(k,v)}},env);
  const original=globalThis.fetch;
  globalThis.fetch=async(url,init)=>{
    requests.push(String(url));
    assert.equal(init.headers.Authorization,"Bearer fixture");
    return Response.json(String(url).endsWith("/lookup")?{mode:"pokemon",results:[
      {encounter_id:"1",pokemon_id:25,raw_iv:"14/15/15",reveal_code:"bad",despawn_at_ms:now+500000},
      {encounter_id:"2",pokemon_id:25,raw_iv:"15/15/15",reveal_code:"ok",despawn_at_ms:now+500000}
    ]}:{lat:1,lng:2});
  };
  try {
    const trigger=new Request("https://internal/refresh",{method:"POST"});
    await Promise.all([publisher.fetch(trigger),publisher.fetch(trigger)]);
    await publisher.fetch(trigger);
    const state=await (await publisher.fetch(new Request("https://internal/snapshot"))).json();
    assert.equal(requests.length,2);
    assert.deepEqual(state.entries[0].hundos[0].slice(0,5),["2",25,0,1,2]);
  } finally {globalThis.fetch=original;}
});

test("same spot ID from two sources survives differing form metadata only once",()=>{
  const entry={updated:now,status:"online",hundos:[],spots:[spot]};
  const other=[...spot]; other[2]=1955;
  const data=feed({entries:[{name:"a",...entry},{name:"b",...entry,spots:[other]}]},now);
  assert.equal(data.spots.length,1);
});
