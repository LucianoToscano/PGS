package dev.pgs;

/**
 * Public, non-networking PGS Auth preflight and diagnostic vocabulary.
 * Deliberately exposes neither a launch method nor provider credentials.
 * An authorized SDK integration and backend contract require separate review.
 */
public final class PgsAuthManager {
    public static final String DISPLAY_NAME = "PGS Auth";

    public enum Diagnostic {
        AUTHORIZATION_REQUIRED,
        CONFIGURATION_REJECTED,
        CANCELLED,
        NETWORK_ERROR,
        UNKNOWN
    }

    private PgsAuthManager() {}

    public static Diagnostic preflight(PgsAuthConfig.Provider provider) {
        PgsAuthConfig.availability(provider);
        return Diagnostic.AUTHORIZATION_REQUIRED;
    }

    /** Classify documented Google status codes without retaining provider messages. */
    public static Diagnostic classifyGoogleStatus(int status) {
        switch (status) {
            case 10: return Diagnostic.CONFIGURATION_REJECTED;
            case 16:
            case 12501: return Diagnostic.CANCELLED;
            case 7: return Diagnostic.NETWORK_ERROR;
            default: return Diagnostic.UNKNOWN;
        }
    }

    /** A verified provider registration error, not an inference from generic text. */
    public static Diagnostic classifyRegistrationRejection(boolean confirmed) {
        return confirmed ? Diagnostic.CONFIGURATION_REJECTED : Diagnostic.UNKNOWN;
    }
}
