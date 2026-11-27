import test from "node:test";
import assert from "node:assert/strict";
import worker,{rows,feed,iflowRows} from "./worker.mjs";
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
    status:"offline",failures:8,next:Date.now()+100*3600*1000,updated:null}],history:[]};
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
