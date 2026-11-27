// Exercise the production panel with a small managed Canvas hierarchy, without Unity or a device.
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <vector>
static void *fixture_symbol(void *, const char *);
#define dlsym fixture_symbol
#include "iv_panel.cpp"
#undef dlsym

namespace {
int canvas_class, component_class, game_object_class, graphic_class;
struct Method { const char *name; unsigned count; };
Method methods[] = {{"get_transform",0},{"get_gameObject",0},{"get_layer",0},{"set_layer",1},
 {"get_childCount",0},{"GetChild",1},{"get_parent",0},{"get_sortingOrder",0},
 {"set_sortingOrder",1},{"set_overrideSorting",1},{"GetComponent",1},
 {"GetComponentInParent",1},{"AddComponent",1},{"GetComponentsInChildren",2}};
struct Object {
 Object *game_object=nullptr,*transform=nullptr,*parent=nullptr,*canvas=nullptr;
 int layer=0,order=0;bool override_sorting=false;
 std::vector<Object*> children;
};
Object screen_go,screen_transform,screen_canvas,label_go,label_transform,label,
       panel_go,panel_transform,panel_canvas,child_go,child_transform;
int added=0,boxed=0;bool fail_order=false;

void *object_class(void *) { return &component_class; }
void *object_unbox(void *value) { return value; }
void *identity(void *value) { return value; }
void *find_method(void *,const char *name,int count) {
 for (auto &m:methods) if (!std::strcmp(m.name,name)&&m.count==unsigned(count)) return &m;
 assert(false);return nullptr;
}
bool is_generic(void *) { return false; }
unsigned param_count(void *value) { return static_cast<Method*>(value)->count; }
void *next_method(const void *,void **iterator) {
 auto i=reinterpret_cast<uintptr_t>(*iterator);
 if (i>=sizeof(methods)/sizeof(methods[0])) return nullptr;
 *iterator=reinterpret_cast<void*>(i+1);return &methods[i];
}
const char *method_name(void *value) { return static_cast<Method*>(value)->name; }
const void *method_param(void *,unsigned index) { return index==0?"System.Type":"System.Boolean"; }
char *type_name(const void *value) { return strdup(static_cast<const char*>(value)); }
int resolve(const PgrMetaClassQuery *query,PgrMetaClassResult *out) {
 if (!std::strcmp(query->name,"Canvas")) out->klass=&canvas_class;
 else if (!std::strcmp(query->name,"Component")) out->klass=&component_class;
 else if (!std::strcmp(query->name,"GameObject")) out->klass=&game_object_class;
 else if (!std::strcmp(query->name,"MaskableGraphic")) out->klass=&graphic_class;
 else return -1;
 return 0;
}
PgrMetaApi metadata{};
Object *go(Object *o) { return o->game_object?o->game_object:o; }
void *managed(void *value,void *self,void **args,void **exception) {
 *exception=nullptr;const char *name=static_cast<Method*>(value)->name;
 auto o=static_cast<Object*>(self);assert(o);
 if (!std::strcmp(name,"get_transform")) return o->transform;
 if (!std::strcmp(name,"get_gameObject")) return go(o);
 if (!std::strcmp(name,"get_parent")) return o->parent;
 if (!std::strcmp(name,"get_layer")) { boxed=o->layer;return &boxed; }
 if (!std::strcmp(name,"set_layer")) { o->layer=*static_cast<int*>(args[0]);return nullptr; }
 if (!std::strcmp(name,"get_childCount")) { boxed=int(o->children.size());return &boxed; }
 if (!std::strcmp(name,"GetChild")) return o->children.at(*static_cast<int*>(args[0]));
 if (!std::strcmp(name,"get_sortingOrder")) {
  if (fail_order) { *exception=&component_class;return nullptr; }
  boxed=o->order;return &boxed;
 }
 if (!std::strcmp(name,"set_sortingOrder")) { o->order=*static_cast<int*>(args[0]);return nullptr; }
 if (!std::strcmp(name,"set_overrideSorting")) { o->override_sorting=*static_cast<bool*>(args[0]);return nullptr; }
 if (!std::strcmp(name,"GetComponent")) { assert(args[0]==&canvas_class);return go(o)->canvas; }
 if (!std::strcmp(name,"GetComponentInParent")) {
  assert(args[0]==&canvas_class);
  for (auto current=o->transform?o->transform:o;current;current=current->parent)
   if (go(current)->canvas) return go(current)->canvas;
  return nullptr;
 }
 if (!std::strcmp(name,"AddComponent")) {
  assert(o==&panel_go&&args[0]==&canvas_class&&!o->canvas);++added;
  return o->canvas=&panel_canvas;
 }
 if (!std::strcmp(name,"GetComponentsInChildren")) return nullptr;
 assert(false);return nullptr;
}
}
static void *fixture_symbol(void *,const char *name) {
 if (!std::strcmp(name,"il2cpp_type_get_object")) return reinterpret_cast<void*>(identity);
 if (!std::strcmp(name,"il2cpp_class_get_methods")) return reinterpret_cast<void*>(next_method);
 if (!std::strcmp(name,"il2cpp_method_get_name")) return reinterpret_cast<void*>(method_name);
 if (!std::strcmp(name,"il2cpp_method_get_param")) return reinterpret_cast<void*>(method_param);
 assert(false);return nullptr;
}
extern "C" const void *pgs_runtime_metadata_api(uint32_t) { return &metadata; }
extern "C" const void *pgs_runtime_bootstrap_api(uint32_t) { return nullptr; }
extern "C" const void *pgs_runtime_transport_api(uint32_t) { return nullptr; }
void pgs_iv_display_set_panel_hooks(const PgsIvPanelHooks *) {}

