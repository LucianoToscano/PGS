#pragma once
#include "runtime_metadata.h"
#include "routes_schema.h"
#include <cstdint>

// Feature53/API1: compiled Routes class/field/method discovery. No hook or gameplay
// mutation. Caller supplies the real module and native IL2CPP exports once; all
// descriptors and validation decisions are compiled into the binary.
struct PgsRoutesMetadataConfig {
    uint32_t version,size;
    PgrMetaBindConfig binding;
    void *thread_current;
    uint64_t owner_tid;
};
struct PgsRoutesMetadataOutput {
    uint32_t version,size;
    const void *classes[pgs_routes_schema::kClassCount];
    const void *fields[pgs_routes_schema::kFieldCount];
    const void *methods[pgs_routes_schema::kMethodCount];
    const void *list_count,*list_item,*waypoint_count,*waypoint_item,*constructor;
};
struct PgsRoutesMetadataApi {
    uint32_t version,size,config_size,output_size;
    int (*resolve)(const PgsRoutesMetadataConfig *,PgsRoutesMetadataOutput *);
};
static_assert(sizeof(PgsRoutesMetadataConfig)==88,"LP64 config");
static_assert(sizeof(PgsRoutesMetadataApi)==24,"LP64 API");
extern "C" const void *pgs_routes_metadata_api(uint32_t version);
