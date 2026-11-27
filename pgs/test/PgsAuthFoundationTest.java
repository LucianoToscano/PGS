package dev.pgs;

public final class PgsAuthFoundationTest {
    private static void check(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }

    public static void main(String[] args) {
        for (PgsAuthConfig.Provider provider : PgsAuthConfig.Provider.values()) {
            check(PgsAuthConfig.availability(provider) ==
                PgsAuthConfig.Availability.AUTHORIZATION_REQUIRED, "closed config");
            check(PgsAuthManager.preflight(provider) ==
                PgsAuthManager.Diagnostic.AUTHORIZATION_REQUIRED, "closed preflight");
        }
        check(PgsAuthManager.classifyGoogleStatus(10) ==
            PgsAuthManager.Diagnostic.CONFIGURATION_REJECTED, "registration");
        check(PgsAuthManager.classifyGoogleStatus(12501) ==
            PgsAuthManager.Diagnostic.CANCELLED, "cancel");
        check(PgsAuthManager.classifyGoogleStatus(7) ==
            PgsAuthManager.Diagnostic.NETWORK_ERROR, "network");
        check(PgsAuthManager.classifyGoogleStatus(0) ==
            PgsAuthManager.Diagnostic.UNKNOWN, "status alone not a verified login");
        check(PgsAuthManager.classifyRegistrationRejection(false) ==
            PgsAuthManager.Diagnostic.UNKNOWN, "no inferred rejection");
        check(PgsAuthManager.classifyRegistrationRejection(true) ==
            PgsAuthManager.Diagnostic.CONFIGURATION_REJECTED, "confirmed rejection");

        PgsAuthAttempt a = new PgsAuthAttempt();
        String first = a.begin(100);
        check(a.take(first, 101) == null, "pending");
        String second = a.begin(102);
        check(!first.equals(second), "unique");
        check(!a.finish(first, PgsAuthAttempt.Outcome.COMPLETED, 103), "stale completion");
        check(a.finish(second, PgsAuthAttempt.Outcome.CANCELLED, 104), "cancel");
        check(!a.finish(second, PgsAuthAttempt.Outcome.COMPLETED, 105), "terminal immutable");
        check(a.take(second, 106) == PgsAuthAttempt.Outcome.CANCELLED, "cancel consumed");
        check(a.take(second, 107) == null, "single consumption");
        String third = a.begin(200);
        check(!a.finish(third, PgsAuthAttempt.Outcome.COMPLETED, 300200), "deadline");
        check(a.take(third, 300201) == PgsAuthAttempt.Outcome.EXPIRED, "expiry");
        String fourth = a.begin(300300);
        check(a.finish(fourth, PgsAuthAttempt.Outcome.COMPLETED, 300301), "mock completion");
        check(a.take(fourth, 300302) == PgsAuthAttempt.Outcome.COMPLETED, "mock completion consumed");
        String fifth = a.begin(400000);
        check(a.take(fifth, 399999) == PgsAuthAttempt.Outcome.EXPIRED, "clock regression");
        String sixth = a.begin(500000);
        a.clear();
        check(!a.finish(sixth, PgsAuthAttempt.Outcome.FAILED, 500001), "clear");
        check(a.take(null, 500001) == null, "null handle");
        String seventh = a.begin(600000);
        check(a.finish(seventh, PgsAuthAttempt.Outcome.FAILED, 600001), "failure");
        check(a.take(seventh, 600002) == PgsAuthAttempt.Outcome.FAILED, "failure consumed");
        System.out.println("PGS Auth foundation: PASS (no live authentication)");
    }
}
