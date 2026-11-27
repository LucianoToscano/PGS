import test from "node:test";
import assert from "node:assert/strict";
import worker,{rows,feed,iflowRows,gocoordsRows} from "./worker.mjs";
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

test("GOCoords v2 accepts only explicit perfect IV, fresh exact spots and bounded public rows",async()=>{
  const p={pokemon_id:25,iv:100,atk_iv:15,def_iv:15,sta_iv:15,lat:12.3456789,lon:23.4567891,
    cp:250,lvl:20,form:null,expires_at_utc:new Date(now+600000).toISOString()};
  const envelope=list=>({schema_version:2,generated_at:new Date(now).toISOString(),count:list.length,rows:list});
  const result=await gocoordsRows(envelope([p,p,{...p,atk_iv:null},{...p,iv:99},
    {...p,coordinate_precision:"approximate"},{...p,expires_at_utc:new Date(now-1).toISOString()}]),now);
  assert.equal(result.hundos.length,0);
  assert.equal(result.spots.length,1);
  assert.deepEqual(result.spots[0].slice(1),[25,0,p.lat,p.lon,now+600000,250,20]);
  await assert.rejects(()=>gocoordsRows({...envelope([p]),generated_at:new Date(now-600001).toISOString()},now),/gocoords_schema/);
  await assert.rejects(()=>gocoordsRows(envelope(Array(11).fill(p)),now),/gocoords_schema/);
});
test("city content negotiation and diagnostics preserve real refusals and distinguish empty JSON",async t=>{
  const names=["nycpokemap","sgpokemap","londonpogomap","sydneypogomap","vanpokemap"];
  const cfg=names.map(name=>({name,kind:"city",url:"https://"+name+".com/query2.php",interval_s:600}));
  // Synthetic fixture: never used as real provider evidence.
  const good={attack:"15",defence:15,stamina:15,pokemon_id:25,lat:12.3456789,lng:23.4567891,
    despawn:Math.floor((now+600000)/1000),cp:100,level:10};
  t.mock.method(globalThis,"fetch",async (url,options)=>{
    assert.equal(options.headers["X-Requested-With"],"XMLHttpRequest");
    assert.match(options.headers["User-Agent"],/^PGS-Hundo-Feed/);
    assert.equal(options.headers.Referer,undefined);
    assert.equal(options.redirect,"manual");
    switch(url.hostname) {
      case "nycpokemap.com":return Response.json({pokemons:[good,{...good,attack:14}]});
      case "sgpokemap.com":return Response.json({pokemons:[]});
      case "londonpogomap.com":return new Response("<html>Not JSON</html>",{headers:{"Content-Type":"text/html"}});
      case "sydneypogomap.com":return new Response(null,{status:403});
      case "vanpokemap.com":return new Response(null,{status:429,headers:{"Retry-After":"7200"}});
    }
    throw Error("unexpected host");
  });
  const db=new Map(), env={SOURCES:JSON.stringify(cfg),FEED:{put:(k,v)=>db.set(k,v),get:k=>JSON.parse(db.get(k)||"null")}};
  await worker.scheduled({},env);
  const result=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  const by=Object.fromEntries(result.connections.map(e=>[e.provider,e]));
  assert.equal(by.nycpokemap.detail_status,"online_with_results");
  assert.equal(by.nycpokemap.received,2);assert.equal(by.nycpokemap.validated,1);assert.equal(by.nycpokemap.discarded,1);
  assert.equal(by.sgpokemap.detail_status,"online_zero_hundos");
  assert.equal(by.londonpogomap.detail_status,"invalid_response");
  assert.equal(by.londonpogomap.reason,"invalid_json");assert.equal(by.londonpogomap.http_status,200);
  assert.equal(by.londonpogomap.content_type,"text/html");
  assert.equal(by.sydneypogomap.detail_status,"access_denied");assert.equal(by.sydneypogomap.http_status,403);
  assert.equal(by.vanpokemap.detail_status,"rate_limited");assert.equal(by.vanpokemap.http_status,429);
  assert.ok(by.vanpokemap.next_attempt>=by.vanpokemap.last_attempt+7200000);
  const feedResult=await (await worker.fetch(new Request("https://example.org/hundos.json"),env)).json();
  assert.equal(feedResult.spots.length,1);
  assert.equal(feedResult.sources.londonpogomap.status,"offline");
});
test("unapproved GOCoords source is not queried; pending config appears in status",async t=>{
  const candidate={name:"gocoords",kind:"gocoords",url:"https://gocoords.com/api/spawns",interval_s:300};
  let calls=0;t.mock.method(globalThis,"fetch",async()=>{calls++;throw Error("must not query");});
  const db=new Map(),env={SOURCES:JSON.stringify([candidate]),FEED:{put:(k,v)=>db.set(k,v),get:k=>JSON.parse(db.get(k)||"null")}};
  const read=()=>worker.fetch(new Request("https://example.org/status.json"),env);
  assert.equal((await (await read()).json()).connections[0].detail_status,"pending");
  await worker.scheduled({},env);
  assert.equal(calls,0);
  assert.equal((await (await read()).json()).connections[0].detail_status,"invalid_configuration");
});


