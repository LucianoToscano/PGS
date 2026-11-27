#pragma once
#include "shared_metadata.h"
#include "unity_scheduler.h"
#include "transfer_execution.h"
#include <stdint.h>

// Feature61. Native catch host; optional gameplay hosts are separate consumers.
enum PgsSharedHostCapability : uint32_t {
 PGS_SHH_SUMMARY=1, PGS_SHH_DETAILS=2, PGS_SHH_RECOVERY=4,
 PGS_SHH_CANVAS=8,PGS_SHH_DISCOVERY=16,PGS_SHH_TRANSFER=32,PGS_SHH_DIRECT=64
};
enum PgsSharedHostFlags : uint32_t { PGS_SHH_ALLOWED=1,PGS_SHH_DISMISS=2,PGS_SHH_TRANSFER_ENABLED=4,PGS_SHH_KEEP_ALL=8 };
struct PgsSharedHostConfig {
 uint32_t version,size;
 PgsSharedMetadataConfig metadata;
 void *object_get_class,*field_get_value,*runtime_invoke,*object_unbox,*string_length;
 uint32_t exclusive_hooks,transport_flags; // bit0: compiled52 settings + event delivery; no JS heartbeat/drain
};
static_assert(sizeof(PgsSharedHostConfig)==152,"LP64 host config");
struct PgsSharedHostOptions {
 uint32_t version,size,flags,protect;
 uint64_t epoch,remaining_ms;
 const int32_t *keep_ids;
 uint32_t keep_count,keep_iv; // keep_iv: PgsTransferInput.keep_iv (0 = the original 90% cutoff)
};
static_assert(sizeof(PgsSharedHostOptions)==48,"LP64 options");
struct PgsSharedHostEvent {
 uint32_t version,size,kind,flags;
 int32_t status,before,after,reason;
 uint64_t serial,slot,tid;
};
static_assert(sizeof(PgsSharedHostEvent)==56,"LP64 event");
struct PgsSharedHostSample {
 uint32_t version,size,ready,capabilities;
 uint32_t stopping,fault,records,roots;
 uint64_t owner_tid,ticks,hook_frames;
};
static_assert(sizeof(PgsSharedHostSample)==56,"LP64 sample");
struct PgsSharedHostApi {
 uint32_t version,size;
 // nullptr: compiled54 snapshot + validated exports; caller must already be
 // attached on Unity owner thread and own exclusive hooks. Returns1 to retry.
 int (*configure)(const PgsSharedHostConfig*);
 int (*update)(const PgsSharedHostOptions*);
 int (*tick)(uint64_t tid,uint64_t sequence);
 int (*stop)();
 int (*sample)(PgsSharedHostSample*);
 int (*next_event)(PgsSharedHostEvent*);
 const PgsSharedMetadataOutput *(*metadata)();
 void (*on_unity_pulse)(void*,const PgsUnityPulse*);
};
static_assert(sizeof(PgsSharedHostApi)==72,"LP64 API");
// One transfer executor, policy epoch and FIFO owner for catch and VGP hosts.
// Owner-thread only. Callers retain their managed arguments across submit.
struct PgsSharedHostTransferApi {
 uint32_t version,size;
 int (*ready)();
 int (*submit)(const PgsTransferExecRequest*,uint64_t*);
 int (*next_event)(PgsTransferExecEvent*);
};
static_assert(sizeof(PgsSharedHostTransferApi)==32,"LP64 transfer broker API2");
extern "C" const void *pgs_shared_host_api(uint32_t version);
