#pragma once
#include <stdint.h>
struct PgrSharedMetadataOutput;
void pgs_buddy_emotion_tick(uint64_t tid,const PgrSharedMetadataOutput *metadata);
void pgs_buddy_emotion_stop(uint64_t tid);
