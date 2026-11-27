package dev.pgrazor;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.Base64;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** Runs the production engine with controlled fault fixtures and, separately, real generated data. */
public final class I18nTest {
    public static void main(String[] args) throws Exception {
        if (args.length == 2 && "catalogs".equals(args[0])) {
            realCatalogs(args[1]);
        } else if (args.length == 2 && "restart".equals(args[0])) {
            equal("en", I18n.language());
            I18n.init(args[1], Locale.US);
            equal(args[1], I18n.language());
            equal("Schließen", I18n.t("Close"));
            System.out.println("PASS I18n new process applies the saved language");
        } else if (args.length == 1 && "fixture".equals(args[0])) {
            fixtures();
        } else {
            throw new AssertionError("Expected fixture, catalogs <fixture-file>, or restart <language>");
        }
    }

    private static void fixtures() {
        Locale initial = Locale.getDefault();
        Locale initialFormat = Locale.getDefault(Locale.Category.FORMAT);
        Locale initialDisplay = Locale.getDefault(Locale.Category.DISPLAY);
        try {
            // Simulate the host game using comma decimals. PGS must neither inherit them for
            // coordinate syntax nor change any of the host's Locale settings.
            Locale.setDefault(Locale.FRANCE);
            Locale.setDefault(Locale.Category.FORMAT, Locale.GERMANY);
            equal("en", I18n.language());
            equal("Close", I18n.t("Close"));
            I18n.Translator french = I18n.forLanguage("fr", Locale.JAPAN);
            I18n.Translator german = I18n.forLanguage("de", Locale.FRANCE);
            equal("fr", french.language());
            equal("Fermer", french.text("Close"));
            equal("Schließen", german.text("Close"));
            equal("en", I18n.language());
            equal("pt-BR", I18n.forLanguage("system", Locale.forLanguageTag("pt-PT")).language());
            equal("fr", I18n.forLanguage("system", Locale.CANADA_FRENCH).language());
            equal("zh-Hant", I18n.forLanguage("system", Locale.forLanguageTag("zh-Hant-TW")).language());
            equal("en", I18n.forLanguage("system", Locale.JAPAN).language());
            equal("en", I18n.forLanguage(null, null).language());
            equal("de", I18n.forLanguage("unknown", Locale.GERMANY).language());
            equal("pt-BR", I18n.forLanguage(" PT_br ", Locale.JAPAN).language());

            equal("", french.text(null));
            equal("", french.text(""));
            equal("Unknown key", french.text("Unknown key"));
            equal("My Close route", french.text("My Close route"));
            equal("Empty translation", french.text("Empty translation"));
            equal("", french.row(null));
            equal("Langue: Close", french.row("Language: Close"));
            equal("Langue: Close: 100% ✨ น้ำ %s\n東京", french.row("Language: Close: 100% ✨ น้ำ %s\n東京"));
            equal("Langue: ", french.row("Language: "));
            equal("Language:Close", french.row("Language:Close"));
            equal("Unknown: Close", french.row("Unknown: Close"));
            equal("Ligne exacte", french.row("Special: fixed"));

            String opaque = "Close %1$s %d 100% IV Pikachu 東京 น้ำ 한국어";
            equal(opaque + " enregistré", french.format("Saved %1$s", opaque));
            equal("7 puis " + opaque, french.format("Pair %1$s / %2$d", opaque, 7));
            equal("Chance : 90%", french.format("Chance: %d%%", 90));
            equal("Coordonnées : 12.345678, -45.678901", french.format("Coordinates: %.6f, %.6f", 12.345678, -45.678901));
            equal("Nombre : 1,234.50", french.format("Number: %1$,.2f", 1234.5));
            equal("Date : 2026-11-27", french.format("Date: %1$tF", LocalDate.of(2026, 11, 27)));
            equal("Unknown " + opaque, french.format("Unknown %1$s", opaque));
            equal("Broken " + opaque, french.format("Broken %1$s", opaque));
            equal("Missing " + opaque, french.format("Missing %1$s", opaque));
            equal("Extra " + opaque, french.format("Extra %1$s", opaque));

            I18n.init("fr", Locale.US);
            equal("fr", I18n.language());
            equal("Fermer", I18n.t("Close"));
            if (I18n.t("PGRazor version %1$s").contains("PGRazor"))
                throw new AssertionError("PGS display brand did not replace legacy name");
            String brandedArgument = "PGRazor saved user text";
            if (!I18n.format("Saved %1$s", brandedArgument).contains(brandedArgument))
                throw new AssertionError("User-supplied arguments must not be renamed");
            String[] source = {"Close", "Unknown key"};
            String[] translated = I18n.options(source);
            if (source == translated) throw new AssertionError("Option array aliases the input");
            equal("Close", source[0]);
            equal("Fermer", translated[0]);
            equal("Unknown key", translated[1]);
            translated[0] = "changed by caller";
            equal("Fermer", I18n.options(source)[0]);

            // Saving another preference and rebuilding an Activity does not change this process.
            I18n.init("de", Locale.GERMANY);
            I18n.init("system", Locale.JAPAN);
            equal("fr", I18n.language());
            equal("Fermer", I18n.t("Close"));
            equal("Langue: Close", I18n.row("Language: Close"));
            equal("Close enregistré", I18n.format("Saved %1$s", "Close"));
            equal("Schließen", german.text("Close"));
            if (!Locale.FRANCE.equals(Locale.getDefault())
                    || !Locale.GERMANY.equals(Locale.getDefault(Locale.Category.FORMAT))
                    || !Locale.FRANCE.equals(Locale.getDefault(Locale.Category.DISPLAY))) {
                throw new AssertionError("Engine changed the host Locale");
            }
        } finally {
            Locale.setDefault(initial);
            Locale.setDefault(Locale.Category.FORMAT, initialFormat);
            Locale.setDefault(Locale.Category.DISPLAY, initialDisplay);
        }
        System.out.println("PASS I18n: language resolution, exact lookup, fallback, opaque data, Locale isolation and frozen startup selection");
    }

