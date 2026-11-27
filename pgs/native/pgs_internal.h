/* Internal (non-exported) declarations shared between the core and the JNI glue. */
#ifndef PGS_INTERNAL_H
#define PGS_INTERNAL_H

#include <stdint.h>

/* Deterministic spawn-policy self-check used by the JNI host surface.
 * Returns 0 on success or the id of the first failing case. No Dobby, no hooking. */
int pgs_policy_selfcheck(void);

#endif /* PGS_INTERNAL_H */
