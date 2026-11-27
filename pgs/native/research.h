#pragma once
#include <stdint.h>
struct PgrSharedMetadataOutput;
void pgs_research_tick(uint64_t tid,const PgrSharedMetadataOutput *metadata);
void pgs_research_stop();
