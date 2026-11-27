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