    private static void realCatalogs(String input) throws Exception {
        Map<String, I18n.Translator> translators = new HashMap<>();
        Map<String, Integer> counts = new HashMap<>();
        for (String line : Files.readAllLines(Paths.get(input), StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t", -1);
            if (fields.length != 3) throw new AssertionError("Malformed expected catalog row");
            String language = fields[0];
            String source = decode(fields[1]);
            String expected = decode(fields[2]);
            I18n.Translator translator = translators.get(language);
            if (translator == null) {
                translator = I18n.forLanguage(language, Locale.JAPAN);
                equal(language, translator.language());
                translators.put(language, translator);
            }
            equal(expected, translator.text(source));
            counts.put(language, counts.getOrDefault(language, 0) + 1);
        }
        if (translators.size() != LanguagePrefs.codes().length - 1 || !counts.containsKey("en")) {
            throw new AssertionError("Real catalog language set is incomplete");
        }
        String opaque = "Close | Pikachu | 100% IV | %1$s | 東京 น้ำ 한국어";
        for (Map.Entry<String, I18n.Translator> entry : translators.entrySet()) {
            equal(counts.get("en").toString(), counts.get(entry.getKey()).toString());
            I18n.Translator translator = entry.getValue();
            // English deliberately has no generated map: the public I18n.t() applies branding.
            // Locale maps have canonical PGS keys while older Java call sites still work.
            if (!"en".equals(entry.getKey()))
                equal(translator.text("PGS VGP"), translator.text("PGRazor VGP"));
            String formatted = translator.format("Saved %1$s to Favorites", opaque);
            if (!formatted.contains(opaque)) throw new AssertionError("Catalog translated opaque data: " + entry.getKey());
            equal(translator.text("Language") + ": " + opaque, translator.row("Language: " + opaque));
            equal("unlisted fixture label", translator.text("unlisted fixture label"));
            String coordinates = translator.format("Selected: %.6f, %.6f", 12.345678, -45.678901);
            if (!coordinates.contains("12.345678") || !coordinates.contains("-45.678901")) {
                throw new AssertionError("Catalog changed numeric coordinate syntax: " + entry.getKey());
            }
        }
        System.out.println("PASS I18n real catalogs: " + translators.size() + " languages x " + counts.get("en")
                + " UTF-8 messages; generated tables match JSON and preserve opaque arguments");
    }

    private static String decode(String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static void equal(String expected, String actual) {
        if (!expected.equals(actual)) throw new AssertionError("Expected <" + expected + ">, got <" + actual + ">");
    }
}
