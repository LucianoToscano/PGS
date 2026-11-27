#pragma once
#include <stdint.h>
struct PgsSharedMetadataOutput;
// Unity owner only. Prepare before gameplay automation, so map taps have an explicit owner.
void pgs_map_auto_throw_tick(uint64_t tid,const PgsSharedMetadataOutput* md,bool blocked);
// True once a tapped Pokemon is being caught; false for a tap that is still waiting for VGP+.
bool pgs_map_auto_throw_active();
// The Pokemon being caught (rooted by the session, owner thread only), or null.
void* pgs_map_auto_throw_target();
void pgs_map_auto_throw_stop();
