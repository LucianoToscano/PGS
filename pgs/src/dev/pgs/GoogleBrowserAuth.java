package dev.pgs;

import android.app.Activity;
import android.net.Uri;

/**
 * Compatibility surface for the retired experimental browser OAuth path.
 * No client identity, browser launch, redirect processing or token exchange is
 * available until an independently authorized PGS implementation is reviewed.
 */
public final class GoogleBrowserAuth {
    private GoogleBrowserAuth() {}

    public static synchronized String begin(Activity activity) { return null; }
    public static synchronized boolean handleRedirect(Uri uri) { return false; }
    public static synchronized String takeResult(String requestId) { return null; }
    public static synchronized void cancel(String requestId) {}
    public static synchronized void onHostPaused(Activity activity) {}
    public static synchronized void onHostResumed(Activity activity) {}
}
