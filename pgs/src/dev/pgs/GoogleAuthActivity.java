package dev.pgs;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;

/**
 * OAuth callback activity for Google browser sign-in.
 *
 * <p>Receives the redirect from Google accounts (custom scheme {@code pgs://oauthredirect}),
 * hands the URI to {@link GoogleBrowserAuth#handleRedirect} and finishes immediately.
 * No UI is shown.
 */
public final class GoogleAuthActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Intent intent = getIntent();
        Uri uri = intent != null ? intent.getData() : null;
        if (uri != null) {
            GoogleBrowserAuth.handleRedirect(uri);
        }
        finish();
    }
}
