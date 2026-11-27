#ifndef PGS_NATIVE_ACCOUNT_HOST_H_
#define PGS_NATIVE_ACCOUNT_HOST_H_

#include <stddef.h>
#include <stdint.h>

#include "accounts.h"
#include "adventure_sync.h"
#include "runtime_bootstrap.h"
#include "runtime_metadata.h"
#include "shared_metadata.h"
#include "unity_scheduler.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
  PGS_ACCOUNT_HOST_FEATURE_ID = 68u,
  PGS_ACCOUNT_HOST_API_VERSION = 1u,

  PGS_ACH_CONFIG_VERSION = 1u,
  PGS_ACH_RUNTIME_VERSION = 1u,
  PGS_ACH_LOOKUP_VERSION = 1u,
  PGS_ACH_META_OUT_VERSION = 1u,
  PGS_ACH_OPTIONS_VERSION = 1u,
  PGS_ACH_SAMPLE_VERSION = 1u,
  PGS_ACH_EVENT_VERSION = 1u,

  PGS_ACH_MAX_ACCOUNTS_LEASE_MS = 2000u,
  PGS_ACH_MAX_ADVSYNC_LEASE_MS = 2500u,
  PGS_ACH_EVENT_QUEUE_MAX = 64u,
  PGS_ACH_CMD_MAX_BYTES = 256u,
  PGS_ACH_TOKEN_MAX_BYTES = 64u
};

enum PgsAccountHostStatus {
  PGS_ACH_OK = 0,
  PGS_ACH_NOT_READY = 1,
  PGS_ACH_ERR_BAD_CONFIG = -1,
  PGS_ACH_ERR_NOT_CONFIGURED = -2,
  PGS_ACH_ERR_OFF_OWNER = -3,
  PGS_ACH_ERR_BUSY = -4,
  PGS_ACH_ERR_STOPPED = -5,
  PGS_ACH_ERR_CLOCK = -6,
  PGS_ACH_ERR_RECONFIG = -7,
  PGS_ACH_ERR_METADATA = -8,
  PGS_ACH_ERR_INSTALL = -9,
  PGS_ACH_ERR_EMPTY = -10
};

enum PgsAccountHostCaps {
  PGS_ACH_CAP_NONE = 0u,
  PGS_ACH_CAP_ACCOUNTS = 1u << 0,
  PGS_ACH_CAP_ADVENTURE_SYNC = 1u << 1
};

enum PgsAccountHostConfigFlags {
  PGS_ACH_CFG_NONE = 0u,
  PGS_ACH_CFG_USE_TRANSPORT = 1u << 0,
  PGS_ACH_CFG_USE_BOOTSTRAP = 1u << 1,
  PGS_ACH_CFG_SUBSTITUTE_METADATA = 1u << 2,
  PGS_ACH_CFG_REQ_ACCOUNTS = 1u << 3,
  PGS_ACH_CFG_REQ_ADVSYNC = 1u << 4,
  PGS_ACH_CFG_REQ_ALL = PGS_ACH_CFG_REQ_ACCOUNTS | PGS_ACH_CFG_REQ_ADVSYNC,
  PGS_ACH_CFG_KNOWN_MASK = 0x1Fu
};

enum PgsAccountHostOptionFlags {
  PGS_ACH_OPT_NONE = 0u,
  PGS_ACH_OPT_SET_ACCOUNTS = 1u << 0,
  PGS_ACH_OPT_SET_ADVSYNC = 1u << 1,
  PGS_ACH_OPT_REVOKE_ONLY = 1u << 2,
  PGS_ACH_OPT_KNOWN_MASK = 0x7u
};

