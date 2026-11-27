#pragma once
#include <stdint.h>
struct PgsSharedMetadataOutput;
void pgs_research_tick(uint64_t tid,const PgsSharedMetadataOutput *metadata);
void pgs_research_stop();
