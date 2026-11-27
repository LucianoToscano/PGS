package dev.pgrazor;

import java.util.Collections;
import java.util.IllegalFormatException;
import java.util.Locale;
import java.util.Map;

/** Offline translations for PGS-owned UI. Never changes the host game's Locale or data. */
public final class I18n {
    private static volatile Translator active = new Translator("en", Collections.emptyMap());
    private static boolean initialized;

    private I18n() {}

    /** A saved preference takes effect only at the next process start, not on Activity resume. */
    public static synchronized void init(String selection, Locale systemLocale) {
        if (initialized) return;
        active = forLanguage(selection, systemLocale);
        initialized = true;
    }

    /** An independent immutable translator, also used by the host-JVM regression suite. */
    public static Translator forLanguage(String selection, Locale systemLocale) {
        String code = LanguagePrefs.resolve(selection, systemLocale);
        return new Translator(code, I18nCatalog.load(code));
    }

    public static String language() { return active.language(); }
    /** Display-only branding: preserve catalog keys, serialized preferences and opaque arguments. */
    private static String brand(String text) { return text == null ? "" : text.replace("PGRazor", "PGS"); }
    public static String t(String english) { return brand(active.text(english)); }
    public static String format(String english, Object... arguments) {
        try {
            return String.format(Locale.ROOT, brand(active.text(english)), arguments);
        } catch (IllegalFormatException invalidTranslation) {
            return String.format(Locale.ROOT, brand(english), arguments);
        }
    }

    /** Only call for fixed UI choices; account names, route names and game data stay untouched. */
    public static String[] options(String[] english) {
        String[] result = new String[english.length];
        for (int i = 0; i < english.length; i++) result[i] = t(english[i]);
        return result;
    }

    /** A settings label followed by an opaque value. Never translates the value itself. */
    public static String row(String english) { return brand(active.row(english)); }

    public static final class Translator {
        private final String language;
        private final Map<String, String> messages;

        private Translator(String language, Map<String, String> messages) {
            this.language = language;
            this.messages = Collections.unmodifiableMap(messages);
        }

        public String language() { return language; }

        /** Exact keys only: never rewrite arbitrary substrings or user-supplied arguments. */
        public String text(String english) {
            if (english == null) return "";
            String translated = messages.get(english);
            return translated == null || translated.isEmpty() ? english : translated;
        }

        public String row(String english) {
            if (english == null) return "";
            String translated = messages.get(english);
            if (translated != null && !translated.isEmpty()) return translated;
            int split = english.indexOf(": ");
            if (split > 0) {
                String label = messages.get(english.substring(0, split));
                if (label != null && !label.isEmpty()) return label + ": " + english.substring(split + 2);
            }
            return english;
        }

        /** Formatting is confined to UI templates; arguments and coordinate syntax are preserved. */
        public String format(String english, Object... arguments) {
            try {
                return String.format(Locale.ROOT, text(english), arguments);
            } catch (IllegalFormatException invalidTranslation) {
                // A broken translation must not crash the game. Catalog checks reject it in CI.
                return String.format(Locale.ROOT, english, arguments);
            }
        }
    }
}
