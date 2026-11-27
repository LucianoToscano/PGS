#pragma once
#include "game_bindings.h"
#include "runtime_bootstrap.h"
#include "runtime_metadata.h"
#include <cstdint>

// Feature 59 / API 1: complete compiled port of diagnostics/camera-probe.js
// discover(module, api, domain, sampleCamera, continuous) and its validation helpers
// (text, typeName, pointerHandleAbi, executable, DEBUG_INFO_WORDS, TARGETS, LIMITS).
// Built on feature 47's reusable metadata primitives (pgs_runtime_metadata_api(1))
// and cross-checked against feature 54's bootstrap snapshot (pgs_runtime_bootstrap_api(1))
// where active, using the canonical raw PT_LOAD module range consistent with quickball (55)
// and routes (53). No hooks, no Gum/Dobby, no GC handle creation, no runtime_invoke, no JS
// evaluator: pure metadata discovery + read-only code fingerprints.

#ifdef __cplusplus
extern "C" {
#endif

static_assert(sizeof(void *) == 8, "CameraMetadata native ABI requires LP64");

enum PgsCameraMetaInfo {
  PGS_CAM_FEATURE_ID      = 59,
  PGS_CAM_API_VERSION     = 1,
  PGS_CAM_CFG_VERSION     = 1,
  PGS_CAM_EXTRA_VERSION   = 1,
  PGS_CAM_OUT_VERSION     = 1,
  PGS_CAM_REASON_MAX      = 120,
  PGS_CAM_ASM_LIMIT       = 128,        // camera-probe LIMITS.assemblies
  PGS_CAM_SCAN_MS         = 3000,       // camera-probe LIMITS.scanMs
  PGS_CAM_NAME_MAX        = 256,        // camera-probe LIMITS.nameBytes
  PGS_CAM_MAIN_CAMERA_RVA = PGS_GAME_CAMERA_METADATA_H_PGS_CAM_MAIN_CAMERA_RVA_RVA  // CameraStack.get_MainCamera pinned RVA
};

// resolve() return codes.
//  0 (PGS_CAM_OK)          : discovery succeeded; output fully populated.
//  1 (PGS_CAM_RETRY)       : retriable readiness status ({retry: out->reason}).
//  2 (PGS_CAM_UNAVAILABLE) : terminal unavailable status ({unavailable: out->reason}).
// <0                       : fatal caller/metadata/environment fault (throws in adapter).
enum PgsCameraMetaStatus {
  PGS_CAM_OK                     = 0,
  PGS_CAM_RETRY                  = 1,
  PGS_CAM_UNAVAILABLE            = 2,
  PGS_CAM_ERR_ATTACH             = -30,  // thread not attached or owner_tid != gettid()
  PGS_CAM_ERR_METADATA           = -31,  // feature 47 runtime_metadata API unavailable
  PGS_CAM_ERR_INTERNAL           = -32,  // internal schema fault
  PGS_CAM_ERR_RVA_OVERFLOW       = -33,  // module_base + rva overflow
  PGS_CAM_ERR_EXTRA_MISSING      = -34,  // extra null/bad-version/bad-size/reserved!=0 or image_get_name null
  PGS_CAM_ERR_NULL_ASSEMBLIES    = -35,  // domain_get_assemblies returned null with non-zero count
  PGS_CAM_ERR_NULL_STRING        = -36,  // null metadata string from image_get_name or method_get_name
  PGS_CAM_ERR_NULL_TYPE          = -37,  // null metadata type from return/field/param type accessor
  PGS_CAM_ERR_BOOTSTRAP          = -38   // active feature 54 bootstrap snapshot mismatched domain/ExecuteTasks
};

// Vector3 preparatory field validation status (camera-probe discover() vectorFields).
enum PgsCameraVectorFields {
  PGS_CAM_VF_NONE                = 0,
  PGS_CAM_VF_EXPORTS_UNAVAILABLE = 1,  // "exports-unavailable"
  PGS_CAM_VF_CLASS_UNAVAILABLE   = 2,  // "class-unavailable"
  PGS_CAM_VF_SIGNATURE_MISMATCH  = 3,  // "signature-mismatch"
  PGS_CAM_VF_VERIFIED            = 4   // "verified"
};

// Optional export presence bitmask (PgsCameraMetaExtra.present).
enum PgsCameraExport {
  PGS_CAM_EXP_CLASS_GET_FIELD_FROM_NAME = 1u << 0,
  PGS_CAM_EXP_FIELD_GET_TYPE            = 1u << 1,
  PGS_CAM_EXP_FIELD_GET_PARENT          = 1u << 2,
  PGS_CAM_EXP_FIELD_GET_FLAGS           = 1u << 3,
  PGS_CAM_EXP_RUNTIME_INVOKE            = 1u << 4,
  PGS_CAM_EXP_OBJECT_GET_CLASS          = 1u << 5,
  PGS_CAM_EXP_OBJECT_UNBOX              = 1u << 6,
  PGS_CAM_EXP_GCHANDLE_NEW              = 1u << 7,
  PGS_CAM_EXP_GCHANDLE_GET_TARGET       = 1u << 8,
  PGS_CAM_EXP_GCHANDLE_FREE             = 1u << 9,
  PGS_CAM_EXP_FIELD_GET_VALUE           = 1u << 10,
  PGS_CAM_EXP_GET_CORLIB                = 1u << 11,
  PGS_CAM_EXP_CLASS_IS_ASSIGNABLE_FROM  = 1u << 12,
  PGS_CAM_EXP_CLASS_IS_VALUETYPE        = 1u << 13,
  PGS_CAM_EXP_CLASS_VALUE_SIZE          = 1u << 14,
  PGS_CAM_EXP_DEBUG_GET_METHOD_INFO     = 1u << 15,
  PGS_CAM_EXP_METHOD_IS_GENERIC         = 1u << 16,
  PGS_CAM_EXP_METHOD_IS_INFLATED        = 1u << 17,
  PGS_CAM_EXP_METHOD_GET_PARAM          = 1u << 18,
  PGS_CAM_EXP_STRING_NEW                = 1u << 19
};

#ifdef __cplusplus
}  // extern "C"

