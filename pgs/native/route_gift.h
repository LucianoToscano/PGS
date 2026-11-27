#pragma once
#include <cstdint>
struct PgsSharedMetadataOutput;
// Exchange gifts with Mateo on Routes: presses the game's own buttons through a gift-exchange NPC
// encounter (conversation, "Exchange gift", send, open). Owner-thread tick; config in transport slot 24.
void pgs_route_gift_tick(uint64_t tid, const PgsSharedMetadataOutput *metadata);
void pgs_route_gift_stop();
