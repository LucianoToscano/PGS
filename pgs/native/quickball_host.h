#pragma once
#include "quickball_metadata.h"
#include "throws.h"
#include "unity_scheduler.h"
#include <stdint.h>

enum PgsQuickballHostStatus {
 PGS_QBH_OK=0,PGS_QBH_NOT_READY=1,PGS_QBH_EMPTY=2,
 PGS_QBH_BAD_CONFIG=-1,PGS_QBH_RECONFIG=-2,PGS_QBH_OFF_OWNER=-3,
 PGS_QBH_BUSY=-4,PGS_QBH_METADATA=-5,PGS_QBH_LEAF=-6,
 PGS_QBH_STOPPED=-7,PGS_QBH_OVERFLOW=-8,PGS_QBH_CLOCK=-9
};
enum PgsQuickballHostFlags {PGS_QBH_TRANSPORT=1};
enum PgsQuickballHostSites {PGS_QBH_SUBMIT=1,PGS_QBH_NAMEPLATE=2};
enum PgsQuickballHostCapabilities {
 PGS_QBH_SPEED=1,PGS_QBH_OBSERVERS=2,PGS_QBH_THROWS=4,
 PGS_QBH_ALWAYS_HIT=8,PGS_QBH_AR=16,PGS_QBH_MAP=32,PGS_QBH_IV=64
};
struct PgsQuickballHostRuntime {
 void *runtime_invoke,*gchandle_new,*gchandle_get_target,*gchandle_free;
 void *object_get_class,*object_unbox,*field_get_value,*class_is_assignable_from;
 void *object_new,*field_set_value,*string_new,*string_length,*string_chars,*type_get_object;
};
struct PgsQuickballHostConfig {
 uint32_t version,size,flags,reserved;
 const PgsQuickballMetaConfig *metadata;
 const PgsQuickballHostRuntime *runtime;
};
// Independent groups preserve original setters: the lease belongs to the settings
// update, never to the consumer tick. Deadline is measured by CLOCK_BOOTTIME.
struct PgsQuickballHostOptions {
 uint32_t version,size;
 uint32_t quick_allowed,throw_allowed,ar_allowed,map_allowed,iv_allowed;
 uint32_t grade,curve,always_hit,ar_enabled,map_mode,iv_catch,iv_owned;
 uint32_t lease_ms,reserved;
 uint64_t map_epoch;
};
struct PgsQuickballHostSample {
 uint32_t version,size,configured,metadata_ready,ready,stopping,capabilities,shared_sites;
 uint64_t owner_tid,ticks;
 uint32_t owned,queued;
 int32_t error,metadata_error;
};
struct PgsQuickballHostEvent {uint32_t version,size;uint64_t sequence;char kind[48];char json[1536];};
struct PgsQuickballHostApi {
 uint32_t version,size;
 int (*configure)(const PgsQuickballHostConfig *); // null selects bootstrap54+transport52
 int (*set_options)(const PgsQuickballHostOptions *);
 int (*shared_sites)(uint32_t installed_mask); // only0..3; attestation, not hook detection
 int (*tick)(uint64_t proven_tid);
 int (*stop)(); // revoke immediately; owner ticks restore/free before owned reaches0
 int (*sample)(PgsQuickballHostSample *);
 int (*next_event)(PgsQuickballHostEvent *);
 int (*rewrite_submit)(void *,PgsThrowValue *);
 // Output must hold TWO pointers: refreshed [nameplate, mapPokemon].
 uint64_t (*begin_catch)(void *,void *,uint64_t,void **);
 int (*end_catch)(uint64_t,uint64_t);
 PgsUnityWork on_unity_pulse;
};
static_assert(sizeof(PgsQuickballHostRuntime)==112,"Runtime ABI");
static_assert(sizeof(PgsQuickballHostConfig)==32,"Config ABI");
static_assert(sizeof(PgsQuickballHostOptions)==72,"Options ABI");
static_assert(sizeof(PgsQuickballHostSample)==64,"Sample ABI");
static_assert(sizeof(PgsQuickballHostEvent)==1600,"Event ABI");
static_assert(sizeof(PgsQuickballHostApi)==96,"API ABI");
extern "C" const void *pgs_quickball_host_api(uint32_t version);