function envFor(sources,previous) {
  const db=new Map();
  if (previous) db.set("pgs-feed-v1",JSON.stringify(previous));
  return {db,env:{SOURCES:JSON.stringify(sources),FEED:{put:(k,v)=>db.set(k,v),get:k=>JSON.parse(db.get(k)||"null")}}};
}
const statusFor=async env=>(await (await worker.fetch(new Request("https://example.org/status.json"),env)).json()).connections;
test("candidate iFlowGo pagination filters locally and obeys provider page count",async t=>{
  const calls=[],cfg={...iflow,min_iv_100:true,max_pages:5};
  t.mock.method(globalThis,"fetch",async url=>{
    const p=Number(url.searchParams.get("page"));
    calls.push(p);assert.equal(url.searchParams.get("min_iv"),"100");
    return Response.json({total_pages:99,items:[{...perfect,id:String(5000+p),lat:10+p},
      {...perfect,id:String(6000+p),attack_iv:14}]});
  });
  const {env}=envFor([cfg]);
  await worker.scheduled({},env);
  assert.deepEqual(calls,[1,2,3,4,5]);
  const [s]=await statusFor(env);
  assert.equal(s.status,"online");assert.equal(s.collected_pages,5);
  assert.equal(s.received,10);assert.equal(s.validated,5);assert.equal(s.discarded,5);
});
test("Moonani candidate reads up to three DataTables pages and deduplicates",async t=>{
  const fmt=ms=>new Date(ms).toISOString().slice(0,19).replace("T"," ");
  const make=i=>({Number:String(i+1),Coords:"12.34567, 23.45678",Attack:"15",Defense:"15",HP:"15",
    CP:"-1",Level:"-1","Start Time":fmt(now-60000),"End Time":fmt(now+600000)});
  const calls=[],cfg={name:"moonani",kind:"moonani",url:"https://moonani.com/PokeList/ajax.php",interval_s:900,max_pages:3};
  t.mock.method(globalThis,"fetch",async (url,options)=>{
    const form=new URLSearchParams(options.body),start=Number(form.get("start"));
    calls.push(start);assert.equal(form.get("iv"),"100");assert.equal(form.get("length"),"100");
    return Response.json({recordsFiltered:203,data:Array.from({length:Math.min(100,203-start)},(_,i)=>make(start+i))});
  });
  const {env}=envFor([cfg]);
  await worker.scheduled({},env);
  assert.deepEqual(calls,[0,100,200]);const [s]=await statusFor(env);
  assert.equal(s.collected_pages,3);assert.equal(s.received,203);assert.equal(s.validated,203);
});
test("later-page rate limit is not hidden; last good data and Retry-After survive",async t=>{
  const cfg={...iflow,max_pages:5,min_iv_100:true};
  const previous={time:now-1000,entries:[{...cfg,updated:now-1000,status:"online",next:now-1,hundos:[],spots:[spot],received:1,validated:1,discarded:0}],history:[]};
  const {env,db}=envFor([cfg],previous);let calls=0;
  t.mock.method(globalThis,"fetch",async()=>{
    if (++calls===1)return Response.json({total_pages:5,items:[perfect]});
    return new Response(null,{status:429,headers:{"Retry-After":"90000"}});
  });
  await worker.scheduled({},env);
  const [s]=await statusFor(env);
  assert.equal(calls,2);assert.equal(s.detail_status,"rate_limited");assert.equal(s.attempted_pages,2);
  assert.ok(s.next_attempt>=s.last_attempt+90000000);assert.equal(s.last_success,now-1000);
  assert.deepEqual(JSON.parse(db.get("pgs-feed-v1")).entries[0].spots,[spot]);
  await worker.scheduled({},env);assert.equal(calls,2);
});
test("one-time city recovery resets old invalid JSON delay, not access refusal or Retry-After",async t=>{
  const names=["nycpokemap","sgpokemap","londonpogomap"];
  const cfg=names.map(name=>({name,kind:"city",url:"https://"+name+".com/query2.php",interval_s:600}));
  const prev={time:now,entries:cfg.map((s,i)=>({...s,status:"offline",next:now+76800000,failures:8,
    reason:i===0?"invalid_json":"upstream_http",httpStatus:i===0?null:i===1?403:429})),history:[]};
  const {env,db}=envFor(cfg,prev);let calls=0;
  t.mock.method(globalThis,"fetch",async url=>{calls++;assert.equal(url.hostname,"nycpokemap.com");return new Response("",{status:200});});
  await worker.scheduled({},env);
  const by=Object.fromEntries((await statusFor(env)).map(s=>[s.provider,s]));
  assert.equal(calls,1);assert.equal(by.nycpokemap.reason,"empty_response");assert.equal(by.nycpokemap.http_status,200);
  assert.ok(by.nycpokemap.next_attempt<=Date.now()+3601000);
  assert.equal(by.sgpokemap.next_attempt,prev.entries[1].next);assert.equal(by.londonpogomap.next_attempt,prev.entries[2].next);
  assert.equal(JSON.parse(db.get("pgs-feed-v1")).entries[0].adapter_v,2);
  await worker.scheduled({},env);assert.equal(calls,1);
});
test("source validation rejects ambiguous numeric input, approximate coordinates and excessive request budget",async t=>{
  const city={name:"nycpokemap",kind:"city",url:"https://nycpokemap.com/query2.php",interval_s:600};
  const p={pokemon_id:"25",lat:"12.3456789",lng:"23.4567891",despawn:Math.floor((now+600000)/1000),
    attack:"15",defence:"15",stamina:15,cp:"-1",level:-1,form:-1};
  t.mock.method(globalThis,"fetch",async()=>Response.json({pokemons:[p,{...p,lat:"0x10"},{...p,pokemon_id:true},
    {...p,coordinate_precision:"approximate"},{...p,defense:14}]}));
  const {env,db}=envFor([city]);await worker.scheduled({},env);
  const r=JSON.parse(db.get("pgs-feed-v1")).entries[0];assert.equal(r.spots.length,1);assert.equal(r.discarded,4);
  assert.deepEqual(r.spots[0].slice(6),[0,0]);assert.equal(r.spots[0][2],0);
  const over=envFor(Array.from({length:4},(_,i)=>({...iflow,name:"iflow-"+i,max_pages:5}))).env;
  await assert.rejects(()=>worker.scheduled({},over),/invalid_config/);
});


test("city time uses epoch seconds; diagnostic labels and summary count actual active states",async t=>{
  const cities=["nycpokemap","sgpokemap"].map(name=>({name,kind:"city",url:"https://"+name+".com/query2.php",interval_s:600}));
  t.mock.method(globalThis,"fetch",async url=>{
    assert.ok(Math.abs(Number(url.searchParams.get("time"))-Math.floor(Date.now()/1000))<5);
    if(url.hostname==="nycpokemap.com")return Response.json({pokemons:[]});
    return new Response(null,{status:403});
  });
  const {env}=envFor(cities);
  await worker.scheduled({},env);
  const result=await (await worker.fetch(new Request("https://example.org/status.json"),env)).json();
  assert.equal(result.connections[0].status,"online");
  assert.equal(result.connections[0].detail_status,"online_zero_hundos");
  assert.equal(result.connections[0].state_label,"Online sem Hundos");
  assert.equal(result.connections[1].state_label,"Acesso recusado");
  assert.deepEqual(result.summary,{online_zero_hundos:1,access_denied:1});
});
