package dev.pgs;

import java.util.UUID;

/**
 * Device-free lifecycle model for one future PGS-owned browser attempt.
 * Tracks only a local opaque handle and a terminal outcome, never OAuth codes,
 * tokens, accounts or redirect URIs. No browser or game access is implemented.
 * All methods use the same monotonic millisecond clock supplied by the caller.
 */
final class PgsAuthAttempt {
    static final long LIFETIME_MS = 300_000L;
    enum Outcome { COMPLETED, CANCELLED, EXPIRED, FAILED }

    private String pending;
    private long started;
    private Outcome outcome;

    synchronized String begin(long nowMs) {
        requireTime(nowMs);
        pending = UUID.randomUUID().toString();
        started = nowMs;
        outcome = null;
        return pending;
    }

    synchronized boolean finish(String handle, Outcome result, long nowMs) {
        requireTime(nowMs);
        if (result == null || result == Outcome.EXPIRED)
            throw new IllegalArgumentException("terminal provider outcome required");
        if (!matches(handle)) return false;
        expire(nowMs);
        if (outcome != null) return false;
        outcome = result;
        return true;
    }

    synchronized Outcome take(String handle, long nowMs) {
        requireTime(nowMs);
        if (!matches(handle)) return null;
        expire(nowMs);
        if (outcome == null) return null;
        Outcome result = outcome;
        clear();
        return result;
    }

    synchronized void clear() {
        pending = null;
        started = 0;
        outcome = null;
    }

    private boolean matches(String handle) {
        return pending != null && pending.equals(handle);
    }

    private void expire(long nowMs) {
        if (outcome == null && (nowMs < started || nowMs - started >= LIFETIME_MS))
            outcome = Outcome.EXPIRED;
    }

    private static void requireTime(long nowMs) {
        if (nowMs < 0) throw new IllegalArgumentException("monotonic time required");
    }
}