int main() {
 metadata.resolve_class=resolve;
 boot.runtime.object_get_class=(void*)object_class;boot.runtime.object_unbox=(void*)object_unbox;
 boot.runtime.runtime_invoke=(void*)managed;boot.meta.class_get_method_from_name=(void*)find_method;
 boot.meta.class_get_type=(void*)identity;boot.meta.method_is_generic=(void*)is_generic;
 boot.meta.method_get_param_count=(void*)param_count;boot.meta.type_get_name=(void*)type_name;boot.meta.mem_free=(void*)free;
 get_component=find_method(nullptr,"GetComponent",1);
 screen_go.transform=&screen_transform;screen_go.canvas=&screen_canvas;
 screen_transform.game_object=&screen_go;screen_canvas.order=10;
 label_go.transform=&label_transform;label_go.layer=9;label_transform.game_object=&label_go;
 label_transform.parent=&screen_transform;label.game_object=&label_go;label.transform=&label_transform;
 panel_go.transform=&panel_transform;panel_transform.game_object=&panel_go;panel_transform.parent=&label_transform;
 child_transform.game_object=&child_go;panel_transform.children.push_back(&child_transform);
 Line line;line.panel=&panel_go;

 draw_in_front(line,&label);
 assert(added==1&&panel_canvas.override_sorting&&panel_canvas.order==11);
 assert(panel_go.layer==9&&child_go.layer==9);
 // Reusing the same details panel over the Pokedex raises the parent canvas order.
 screen_canvas.order=30;draw_in_front(line,&label);
 assert(added==1&&panel_canvas.order==31);
 // Repeated layout never selects its own nested canvas and climbs one layer per frame.
 draw_in_front(line,&label);assert(added==1&&panel_canvas.order==31);
 screen_canvas.order=4;draw_in_front(line,&label);assert(panel_canvas.order==5);
 // A detached panel or absent screen canvas is left untouched, without adding another canvas.
 panel_transform.parent=nullptr;draw_in_front(line,&label);assert(added==1&&panel_canvas.order==5);
 panel_transform.parent=&label_transform;screen_go.canvas=nullptr;
 draw_in_front(line,&label);assert(added==1&&panel_canvas.order==5);
 screen_go.canvas=&screen_canvas;fail_order=true;bool rejected=false;
 try { draw_in_front(line,&label); } catch (const Failure &) { rejected=true; }
 assert(rejected&&added==1&&panel_canvas.order==5);
 puts("PASS IV panel production canvas: first show, reused screen order, stable relayout, missing parent and managed failure");
}
