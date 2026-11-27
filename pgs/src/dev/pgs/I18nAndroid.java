package dev.pgs;

import android.app.Application;
import android.content.res.Resources;
import android.os.LocaleList;
import java.util.Locale;

/** Initializes only PGS's translator, including when Android restores a standalone PGS activity. */
final class I18nAndroid {
    private I18nAndroid() {}

    static void init(Application app) {
        String selection = Control.readPgsLanguage(app);
        LocaleList locales = Resources.getSystem().getConfiguration().getLocales();
        I18n.init(selection, locales.isEmpty() ? Locale.ENGLISH : locales.get(0));
    }
}
