#pragma once
#include <stdint.h>
struct PgrSharedMetadataOutput;
void pgs_evolution_tick(uint64_t,const PgrSharedMetadataOutput*);
void pgs_evolution_stop(uint64_t);
bool pgs_evolution_busy();
