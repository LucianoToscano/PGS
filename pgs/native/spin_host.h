#pragma once
#include "shared_metadata.h"
#include "unity_scheduler.h"
#include <stdint.h>
enum PgsSpinHostStatus {PGS_SPH_OK=0,PGS_SPH_EMPTY=1,PGS_SPH_BAD_CONFIG=-1,PGS_SPH_REBIND=-2,PGS_SPH_OFF_OWNER=-3,PGS_SPH_BUSY=-4,PGS_SPH_STOPPED=-5,PGS_SPH_FAULT=-6};
enum PgsSpinHostFlags {PGS_SPH_TRANSPORT=1};
enum PgsSpinHostCapabilities {PGS_SPH_CAMERA=1,PGS_SPH_QUICK=2};
struct PgsSpinHostConfig {
 uint32_t version,size,flags,exclusive_owner;
 const PgrSharedMetadataOutput *metadata;
 const PgrSharedMetaExtraExports *extra;
 void *object_get_class,*field_get_value,*runtime_invoke,*object_unbox;
 void *(*thread_current)();
 uint64_t owner_tid;
};
struct PgsSpinHostOptions {uint32_t version,size,enabled,lease_ms;uint64_t epoch;};
struct PgsSpinHostSample {
 uint32_t version,size,configured,capabilities,stopping,owned;
 int32_t camera_error,quick_error;
 uint64_t owner_tid,ticks;
};
struct PgsSpinHostEvent {uint32_t version,size;char kind[48],json[640];};
struct PgsSpinHostApi {
 uint32_t version,size;
 int (*configure)(const PgsSpinHostConfig*);
 int (*update)(const PgsSpinHostOptions*);
 int (*tick)(uint64_t tid,uint64_t sequence,uint64_t opener_depth);
 int (*stop)();
 int (*sample)(PgsSpinHostSample*);
 int (*next_event)(PgsSpinHostEvent*);
 PgrUnityWork on_unity_pulse;
};
static_assert(sizeof(PgsSpinHostConfig)==80,"Spin host config");
static_assert(sizeof(PgsSpinHostOptions)==24,"Spin host options");
static_assert(sizeof(PgsSpinHostSample)==48,"Spin host sample");
static_assert(sizeof(PgsSpinHostEvent)==696,"Spin host event");
static_assert(sizeof(PgsSpinHostApi)==64,"Spin host API");
extern "C" const void *pgs_spin_host_api(uint32_t version);
