// Reuse the existing managed heap/metadata fixtures, linking the real iv_display.cpp.
// Hook dispatch is simulated; this does not test Dobby, Unity rendering or game offsets.
#define main retained_iv_display_fixture_main
#include "iv_display_test.cpp"
#undef main
#include <vector>

int pgs_hook(void *address,void *replacement,void **original) {
 *original=address;
 if (address==(void*)target_owned) call_owned=reinterpret_cast<decltype(call_owned)>(replacement);
 else if (address==(void*)target_setup) call_setup=reinterpret_cast<decltype(call_setup)>(replacement);
 else return -1;
 return 0;
}
extern "C" const void *pgs_runtime_bootstrap_api(uint32_t) { return nullptr; }

namespace {
int shown_level=0,shows=0,hides=0,destroyed_panel_reads=0;
void *shown_text=nullptr;
FakePanel *destroy_on_show=nullptr;
void *fail_root_object=nullptr;
uintptr_t refresh_gc_new(void *object,int pinned) {
 return object==fail_root_object?0:fake_gc_new(object,pinned);
}
void refresh_field_get(void *object,void *field,void *out) {
 if (fake_obj_class(object)==&cls_panel&&static_cast<FakePanel*>(object)->destroyed)
  ++destroyed_panel_reads;
 fake_field_get(object,field,out);
}
bool panel_ready() { return true; }
bool panel_show(bool owned,void *text,int32_t level,int,int,int,const PgsPvpBest *) {
 assert(owned);shown_text=text;shown_level=level;++shows;
 if (destroy_on_show) {destroy_on_show->destroyed=true;destroy_on_show=nullptr;}
 return true;
}
void panel_hide(void *) { ++hides; }
const PgsIvPanelHooks panel_hooks{panel_ready,panel_show,panel_hide};
void poll_owned() { usleep(160000);assert(g_api->tick(g_owner,0)==PGS_IV_OK); }
void enable_owned(uint64_t lease=2000) { assert(g_api->update(0,1,lease,g_owner)==PGS_IV_OK); }
void clean() {
 assert(g_api->tick(g_owner,1)==PGS_IV_OK);
 auto s=take_sample();assert(s.owned_count==0&&s.owned_root_count==0&&g_live.empty());
}
}