namespace pgs_camera_schema {

enum ClassIndex {
  C_CAMERA = 0,     // UnityEngine.Camera (CoreModule, mandatory)
  C_COMPONENT,      // UnityEngine.Component (CoreModule, mandatory)
  C_TRANSFORM,      // UnityEngine.Transform (CoreModule, mandatory)
  C_SYNCCTX,        // UnityEngine.UnitySynchronizationContext (CoreModule, mandatory)
  C_OBJECT,         // UnityEngine.Object (CoreModule, sampleCamera)
  C_VECTOR3,        // UnityEngine.Vector3 (CoreModule, vector field check)
  C_INT32,          // System.Int32 (corlib, sampleCamera)
  C_RIG,            // Niantic.Holoholo.CameraRig.MainCameraRig (holo-game, continuous)
  C_STACK,          // Niantic.Holoholo.Cameras.CameraStack (holo-game, continuous)
  C_STRING,         // System.String (corlib, continuous)
  C_LAYERMASK,      // UnityEngine.LayerMask (CoreModule, continuous)
  C_CLASS_END
};
inline constexpr uint32_t kClassCount = C_CLASS_END;
static_assert(kClassCount == 11, "camera_metadata resolves 11 class slots");

enum FieldIndex {
  F_X = 0,          // UnityEngine.Vector3.x (non-static System.Single)
  F_Y,              // UnityEngine.Vector3.y (non-static System.Single)
  F_Z,              // UnityEngine.Vector3.z (non-static System.Single)
  F_FIELD_END
};
inline constexpr uint32_t kFieldCount = F_FIELD_END;
static_assert(kFieldCount == 3, "camera_metadata resolves 3 Vector3 fields");

enum MethodIndex {
  M_GET_MAIN = 0,        // UnityEngine.Camera.get_main() -> UnityEngine.Camera (static)
  M_GET_TRANSFORM,       // UnityEngine.Component.get_transform() -> UnityEngine.Transform (instance)
  M_GET_FORWARD,         // UnityEngine.Transform.get_forward() -> UnityEngine.Vector3 (instance)
  M_EXECUTE_TASKS,       // UnityEngine.UnitySynchronizationContext.ExecuteTasks() -> System.Void (static)
  M_GET_INSTANCE_ID,     // UnityEngine.Object.GetInstanceID() -> System.Int32 (instance, sampleCamera)
  M_GET_MAIN_CAMERA,     // Niantic.Holoholo.Cameras.CameraStack.get_MainCamera() -> UnityEngine.Camera (continuous)
  M_GET_CULLING_MASK,    // UnityEngine.Camera.get_cullingMask() -> System.Int32 (continuous)
  M_NAME_TO_LAYER,       // UnityEngine.LayerMask.NameToLayer(System.String) -> System.Int32 (static, continuous)
  M_METHOD_END
};
inline constexpr uint32_t kMethodCount = M_METHOD_END;
static_assert(kMethodCount == 8, "camera_metadata resolves 8 method slots");

struct TargetSpec {
  uint32_t class_idx;
  uint32_t method_idx;
  const char *class_name;
  const char *method_name;
  const char *return_type;
  uint32_t is_static;
  uint32_t sample_only;
};

inline constexpr TargetSpec kTargets[] = {
  {C_CAMERA,    M_GET_MAIN,        "Camera",                      "get_main",       "UnityEngine.Camera",    1, 0},
  {C_COMPONENT, M_GET_TRANSFORM,   "Component",                   "get_transform",  "UnityEngine.Transform", 0, 0},
  {C_TRANSFORM, M_GET_FORWARD,     "Transform",                   "get_forward",    "UnityEngine.Vector3",   0, 0},
  {C_SYNCCTX,   M_EXECUTE_TASKS,   "UnitySynchronizationContext", "ExecuteTasks",   "System.Void",           1, 0},
  {C_OBJECT,    M_GET_INSTANCE_ID, "Object",                      "GetInstanceID",  "System.Int32",          0, 1},
};
inline constexpr uint32_t kTargetCount = sizeof(kTargets) / sizeof(kTargets[0]);
static_assert(kTargetCount == 5, "camera_metadata has 4 base targets + 1 sampleCamera target");

inline constexpr const char *kVectorFieldNames[kFieldCount] = {"x", "y", "z"};

// pointerHandleAbi (camera-probe.js lines 80..111): read-only AArch64 code fingerprint of
// il2cpp_gchandle_new / il2cpp_gchandle_get_target / il2cpp_gchandle_free.
inline constexpr uint32_t kGcCreateWords[] = PGS_GAME_CAMERA_METADATA_H_KGCCREATEWORDS_FINGERPRINT;
inline constexpr uint32_t kGcCreateWordCount = 5;
inline constexpr uint64_t kGcCreateBranchOff = PGS_GAME_CAMERA_METADATA_H_KGCCREATEBRANCHOFF;
inline constexpr uint64_t kGcCreateBodyOff   = PGS_GAME_CAMERA_METADATA_H_KGCCREATEBODYOFF;
inline constexpr uint32_t kGcCreateBodyWord  = PGS_GAME_CAMERA_METADATA_H_KGCCREATEBODYWORD;
inline constexpr uint32_t kGcGetHead         = PGS_GAME_CAMERA_METADATA_H_KGCGETHEAD;
inline constexpr uint64_t kGcGetTailOff      = PGS_GAME_CAMERA_METADATA_H_KGCGETTAILOFF;
inline constexpr uint32_t kGcGetTail[]       = PGS_GAME_CAMERA_METADATA_H_KGCGETTAIL_FINGERPRINT;
inline constexpr uint32_t kGcFreeHead        = PGS_GAME_CAMERA_METADATA_H_KGCFREEHEAD;
inline constexpr uint64_t kGcFreeTailOff     = PGS_GAME_CAMERA_METADATA_H_KGCFREETAILOFF;
inline constexpr uint32_t kGcFreeTail[]      = PGS_GAME_CAMERA_METADATA_H_KGCFREETAIL_FINGERPRINT;

// 80-byte il2cpp_debug_get_method_info prologue (camera-probe.js DEBUG_INFO_WORDS, lines 26..29).
inline constexpr unsigned char kDebugPrologue[] = PGS_GAME_CAMERA_METADATA_H_KDEBUGPROLOGUE_FINGERPRINT;
inline constexpr uint32_t kDebugPrologueLen = sizeof(kDebugPrologue);
static_assert(kDebugPrologueLen == 80, "DEBUG_INFO_WORDS is 20 AArch64 words (80 bytes)");

// CameraStack.get_MainCamera 2-word leaf getter prologue at RVA 0xad814b8 (ldr x0,[x0,#24]; ret).
inline constexpr uint32_t kGetMainCameraWords[] = PGS_GAME_CAMERA_METADATA_H_KGETMAINCAMERAWORDS_FINGERPRINT;
inline constexpr uint32_t kGetMainCameraByteLen = sizeof(kGetMainCameraWords);
static_assert(kGetMainCameraByteLen == 8, "get_MainCamera leaf getter prologue is 8 bytes");

}  // namespace pgs_camera_schema