enum PgsAccountHostEventKind {
  PGS_ACH_EVT_NONE = 0u,
  PGS_ACH_EVT_ACCOUNTS_READY = 1u,
  PGS_ACH_EVT_SESSION_ENDED = 2u,
  PGS_ACH_EVT_LOGOUT_REQUESTED = 3u,
  PGS_ACH_EVT_LOGOUT_COMPLETE = 4u,
  PGS_ACH_EVT_LOGOUT_FAILED = 5u,
  PGS_ACH_EVT_SESSION_SAVED = 6u,
  PGS_ACH_EVT_LOGIN_RESET_COMPLETE = 7u,
  PGS_ACH_EVT_IDENTITY = 8u,
  PGS_ACH_EVT_ACCOUNTS_READ_ERROR = 9u,
  PGS_ACH_EVT_ADVSYNC_READY = 10u,
  PGS_ACH_EVT_ADVSYNC_UNAVAILABLE = 11u
};

// Fixed 192-byte runtime export bundle: Bootstrap 54 fixed 20 runtime exports
// plus the 3 additional dlsym-resolved IL2CPP exports required by Feature 16.
typedef struct PgsAccountHostRuntime {
  uint32_t version;
  uint32_t size;
  PgsBootRuntimeExports boot;
  void *type_get_object;
  void *string_new;
  void *string_length;
} PgsAccountHostRuntime;

// Explicit 40-byte service lookup handles (matches Feature 56 OPT_ITEMS_LOOKUP:
// H_IL_MAP, H_IL_FIND_M, H_IL_CONTAINER_M, H_IL_RESOLVE_M).
typedef struct PgsAccountHostItemsLookup {
  uint32_t version;
  uint32_t size;
  void *map_scene_context_class;
  void *find_object_of_type_method;
  void *map_get_container_method;
  void *container_resolve_method;
} PgsAccountHostItemsLookup;

// Fixed 352-byte validated metadata output for Feature 16 (Accounts) and Feature 2 (AdventureSync).
typedef struct PgsAccountHostMetadataOutput {
  uint32_t version;
  uint32_t size;
  uint32_t accounts_valid;
  uint32_t advsync_valid;
  int32_t accounts_error;
  int32_t advsync_error;
  int32_t promise_succeeded_value;
  int32_t promise_failed_value;

  // Accounts (Feature 16) resolved classes (12)
  void *boolean_class;
  void *string_class;
  void *future_class;
  void *map_scene_context_class;
  void *di_container_class;
  void *player_service_class;
  void *iplayer_service_class;
  void *auth_service_class;
  void *iauth_service_class;
  void *logout_wrapper_class;
  void *ilogout_wrapper_class;
  void *player_prefs_class;

  // Accounts (Feature 16) validated fields (3)
  void *auth_active_provider_field;
  void *future_status_field;
  void *future_is_disposed_field;

  // Accounts (Feature 16) validated methods (12) + hook target (1)
  void *find_object_of_type_method;
  void *map_get_container_method;
  void *container_resolve_method;
  void *player_get_id_method;
  void *player_get_name_method;
  void *auth_get_is_connected_method;
  void *auth_get_cached_credentials_method;
  void *wrapper_logout_method;
  void *auth_logout_method;
  void *prefs_has_key_method;
  void *prefs_delete_key_method;
  void *prefs_save_method;
  void *auth_logout_target_fn;

  // AdventureSync (Feature 2) resolved class (1), methods (2), code targets (6), offsets (2)
  void *adv_controller_class;
  void *adv_method_on_confirm;
  void *adv_method_on_decline;
  void *adv_code_update;
  void *adv_code_on_confirm;
  void *adv_code_on_decline;
  void *adv_code_init_initial;
  void *adv_code_init_instruction;
  void *adv_code_init_result;
  uint64_t adv_off_on_confirm;
  uint64_t adv_off_on_decline;
  uint64_t reserved;
} PgsAccountHostMetadataOutput;

