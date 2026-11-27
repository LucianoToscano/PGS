#pragma once
#include <stdint.h>
struct PgsTransferExecRequest;
struct PgsTransferExecEvent;
struct PgsSharedMetadataOutput;
// 0: ordinary transfer; 1: queued; 2: kept/refused. Never scan existing storage.
int pgs_evolve_transfer_offer(const PgsTransferExecRequest*,bool honor_keep_all);
void pgs_evolve_transfer_tick(uint64_t,const PgsSharedMetadataOutput*);
void pgs_evolve_transfer_stop(uint64_t);
bool pgs_evolve_transfer_event(const PgsTransferExecEvent*);
bool pgs_evolve_transfer_busy();
