/*
 * Stable C ABI for the PGS native migration pilot.
 *
 * New native clients resolve `pgs_native_api`; existing gameplay clients keep
 * resolving `pgrazor_native_api` (both names return the exact same ABI table).
 * calls it with the ABI version it was built against, and (on an exact match)
 * receives a pointer to a read-only, ordered function table prefixed by a
 * {version, size} header. Fields are never reordered or removed; a new ABI
 * version only appends fields and bumps PGS_NATIVE_API_VERSION.
 *
 * This PGS source header retains the legacy exported symbol and struct layout
 * as an explicit compatibility contract; the PGS factory is additive.
 */
#ifndef PGS_NATIVE_API_H
#define PGS_NATIVE_API_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Current version shared by both PGS and compatibility factories. */
#define PGS_NATIVE_API_VERSION 1u
#define PGRAZOR_NATIVE_API_VERSION PGS_NATIVE_API_VERSION

/* Fixed radius floor (metres) applied while the spawn policy is active. */
#define PGS_SPAWN_FLOOR 80.0
#define PGRAZOR_SPAWN_FLOOR PGS_SPAWN_FLOOR

/* Maximum accepted lease for a single policy window, in milliseconds. */
#define PGS_MAX_LEASE_MS 2500u
#define PGRAZOR_MAX_LEASE_MS PGS_MAX_LEASE_MS

/* Status codes returned by every table function. 0 == success. */
enum {
    PGS_OK = 0,
    PGS_ERR_NULL_ARG = 1,        /* required pointer argument was null */
    PGS_ERR_ALREADY_BOUND = 2,   /* install() requested at a different address (rebind refused) */
    PGS_ERR_HOOK_FAILED = 3,     /* Dobby could not install the hook / publish the original */
    PGS_ERR_BAD_LEASE = 4,       /* lease was 0 or exceeded PGS_MAX_LEASE_MS */
    PGS_ERR_NO_CLOCK = 5,        /* CLOCK_BOOTTIME was unavailable */
    PGS_ERR_NOT_INSTALLED = 6,   /* reserved: operation needs an installed hook */
    PGS_ERR_SELFTEST = 7,        /* a self-check assertion failed */
    PGS_ERR_UNSUPPORTED_VERSION = 8 /* reserved for negotiation callers */
};

/* Source aliases required by already-compiled C/C++ modules. */
#define PGRAZOR_OK PGS_OK
#define PGRAZOR_ERR_NULL_ARG PGS_ERR_NULL_ARG
#define PGRAZOR_ERR_ALREADY_BOUND PGS_ERR_ALREADY_BOUND
#define PGRAZOR_ERR_HOOK_FAILED PGS_ERR_HOOK_FAILED
#define PGRAZOR_ERR_BAD_LEASE PGS_ERR_BAD_LEASE
#define PGRAZOR_ERR_NO_CLOCK PGS_ERR_NO_CLOCK
#define PGRAZOR_ERR_NOT_INSTALLED PGS_ERR_NOT_INSTALLED
#define PGRAZOR_ERR_SELFTEST PGS_ERR_SELFTEST
#define PGRAZOR_ERR_UNSUPPORTED_VERSION PGS_ERR_UNSUPPORTED_VERSION

/* Telemetry snapshot of the spawn getter. Pull-only: the native layer never calls back into JS. */
typedef struct pgrazor_spawn_snapshot {
    double   original;  /* last radius the original getter returned */
    double   effective; /* last radius this layer returned to the caller */
    uint64_t count;     /* number of times the policy raised the radius to the floor */
} pgrazor_spawn_snapshot;

/*
 * install(address): install the spawn-getter hook at `address` once for the process
 * lifetime. The original pointer is published before the bound address so the
 * replacement never fabricates a radius. Installing the same address again returns
 * PGS_OK (idempotent); a different address returns PGS_ERR_ALREADY_BOUND.
 * The hook is never removed; see update(..., enabled=0) to disable its effect.
 */
typedef int (*pgrazor_install_fn)(void *address);
typedef pgrazor_install_fn pgs_install_fn;

/*
 * update(enabled, allowed, lease_ms): arm or clear the policy window.
 *   enabled == 0            -> clear immediately, hook passes the original radius through.
 *   enabled != 0            -> require 0 < lease_ms <= PGS_MAX_LEASE_MS and a usable
 *                              CLOCK_BOOTTIME; sets a monotonic deadline of now+lease.
 *   allowed                 -> existing foreground/readiness permission lease.
 * The floor only applies while enabled && allowed && now < deadline.
 */
typedef int (*pgrazor_update_fn)(int enabled, int allowed, uint64_t lease_ms);
typedef pgrazor_update_fn pgs_update_fn;

/* sample(out): copy the latest telemetry snapshot. Does not clear counters. */
typedef int (*pgrazor_sample_fn)(pgrazor_spawn_snapshot *out);
typedef pgrazor_sample_fn pgs_sample_fn;

/*
 * selftest(): run the self-contained Dobby hook self-check against an own function
 * (original chaining + clean detach, leaving no dangling hook). Explicit call only;
 * NEVER run automatically in production. Returns PGS_OK or PGS_ERR_SELFTEST.
 */
typedef int (*pgrazor_selftest_fn)(void);
typedef pgrazor_selftest_fn pgs_selftest_fn;

/* Ordered, read-only function table. Header first; function pointers in fixed order. */
typedef struct pgrazor_native_api_v1 {
    uint32_t version;              /* == PGS_NATIVE_API_VERSION */
    uint32_t size;                 /* == sizeof(pgs_native_api_v1) */
    pgs_install_fn  install;
    pgs_update_fn   update;
    pgs_sample_fn   sample;
    pgs_selftest_fn selftest;
} pgrazor_native_api_v1;

/* v1 remains available unchanged. v2 appends independent feature discovery. */
typedef const void *(*pgrazor_query_feature_fn)(uint32_t id, uint32_t version);
typedef pgrazor_query_feature_fn pgs_query_feature_fn;
typedef struct pgrazor_native_api_v2 {
    uint32_t version;
    uint32_t size;
    pgs_install_fn install;
    pgs_update_fn update;
    pgs_sample_fn sample;
    pgs_selftest_fn selftest;
    pgs_query_feature_fn query_feature;
} pgrazor_native_api_v2;

/*
 * Returns a pointer to a static const pgs_native_api_v1 when `version` matches
 * PGS_NATIVE_API_VERSION, otherwise NULL. The returned table lives for the
 * process lifetime and must not be freed or modified by the caller.
 */
/* Primary PGS C factory, sharing immutable function tables with the old name. */
const void *pgs_native_api(uint32_t version);

/* Required compatibility export for existing Android clients. */
const void *pgrazor_native_api(uint32_t version);

/* PGS source types retain the exact legacy ABI layout. */
typedef pgrazor_spawn_snapshot pgs_spawn_snapshot;
typedef pgrazor_native_api_v1 pgs_native_api_v1;
typedef pgrazor_native_api_v2 pgs_native_api_v2;

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* PGS_NATIVE_API_H */
