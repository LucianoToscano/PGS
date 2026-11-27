// Exercise the actual inventory host's public policy boundary. Leaf APIs are
// spies: no game, hooks, network or inventory mutations are performed here.
#include "inventory_host.h"
#include "items.h"
#include "buddy_feeding.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
#include <unistd.h>

namespace {
int32_t observed_berry = -1;
uint64_t observed_lease = 0;
pgrazor_items_rules_v1 observed_rules{};
int install_items(const pgrazor_items_config_v1 *) { return 0; }
int tick_items(const pgrazor_items_rules_v1 *rules, uint32_t, uint64_t, uint64_t) {
    observed_rules = *rules; return 0;
}
int clear_items(uint64_t) { return 0; }
int sample_items(pgrazor_items_sample_v1 *sample) { *sample = {}; return 0; }
int catalog_items(pgrazor_item_row *, uint32_t, uint32_t *written) { *written = 0; return 0; }
int drain_items(pgrazor_item_event *, uint32_t, uint32_t *written) { *written = 0; return 0; }
void *no_service() { return nullptr; }
const pgrazor_items_api_v1 item_api{1, sizeof(pgrazor_items_api_v1), install_items,
    tick_items, clear_items, sample_items, catalog_items, no_service, drain_items, no_service};
int install_buddy(const pgrazor_buddy_config_v1 *) { return 0; }
int tick_buddy(int32_t berry, uint64_t lease, uint64_t) {
    observed_berry = berry; observed_lease = lease; return 0;
}
int clear_buddy(uint64_t) { return 0; }
int sample_buddy(pgrazor_buddy_sample_v1 *sample) { *sample = {}; return 0; }
const pgrazor_buddy_api_v1 buddy_api{1, sizeof(pgrazor_buddy_api_v1), install_buddy,
    tick_buddy, clear_buddy, sample_buddy};
void *attached_thread() { static int token; return &token; }
}

extern "C" const void *pgrazor_items_api(uint32_t v) { return v == 1 ? &item_api : nullptr; }
extern "C" uint64_t pgrazor_items_cleanup_serial() { return 0; }
extern "C" const void *pgrazor_buddy_feeding_api(uint32_t v) { return v == 1 ? &buddy_api : nullptr; }
extern "C" const void *pgrazor_incubation_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_incoming_gifts_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_outgoing_gifts_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_runtime_transport_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_shared_host_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_runtime_bootstrap_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_unity_scheduler_api(uint32_t) { return nullptr; }
extern "C" const void *pgrazor_catch_canvas_api(uint32_t) { return nullptr; }
int pgrazor_hook(void *, void *, void **) { assert(false && "no social hooks in this fixture"); return -1; }

int main() {
    using namespace pgr_shared_meta;
    const auto *host = static_cast<const PgrInventoryHostApi *>(pgrazor_inventory_host_api(1));
    assert(host && host->version == 1);
    PgrSharedMetadataOutput metadata{};
    metadata.version = 2; metadata.size = sizeof(metadata);
    metadata.optional[OPT_ITEMS] = metadata.optional[OPT_ITEMS_LOOKUP] = metadata.optional[OPT_BUDDY] = PGR_SHARED_OPT_AVAILABLE;
    PgrInventoryRuntime runtime{};
    runtime.boot.thread_current = reinterpret_cast<void *>(&attached_thread);
    PgrInventoryHostConfig config{1, sizeof(config), 0, 0, &metadata, &runtime};
    assert(host->configure(&config) == 0);
    PgrInventoryHostOptions options{};
    options.version = 1; options.size = sizeof(options); options.lease_ms = 2500;
    options.buddy_allowed = 1; options.item_enabled = options.item_allowed = 1;
    options.item_rules = "707:13;708:29";
    assert(host->update(&options) == 0);
    for (int i = 0; i < 3; ++i) assert(host->tick(gettid()) == 0);
    for (int32_t berry : {701, 703, 705, 706, 708}) {
        options.buddy_berry = berry;
        assert(host->update(&options) == 0 && host->tick(gettid()) == 0);
        assert(observed_berry == berry && observed_lease > 0);
    }
    for (int32_t unsupported : {0, 707, 702, 709, -1}) {
        options.buddy_berry = unsupported;
        assert(host->update(&options) == 0 && host->tick(gettid()) == 0);
        assert(observed_berry == 0);
    }
    // Selecting Silver Pinap never rewrites inventory item identifiers or caps.
    assert(observed_rules.enabled && observed_rules.count == 2);
    assert(observed_rules.entries[0].id == 707 && observed_rules.entries[0].cap == 13);
    assert(observed_rules.entries[1].id == 708 && observed_rules.entries[1].cap == 29);
    options.buddy_berry = 708; options.buddy_allowed = 0;
    assert(host->update(&options) == 0 && host->tick(gettid()) == 0);
    assert(observed_berry == 708 && observed_lease == 0);
    assert(host->tick(gettid() + 1) == -5);
    std::puts("PASS inventory berry policy: Silver Pinap708, invalid707, lease gate, unchanged real item IDs");
}
