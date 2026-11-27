"""Exercise the production settings-search catalogue without requiring an Android runtime."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest

ROOT = Path(__file__).resolve().parents[1]

# Only the translation catalog is a fixture; all normalization, indexing, ranking and display
# fields below run the production SettingsSearch. Engine/catalog completeness has its own tests.
I18N_FIXTURE = '''package dev.pgrazor;
import java.util.HashMap;
import java.util.Locale;
final class I18n {
    private static String language = "en";
    private static final HashMap<String, String> PT = new HashMap<>();
    static {
        PT.put("Dark theme", "Tema escuro");
        PT.put("Switch the whole interface between the dark and light palette.", "Alterne toda a interface entre as paletas escura e clara.");
        PT.put("Display & Performance", "Exibição e desempenho");
        PT.put("Location spoofing", "Localização simulada");
        PT.put("Location & movement", "Localização e movimento");
        PT.put("Location & Map", "Localização e mapa");
        PT.put("Quick menu entries", "Entradas do menu rápido");
        PT.put("Favorite filters", "Filtros favoritos");
        PT.put("Show %s in the quick menu.", "Mostrar %s no menu rápido.");
        PT.put("%s option.", "Opção de %s.");
    }
    static void fixtureLanguage(String value) { language = value; }
    public static String t(String source) { return "pt".equals(language) && PT.containsKey(source) ? PT.get(source) : source; }
    public static String format(String source, Object... arguments) { return String.format(Locale.ROOT, t(source), arguments); }
}
'''


class SettingsSearchTests(unittest.TestCase):
    def test_search_catalogue(self):
        home = Path(os.environ.get('JAVA_HOME', '')) / 'bin'
        suffix = '.exe' if os.name == 'nt' else ''
        javac = str(home / ('javac' + suffix)) if (home / ('javac' + suffix)).is_file() else shutil.which('javac')
        java = str(home / ('java' + suffix)) if (home / ('java' + suffix)).is_file() else shutil.which('java')
        if not javac or not java:
            self.skipTest('JDK required')
        with tempfile.TemporaryDirectory(prefix='pgrazor-settings-search-') as work:
            fixture = Path(work) / 'I18n.java'
            fixture.write_text(I18N_FIXTURE, encoding='utf-8')
            subprocess.run(
                [javac, '-encoding', 'UTF-8', '-d', work,
                 str(fixture),
                 str(ROOT / 'src/dev/pgrazor/SettingsSearch.java'),
                 str(ROOT / 'test/SettingsSearchTest.java')],
                check=True, timeout=45)
            result = subprocess.run([java, '-cp', work, 'dev.pgrazor.SettingsSearchTest'],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('SettingsSearch', result.stdout)
            print(result.stdout.strip())
