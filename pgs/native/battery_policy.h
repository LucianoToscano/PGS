#pragma once
// Conditional restoration: do not overwrite a newer value selected by the game.
namespace battery_policy {
template<class T>struct Knob {
 bool applied=false;T original{},ours{};
 template<class Get,class Set,class Lower>bool on(Get get,Set set,Lower lower){
  const T now=get();
  if(applied&&now==ours){
   const T want=lower(original);if(want==ours)return false;
   const T previous=ours;ours=want;
   try{set(want);}catch(...){try{if(get()==previous)ours=previous;}catch(...){}throw;}
   return true;
  }
  const T want=lower(now);
  if(want==now){applied=false;return false;}
  original=now;ours=want;applied=true;set(want);return true;
 }
 template<class Get,class Set>bool off(Get get,Set set){
  if(!applied)return false;
  if(get()!=ours){applied=false;return false;}
  set(original);applied=false;return true;
 }
};
}