extern "C" {
#endif  // __cplusplus

// Extra typed il2cpp primitives beyond feature 47's 31 metadata exports, plus an optional monotonic
// clock test seam for deterministic scan-budget verification.
struct PgsCameraMetaExtra {
  uint32_t version, size;               // 0..7    (1, 112)
  void *image_get_name;                 // 8..15   mandatory: const char* (void* image)
  void *get_corlib;                     // 16..23  optional (sampleCamera): void* (void)
  void *runtime_invoke;                 // 24..31  optional (sampleCamera)
  void *object_get_class;               // 32..39  optional (sampleCamera)
  void *object_unbox;                   // 40..47  optional (sampleCamera)
  const void *gchandle_new;             // 48..55  optional (pointerHandleAbi + sampleCamera)
  const void *gchandle_get_target;      // 56..63  optional (pointerHandleAbi + sampleCamera)
  const void *gchandle_free;            // 64..71  optional (pointerHandleAbi + sampleCamera)
  void *field_get_value;                // 72..79  optional (sampleCamera)
  void *string_new;                     // 80..87  optional (continuous)
  double (*clock_ms)(void *ctx);        // 88..95  optional monotonic ms seam (null -> CLOCK_MONOTONIC)
  void *clock_ctx;                      // 96..103 ctx for clock_ms
  uint32_t present;                     // 104..107 PgsCameraExport bitmask
  uint32_t reserved;                    // 108..111 must be 0
};

struct PgsCameraMetaConfig {
  uint32_t version, size;               // 0..7    (1, 112)
  PgsMetaBindConfig binding;            // 8..71   (64 bytes, feature 47 bind config)
  void *thread_current;                 // 72..79  mandatory (il2cpp_thread_current)
  uint64_t owner_tid;                   // 80..87  gettid() of attached caller thread
  const void *domain;                   // 88..95  optional explicit domain (null -> domain_get())
  const PgsCameraMetaExtra *extra;      // 96..103 mandatory
  uint32_t sample_camera;               // 104..107 0 or 1
  uint32_t continuous;                  // 108..111 0 or 1
};

#ifdef __cplusplus
struct PgsCameraMetaOutput {
  uint32_t version, size;                                // 0..7    (1, 368)
  int32_t status;                                        // 8..11   0=OK, 1=RETRY, 2=UNAVAILABLE
  uint32_t vector_fields;                                // 12..15  PgsCameraVectorFields (1..4 on OK)
  uint32_t target_count;                                 // 16..19  4 or 5 on OK, else 0
  uint32_t reserved;                                     // 20..23  0
  const void *core_image;                                // 24..31  UnityEngine.CoreModule.dll image
  const void *game_image;                                // 32..39  image defining the rig classes (continuous)
  const void *corlib_image;                              // 40..47  get_corlib() image (sampleCamera)
  const void *execute;                                   // 48..55  ExecuteTasks MethodInfo*
  const void *debug_address;                             // 56..63  debug_get_method_info (continuous)
  const void *get_main_camera_address;                   // 64..71  get_MainCamera code (continuous)
  const void *classes[pgs_camera_schema::kClassCount];   // 72..159 (11 * 8 = 88)
  const void *fields[pgs_camera_schema::kFieldCount];    // 160..183 (3 * 8 = 24)
  const void *methods[pgs_camera_schema::kMethodCount];  // 184..247 (8 * 8 = 64)
  char reason[PGS_CAM_REASON_MAX];                       // 248..367 (120 bytes)
};

struct PgsCameraMetaApi {
  uint32_t version, size, config_size, output_size;
  int (*resolve)(const PgsCameraMetaConfig *, PgsCameraMetaOutput *);
};

static_assert(sizeof(PgsCameraMetaExtra) == 112, "LP64 extra block");
static_assert(sizeof(PgsCameraMetaConfig) == 112, "LP64 config");
static_assert(sizeof(PgsCameraMetaOutput) == 368, "LP64 output");
static_assert(sizeof(PgsCameraMetaApi) == 24, "LP64 API");
#endif

const void *pgs_camera_metadata_api(uint32_t version);

#ifdef __cplusplus
}
#endif
