#pragma once
#include <stdint.h>
struct PgrSharedMetadataOutput;
void pgs_gift_batch_tick(uint64_t tid,const PgrSharedMetadataOutput *metadata);
void pgs_gift_batch_stop();
