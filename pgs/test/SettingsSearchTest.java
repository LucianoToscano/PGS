package dev.pgs;

import java.util.List;

/** Host-JVM checks for the settings search catalogue. No Android runtime is involved. */
public final class SettingsSearchTest {
    public static void main(String[] args) {
        normalization();
        nonLatinNormalization();
        cleanNames();
        ranking();
        matching();
        synonyms();
        emptyQueries();
        localizedIndex();
        System.out.println("SettingsSearch: Latin/non-Latin normalization, bilingual labels, stable IDs, ranking, synonyms and empty states pass");
    }

    private static void normalization() {
        eq("pokemon go", SettingsSearch.normalize("  Pokémon GO  "));
        eq("pokemon", SettingsSearch.normalize("POKÉMON"));
        eq("favorites", SettingsSearch.normalize("Favorites"));
        eq("", SettingsSearch.normalize(null));
        eq("", SettingsSearch.normalize("   "));
        eq("cafe", SettingsSearch.normalize("cafe\u0301"));
        eq("pokemon go", SettingsSearch.normalize("\u3000Pokémon\u00a0GO\u3000"));
    }

    private static void nonLatinNormalization() {
        eq("น้ำ", SettingsSearch.normalize("น้ำ"));
        eq("ก่า", SettingsSearch.normalize("ก่า"));
        different(SettingsSearch.normalize("กา"), SettingsSearch.normalize("ก่า"));
        eq("ёлка й", SettingsSearch.normalize("ЁЛКА Й"));
        different(SettingsSearch.normalize("и"), SettingsSearch.normalize("й"));
        different(SettingsSearch.normalize("е"), SettingsSearch.normalize("ё"));
        eq("й", SettingsSearch.normalize("и\u0306"));
        eq("繁體中文", SettingsSearch.normalize("繁體中文"));
        eq("한국어", SettingsSearch.normalize("한국어"));
        eq("pokemon น้ำ й 한국어", SettingsSearch.normalize("Pokémon น้ำ Й 한국어"));

        SettingsSearch catalogue = new SettingsSearch();
        catalogue.add("กา", "", "", 0);
        catalogue.add("ก่า", "", "", 1);
        catalogue.add("Й", "", "", 2);
        eq("ก่า", single(catalogue.find("ก่า")));
        eq("Й", single(catalogue.find("и\u0306")));
    }

    private static void cleanNames() {
        eq("Throw rating", SettingsSearch.cleanName("Throw rating: Great"));
        eq("Evolve stages", SettingsSearch.cleanName("Evolve: all available stages"));
        eq("Evolve applies to", SettingsSearch.cleanName("Applies to: current transfer rules"));
        eq("Evolve species", SettingsSearch.cleanName("Selected species (3)"));
        eq("Auto ball target", SettingsSearch.cleanName("  Auto ball target: 90%  "));
        eq("", SettingsSearch.cleanName(null));
    }

    private static void ranking() {
        SettingsSearch search = new SettingsSearch();
        int first = search.add("Auto ball target", "Catching", "Catching", 1);
        int exact = search.add("Auto ball", "Catching", "Catching", 1);
        search.add("Auto throw", "Catching", "Catching", 1);
        eq("0", Integer.toString(first));
        eq("1", Integer.toString(exact));
        eq("3", Integer.toString(search.size()));

        List<SettingsSearch.Entry> hits = search.find("auto ball");
        eq("3", Integer.toString(hits.size()));
        eq("Auto ball", hits.get(0).name);
        eq("Auto ball target", hits.get(1).name);
        // Description matches rank after every name match, so a broader row stays last.
        eq("Auto throw", hits.get(2).name);
        eq("1", Integer.toString(hits.get(0).page));

        // A token that is not in a name still matches its description or synonyms.
        List<SettingsSearch.Entry> descriptionHits = search.find("cheapest ball");
        eq("1", Integer.toString(descriptionHits.size()));
        eq("Auto ball", descriptionHits.get(0).name);
    }

