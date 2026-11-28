#include "battery_policy.h"
#include <cassert>
#include <cstdio>
#include <stdexcept>
using battery_policy::Knob;
int main(){
 Knob<int> k;int value=60,writes=0;
 auto get=[&]{return value;};auto set=[&](int v){value=v;++writes;};
 auto cap=[](int n){return n>20?20:n;};auto cap10=[](int n){return n>10?10:n;};
 assert(k.on(get,set,cap)&&value==20&&k.applied&&writes==1);
 assert(!k.on(get,set,cap)&&writes==1);
 value=15;assert(!k.off(get,set)&&value==15&&!k.applied&&writes==1);
 value=60;assert(k.on(get,set,cap));value=45;
 assert(k.on(get,set,cap)&&value==20&&k.original==45);
 assert(k.off(get,set)&&value==45&&!k.applied);
 value=60;k.on(get,set,cap);assert(k.on(get,set,cap10)&&value==10&&k.original==60);
 assert(k.off(get,set)&&value==60);
 int first=60,second=90;
 k.on([&]{return first;},[&](int v){first=v;},cap);
 k.off([&]{return first;},[&](int v){first=v;});
 k.on([&]{return second;},[&](int v){second=v;},cap);
 k.off([&]{return second;},[&](int v){second=v;});
 assert(first==60&&second==90&&!k.applied);
 value=60;
 try{k.on(get,[](int){throw std::runtime_error("before");},cap);assert(false);}catch(const std::runtime_error&){}
 assert(!k.off(get,set)&&value==60&&!k.applied);
 try{k.on(get,[&](int v){value=v;throw std::runtime_error("after");},cap);assert(false);}catch(const std::runtime_error&){}
 assert(k.off(get,set)&&value==60&&!k.applied);
 k.on(get,set,cap);
 try{k.on(get,[](int){throw std::runtime_error("before");},cap10);assert(false);}catch(const std::runtime_error&){}
 assert(k.off(get,set)&&value==60&&!k.applied);
 k.on(get,set,cap);
 try{k.off(get,[](int){throw std::runtime_error("restore");});assert(false);}catch(const std::runtime_error&){}
 assert(k.applied&&k.off(get,set)&&value==60&&!k.applied);
 std::puts("PASS battery ownership: external change, independent assets, setter failure and restore");
}
