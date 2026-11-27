#pragma once
#include <stdint.h>
// Feature57: compiled result/error callback dispatch for feature23. Exact game
// ABI: instance void zlc(ReleasePokemonOutProto), zld(System.String), followed
// by MethodInfo*. No JavaScript callback or event draining inside either hook.
// Caller validates metadata and relinquishes both Gum targets before install.
// Hooks/trampolines remain process lifetime, including partial install failure.
struct PgsTransferObserversConfig {
 uint32_t version,size;
 void *result_address,*error_address;
 void *thread_current,*gchandle_new,*gchandle_get_target,*gchandle_free;
};
struct PgsTransferObserversApi {
 uint32_t version,size;
 int (*install)(const PgsTransferObserversConfig *);
 int (*installed)();
};
static_assert(sizeof(PgsTransferObserversConfig)==56,"Transfer observers config");
static_assert(sizeof(PgsTransferObserversApi)==24,"Transfer observers API");
extern "C" const void *pgs_transfer_observers_api(uint32_t);
