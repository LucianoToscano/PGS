import test from "node:test";
import assert from "node:assert/strict";
import worker,{rows,feed} from "./worker.mjs";
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
test("scheduled fixture uses isolated KV, public feed requires a successful poll",async()=>{
  const db=new Map();
  const env={FEED:{put:(key,data)=>db.set(key,data),get:key=>JSON.parse(db.get(key)||"null")}};
  await worker.scheduled({scheduledTime:now},env);
  const get=path=>worker.fetch(new Request("https://example.org"+path),env);
  assert.equal((await get("/hundos.json")).status,503);
  const body=await (await get("/simulation/hundos.json")).json();
  assert.equal(body.simulated,true); assert.equal(body.hundos.length,1);
});

test("iFlowGo isolates categories, deduplicates IDs and excludes expired records",async t=>{
  const source={name:"iflowgo-pokemon",kind:"iflow",category:"pokemon",interval_s:600,
    url:"https://pokecoords.iflowgo.com/iflowgopokecoords/api/v1/pokemon-search"};
  const record={id:"1234",pokemon_id:25,lat:12.3456789,lon:0,expires_at:new Date(now+600000).toISOString(),
    attack_iv:15,defense_iv:15,stamina_iv:15,cp:10,level:1};
  t.mock.method(globalThis,"fetch",async()=>Response.json({items:[record,record,{...record,id:"2",expires_at:new Date(0).toISOString()}]}));
  const db=new Map();
  const env={SOURCES:JSON.stringify([source]),FEED:{put:(k,v)=>db.set(k,v),get:k=>JSON.parse(db.get(k)||"null")}};
  await worker.scheduled({scheduledTime:now},env);
  const read=path=>worker.fetch(new Request("https://example.org"+path),env);
  const pokemon=await (await read("/pokemon.json")).json();
  assert.equal(pokemon.records.length,1);
  assert.equal(pokemon.records[0].lat,record.lat);
  assert.equal((await read("/raids.json")).status,404);
  assert.equal((await (await read("/hundos.json")).json()).spots.length,1);
  env.SOURCES="[]"; assert.equal((await read("/pokemon.json")).status,503);
});
