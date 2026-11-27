#pragma once
#include "throws.h"

inline PgsThrowValue pgs_raid_throw_value(int ball) {
    PgsThrowValue value{};
    value.item=ball;value.radius=0.1f;value.bullseye=1;value.spinning=1;
    return value;
}

// Start with an ordinary straight hit, then use the same policy as a hand throw.
// This includes rating, per-throw variety and curveball preferences. Always Hit
// is intrinsic to Auto Throw; rating/curve defaults are exclusive to Auto-Raid.
inline bool pgs_manual_throw_value(const PgsThrowApi* api,void* ball,int item,PgsThrowValue& value) {
    value={};value.item=item;value.radius=1.0f;
    if(!api||!api->rewrite_submit||api->rewrite_submit(ball,&value)!=0)return false;
    value.missed=0;
    return true;
}
