// Standalone Android integration test. Never linked into the app library.
#include "pgs_native_api.h"
#include <dlfcn.h>
#include <cstdio>
#include <cmath>
#include <ctime>
#include <limits>

__attribute__((noinline)) double target(void *value, void *) {
    // Give the relocator a realistic, non-foldable entry on both architectures.
    asm volatile("nop; nop; nop; nop; nop; nop; nop; nop" ::: "memory");
    return *static_cast<double *>(value);
}
int main(int argc,char **argv) {
    if(argc!=2)return 1;
    void *lib=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!lib){std::puts(dlerror());return 2;}
    auto get=reinterpret_cast<const void *(*)(uint32_t)>(dlsym(lib,"pgs_native_api"));
    auto legacy=reinterpret_cast<const void *(*)(uint32_t)>(dlsym(lib,"pgs_native_api"));
    if(!get||!legacy||get(0)!=nullptr||legacy(0)!=nullptr)return 3;
    // Old and new names must point to identical read-only ABI tables.
    if(get(1)!=legacy(1)||get(2)!=legacy(2)||get(3)!=nullptr)return 20;
    auto api=static_cast<const pgs_native_api_v1 *>(get(1));
    if(!api||api->size!=sizeof(*api))return 4;
    if(api->selftest()!=0)return 5;
    double (*volatile call)(void*,void*)=&target;
    double value=50;
    if(call(&value,nullptr)!=50)return 6;
    if(api->install(reinterpret_cast<void *>(&target))!=0)return 7;
    if(call(&value,nullptr)!=50)return 8;
    if(api->update(1,1,2500)!=0||call(&value,nullptr)!=80)return 9;
    value=120;if(call(&value,nullptr)!=120)return 10;
    value=std::numeric_limits<double>::quiet_NaN();if(!std::isnan(call(&value,nullptr)))return 11;
    value=50;if(api->update(0,0,0)!=0||call(&value,nullptr)!=50)return 12;
    if(api->update(1,1,10)!=0||call(&value,nullptr)!=80)return 13;
    timespec pause{0,30000000};nanosleep(&pause,nullptr);
    if(call(&value,nullptr)!=50)return 14;
    if(api->update(1,0,2500)!=0||call(&value,nullptr)!=50)return 15;
    if(api->update(1,1,2501)!=PGS_ERR_BAD_LEASE||call(&value,nullptr)!=50)return 16;
    if(api->install(reinterpret_cast<void *>(&target))!=0)return 17;
    if(api->install(reinterpret_cast<void *>(&main))!=PGS_ERR_ALREADY_BOUND)return 18;
    pgs_spawn_snapshot sample{};
    if(api->sample(&sample)!=0||sample.count!=2||sample.effective!=50)return 19;
    std::puts("PASS PGS/legacy native factories, Dobby chaining, policy, disable, invalid input, lease expiry, idempotence, telemetry");
    // Process lifetime hook: deliberately do not dlclose while target is patched.
    return 0;
}
