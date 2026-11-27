#pragma once
#include <stdint.h>

// Feature70: compiled owner of the single post-ExecuteTasks scheduler. This
// foundation intentionally reports unintegrated hosts as PENDING, never ready.
enum PgsRuntimeHostState : uint32_t {
 PGS_RTH_WAITING=0,PGS_RTH_CONFIGURED=1,PGS_RTH_READY=2,
 PGS_RTH_FAILED=3,PGS_RTH_STOPPED=4,PGS_RTH_PENDING=5
};
struct PgsRuntimeHostConfig {
 uint32_t version,size,exclusive_owner,reserved;
 // exclusive_owner must be exactly1: ALL JavaScript/Gum owners have retired.
 // This attests process ownership; it cannot detect an undisclosed hook owner.
};
struct PgsRuntimeHostStatus {
 uint32_t feature,state;int32_t error;uint32_t capabilities,owned,reserved;
};
struct PgsRuntimeHostSample {
 uint32_t version,size,installed,stopping;
 int32_t fault;uint32_t pending_mask,ready_mask,reserved;
 uint64_t owner_tid,generation,pulses;
 PgsRuntimeHostStatus hosts[12]; // features60..69,58,71; masks index this array
};
struct PgsRuntimeHostApi {
 uint32_t version,size;
 // Only an already-attached Unity owner may configure.54 and52 must be ready.
 // Returns1 for bootstrap/transport not ready; no hooks before attestation.
 int (*configure)(const PgsRuntimeHostConfig*);
 // Immediate leaf revocation. Scheduler remains active for owner-thread cleanup.
 int (*stop)();
 int (*sample)(PgsRuntimeHostSample*);
};
static_assert(sizeof(PgsRuntimeHostConfig)==16,"runtime manager config");
static_assert(sizeof(PgsRuntimeHostStatus)==24,"runtime manager host status");
static_assert(sizeof(PgsRuntimeHostSample)==344,"runtime manager sample");
static_assert(sizeof(PgsRuntimeHostApi)==32,"runtime manager API");
extern "C" const void *pgs_runtime_host_api(uint32_t version);