int main() {
 g_api=static_cast<const PgrIvDisplayApi*>(pgs_iv_display_api(1));assert(g_api);
 g_owner=this_tid();auto config=make_config();config.gchandle_new=(void*)refresh_gc_new;
 config.field_get_value=(void*)refresh_field_get;
 assert(g_api->install(&config)==PGS_IV_OK);
 pgs_iv_display_set_panel_hooks(&panel_hooks);enable_owned();
 FakeText text;init_text(&text);FakePokemon pokemon{&cls_pokemon,123,15,15,15,.5f,0};
 FakePanel panel{&cls_panel,&text,&pokemon,&g_gm_obj};
 call_owned(&panel,&pokemon,nullptr);
 auto s=take_sample();assert(s.owned_count==1&&s.owned_cp==123&&shown_level==20);
 const size_t retained=g_live.size();

 pokemon.cp=200;pokemon.cpmul=.55f;poll_owned();
 s=take_sample();assert(s.owned_cp==200&&s.owned_level_half==22&&shown_level==22);
 assert(s.owned_count==1&&g_live.size()==retained&&retained==3); // Text, source panel and proto identity.
 // A level change can matter even when the integer CP remains the same.
 pokemon.cpmul=.6f;poll_owned();assert(take_sample().owned_level_half==24&&shown_level==24);
 FakePokemon replacement{&cls_pokemon,333,15,15,15,.65f,0};panel.displayed=&replacement;
 poll_owned();assert(take_sample().owned_cp==333&&shown_level==26);

 // Replacing a proto at identical CP/level must refresh its IV/PvP identity too.
 FakePokemon same_stats=replacement;same_stats.atk=0;panel.displayed=&same_stats;
 poll_owned();assert(take_sample().owned_attack==0&&g_live.size()==retained);
 same_stats.atk=1;poll_owned();assert(take_sample().owned_attack==1); // in-place IV change
 enable_owned();
 FakePokemon same_values=same_stats;panel.displayed=&same_values;
 auto serial=take_sample().owned_serial;
 poll_owned();assert(take_sample().owned_serial==serial+1&&g_live.size()==retained);
 panel.displayed=&replacement;poll_owned();assert(take_sample().owned_attack==15);

 // Moving GC targets are resolved from handles, not retained panel addresses.
 FakePanel moved=panel;replacement.cp=444;replacement.cpmul=.7f;
 g_redirect_from=&panel;g_redirect_to=&moved;poll_owned();
 assert(take_sample().owned_cp==444&&shown_level==28&&g_live.size()==retained);
 g_redirect_from=g_redirect_to=nullptr;
 for (const auto &entry:g_live) assert(entry.second!=&panel);

 replacement.cp=555;fail_root_object=&moved;poll_owned();
 assert(take_sample().owned_cp==444&&g_live.size()==retained);
 fail_root_object=nullptr;poll_owned();assert(take_sample().owned_cp==555&&g_live.size()==retained);
 replacement.klass=&cls_other;replacement.cp=600;poll_owned();
 assert(take_sample().owned_cp==555);replacement.klass=&cls_pokemon;

 assert(g_api->disable()==PGS_IV_OK);int prior=shown_level;poll_owned();
 assert(take_sample().owned_cp==555&&shown_level==prior);
 enable_owned();poll_owned();assert(take_sample().owned_cp==600);
 replacement.cp=700;enable_owned(1);poll_owned();assert(take_sample().owned_cp==600);
 enable_owned();poll_owned();assert(take_sample().owned_cp==700);

 replacement.cp=800;usleep(160000);
 std::thread wrong([&]{assert(g_api->tick(g_owner,0)==PGS_IV_OK);});wrong.join();
 assert(take_sample().owned_cp==700);
 assert(g_api->tick(g_owner,0)==PGS_IV_OK);assert(take_sample().owned_cp==800);
 // Revoking while capturing the refreshed label must not apply the new level.
 replacement.cp=900;replacement.cpmul=.75f;g_getfont_disables=true;poll_owned();
 assert(shown_level==28&&take_sample().owned_cp==900);
 enable_owned();poll_owned();assert(shown_level==30);

 // A moved proto retains identity through its handle; no unnecessary recapture follows GC.
 FakePokemon moved_proto=replacement;moved.displayed=&moved_proto;
 g_redirect_from=&replacement;g_redirect_to=&moved_proto;serial=take_sample().owned_serial;
 poll_owned();assert(take_sample().owned_serial==serial&&g_live.size()==retained);
 moved.displayed=&replacement;g_redirect_from=g_redirect_to=nullptr;

 // Rebuilding cpText on the same panel replaces one record, even without a CP change.
 FakeText new_text;init_text(&new_text);moved.cp_text=&new_text;enable_owned();
 poll_owned();s=take_sample();
 assert(s.owned_count==1&&g_live.size()==retained&&shown_text==&new_text);
 for (const auto &entry:g_live) assert(entry.second!=&text);
 serial=s.owned_serial;const int before_hides=hides;
 poll_owned();assert(take_sample().owned_serial==serial&&hides==before_hides&&g_live.size()==retained);
 // The original DoUpdate hook also deduplicates a panel whose Text was replaced.
 FakeText newest_text;init_text(&newest_text);moved.cp_text=&newest_text;
 call_owned(&moved,&replacement,nullptr);
 assert(take_sample().owned_count==1&&g_live.size()==retained&&shown_text==&newest_text);
 for (const auto &entry:g_live) assert(entry.second!=&new_text);

 // A destroyed panel is discarded even if its former Text remains alive. Never inspect its fields.
 moved.destroyed=true;replacement.cp=901;serial=take_sample().owned_serial;
 poll_owned();s=take_sample();
 assert(s.owned_count==0&&s.owned_root_count==0&&g_live.empty()&&destroyed_panel_reads==0);
 assert(s.owned_serial==serial);
 // Destruction can also reenter from relayout after the tick's first life check.
 moved.destroyed=false;enable_owned();call_owned(&moved,&replacement,nullptr);
 destroy_on_show=&moved;replacement.cp=902;serial=take_sample().owned_serial;
 poll_owned();s=take_sample();
 assert(moved.destroyed&&s.owned_count==0&&g_live.empty()&&destroyed_panel_reads==0);
 assert(s.owned_serial==serial);
 clean();int old_shows=shows;replacement.cp=901;poll_owned();assert(shows==old_shows&&g_live.empty());

 // Tracking inherits the existing eight-panel cap and stop cleanup, with no global storage scan.
 FakeText texts[PGS_IV_MAX_OWNED+2];FakePanel panels[PGS_IV_MAX_OWNED+2];
 enable_owned();
 for (int i=0;i<PGS_IV_MAX_OWNED+2;++i) {
  init_text(&texts[i]);panels[i]=FakePanel{&cls_panel,&texts[i],&replacement,&g_gm_obj};
  call_owned(&panels[i],&replacement,nullptr);
  assert(take_sample().owned_count<=PGS_IV_MAX_OWNED&&g_live.size()<=3*PGS_IV_MAX_OWNED);
 }
 assert(take_sample().owned_count==PGS_IV_MAX_OWNED);clean();
 puts("PASS owned IV refresh: CP, level-only, same-stat proto replacement, moving GC, replaced Text, destroyed panel, allocation failure, lease, owner, revocation, cap and stop");
}
