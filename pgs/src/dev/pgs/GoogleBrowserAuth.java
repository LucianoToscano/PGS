package dev.pgs;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;

import androidx.browser.custom.CustomTabsIntent;

import java.security.SecureRandom;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

/**
 * Browser-based Google OAuth authentication for PGS.
 *
 * <p>Implements the PKCE authorization-code flow using Chrome Custom Tabs.
 * {@link #begin(Activity)} launches the Google accounts page and returns an opaque
 * request id; {@link #takeResult(String)} returns the stored JSON result once the
 * redirect has been delivered to {@link GoogleAuthActivity}. Browser authentication
 * deliberately survives the game's background pause.
 *
 * <p>No client identity, tokens or email addresses are logged. The deploying
 * organization must supply its own Google OAuth client ID and redirect URI.
 */
public final class GoogleBrowserAuth {
    private static final Map<String, PendingRequest> pending = new HashMap<>();
    static final Map<String, String> results = new HashMap<>();
    private static final SecureRandom random = new SecureRandom();
    private static final Handler mainHandler = new Handler(Looper.getMainLooper());

    // Configured by the deploying organization. Placeholder values must be replaced
    // before a release build signs in real users.
    private static final String CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";
    private static final String REDIRECT_URI = "pgs://oauthredirect";

    static int beginCount = 0;

    private GoogleBrowserAuth() {}

    /**
     * Starts a browser sign-in and returns an opaque request id. The caller polls
     * {@link #takeResult(String)} until a non-null result arrives.
     */
    public static synchronized String begin(Activity activity) {
        String codeVerifier = generateCodeVerifier();
        String codeChallenge = generateCodeChallenge(codeVerifier);
        String state = generateState();
        String requestId = "req_" + System.currentTimeMillis() + "_" + random.nextInt(100000);

        pending.put(requestId, new PendingRequest(codeVerifier, state, requestId));

        String authUrl = "https://accounts.google.com/o/oauth2/v2/auth"
                + "?client_id=" + encode(CLIENT_ID)
                + "&redirect_uri=" + encode(REDIRECT_URI)
                + "&response_type=code"
                + "&scope=openid%20email%20profile"
                + "&code_challenge=" + encode(codeChallenge)
                + "&code_challenge_method=S256"
                + "&state=" + encode(state)
                + "&access_type=offline"
                + "&prompt=select_account";

        try {
            CustomTabsIntent intent = new CustomTabsIntent.Builder().build();
            Intent launch = intent.intent;
            launch.setData(Uri.parse(authUrl));
            launch.addFlags(Intent.FLAG_ACTIVITY_NO_HISTORY);
            activity.startActivity(launch);
        } catch (Throwable ignored) {
            Intent fallback = new Intent(Intent.ACTION_VIEW, Uri.parse(authUrl));
            fallback.addFlags(Intent.FLAG_ACTIVITY_NO_HISTORY);
            activity.startActivity(fallback);
        }

        beginCount++;
        return requestId;
    }

    /**
     * Called by {@link GoogleAuthActivity} when the OAuth redirect arrives.
     * Stores the result for the matching pending request.
     */
    public static synchronized boolean handleRedirect(Uri uri) {
        if (uri == null) return false;
        String state = uri.getQueryParameter("state");
        String code = uri.getQueryParameter("code");
        String error = uri.getQueryParameter("error");

        if (error != null) {
            for (Map.Entry<String, PendingRequest> entry : pending.entrySet()) {
                if (entry.getValue().state.equals(state)) {
                    PendingRequest pr = entry.getValue();
                    pending.remove(entry.getKey());
                    results.put(pr.requestId, "{\"status\":\"Fail\",\"error\":\"" + jsonEscape(error) + "\"}");
                    return true;
                }
            }
            return false;
        }

        if (code != null && state != null) {
            for (Map.Entry<String, PendingRequest> entry : pending.entrySet()) {
                if (entry.getValue().state.equals(state)) {
                    PendingRequest pr = entry.getValue();
                    pending.remove(entry.getKey());
                    results.put(pr.requestId,
                            "{\"status\":\"Success\",\"email\":\"\",\"idToken\":\"" + jsonEscape(code) + "\"}");
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Returns the stored JSON result for a request id, or null when none is ready.
     * The result is removed after the first read.
     */
    public static synchronized String takeResult(String id) {
        return results.remove(id);
    }

    /**
     * Cancels a pending request and stores a Cancelled result.
     */
    public static synchronized void cancel(String id) {
        PendingRequest pr = pending.remove(id);
        if (pr != null) {
            results.put(id, "{\"status\":\"Cancelled\"}");
        }
    }

    public static synchronized void onHostPaused(Activity activity) {
        // Browser auth survives backgrounding; nothing to do.
    }

    public static synchronized void onHostResumed(Activity activity) {
        // Nothing to do.
    }

    private static String generateCodeVerifier() {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    private static String generateCodeChallenge(String verifier) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(verifier.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(hash);
        } catch (NoSuchAlgorithmException ignored) {
            return verifier;
        }
    }

    private static String generateState() {
        byte[] bytes = new byte[16];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    private static String encode(String s) {
        return java.net.URLEncoder.encode(s, java.nio.charset.StandardCharsets.UTF_8);
    }

    private static String jsonEscape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static final class PendingRequest {
        final String codeVerifier;
        final String state;
        final String requestId;
        PendingRequest(String codeVerifier, String state, String requestId) {
            this.codeVerifier = codeVerifier;
            this.state = state;
            this.requestId = requestId;
        }
    }
}
