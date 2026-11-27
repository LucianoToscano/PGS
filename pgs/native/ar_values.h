#pragma once
#include <stdint.h>
struct PgsSharedMetadataOutput;
// Reads the game master's AR+ thresholds once and hands the AR+ throw hook values inside them.
void pgs_ar_values_tick(uint64_t tid,const PgsSharedMetadataOutput *metadata);
