#include "routes_gate.h"
#include <cmath>
#include <mutex>

namespace {
std::mutex mutex;
uint64_t generation=0,last=0,pending=0;
uint32_t action=0;
double lease=0,until=0,clockLast=0;
bool clockSeen=false,cancelled=false;
void revoke(){until=0;if(pending)cancelled=true;}
bool timeValid(double now){
  if(!std::isfinite(now)||now<0||(clockSeen&&now<clockLast)){revoke();return false;}
  clockLast=now;clockSeen=true;return true;
}
bool valid(uint64_t h){return h!=0&&h==generation;}
uint64_t open(double duration){
  std::lock_guard<std::mutex> guard(mutex);
  if(!std::isfinite(duration)||duration<=0||duration>2500||generation==UINT64_MAX)return 0;
  ++generation;lease=duration;until=0;pending=0;action=0;cancelled=false;
  return generation;
}
int set(uint64_t h,int allowed,int parsed,uint64_t seq,uint32_t nextAction,double now){
  std::lock_guard<std::mutex> guard(mutex);
  if(!valid(h))return PGS_RG_BAD_HANDLE;
  if(!timeValid(now))return PGS_RG_BAD_TIME;
  until=allowed==1?now+lease:0;
  if(!std::isfinite(until)){revoke();return PGS_RG_BAD_TIME;}
  if(allowed!=1){revoke();return PGS_RG_NOT_ALLOWED;}
  if(parsed!=1){if(parsed==0&&pending)cancelled=true;return parsed==0?PGS_RG_NO_COMMAND:PGS_RG_INVALID_COMMAND;}
  // JS numbers represent the bridge sequence. Reject values beyond exact integer precision.
  if(seq==0||seq>9007199254740991ULL||nextAction<PGS_RG_DISCOVER||nextAction>PGS_RG_PAUSE)
    return PGS_RG_INVALID_COMMAND;
  if(seq<=last)return PGS_RG_STALE_SEQ;
  last=seq;pending=seq;action=nextAction;cancelled=false;
  return PGS_RG_ACCEPTED;
}
int take(uint64_t h,double now,PgsRoutesGateResult *out){
  std::lock_guard<std::mutex> guard(mutex);
  if(!valid(h))return PGS_RG_BAD_HANDLE;
  if(!out)return PGS_RG_BAD_ARG;
  const bool clockOk=timeValid(now);
  *out={0,0,0};
  if(!pending)return clockOk?0:PGS_RG_BAD_TIME;
  *out={pending,action,static_cast<uint32_t>(!clockOk||cancelled||now>=until)};
  pending=0;action=0;cancelled=false;
  return 1;
}
int active(uint64_t h,double now){
  std::lock_guard<std::mutex> guard(mutex);
  if(!valid(h))return PGS_RG_BAD_HANDLE;
  if(!timeValid(now))return PGS_RG_BAD_TIME;
  return until!=0&&now<until?1:0;
}
int clear(uint64_t h){
  std::lock_guard<std::mutex> guard(mutex);
  if(!valid(h))return PGS_RG_BAD_HANDLE;
  pending=0;action=0;cancelled=false;return 0;
}
uint64_t lastSeq(uint64_t h){std::lock_guard<std::mutex> guard(mutex);return valid(h)?last:0;}
const PgsRoutesGateApi api={1,sizeof(PgsRoutesGateApi),open,set,take,active,clear,lastSeq};
}
extern "C" const void *pgs_routes_gate_api(uint32_t version){return version==1?&api:nullptr;}
