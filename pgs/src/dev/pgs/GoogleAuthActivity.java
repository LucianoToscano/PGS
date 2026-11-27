package dev.pgs;

import android.app.Activity;
import android.os.Bundle;

/** Retained only as an inert compatibility class; no manifest callback is installed. */
public final class GoogleAuthActivity extends Activity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        finish();
    }
}