// Fixed 96-byte host configuration. Passing nullptr to configure() selects
// Bootstrap 54 + Shared Host 61 + Transport 52 mode on the current attached thread.
typedef struct PgsAccountHostConfig {
  uint32_t version;
  uint32_t size;
  uint32_t flags;
  uint32_t reserved;
  uint64_t owner_tid;
  const void *module_base;
  uint64_t module_size;
  const PgsMetaExports *meta_exports;
  const PgsAccountHostRuntime *runtime;
  const PgsSharedMetadataOutput *shared_metadata;
  const PgsAccountHostItemsLookup *items_lookup;
  const PgsAccountHostMetadataOutput *substituted_metadata;
  pgs_meta_seg_fn seg_query;
  void *seg_ctx;
} PgsAccountHostConfig;

// Fixed 48-byte options struct.
typedef struct PgsAccountHostOptions {
  uint32_t version;
  uint32_t size;
  uint32_t flags;
  uint32_t accounts_allowed;
  uint32_t accounts_lease_ms;
  uint32_t advsync_allowed;
  uint32_t advsync_lease_ms;
  uint32_t reserved;
  const char *command;
  const char *command_token;
} PgsAccountHostOptions;

// Fixed 72-byte diagnostic sample struct.
typedef struct PgsAccountHostSample {
  uint32_t version;
  uint32_t size;
  uint32_t configured;
  uint32_t capabilities;
  uint32_t stopping;
  uint32_t accounts_cleared;
  uint32_t owned;
  uint32_t active_hook_depth;
  uint32_t active_roots;
  uint32_t last_cmd_kind;
  int32_t accounts_error;
  int32_t advsync_error;
  uint64_t owner_tid;
  uint64_t ticks;
  uint64_t last_cmd_token;
} PgsAccountHostSample;

// Fixed 2048-byte pull-queue event record.
typedef struct PgsAccountHostEvent {
  uint32_t version;
  uint32_t size;
  uint32_t kind_code;
  uint32_t reason_code;
  uint64_t sequence;
  char kind[40];
  char id[512];
  char name[512];
  char reason[128];
  char json[832];
} PgsAccountHostEvent;

// Fixed 80-byte Feature 68 API vtable.
typedef struct PgsAccountHostApi {
  uint32_t version;
  uint32_t size;
  int (*configure)(const PgsAccountHostConfig *config);
  int (*resolve_metadata)(const PgsAccountHostConfig *config, PgsAccountHostMetadataOutput *out);
  int (*set_options)(const PgsAccountHostOptions *options);
  int (*set_adventure_sync_allowed)(int allowed);
  int (*tick)(uint64_t tid);
  int (*stop)(void);
  int (*sample)(PgsAccountHostSample *out);
  int (*next_event)(PgsAccountHostEvent *out);
  void (*on_unity_pulse)(void *ctx, const PgsUnityPulse *pulse);
} PgsAccountHostApi;

#if defined(__cplusplus) && (defined(__LP64__) || defined(_LP64) || defined(__aarch64__) || defined(__x86_64__))
static_assert(sizeof(PgsAccountHostRuntime) == 192, "PgsAccountHostRuntime size must be 192 bytes");
static_assert(sizeof(PgsAccountHostItemsLookup) == 40, "PgsAccountHostItemsLookup size must be 40 bytes");
static_assert(sizeof(PgsAccountHostMetadataOutput) == 352, "PgsAccountHostMetadataOutput size must be 352 bytes");
static_assert(sizeof(PgsAccountHostConfig) == 96, "PgsAccountHostConfig size must be 96 bytes");
static_assert(sizeof(PgsAccountHostOptions) == 48, "PgsAccountHostOptions size must be 48 bytes");
static_assert(sizeof(PgsAccountHostSample) == 72, "PgsAccountHostSample size must be 72 bytes");
static_assert(sizeof(PgsAccountHostEvent) == 2048, "PgsAccountHostEvent size must be 2048 bytes");
static_assert(sizeof(PgsAccountHostApi) == 80, "PgsAccountHostApi size must be 80 bytes");
#endif

const void *pgs_account_host_api(uint32_t version);

#ifdef __cplusplus
}
#endif

#endif  // PGS_NATIVE_ACCOUNT_HOST_H_
