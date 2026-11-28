#pragma once
#include "shared_metadata.h"
#include "runtime_bootstrap.h"
#include "unity_scheduler.h"
#include <stdint.h>
enum PgsInventoryHostCaps : uint32_t {PGS_IH_ITEMS=1,PGS_IH_BUDDY=2,PGS_IH_INCUBATION=4,PGS_IH_INCOMING=8,PGS_IH_OUTGOING=16,PGS_IH_SOCIAL=32};
struct PgsInventoryRuntime {
 PgsBootRuntimeExports boot;
 void *string_length,*object_get_virtual_method,*class_get_type,*type_get_object,*runtime_class_init,*method_get_object;
};
struct PgsInventoryHostConfig {
 uint32_t version,size,flags,reserved; // flags1 native52 transport; null config enables it
 const PgsSharedMetadataOutput *metadata;
 const PgsInventoryRuntime *runtime;
};
struct PgsInventoryHostOptions {
 uint32_t version,size,item_enabled,item_allowed,item_catalog,buddy_allowed,incubator_enabled,incubator_longest,incubator_allowed,gift_mask,gift_allowed,reserved;
 int32_t buddy_berry;uint32_t lease_ms;
 const char *item_rules; // bounded ASCII id:cap; pairs, copied synchronously
};
struct PgsInventoryHostSample {uint32_t version,size,configured,ready,capabilities,stopping,roots,error;uint64_t owner_tid,ticks;};
struct PgsInventoryHostEvent {uint32_t version,size;uint64_t sequence;char json[65536];};
struct PgsInventoryHostApi {
 uint32_t version,size;
 int (*configure)(const PgsInventoryHostConfig*);
 int (*update)(const PgsInventoryHostOptions*);
 int (*tick)(uint64_t);
 int (*stop)();
 int (*sample)(PgsInventoryHostSample*);
 int (*next_event)(PgsInventoryHostEvent*);
 void (*request_item_poll)();
 void *(*acquire_item_service)(); // owned root; caller must release through IL2CPP
 void (*on_unity_pulse)(void*,const PGSUnityPulse*);
 int (*visibility_site)(uint32_t);
 void (*on_visibility)(void*,uint64_t);
};
static_assert(sizeof(PgsInventoryHostConfig)==32,"config");
static_assert(sizeof(PgsInventoryHostOptions)==64,"options");
static_assert(sizeof(PgsInventoryHostSample)==48,"sample");
static_assert(sizeof(PgsInventoryHostApi)==96,"API");
// Separate v2 table preserves the exact v1 layout. Tickets coalesce safely: a
// subsequent successful empty pass satisfies all earlier cleanup requests.
struct PgsInventoryCleanupApi {
 uint32_t version,size;
 uint64_t (*request)(); // Unity owner thread only; zero means unavailable; otherwise an opaque completion ticket
 int (*pending)(uint64_t); // 1 pending, 0 complete or unavailable
};
extern "C" const void *pgs_inventory_host_api(uint32_t);
