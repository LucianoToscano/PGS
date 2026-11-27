// Standalone production-table-injection harness for the feature-33 consolidated VGP controller. Never
// linked into the app library. It dlopen()s the real libpgs-core.so, queries feature 33, then drives the
// production controller with FAKE sibling tables (each matching its real ABI), a FAKE il2cpp GC + a FAKE
// alive() so the orchestration can be exercised deterministically without a VM. The controller merely
// forwards to these tables, so the fakes model only the decisions each sibling would return.
#include "vgp_controller.h"
#include "vgp_policy.h"
#include "vgp_actions.h"
#include "vgp_candidates.h"
#include "vgp_results.h"
#include "vgp_discovery.h"
#include "vgp_maintenance.h"
#include "vgp_marker.h"
#include "items.h"
#include "pgs_native_api.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <set>
#include <string>
#include <thread>
#include <unordered_map>
#include <unistd.h>

namespace {

// ---- aux table view (identical fixed ABI to the controller's private view) -------------------------
struct AuxSpinOut { uint32_t version, size; uint64_t rpc_handle, reflection_handle; void *closed_method; };
struct AuxTransferOut { uint32_t version, size; uint64_t caught_id, pokemon_handle, gm_handle; };
struct AuxApi {
  uint32_t version, size;
  int (*install)(const void *);
  int (*spin)(void *, uint64_t, uint64_t, AuxSpinOut *);
  int (*transfer)(void *, void *, uint64_t, uint64_t, AuxTransferOut *);
};

// ---- fake il2cpp objects / classes -----------------------------------------------------------------
int wildClass, nameplateClass, boolClass, otherClass;
struct Obj { char buf[16]{}; explicit Obj(void *k) { *reinterpret_cast<void **>(buf) = k; } void *p() { return buf; } };
Obj boolTrue(&boolClass), svcObj(&otherClass), bagObj(&otherClass), ibagObj(&otherClass), arrObj(&otherClass),
    candObj(&otherClass), fortObj(&otherClass), rpcObj(&otherClass), reflObj(&otherClass), promiseObj(&otherClass),
    respObj(&otherClass), pkObj(&otherClass), gmObj(&otherClass);
int aliveMethod;  // m_alive sentinel

// ---- fake GC ---------------------------------------------------------------------------------------
std::unordered_map<uint64_t, void *> roots;
uint64_t serial = 0;
uint64_t gcNew(void *o, int) { if (!o) return 0; roots[++serial] = o; return serial; }
void *gcGet(uint64_t h) { auto i = roots.find(h); return i == roots.end() ? nullptr : i->second; }
void gcFree(uint64_t h) { assert(roots.erase(h) == 1); }
void *objClassOf(void *o) { return *reinterpret_cast<void **>(o); }
void *objUnbox(void *o) { return reinterpret_cast<char *>(o) + 8; }
void *invoke(void *method, void *, void **, void **exc) {
  if (exc) *exc = nullptr;
  (void)method;  // the controller only ever invokes m_alive directly
  boolTrue.buf[8] = 1;
  return boolTrue.p();
}

// ---- scenario knobs --------------------------------------------------------------------------------
bool g_due, g_full, g_blocked, g_serviceReady;
uint32_t g_order, g_count;
int32_t g_balls, g_stored, g_capacity, g_total, g_maxItems, g_ball2, g_catchStatus;
int g_snapshotRc, g_enumRc, g_atRc, g_actionRc, g_ballsRc, g_cooldownRc, g_markerRc, g_pollRc, g_auxSpinRc,
    g_auxTransferRc;
bool g_eligible, g_statusKnown, g_success;
int32_t g_reason;
uint64_t g_caughtId;
std::set<std::string> g_seen;
int g_actStopped;

void resetScenario() {
  g_due = true; g_full = false; g_blocked = false; g_serviceReady = true;
  g_order = 0; g_count = 1;
  g_balls = 30; g_stored = 0; g_capacity = 1000; g_total = 0; g_maxItems = 2000; g_ball2 = 30; g_catchStatus = 0;
  g_snapshotRc = PGS_VD_OK; g_enumRc = PGS_VD_OK; g_atRc = PGS_VD_OK; g_actionRc = PGS_VA_ISSUED;
  g_ballsRc = PGS_VM_OK; g_cooldownRc = PGS_VM_OK; g_markerRc = 0; g_pollRc = PGS_VR_PENDING;
  g_auxSpinRc = 1; g_auxTransferRc = 1;
  g_eligible = true; g_statusKnown = true; g_success = true; g_reason = 0; g_caughtId = 0x1122334455667788ull;
  g_seen.clear();
}

// ---- fake sibling tables ---------------------------------------------------------------------------
int pol_install(const PgsVgpPolicyConfig *) { return 0; }
int pol_update(uint64_t, uint64_t) { return 0; }
int pol_reset(uint64_t) { g_seen.clear(); return 0; }
int pol_due(uint64_t) { return g_due ? PGS_VP_YES : PGS_VP_OK; }
int pol_order(uint64_t, uint32_t *o) { *o = g_order; return 0; }
int pol_sweep(uint64_t, uint32_t *s) { *s = (uint32_t)g_seen.size(); return g_full ? PGS_VP_YES : PGS_VP_OK; }
int pol_seen(uint64_t, const char *k, uint32_t n) { return g_seen.count(std::string(k, n)) ? PGS_VP_YES : PGS_VP_OK; }
int pol_touch(uint64_t, const char *k, uint32_t n, uint64_t) { g_seen.insert(std::string(k, n)); return PGS_VP_OK; }
int pol_arm(uint64_t, uint64_t) { return 0; }
int pol_block(uint64_t) { g_blocked = true; return 0; }
int pol_clearBlock(uint64_t) { g_blocked = false; return 0; }
int pol_catchDelay(int32_t, uint64_t *ms) { *ms = 30000; return 0; }
int pol_sample(PgsVgpPolicySample *) { return 0; }

int act_install(const PgsVgpActionsConfig *) { return 0; }
int act_update(uint32_t, uint64_t, uint64_t, uint64_t) { return PGS_VA_OK; }
int act_action(const void *, uintptr_t *h) { if (g_actionRc == PGS_VA_ISSUED) *h = gcNew(promiseObj.p(), 0); return g_actionRc; }
int act_encounter(const PgsVgpActionsTarget *, uintptr_t *h) { return act_action(nullptr, h); }
int act_capture(const PgsVgpActionsTarget *, uintptr_t *h) { return act_action(nullptr, h); }
int act_spin(const PgsVgpActionsSpin *, uintptr_t *h) { return act_action(nullptr, h); }
int act_stop(uint64_t) { g_actStopped++; return PGS_VA_OK; }
int act_sample(PgsVgpActionsSample *) { return 0; }

int cnd_install(const PgsVgpCandidateConfig *) { return 0; }
int cnd_inspect(const PgsVgpCandidateRequest *req, PgsVgpCandidateResult *out) {
  memset(out, 0, sizeof(*out)); out->version = PGS_VC_RESULT_VERSION; out->size = sizeof(*out);
  if (!g_eligible) { out->eligible = 0; out->reason = g_reason; return PGS_VC_NOT; }
  out->eligible = 1; out->reason = 0;
  const char *k = req->action == PGS_VC_ACTION_CATCH ? "pCAT" : "sSTOP";
  out->key_len = (uint32_t)strlen(k); memcpy(out->key, k, out->key_len);
  if (req->action == PGS_VC_ACTION_SPIN) out->fort_handle = gcNew(fortObj.p(), 0);
  return PGS_VC_ELIGIBLE;
}

int res_install(const PgsVgpResultsConfig *) { return 0; }
int res_poll(void *, uint32_t, uint64_t, PgsVgpResultsResult *out) {
  memset(out, 0, sizeof(*out)); out->version = PGS_VR_RESULT_VERSION; out->size = sizeof(*out);
  if (g_pollRc == PGS_VR_DONE) {
    out->state = 1; out->status_known = g_statusKnown; out->status = g_catchStatus; out->success = g_success;
    out->value_handle = gcNew(respObj.p(), 0);
  } else if (g_pollRc == PGS_VR_REJECTED) out->state = 2;
  return g_pollRc;
}
int res_sample(PgsVgpResultsSample *) { return 0; }

int dsc_install(const PgsVgpDiscoveryConfig *) { return 0; }
int dsc_snapshot(void *, uint64_t, uint64_t, PgsVgpDiscoverySnapshot *out) {
  memset(out, 0, sizeof(*out)); out->version = PGS_VD_SNAPSHOT_VERSION; out->size = sizeof(*out);
  if (g_snapshotRc != PGS_VD_OK) return g_snapshotRc;
  out->balls = g_balls; out->stored = g_stored; out->capacity = g_capacity;
  out->total_items = g_total; out->max_items = g_maxItems;
  out->pokemon_bag_handle = gcNew(bagObj.p(), 0); out->item_bag_handle = gcNew(ibagObj.p(), 0);
  return PGS_VD_OK;
}
int dsc_enumerate(uint32_t, uint64_t, uint64_t, PgsVgpDiscoveryEnumeration *out) {
  memset(out, 0, sizeof(*out)); out->version = PGS_VD_ENUM_VERSION; out->size = sizeof(*out);
  if (g_enumRc != PGS_VD_OK) return g_enumRc;
  out->count = g_count; out->array_handle = gcNew(arrObj.p(), 0); return PGS_VD_OK;
}
int dsc_at(void *, uint32_t, uint64_t, uint64_t, uintptr_t *h) {
  *h = 0; if (g_atRc != PGS_VD_OK) return g_atRc; *h = gcNew(candObj.p(), 0); return PGS_VD_OK;
}

int mnt_install(const PgsVgpMaintenanceConfig *) { return 0; }
int mnt_balls(void *, uint64_t, uint64_t, int32_t *c) { *c = g_ball2; return g_ballsRc; }
int mnt_cooldown(void *, void *, uint64_t, uint64_t) { return g_cooldownRc; }

int mrk_install(const PgsVgpMarkerConfig *) { return 0; }
int mrk_project(void *, uint64_t, uint64_t, PgsVgpMarkerResult *out) {
  memset(out, 0, sizeof(*out)); out->version = 1; out->size = sizeof(*out); return g_markerRc;
}

int itm_install(const pgs_items_config_v1 *) { return 0; }
int itm_tick(const pgs_items_rules_v1 *, uint32_t, uint64_t, uint64_t) { return 0; }
int itm_clear(uint64_t) { return 0; }
int itm_sample(pgs_items_sample_v1 *) { return 0; }
int itm_catalog(pgs_item_row *, uint32_t, uint32_t *) { return 0; }
void *itm_serviceHandle() { return nullptr; }
int itm_drain(pgs_item_event *, uint32_t, uint32_t *) { return 0; }
void *itm_serviceAcquire() { return g_serviceReady ? reinterpret_cast<void *>(gcNew(svcObj.p(), 0)) : nullptr; }

int aux_install(const void *) { return 0; }
int aux_spin(void *, uint64_t, uint64_t, AuxSpinOut *out) {
  memset(out, 0, sizeof(*out)); out->version = 1; out->size = sizeof(*out);
  if (g_auxSpinRc != 1) return g_auxSpinRc;
  out->rpc_handle = gcNew(rpcObj.p(), 0); out->reflection_handle = gcNew(reflObj.p(), 0);
  out->closed_method = &aliveMethod; return 1;
}
int aux_transfer(void *, void *, uint64_t, uint64_t, AuxTransferOut *out) {
  memset(out, 0, sizeof(*out)); out->version = 1; out->size = sizeof(*out);
  if (g_auxTransferRc != 1) return g_auxTransferRc;
  out->caught_id = g_caughtId; out->pokemon_handle = gcNew(pkObj.p(), 0); out->gm_handle = gcNew(gmObj.p(), 0);
  return 1;
}

PgsVgpPolicyApi POL{PGS_VP_API_VERSION, sizeof(PgsVgpPolicyApi), pol_install, pol_update, pol_reset, pol_due,
                    pol_order, pol_sweep, pol_seen, pol_touch, pol_arm, pol_block, pol_clearBlock,
                    pol_catchDelay, pol_sample};
PgsVgpActionsApi ACT{PGS_VA_API_VERSION, sizeof(PgsVgpActionsApi), act_install, act_update, act_encounter,
                     act_capture, act_spin, act_stop, act_sample};
PgsVgpCandidateApi CND{PGS_VC_API_VERSION, sizeof(PgsVgpCandidateApi), cnd_install, cnd_inspect};
PgsVgpResultsApi RES{PGS_VR_API_VERSION, sizeof(PgsVgpResultsApi), res_install, res_poll, res_sample};
PgsVgpDiscoveryApi DSC{PGS_VD_API_VERSION, sizeof(PgsVgpDiscoveryApi), dsc_install, dsc_snapshot,
                       dsc_enumerate, dsc_at};
PgsVgpMaintenanceApi MNT{PGS_VM_API_VERSION, sizeof(PgsVgpMaintenanceApi), mnt_install, mnt_balls, mnt_cooldown};
PgsVgpMarkerApi MRK{1, sizeof(PgsVgpMarkerApi), mrk_install, mrk_project};
pgs_items_api_v1 ITM{PGS_ITEMS_API_VERSION, sizeof(pgs_items_api_v1), itm_install, itm_tick,
                         itm_clear, itm_sample, itm_catalog, itm_serviceHandle, itm_drain, itm_serviceAcquire};
AuxApi AUX{1, sizeof(AuxApi), aux_install, aux_spin, aux_transfer};

const PgsVgpControllerApi *api = nullptr;
uint64_t tid = 0;

PgsVgpControllerConfig makeConfig() {
  PgsVgpControllerConfig c{};
  c.version = PGS_VGC_CONFIG_VERSION; c.size = sizeof(c);
  c.policy_table = &POL; c.actions_table = &ACT; c.candidates_table = &CND; c.results_table = &RES;
  c.discovery_table = &DSC; c.maintenance_table = &MNT; c.marker_table = &MRK; c.items_table = &ITM;
  c.aux_table = &AUX;
  c.gc_new = reinterpret_cast<void *>(gcNew); c.gc_get = reinterpret_cast<void *>(gcGet);
  c.gc_free = reinterpret_cast<void *>(gcFree); c.object_class = reinterpret_cast<void *>(objClassOf);
  c.runtime_invoke = reinterpret_cast<void *>(invoke); c.object_unbox = reinterpret_cast<void *>(objUnbox);
  c.m_alive = &aliveMethod; c.class_wild = &wildClass; c.class_nameplate = &nameplateClass;
  c.class_bool = &boolClass; c.rpc_id = 42;
  return c;
}
PgsVgpControllerTick makeTick() {
  PgsVgpControllerTick t{};
  t.version = PGS_VGC_TICK_VERSION; t.size = sizeof(t); t.owner = tid; t.epoch = 1;
  t.lease_ms = 2000; t.allowed_ms = 2000; t.cleanup_ms = 0; t.generation = api->generation();
  t.lat = 10; t.lon = 20; t.mask = 3;
  t.flags = PGS_VGC_TF_TRANSFER_ENABLED | PGS_VGC_TF_MANUAL_READY;
  return t;
}
PgsVgpControllerOut run(PgsVgpControllerTick t) {
  PgsVgpControllerOut o{};
  assert(api->tick(&t, &o) == PGS_VGC_OK);
  return o;
}
void freeExports(const PgsVgpControllerOut &o) {
  gcFree(o.response_handle); gcFree(o.bag_handle); gcFree(o.pokemon_handle); gcFree(o.gm_handle);
}
}  // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  void *lib = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
  if (!lib) { std::puts(dlerror()); return 2; }
  auto load = reinterpret_cast<const void *(*)(uint32_t)>(dlsym(lib, "pgs_native_api"));
  assert(load);
  auto *core = static_cast<const pgs_native_api_v2 *>(load(2));
  assert(core);
  assert(!core->query_feature(33, 2));
  api = static_cast<const PgsVgpControllerApi *>(core->query_feature(33, 1));
  assert(api && api->version == 1 && api->size == 72);
  tid = static_cast<uint64_t>(gettid());

  // --- install validation --------------------------------------------------------------------------
  assert(api->install(nullptr) == PGS_VGC_ERR_NULL_ARG);
  { PgsVgpControllerConfig c = makeConfig(); c.gc_new = nullptr; assert(api->install(&c) == PGS_VGC_ERR_MISSING_PTR); }
  { PgsVgpControllerConfig c = makeConfig(); PgsVgpPolicyApi bad = POL; bad.size = 1; c.policy_table = &bad;
    assert(api->install(&c) == PGS_VGC_ERR_BAD_TABLE); }
  PgsVgpControllerConfig cfg = makeConfig();
  assert(api->install(&cfg) == PGS_VGC_OK);
  assert(api->install(&cfg) == PGS_VGC_OK);  // idempotent
  { PgsVgpControllerConfig c = makeConfig(); c.rpc_id = 7; assert(api->install(&c) == PGS_VGC_ERR_RECONFIG); }

  // tick() before any owner work must reject a foreign owner and a bad header.
  { PgsVgpControllerOut o{}; PgsVgpControllerTick t = makeTick(); t.owner = tid + 1;
    assert(api->tick(&t, &o) == PGS_VGC_ERR_OFF_OWNER); }
  { PgsVgpControllerOut o{}; PgsVgpControllerTick t = makeTick(); t.version = 9;
    assert(api->tick(&t, &o) == PGS_VGC_ERR_BAD_VERSION); }

  resetScenario();

  // --- OFF (mask 0) and WAIT_READY (no lease) ------------------------------------------------------
  { PgsVgpControllerTick t = makeTick(); t.mask = 0; auto o = run(t);
    assert(o.status == PGS_VGC_ST_OFF && o.phase == PGS_VGC_PH_NONE); }
  { PgsVgpControllerTick t = makeTick(); t.lease_ms = 0; auto o = run(t);
    assert(o.status == PGS_VGC_ST_WAIT_READY); }

  // --- no balls / storage full / item bag full -----------------------------------------------------
  { resetScenario(); g_balls = 0; PgsVgpControllerTick t = makeTick(); t.mask = 1; auto o = run(t);
    assert(o.status == PGS_VGC_ST_OUT_BALLS); assert(roots.empty()); }
  { resetScenario(); g_stored = 1000; g_capacity = 1000; PgsVgpControllerTick t = makeTick(); t.mask = 1;
    auto o = run(t); assert(o.status == PGS_VGC_ST_STORAGE_FULL); assert(roots.empty()); }

  // --- full catch -> transfer handoff -> feedback flow ---------------------------------------------
  resetScenario();
  g_pollRc = PGS_VR_PENDING;  // scan issues the encounter
  auto o1 = run(makeTick());
  assert(o1.status == PGS_VGC_ST_CATCHING && !(o1.flags & PGS_VGC_EV_CATCH_ISSUED) && o1.phase == PGS_VGC_PH_ENCOUNTER);
  { PgsVgpControllerSample s{}; api->sample(&s); assert(s.roots == 3 && s.phase == PGS_VGC_PH_ENCOUNTER); }

  g_pollRc = PGS_VR_DONE;  // encounter resolves -> capture issued
  auto o2 = run(makeTick());
  assert(o2.status == PGS_VGC_ST_CATCHING && o2.phase == PGS_VGC_PH_CATCH);

  g_pollRc = PGS_VR_DONE; g_success = true; g_statusKnown = true; g_catchStatus = 100;  // catch succeeds
  auto o3 = run(makeTick());
  assert(o3.status == PGS_VGC_ST_CHECK_TRANSFER && (o3.flags & PGS_VGC_EV_CATCH_RESULT) &&
         (o3.flags & PGS_VGC_EV_ITEM_CLEANUP) && o3.success == 1 && o3.catch_status == 100);
  assert(o3.phase == PGS_VGC_PH_INVENTORY_WAIT);

  auto o4 = run(makeTick());  // inventory ready -> handoff
  assert((o4.flags & PGS_VGC_EV_TRANSFER_READY) && o4.caught_id == g_caughtId && o4.response_handle &&
         o4.bag_handle && o4.pokemon_handle && o4.gm_handle && o4.phase == PGS_VGC_PH_HANDED_OFF);
  uint64_t token = o4.transfer_token;
  freeExports(o4);  // the shared JS executor adopts all four handles
  { PgsVgpControllerSample s{}; api->sample(&s); assert(s.roots == 0); }  // controller kept no export

  assert(api->transfer_feedback(token, PGS_VGC_FB_REQUESTED, tid) == PGS_VGC_OK);
  assert(run(makeTick()).status == PGS_VGC_ST_TRANSFERRING);
  assert(api->transfer_feedback(token, PGS_VGC_FB_SUCCESS, tid) == PGS_VGC_OK);
  auto o6 = run(makeTick());
  assert(o6.status == PGS_VGC_ST_TRANSFERRED && (o6.flags & PGS_VGC_EV_TRANSFER_CANCEL) &&
         o6.transfer_token == token && o6.phase == PGS_VGC_PH_NONE);
  assert(roots.empty());  // no leak across the whole catch+transfer cycle

  // --- spin success flow (order spin-first) --------------------------------------------------------
  resetScenario(); g_order = 1; g_pollRc = PGS_VR_PENDING;
  auto s1 = run(makeTick());
  assert(s1.status == PGS_VGC_ST_SPINNING && (s1.flags & PGS_VGC_EV_SPIN_ISSUED) && s1.phase == PGS_VGC_PH_SPIN);
  g_pollRc = PGS_VR_DONE; g_success = true;
  auto s2 = run(makeTick());
  assert(s2.status == PGS_VGC_ST_SPUN && (s2.flags & PGS_VGC_EV_SPIN_RESULT) && s2.success == 1);
  assert(roots.empty());

  // --- observe(): nameplate gui + wild target latches / clears the manual-exclusion root -----------
  resetScenario();
  Obj gui(&nameplateClass), manual(&wildClass), notGui(&otherClass);
  assert(api->observe(gui.p(), manual.p(), tid) == PGS_VGC_OK);
  { PgsVgpControllerSample s{}; api->sample(&s); assert(s.roots == 1); }   // the manual root is held
  assert(api->observe(notGui.p(), manual.p(), tid) == PGS_VGC_OK);         // not the nameplate: ignored
  { PgsVgpControllerSample s{}; api->sample(&s); assert(s.roots == 1); }
  assert(api->observe(gui.p() /*nameplate*/, nullptr, tid) == PGS_VGC_OK); // non-wild target clears it
  { PgsVgpControllerSample s{}; api->sample(&s); assert(s.roots == 0); }
  assert(api->observe(gui.p(), manual.p(), tid + 1) == PGS_VGC_ERR_OFF_OWNER);  // foreign owner refused
  assert(roots.empty());

  // --- rejected response retries and drops ---------------------------------------------------------
  resetScenario(); g_pollRc = PGS_VR_PENDING; run(makeTick());  // issue encounter
  g_pollRc = PGS_VR_REJECTED;
  auto rej = run(makeTick());
  assert(rej.status == PGS_VGC_ST_REJECTED && rej.phase == PGS_VGC_PH_NONE && roots.empty());

  // --- refusal (action returns 0: not issued) vs uncertain (negative) ------------------------------
  resetScenario(); g_actionRc = PGS_VA_OK;  // refused admission
  auto ref = run(makeTick());
  assert(ref.status == PGS_VGC_ST_WAIT_READY && ref.phase == PGS_VGC_PH_NONE && roots.empty());
  assert(g_seen.count("pCAT"));  // the target was quarantined 5 s

  resetScenario(); g_actionRc = PGS_VA_ERR_UNCERTAIN;  // issued-but-uncertain: block, no retry
  auto unc = run(makeTick());
  assert(unc.status == PGS_VGC_ST_ERROR && unc.error == PGS_VA_ERR_UNCERTAIN && g_blocked && roots.empty());

  // --- a conservative sibling failure pauses with the sibling code ---------------------------------
  resetScenario(); g_snapshotRc = PGS_VD_ERR_MANAGED;
  auto pse = run(makeTick());
  assert(pse.status == PGS_VGC_ST_ERROR && pse.error == PGS_VD_ERR_MANAGED && roots.empty());

  // --- stale generation blocks a NEW scan (adapter captured an older generation) -------------------
  resetScenario();
  assert(api->revoke() == PGS_VGC_OK);  // bumps the generation + stops actions
  int stoppedBefore = g_actStopped;
  { PgsVgpControllerTick t = makeTick(); t.generation = api->generation() - 1; auto o = run(t);
    assert(o.status == PGS_VGC_ST_NATIVE_UNAVAILABLE && roots.empty()); }
  assert(stoppedBefore >= 1);

  // --- result still finishes after VGP mask drops (in-flight completion) ---------------------------
  resetScenario(); g_pollRc = PGS_VR_PENDING; run(makeTick());  // issue encounter (pending)
  g_pollRc = PGS_VR_DONE; g_success = true; g_statusKnown = true; g_catchStatus = 100;
  { PgsVgpControllerTick t = makeTick(); t.mask = 0; /* mask dropped but transfer disabled keeps it simple */
    t.flags = 0; auto o = run(t);  // encounter branch requires mask bit1 -> retry + drop
    assert(o.phase == PGS_VGC_PH_NONE); }
  // drain any quarantine and roots
  assert(roots.empty());

  // --- foreign-thread stop: cleanup deferred to the owner tick -------------------------------------
  resetScenario(); g_pollRc = PGS_VR_PENDING; run(makeTick());  // leave a pending record (3 roots)
  assert(!roots.empty());
  std::thread([] { assert(api->stop(tid) == PGS_VGC_OK); }).join();  // foreign thread: defers the free
  { PgsVgpControllerOut o{}; PgsVgpControllerTick t = makeTick(); assert(api->tick(&t, &o) == PGS_VGC_OK);
    assert(o.status == PGS_VGC_ST_OFF && o.phase == PGS_VGC_PH_NONE); }
  assert(roots.empty());  // the owner tick freed every deferred root

  std::puts("PASS VGP controller production API: install/table validation, owner gate, OFF/wait, catch+"
            "encounter+capture+result, transfer handoff+feedback+cancel, spin, manual exclude, reject, "
            "refusal vs uncertain, sibling pause, stale generation, foreign stop cleanup, zero leaks");
  dlclose(lib);
  return 0;
}
