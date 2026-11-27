#pragma once
#include "shared_metadata.h"
#include "unity_scheduler.h"
#include <stdint.h>
enum PgsSpawnHostStatus {PGS_SPAH_OK=0,PGS_SPAH_NOT_READY=1,PGS_SPAH_EMPTY=2,PGS_SPAH_BAD_CONFIG=-1,PGS_SPAH_REBIND=-2,PGS_SPAH_OFF_OWNER=-3,PGS_SPAH_BUSY=-4,PGS_SPAH_UNAVAILABLE=-5,PGS_SPAH_STOPPED=-6,PGS_SPAH_TRANSPORT_ERROR=-7};
enum PgsSpawnHostFlags {PGS_SPAH_TRANSPORT=1};
// Explicit metadata is a validated56 output; test fixtures may supply a synthetic
// universe. Production passes null to configure and uses54+61 exclusively.
struct PgsSpawnHostConfig {uint32_t version,size,flags,exclusive_owner;const PgsSharedMetadataOutput *metadata;void *thread_current;uint64_t owner_tid;};
struct PgsSpawnHostOptions {uint32_t version,size,enabled,allowed,lease_ms,reserved;};
struct PgsSpawnHostSample {uint32_t version,size,configured,installed,stopping,ready;int32_t error,leaf_error;uint64_t owner_tid,ticks;double original,effective;uint64_t count;};
struct PgsSpawnHostEvent {uint32_t version,size;char json[384];};
struct PgsSpawnHostApi {
 uint32_t version,size;
 int (*configure)(const PgsSpawnHostConfig*);
 int (*update)(const PgsSpawnHostOptions*);
 int (*tick)(uint64_t tid);
 int (*stop)();
 int (*sample)(PgsSpawnHostSample*);
 int (*next_event)(PgsSpawnHostEvent*);
 PgsUnityWork on_unity_pulse;
};
static_assert(sizeof(PgsSpawnHostConfig)==40,"Spawn host config");
static_assert(sizeof(PgsSpawnHostOptions)==24,"Spawn host options");
static_assert(sizeof(PgsSpawnHostSample)==72,"Spawn host sample");
static_assert(sizeof(PgsSpawnHostApi)==64,"Spawn host API");
extern "C" const void *pgs_spawn_host_api(uint32_t version);
