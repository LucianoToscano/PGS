#pragma once
#include <stdint.h>
struct PgsSharedMetadataOutput;
void pgs_buddy_emotion_tick(uint64_t tid,const PgsSharedMetadataOutput *metadata);
void pgs_buddy_emotion_stop(uint64_t tid);
