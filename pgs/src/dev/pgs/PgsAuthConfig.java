package dev.pgs;

/**
 * Authorization boundary for a future independent PGS account integration.
 * This candidate contains no approved provider registration or game backend
 * agreement. A build flag, saved setting or successful local test cannot grant it.
 */
public final class PgsAuthConfig {
    public enum Provider { GOOGLE, FACEBOOK }
    public enum Availability { AUTHORIZATION_REQUIRED }

    private PgsAuthConfig() {}

    public static Availability availability(Provider provider) {
        if (provider == null) throw new IllegalArgumentException("provider required");
        return Availability.AUTHORIZATION_REQUIRED;
    }
}