    private static void matching() {
        SettingsSearch catalogue = new SettingsSearch();
        catalogue.add("Dark theme", "Interface", "Display & Performance", 4);
        catalogue.add("Location spoofing", "Location & movement", "Location & Map", 0);
        catalogue.add("Show joystick", "Location & movement", "Location & Map", 0);

        List<SettingsSearch.Entry> theme = catalogue.find("DARK");
        eq("1", Integer.toString(theme.size()));
        eq("Dark theme", theme.get(0).name);

        // Category text is searchable.
        List<SettingsSearch.Entry> performance = catalogue.find("performance");
        eq("1", Integer.toString(performance.size()));
        eq("Dark theme", performance.get(0).name);

        // Group text is searchable, and every token must match.
        List<SettingsSearch.Entry> movement = catalogue.find("location movement");
        eq("2", Integer.toString(movement.size()));
        List<SettingsSearch.Entry> joystick = catalogue.find("movement joystick");
        eq("1", Integer.toString(joystick.size()));
        eq("Show joystick", joystick.get(0).name);

        // Case and accents fold for every surface, including names.
        SettingsSearch accented = new SettingsSearch();
        accented.add("Pokémon stats IV display", "Display", "Catching", 2);
        eq("1", Integer.toString(accented.find("POKEMON").size()));
        eq("1", Integer.toString(accented.find("pokémon").size()));
    }

    private static void synonyms() {
        SettingsSearch search = new SettingsSearch();
        search.add("Location spoofing", "Location & movement", "Location & Map", 0);
        search.add("Dark theme", "Interface", "Display & Performance", 4);
        eq("Location spoofing", single(search.find("fake gps")));
        eq("Location spoofing", single(search.find("mock location")));
        eq("Dark theme", single(search.find("light mode")));
    }

    private static void emptyQueries() {
        SettingsSearch search = new SettingsSearch();
        search.add("Auto ball", "Catching", "Catching", 1);
        eq("0", Integer.toString(search.find("").size()));
        eq("0", Integer.toString(search.find("   ").size()));
        eq("0", Integer.toString(search.find(null).size()));
        eq("0", Integer.toString(search.find("helicopter").size()));
        eq("1", Integer.toString(search.find("ball").size()));
    }

    private static void localizedIndex() {
        I18n.fixtureLanguage("pt");
        try {
            SettingsSearch search = new SettingsSearch();
            int dark = search.add("Dark theme", "Interface", "Display & Performance", 4);
            int location = search.add("Location spoofing", "Location & movement", "Location & Map", 0);
            search.add("Favorite filters", "Quick menu entries", "Interface", 5);
            search.add("Unknown setting", "Interface", "Interface", 6);

            SettingsSearch.Entry translated = search.find("tema escuro").get(0);
            eq("Tema escuro", translated.name);
            eq("Exibição e desempenho", translated.category);
            eq("Alterne toda a interface entre as paletas escura e clara.", translated.description);
            eq(Integer.toString(dark), Integer.toString(translated.id));
            eq("4", Integer.toString(translated.page));
            eq("Tema escuro", single(search.find("DARK")));
            eq("Tema escuro", single(search.find("light mode")));
            eq("Tema escuro", single(search.find("exibicao")));
            eq("Tema escuro", single(search.find("tema performance")));

            SettingsSearch.Entry gps = search.find("simulada movimento").get(0);
            eq("Localização simulada", gps.name);
            eq("Localização e movimento", gps.group);
            eq(Integer.toString(location), Integer.toString(gps.id));
            eq("0", Integer.toString(gps.page));
            eq("Localização simulada", single(search.find("fake gps")));
            eq("Mostrar Filtros favoritos no menu rápido.", search.find("favorite filters").get(0).description);
            eq("Opção de Interface.", search.find("unknown setting").get(0).description);
            eq("Unknown setting", single(search.find("unknown setting")));

            // The built index is a language snapshot, matching the restart-only language policy.
            I18n.fixtureLanguage("en");
            eq("Tema escuro", single(search.find("tema escuro")));
            SettingsSearch nextSession = new SettingsSearch();
            nextSession.add("Dark theme", "Interface", "Display & Performance", 4);
            eq("Dark theme", single(nextSession.find("DARK")));
        } finally {
            I18n.fixtureLanguage("en");
        }
    }

    private static String single(List<SettingsSearch.Entry> hits) {
        eq("1", Integer.toString(hits.size()));
        return hits.get(0).name;
    }

    private static void eq(String expected, String actual) {
        if (!expected.equals(actual)) throw new AssertionError("expected <" + expected + "> but was <" + actual + ">");
    }

    private static void different(String left, String right) {
        if (left.equals(right)) throw new AssertionError("Distinct scripts/marks collapsed to <" + left + ">");
    }
}
