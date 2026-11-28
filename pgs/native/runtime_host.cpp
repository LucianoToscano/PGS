#include "runtime_host.h"
#include "events/event_collector.h"
#include "runtime_bootstrap.h"
#include "runtime_transport.h"
#include "unity_scheduler.h"
#include "shared_host.h"
#include "quickball_host.h"
#include "routes_host.h"
#include "inventory_host.h"
#include "spin_host.h"
#include "catch_wait.h"
#include "spawn_host.h"
#include "camera_host.h"
#include "combat_host.h"
#include "account_host.h"
#include "interaction_host.h"
#include "encounter_host.h"
#include "runtime_diag.h"
#include "hook_engine_diag.h"
#include <cstdio>
#include <cmath>
#include <atomic>
#include <cstring>
#include <mutex>
#include <initializer_list>
#include <time.h>
#include <unistd.h>

// Weak: isolated fixtures include this file without linking the hook engine,
// and then simply report no hook detail.
int pgs_hook_diag(PgsHookDiag *) __attribute__((weak));
namespace {
template<class T> const T *as(const void *p){return static_cast<const T*>(p);}
const auto scheduler=as<PgsUnitySchedulerApi>(pgs_unity_scheduler_api(2));
const auto shared=as<PgsSharedHostApi>(pgs_shared_host_api(1));
const auto quick=as<PgsQuickballHostApi>(pgs_quickball_host_api(1));
const auto routes=as<PgsRoutesHostApi>(pgs_routes_host_api(1));
const auto inventory=as<PgsInventoryHostApi>(pgs_inventory_host_api(1));
const auto spin=as<PgsSpinHostApi>(pgs_spin_host_api(1));
const auto wait_host=as<PgsCatchWaitApi>(pgs_catch_wait_api(1));
const auto spawn=as<PgsSpawnHostApi>(pgs_spawn_host_api(1));
const auto camera=as<PgsCameraHostApi>(pgs_camera_host_api(1));
const auto combat=as<PgsCombatHostApi>(pgs_combat_host_api(1));
const auto account=as<PGSAccountHostApi>(pgs_account_host_api(1));
const auto interaction=as<PgsInteractionHostApi>(pgs_interaction_host_api(1));
const auto encounter=as<PgsEncounterHostApi>(pgs_encounter_host_api(1));
constexpr uint32_t pending_mask=0;
struct Slot {std::atomic<uint32_t> state{PGS_RTH_WAITING},caps{0},owned{0};std::atomic<int32_t> error{0};std::atomic<bool> configured{false};uint64_t retry=0;uint32_t attempts=0;bool retry_pending=false;};
Slot slots[12];
uint32_t reported_states[12]{},reported_caps[12]{};
int32_t reported_errors[12]{};
std::atomic_flag setup_busy=ATOMIC_FLAG_INIT,pulse_busy=ATOMIC_FLAG_INIT;
std::atomic<bool> installed{false},stopping{false};
std::atomic<int32_t> fault{0};
std::atomic<uint64_t> owner{0},generation{0},pulses{0};
PgsBootBinding binding{};
PgsUnitySchedulerConfig scheduler_config{};
PgsSharedMetaExtraExports spin_extra{};
PgsSpinHostConfig spin_config{};
uint32_t interaction_forwarding=0;
// Startup diagnostics: delivered through the transport event queue (opcode 19,
// channel "native-runtime-start") so a failed native startup is visible even
// when the scheduler never pulses. Only configure() touches the throttle, which
// startup_mutex serializes; emission is best-effort and never changes a return.
std::mutex startup_mutex;
PgsStartupThrottle startup_throttle{};
void update_interaction_sites(){
 PgsSharedHostSample s{};if(!shared->sample(&s)&&s.ready)interaction_forwarding|=PGS_IH_SHARED_MASK_61;
 PgsQuickballHostSample q{};if(!quick->sample(&q)&&(q.capabilities&PGS_QBH_OBSERVERS))interaction_forwarding|=PGS_IH_SHARED_MASK_49;
 PgsSpinHostSample p{};if(!spin->sample(&p)){
  if(p.capabilities&1)interaction_forwarding|=PGS_IH_SHARED_MASK_67_CAMERA;
  if(p.capabilities&2)interaction_forwarding|=PGS_IH_SHARED_MASK_67_QUICK;
 }
 interaction->shared_sites(PGS_IH_SHARED_MASK_ALL,interaction_forwarding);
}
uint64_t clock_ms(){timespec t{};return clock_gettime(CLOCK_BOOTTIME,&t)||t.tv_sec<0?0:uint64_t(t.tv_sec)*1000+uint64_t(t.tv_nsec)/1000000;}
bool attached(){return owner.load()==uint64_t(gettid())&&binding.runtime.thread_current&&reinterpret_cast<void*(*)()>(binding.runtime.thread_current)();}
// Scheduler install calls this while its own installation lock is held. Do not
// reenter48; independent47 reflection and54 snapshot have no managed gameplay calls.
int verify(const PgsUnitySchedulerConfig *c){
 if(!c||!attached()||c->exclusive_owner!=1||c->expected_owner_tid!=gettid())return 0;
 PgsBootBinding b{};const auto boot=as<PgsBootApi>(pgs_runtime_bootstrap_api(1));
 if(boot->snapshot(&b)||b.handle!=binding.handle||b.execute_tasks!=binding.execute_tasks||
 c->execute_tasks!=b.execute_tasks||c->runtime_invoke!=b.runtime.runtime_invoke||
 c->runtime_invoke_convert_args!=b.runtime.runtime_invoke_convert_args||
 reinterpret_cast<void*>(c->thread_current)!=b.runtime.thread_current)return 0;
 const auto md=as<PGS_MetaApi>(pgs_runtime_metadata_api(1));
 const void *addresses[]={c->runtime_invoke,c->runtime_invoke_convert_args,b.runtime.thread_current};
 for(const void *address:addresses){PGS_MetaCodeQuery q{1,sizeof(q),address,4,nullptr,0,0};if(md->validate_code(&q))return 0;}
 if(b.execute_tasks_code){PGS_MetaCodeQuery q{1,sizeof(q),b.execute_tasks_code,4,nullptr,0,0};if(md->validate_code(&q))return 0;}
 PGS_MetaClassQuery cq{1,sizeof(cq),"UnityEngine","UnitySynchronizationContext","UnityEngine.UnitySynchronizationContext",PGS_MD_MATCH_EXACT,0};
 PGS_MetaClassResult klass{};if(md->resolve_class(&cq,&klass))return 0;
 PGS_MetaMethodQuery mq{};mq.version=1;mq.size=sizeof(mq);mq.owner=klass.klass;mq.name="ExecuteTasks";mq.return_type="System.Void";mq.return_match=PGS_MD_MATCH_EXACT;mq.is_static=1;
 PGS_MetaMethodResult method{};return md->validate_method(&mq,&method)==0&&method.method==b.execute_tasks;
}
void stop_host(unsigned i){if(!slots[i].configured.load(std::memory_order_acquire))return;
 switch(i){case 0:routes->stop(uint64_t(gettid()));break;case 1:shared->stop();break;case 2:quick->stop();break;case 3:encounter->stop(uint64_t(gettid()));break;case 4:camera->stop("manager-stop");break;case 5:inventory->stop();break;case 6:combat->stop(uint64_t(gettid()));break;case 7:spin->stop();break;case 8:account->stop();break;case 9:interaction->stop("manager-stop");break;case 10:wait_host->stop();break;case 11:spawn->stop();break;}
}
void report_hook_failures();
void report_host(unsigned i){
 const uint32_t state=slots[i].state.load(),caps=slots[i].caps.load();const int error=slots[i].error.load();
 if(reported_states[i]==state&&reported_errors[i]==error&&reported_caps[i]==caps)return;
 static const char *names[]={"routes","shared","quick-ball","encounter","camera","inventory","combat","spin","account","interaction","catch-wait","spawn"};
 static const char *states[]={"waiting","configured","ready","failed","stopped","pending"};
 char json[320];std::snprintf(json,sizeof(json),"{\"feature\":%u,\"name\":\"%s\",\"state\":%u,\"stateName\":\"%s\",\"previousState\":%u,\"error\":%d,\"capabilities\":%u,\"owned\":%u}",
  i<10?60+i:i==10?58u:71u,names[i],state,state<6?states[state]:"unknown",reported_states[i],error,caps,slots[i].owned.load());
 const char channel[]="native-runtime";
 PgsRuntimeTransportString strings[]={{channel,sizeof(channel)-1},{json,uint32_t(std::strlen(json))}};
 if(as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1))->emit(19,nullptr,0,strings,2)==0){reported_states[i]=state;reported_errors[i]=error;reported_caps[i]=caps;}
}
void failed(unsigned i,int error){slots[i].error=error;slots[i].state=PGS_RTH_FAILED;stop_host(i);report_host(i);}
int configure_host(unsigned i){
 switch(i){
 case 1:return shared->configure(nullptr);
 case 2:return quick->configure(nullptr);
 case 3:{if(!shared->metadata())return 1;int rc=encounter->configure(nullptr);return rc?rc:encounter->install();}
 case 10:{const int rc=wait_host->install(nullptr);return rc==1||rc==-5||rc==-10||rc==-27?1:rc;}
 case 11:return spawn->configure(nullptr);
 case 9:{int rc=interaction->configure(nullptr);if(rc)return rc;
  // Reserve all shared sites before any late owner installation. The linked
  // owners provide ABI2 observer calls;69 must never install a second hook.
  update_interaction_sites();
  return interaction->schedule(PGS_IH_SCHEDULE_DELAY_MS);}
 case 6:return combat->configure(nullptr);
 case 8:{int rc=account->configure(nullptr);return rc==PGS_ACH_ERR_BUSY?1:rc;}
 case 4:{int rc=camera->configure(nullptr);if(rc==PGS_CH_RETRY)return 1;if(rc)return rc<0?rc:-10064;
  PgsCameraHostOptions options{};options.version=1;options.size=sizeof(options);options.enabled=options.sample_camera=options.continuous=1;
  rc=camera->start(&options);return rc==PGS_CH_OK||rc==PGS_CH_RETRY?0:rc<0?rc:-10064;}
 case 0:{PgsRoutesHostConfig c{};c.version=1;c.size=sizeof(c);c.flags=PGS_RH_CFG_PREFER_BOOTSTRAP|PGS_RH_CFG_EMIT_TRANSPORT52|PGS_RH_CFG_POLL_TRANSPORT52|PGS_RH_CFG_SKIP_QUEUE;return routes->configure(&c);}
 case 5:if(!shared->metadata())return 1;return inventory->configure(nullptr);
 case 7:{const auto metadata=shared->metadata();if(!metadata)return 1;
  spin_extra={};spin_extra.field_static_get_value=binding.runtime.field_static_get_value;spin_extra.gchandle_new=binding.runtime.gchandle_new;spin_extra.gchandle_get_target=binding.runtime.gchandle_get_target;spin_extra.gchandle_free=binding.runtime.gchandle_free;
  spin_config={1,sizeof(spin_config),PGS_SPH_TRANSPORT,1,metadata,&spin_extra,binding.runtime.object_get_class,binding.runtime.field_get_value,binding.runtime.runtime_invoke,binding.runtime.object_unbox,reinterpret_cast<void*(*)()>(binding.runtime.thread_current),owner.load()};
  return spin->configure(&spin_config);}
 default:return -1;
 }
}
void observe(unsigned i){auto &s=slots[i];uint32_t ready=0,cap=0,owned=0;int error=0;bool terminal=false;
 switch(i){
 case 0:{PgsRoutesHostSample v{};if(routes->sample(&v)){failed(i,-10060);return;}ready=v.meta_ready&&v.tracking_ready;cap=(v.meta_ready?1u:0)|(v.tracking_ready?2u:0)|(v.services_ready?4u:0);error=v.last_error;terminal=error<0&&!v.meta_ready;break;}
 case 1:{PgsSharedHostSample v{};if(shared->sample(&v)){failed(i,-10061);return;}ready=v.ready&&!v.stopping;cap=v.capabilities;owned=v.roots;terminal=v.fault;error=v.fault?-10061:0;break;}
 case 2:{PgsQuickballHostSample v{};if(quick->sample(&v)){failed(i,-10062);return;}ready=v.ready;cap=v.capabilities;owned=v.owned;error=v.error?v.error:v.metadata_error;terminal=v.stopping&&v.error;break;}
 case 3:{PgsEncounterHostSample v{};v.version=1;v.size=sizeof(v);if(encounter->sample(&v)){failed(i,-10063);return;}ready=v.installed;cap=v.active_capabilities;error=v.last_error;break;}
 case 5:{PgsInventoryHostSample v{};if(inventory->sample(&v)){failed(i,-10065);return;}ready=v.ready;cap=v.capabilities;owned=v.roots;error=int32_t(v.error);terminal=v.stopping&&v.error;break;}
 case 7:{PgsSpinHostSample v{};if(spin->sample(&v)){failed(i,-10067);return;}ready=v.capabilities==3&&!v.stopping&&!v.camera_error&&!v.quick_error;cap=v.capabilities;owned=v.owned;error=v.camera_error?v.camera_error:v.quick_error;terminal=v.stopping&&error;break;}
 case 10:{PgsCatchWaitSample v{};if(wait_host->sample(&v)){failed(i,-10058);return;}ready=v.ready;cap=v.ready;error=v.fault;terminal=v.fault!=0;break;}
 case 11:{PgsSpawnHostSample v{};if(spawn->sample(&v)){failed(i,-10071);return;}ready=v.ready;cap=v.installed;error=v.error;terminal=v.stopping&&v.error;break;}
 case 4:{PgsCameraHostSample v{};v.version=1;v.size=sizeof(v);if(camera->sample(&v)){failed(i,-10064);return;}ready=v.ready&&!v.stopping;cap=v.ready;error=v.last_error;terminal=!v.active&&v.last_error!=0;break;}
 case 6:{PgsCombatHostSample v{};if(combat->sample(&v)){failed(i,-10066);return;}ready=v.ready&&!v.stopping;cap=v.capabilities;owned=v.roots;error=v.last_error;terminal=v.failed;break;}
 case 9:{PgsInteractionHostSample v{};if(interaction->sample(&v)){failed(i,-10069);return;}ready=v.configured;cap=v.installed_target_mask;owned=v.in_flight;error=v.status==PGS_IH_STATUS_FAILED?-10069:0;break;}
 case 8:{PgsAccountHostSample v{};if(account->sample(&v)){failed(i,-10068);return;}ready=v.configured&&v.capabilities&&!v.stopping;cap=v.capabilities;owned=v.active_roots;error=v.accounts_error?v.accounts_error:v.advsync_error;terminal=v.stopping&&error;break;}
 }
 s.caps=cap;s.owned=owned;
 if(s.state.load()==PGS_RTH_FAILED)return;
 s.error=error;if(terminal){failed(i,error);return;}
 s.state=stopping.load()?PGS_RTH_STOPPED:ready?PGS_RTH_READY:PGS_RTH_CONFIGURED;
}
void wait_tick(bool cleanup){
 const auto tr=as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1));
 if(!cleanup){PGSRuntimeTransportSample before{},after{};int allowed=0;
  const bool fresh=!tr->sample(&before)&&before.snapshot_fresh&&!before.fault&&
   !tr->get_bool(25,&allowed)&&!tr->sample(&after)&&after.snapshot_fresh&&!after.fault&&
   before.snapshot_seq==after.snapshot_seq&&before.generation==after.generation;
  if(wait_host->update(fresh&&allowed==1?1:0,fresh&&allowed==1?100:0)){failed(10,-10058);return;}
 }
 for(unsigned n=0;n<128;++n){PgsCatchWaitEvent e{};int rc=wait_host->next_event(&e);if(!rc)break;
  if(rc!=1||(e.kind!=1&&e.kind!=2)||!std::isfinite(e.original_seconds)||!std::isfinite(e.new_seconds)){failed(10,-10058);return;}
  char json[512];int count=std::snprintf(json,sizeof(json),"{\"kind\":\"%s\",\"tid\":%d,\"state\":7,\"resultStatus\":%d,\"originalSeconds\":%.9g,\"branch\":%s,\"boottimeMs\":%llu%s",
   e.kind==1?"wait-observed":"wait-shortened",e.tid,e.status,double(e.original_seconds),e.branch==1?"true":"false",(unsigned long long)e.boottime_ms,e.kind==1?"}":",");
  if(e.kind==2&&count>0&&size_t(count)<sizeof(json))std::snprintf(json+count,sizeof(json)-size_t(count),"\"newSeconds\":%.9g}",double(e.new_seconds));
  const char channel[]="quick-catch-wait";PgsRuntimeTransportString strings[]={{channel,sizeof(channel)-1},{json,uint32_t(std::strlen(json))}};
  if(tr->emit(19,nullptr,0,strings,2)){failed(10,-10058);return;}
 }
}
// Diagnostic tick/scan totals and distance are sampled at the heartbeat, not status changes.
void collector_status_key(const PgsEventCollectorState &s,bool stopped,char *json,size_t capacity){
   std::snprintf(json,capacity,"{\"available\":%s,\"error\":%d,\"enabled\":%d,\"inflight\":%d,\"timedOut\":%d,\"attempted\":%llu,\"completed\":%llu,\"failed\":%llu,\"skippedEncounters\":%llu,\"candy\":%llu,\"rareCandy\":%llu}",
    s.ready&&!s.error&&!stopped?"true":"false",s.error,s.enabled,s.inflight,s.timed_out,
    (unsigned long long)s.attempted,(unsigned long long)s.completed,(unsigned long long)s.failed,
    (unsigned long long)s.skipped_encounters,(unsigned long long)s.candy,(unsigned long long)s.rare_candy);
}
void pulse(void*,const PGSUnityPulse *p){
 if(!p||p->reserved||p->tid!=gettid()||!attached()||p->generation!=generation.load()||scheduler->valid(p->generation)!=1)return;
 if(pulse_busy.test_and_set(std::memory_order_acquire))return;
 struct Clear{~Clear(){pulse_busy.clear(std::memory_order_release);}} clear;
 ++pulses;const uint64_t time=clock_ms();if(!time){fault=-8;stopping=true;}
 {
  const auto tr=as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1));
  PGSRuntimeTransportSample before{},after{};int enabled=0,has_lat=0,has_lng=0;
  double lat=NAN,lng=NAN;
  const bool fresh=!stopping.load()&&!tr->sample(&before)&&before.snapshot_fresh&&!before.fault&&
   !tr->get_bool(39,&enabled)&&!tr->get_double(0,&lat,&has_lat)&&!tr->get_double(1,&lng,&has_lng)&&has_lat&&has_lng&&
   !tr->sample(&after)&&after.snapshot_fresh&&!after.fault&&
   before.snapshot_seq==after.snapshot_seq&&before.generation==after.generation;
  pgs_event_collector_location(fresh?lat:NAN,fresh?lng:NAN,fresh?time:0);
  pgs_event_collector_tick(fresh&&enabled==1,owner.load());
  static uint64_t report_at=0,sent_at=0;static char sent[1024]={};
  if(time>=report_at){
   report_at=time+2000;
   const auto s=pgs_event_collector_state();char json[1024];
   collector_status_key(s,stopping.load(),json,sizeof(json));
   char status_key[1024];std::snprintf(status_key,sizeof(status_key),"%s",json);
   const size_t used=std::strlen(json);
   if(used&&used<sizeof(json))std::snprintf(json+used-1,sizeof(json)-used+1,
    ",\"updates\":%llu,\"ownerUpdates\":%llu,\"scans\":%llu,\"sessionActive\":%d,\"reason\":%d,\"listCount\":%d,\"boxes\":%d,\"visibleCandidates\":%d,\"expired\":%d,\"zeroExpiry\":%d,\"nearestMeters\":%.1f,\"pendingEncounters\":%d,\"staleEncounters\":%d}",
    (unsigned long long)s.update_calls,(unsigned long long)s.owner_updates,(unsigned long long)s.scan_calls,s.session_active,s.pump_reason,s.list_count,s.matched_box_count,s.visible_count,s.expired_count,s.zero_expiry_count,s.nearest_meters,s.pending_encounters,s.stale_encounters);
   // Java only needs availability changes; unchanged idle snapshots are resent every 30 s, not every 2 s.
   if(std::strcmp(status_key,sent)||time-sent_at>=30000){
    const char channel[]="event-boxes";PgsRuntimeTransportString strings[]={{channel,sizeof(channel)-1},{json,uint32_t(std::strlen(json))}};
    if(tr->emit(19,nullptr,0,strings,2)==0){std::snprintf(sent,sizeof(sent),"%s",status_key);sent_at=time;}
   }
  }
 }
 // Dependency order is stable; interaction observers follow their hook owners.
 for(unsigned i:{1u,2u,3u,0u,5u,7u,10u,11u,4u,6u,8u,9u}){
  if(scheduler->valid(p->generation)!=1)return;auto &s=slots[i];
  if((!s.configured.load(std::memory_order_acquire)||s.retry_pending)&&s.state.load()!=PGS_RTH_FAILED&&!stopping.load()&&time>=s.retry){
   s.retry=time+(i==10?1000:2000);++s.attempts;const int rc=configure_host(i);if(rc<0){failed(i,rc);continue;}
   s.retry_pending=rc>0;
   if(rc>0){
    bool partial=false;if(i==8){PgsAccountHostSample v{};partial=!account->sample(&v)&&v.configured&&v.capabilities;}
    if(!partial){if(i==10&&s.attempts>=20)failed(i,-10058);continue;}
   }
   s.configured.store(true,std::memory_order_release);s.state=PGS_RTH_CONFIGURED;
   if(i==10){PgsCatchWaitSample v{};if(wait_host->sample(&v)){failed(i,-10058);continue;}
    char json[192];std::snprintf(json,sizeof(json),"{\"kind\":\"metadata-ready\",\"backend\":\"native\",\"allowed\":false,\"leaseMs\":2500,\"state\":7,\"successValue\":%d}",v.success_value);
    const char channel[]="quick-catch-wait";PgsRuntimeTransportString strings[]={{channel,sizeof(channel)-1},{json,uint32_t(std::strlen(json))}};
    if(as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1))->emit(19,nullptr,0,strings,2)){failed(i,-10058);continue;}
   }
  }
  if(!s.configured.load(std::memory_order_acquire))continue;
  const bool cleanup=stopping.load()||s.state.load()==PGS_RTH_FAILED;
  if(i==9&&!cleanup)update_interaction_sites();
  if(cleanup)stop_host(i);
  // Routes stop is currently a drain/revoke, not a terminal latch. Calling its
  // ordinary tick after stop would poll52 and reacquire a gameplay lease.
  switch(i){case 0:if(!cleanup)routes->on_unity_pulse(nullptr,p);break;case 1:shared->on_unity_pulse(nullptr,p);break;case 2:quick->on_unity_pulse(nullptr,p);break;case 3:encounter->tick(owner.load());break;case 4:if(cleanup)camera->tick(owner.load());else{camera->on_unity_begin(nullptr,p);if(scheduler->valid(p->generation)==1)camera->on_unity_end(nullptr,p);}break;case 5:inventory->on_unity_pulse(nullptr,p);break;case 6:combat->on_unity_pulse(nullptr,p);break;case 7:spin->on_unity_pulse(nullptr,p);break;case 8:account->on_unity_pulse(nullptr,p);break;case 9:interaction->on_unity_pulse(nullptr,p);break;case 10:wait_tick(cleanup);break;case 11:spawn->on_unity_pulse(nullptr,p);break;}
  observe(i);
  report_host(i);
 }
 report_hook_failures();
}
// Build one startup-diagnostic event and best-effort emit it. Assumes
// startup_mutex is held. Makes no managed/il2cpp call and never aborts a
// gameplay path: a failed emit (transport not yet installed) only means the
// throttle heartbeat will retry delivery. identity==true appends the scheduler
// method/hook identity (code addresses + which hook failed) for a hook failure.
// Append the hook engine's own account of a failed hook (failure==true) or of
// where the working island came from (failure==false). Writes at most cap-1
// characters and returns how many, or 0 when there is nothing to add or it does
// not fit. The caller closes the JSON object at the returned offset.
int append_hook_diag(char *out,size_t cap,bool failure){
 PgsHookDiag h{};
 if(!pgs_hook_diag||pgs_hook_diag(&h)!=0||h.version!=1||h.size!=sizeof(h))return 0;
 int m=0;
 if(failure){
  if(!h.failures)return 0;
  m=std::snprintf(out,cap,",\"hookReason\":\"%s\",\"hookTarget\":\"0x%llx\",\"hookRc\":%d,\"hookErrno\":%d,\"islandGaps\":%u,\"islandPadding\":%u,\"islandPages\":%u,\"hookFailures\":%u",
   h.reason==PGS_HOOK_REASON_NEAR_ISLAND?"near-island":h.reason==PGS_HOOK_REASON_DOBBY?"dobby":h.reason==PGS_HOOK_REASON_BAD_ARGS?"bad-args":"unknown",
   (unsigned long long)h.target,h.rc,h.error,h.gaps,h.padding,h.island_pages,h.failures);
 }else{
  if(!h.island_source)return 0;
  m=std::snprintf(out,cap,",\"island\":\"%s\",\"hookFailures\":%u",
   h.island_source==PGS_HOOK_ISLAND_MMAP?"mmap":h.island_source==PGS_HOOK_ISLAND_ELF_PADDING?"elf-padding":"page-padding",h.failures);
 }
 return m<0||size_t(m)>=cap?0:m;
}
// A hook that fails after startup (a feature installing later) is otherwise only in logcat. Report the
// engine's account of it to the run log once each time the failure count grows; the reason, target and
// island search are those of the first failure, hookFailures is the running total.
void report_hook_failures(){
 static uint32_t reported=0;
 PgsHookDiag h{};
 if(!pgs_hook_diag||pgs_hook_diag(&h)!=0||h.version!=1||h.size!=sizeof(h)||h.failures<=reported)return;
 char json[420];size_t t=size_t(std::snprintf(json,sizeof(json),"{\"kind\":\"hook-failure\""));
 t+=size_t(append_hook_diag(json+t,sizeof(json)-t-1,true));
 if(t+2>sizeof(json))return;
 json[t++]='}';json[t]=0;
 const char channel[]="native-hook";
 PgsRuntimeTransportString strings[]={{channel,sizeof(channel)-1},{json,uint32_t(t)}};
 if(as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1))->emit(19,nullptr,0,strings,2)==0)reported=h.failures;
}
void emit_startup_locked(const char *stage,const char *reason,int32_t status,int32_t detail,bool identity){
 const uint64_t now=clock_ms();
 if(!pgs_rtd_should_emit(&startup_throttle,stage,reason,status,detail,now))return;
 char json[768];
 int n=pgs_rtd_base_json(json,int(sizeof(json)),stage,reason,status,detail);
 if(!n)return;
 if(identity){
  const auto sched4=as<PgsUnitySchedulerApi4>(pgs_unity_scheduler_api(4));
  PgsUnitySchedulerDiag d{};const char *hook_stage="unknown";int inv_rc=0,con_rc=0;
  if(sched4&&sched4->version==4&&sched4->size==sizeof(PgsUnitySchedulerApi4)&&sched4->diagnostics&&!sched4->diagnostics(&d)){
   hook_stage=pgs_rtd_sched_stage(d.failed_stage);inv_rc=d.invoke_hook_rc;con_rc=d.convert_hook_rc;
  }
  int m=std::snprintf(json+n,sizeof(json)-size_t(n),
   ",\"executeTasks\":\"%p\",\"invoke\":\"%p\",\"convert\":\"%p\",\"hookStage\":\"%s\",\"invokeRc\":%d,\"convertRc\":%d,\"invokeBody\":\"0x%llx\",\"convertBody\":\"0x%llx\",\"hookOutcome\":\"%s\"",
   scheduler_config.execute_tasks,scheduler_config.runtime_invoke,scheduler_config.runtime_invoke_convert_args,hook_stage,inv_rc,con_rc,
   (unsigned long long)d.invoke_body,(unsigned long long)d.convert_body,
   d.failed_stage==PGS_US_STAGE_INVOKE_HOOK?(inv_rc?"installer-error":"missing-trampoline"):
   d.failed_stage==PGS_US_STAGE_CONVERT_HOOK?(con_rc?"installer-error":"missing-trampoline"):"not-hook-failure");
  if(m<0||size_t(n)+size_t(m)+1>=sizeof(json)){json[n]='}';json[n+1]=0;} // bounded fail-safe: close base object
  else{
   size_t t=size_t(n)+size_t(m);
   t+=size_t(append_hook_diag(json+t,sizeof(json)-t-1,true));
   json[t]='}';json[t+1]=0;
  }
 }else{
  if(size_t(n)+1>=sizeof(json))return;
  size_t t=size_t(n);
  t+=size_t(append_hook_diag(json+t,sizeof(json)-t-1,false));
  json[t]='}';json[t+1]=0;
 }
 const char channel[]="native-runtime-start";
 PgsRuntimeTransportString strings[]={{channel,sizeof(channel)-1},{json,uint32_t(std::strlen(json))}};
 as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1))->emit(19,nullptr,0,strings,2);
}
void emit_startup(const char *stage,const char *reason,int32_t status,int32_t detail,bool identity){
 std::lock_guard<std::mutex> l(startup_mutex);emit_startup_locked(stage,reason,status,detail,identity);
}
// Re-announce a latched negative startup fault (e.g. the permanent scheduler
// hook poison) on the heartbeat cadence, so a Java subscriber that attached
// after the failure still learns the terminal cause instead of waiting forever.
void reemit_startup_latched(){
 std::lock_guard<std::mutex> l(startup_mutex);
 if(!startup_throttle.have||startup_throttle.status>=0)return;
 char stage[sizeof(startup_throttle.stage)],reason[sizeof(startup_throttle.reason)];
 std::snprintf(stage,sizeof(stage),"%s",startup_throttle.stage);
 std::snprintf(reason,sizeof(reason),"%s",startup_throttle.reason);
 const bool identity=!std::strcmp(stage,"scheduler-install")||!std::strcmp(stage,"scheduler-activate");
 emit_startup_locked(stage,reason,startup_throttle.status,startup_throttle.detail,identity);
}
int configure(const PgsRuntimeHostConfig *c){
 if(!c||c->version!=1||c->size!=sizeof(*c)||c->exclusive_owner!=1||c->reserved)return -1;
 if(stopping.load())return -5;if(fault.load()){reemit_startup_latched();return fault.load();}
 if(setup_busy.test_and_set(std::memory_order_acquire))return 1;
 struct Clear{~Clear(){setup_busy.clear(std::memory_order_release);}} clear;
 if(installed.load())return attached()?0:-2;
 PgsBootBinding b{};const auto boot=as<PgsBootApi>(pgs_runtime_bootstrap_api(1));const int status=boot->snapshot(&b);
 if(status){if(status<0)emit_startup("bootstrap",pgs_rtd_boot_reason(status),status,b.detail,false);else emit_startup("bootstrap","not-ready",1,0,false);return status>0?1:status;}
 if(!b.runtime.thread_current||!reinterpret_cast<void*(*)()>(b.runtime.thread_current)()){emit_startup("attach","not-attached",-2,0,false);return -2;}
 PGSRuntimeTransportSample transport{};
 if(as<PgsRuntimeTransportApi>(pgs_runtime_transport_api(1))->sample(&transport)!=0){emit_startup("transport","unavailable",1,0,false);return 1;}
 if(transport.fault){emit_startup("transport","faulted",-6,0,false);return -6;}
 if(!transport.snapshot_fresh){emit_startup("transport","stale",1,0,false);return 1;}
 binding=b;owner=uint64_t(gettid());scheduler_config={};scheduler_config.version=2;scheduler_config.size=sizeof(scheduler_config);
 scheduler_config.runtime_invoke=b.runtime.runtime_invoke;scheduler_config.runtime_invoke_convert_args=b.runtime.runtime_invoke_convert_args;scheduler_config.execute_tasks=b.execute_tasks;
 scheduler_config.thread_current=reinterpret_cast<void*(*)()>(b.runtime.thread_current);scheduler_config.verify_metadata=verify;scheduler_config.expected_owner_tid=gettid();scheduler_config.exclusive_owner=1;
 scheduler_config.subscriber_count=1;scheduler_config.subscribers[0]={pulse,nullptr,nullptr};
 if(stopping.load())return -5;const int rc=scheduler->install(&scheduler_config);if(rc){fault=rc;emit_startup("scheduler-install",pgs_rtd_sched_reason(rc),rc,0,true);return rc;}
 installed.store(true,std::memory_order_release);const uint64_t gen=scheduler->activate();if(!gen){fault=-7;emit_startup("scheduler-activate","no-generation",-7,0,false);return -7;}
 generation=gen;emit_startup("ready","ok",0,0,false);return 0;
}
int stop(){if(stopping.exchange(true,std::memory_order_acq_rel))return 0;
 pgs_event_collector_stop();
for(unsigned i:{1u,2u,3u,0u,5u,7u,10u,11u,4u,6u,8u,9u})stop_host(i);return 0;}
int sample(PgsRuntimeHostSample *out){if(!out)return -1;*out={};out->version=1;out->size=sizeof(*out);out->installed=installed;out->stopping=stopping;out->fault=fault;out->pending_mask=pending_mask;out->owner_tid=owner;out->generation=generation;out->pulses=pulses;
 for(unsigned i=0;i<12;++i){const auto state=pending_mask&(1u<<i)?PGS_RTH_PENDING:slots[i].state.load();out->hosts[i]={i<10?60+i:i==10?58u:71u,state,slots[i].error.load(),slots[i].caps.load(),slots[i].owned.load(),0};if(state==PGS_RTH_READY)out->ready_mask|=1u<<i;}return 0;}
const PgsRuntimeHostApi api{1,sizeof(api),configure,stop,sample};
}
extern "C" const void *pgs_runtime_host_api(uint32_t version){return version==1?&api:nullptr;}
