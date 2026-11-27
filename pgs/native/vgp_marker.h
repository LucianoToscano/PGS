#pragma once
#include <atomic>
#include <stdint.h>
// Feature 28 v1: synchronous read-only projection, no hooks/callbacks/retained objects.
// Caller roots target for the call. Native roots and releases every temporary on its owner thread.
struct PgsVgpMarkerConfig {
 uint32_t version,size;
 void *gc_new,*gc_get,*gc_free,*object_class,*invoke,*unbox,*assignable;
 void *alive,*camera,*transform,*position,*project,*width,*height;
 void *bool_class,*int_class,*vector_class,*camera_class,*transform_class,*wild_class,*stop_class;
};
struct PgsVgpMarkerResult {
 uint32_t version,size,visible,reserved;
 double x,y;
};
struct PgsVgpMarkerApi {
 uint32_t version,size;
 int (*install)(const PgsVgpMarkerConfig *);
 // 0 hidden, 1 projected (visible may be false offscreen), negative error. Output always initialized.
 // Lease is residual boottime ms, capped 2500. owner must match actual OS thread; zero lease hides.
 int (*project)(void *target,uint64_t lease_ms,uint64_t owner,PgsVgpMarkerResult *out);
};
static_assert(sizeof(PgsVgpMarkerConfig)==176,"marker config ABI");
static_assert(sizeof(PgsVgpMarkerResult)==32,"marker result ABI");
static_assert(sizeof(PgsVgpMarkerApi)==24,"marker API ABI");
extern "C" const void *pgs_vgp_marker_api(uint32_t version);
// Map tap-to-catch also marks lure, incense and event spawns. It publishes MapPokemon here once it
// has resolved it; until then the marker accepts only the classes in its config (and bound incense).
inline std::atomic<void *> g_pgr_vgp_marker_map_pokemon{nullptr};
