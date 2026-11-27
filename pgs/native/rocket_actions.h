#pragma once
#include <stdint.h>
// Feature 20: Rocket action authorization/cadence only. No hooks or managed pointers.
// Called by the native combat controller, or by the incremental JS adapter when
// that controller is unavailable. Exactly one controller must drive this policy.
// begin() returns a generation ticket before candidate getters. claim() consumes it
// immediately before invoking the game method, rejecting any intervening revoke,
// scope/prompt change, expiry or wrong-thread call. No retry of a claimed action.
enum PgsRocketAction { PGS_ROCKET_QUICK=1, PGS_ROCKET_LEGACY_CHARGE=2,
 PGS_ROCKET_VNEXT_CHARGE=3, PGS_ROCKET_SHIELD=4 };
enum PgsRocketObserve { PGS_ROCKET_EXIT=0, PGS_ROCKET_ENTER=1,
 PGS_ROCKET_PROMPT_OPEN=2, PGS_ROCKET_PROMPT_CLOSE=3, PGS_ROCKET_SHIELD_USED=4 };
struct pgs_rocket_actions_api_v1 {
 uint32_t version,size;
 int (*update)(uint32_t mask,uint64_t remaining_ms,uint64_t proven_tid);
 int (*observe)(uint32_t kind,uint64_t proven_tid);
 uint64_t (*begin)(uint64_t proven_tid);
 int (*claim)(uint64_t ticket,uint32_t action,uint64_t proven_tid);
 int (*stop)(uint64_t proven_tid);
};
extern "C" const void *pgs_rocket_actions_api(uint32_t version);
