#pragma once
#include <stdint.h>
struct PgsSharedMetadataOutput;
// Unity-thread entry points. Auto-Raid calls the shared capture primitive directly;
// only this manual encounter controller is governed by the Throws preference.
void pgs_auto_throw_tick(uint64_t tid, const PgsSharedMetadataOutput* metadata, bool raid_owns_game);
void pgs_auto_throw_enter(void* interaction);
void pgs_auto_throw_exit(void* interaction);
void pgs_auto_throw_stop();
bool pgs_auto_throw_pending();
