#pragma once
#include <stdint.h>
struct PgsSharedMetadataOutput;
void pgs_gift_batch_tick(uint64_t tid,const PgsSharedMetadataOutput *metadata);
void pgs_gift_batch_stop();
