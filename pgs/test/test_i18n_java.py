"""Compile/run the real resource-free i18n engine with fault fixtures and all generated catalogs."""
from pathlib import Path
import base64
import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/dev/pgs'

CATALOG_FIXTURE = '''package dev.pgs;
import java.util.HashMap;
import java.util.Map;
final class I18nCatalog {
    static Map<String, String> load(String language) {
        Map<String, String> values = new HashMap<>();
        if ("de".equals(language)) values.put("Close", "Schließen");
        if ("fr".equals(language)) {
            values.put("Close", "Fermer");
            values.put("Language", "Langue");
            values.put("Empty translation", "");
            values.put("Special: fixed", "Ligne exacte");
            values.put("Saved %1$s", "%1$s enregistré");
            values.put("Pair %1$s / %2$d", "%2$d puis %1$s");
            values.put("Chance: %d%%", "Chance : %d%%");
            values.put("Coordinates: %.6f, %.6f", "Coordonnées : %.6f, %.6f");
            values.put("Number: %1$,.2f", "Nombre : %1$,.2f");
            values.put("Date: %1$tF", "Date : %1$tF");
            values.put("Broken %1$s", "Cassé %1$d");
            values.put("Missing %1$s", "Manquant %2$s");
            values.put("Extra %1$s", "Extra %1$s %q");
        }
        return values;
    }
}
'''


class I18nJavaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = Path(os.environ.get('JAVA_HOME', '')) / 'bin'
        suffix = '.exe' if os.name == 'nt' else ''
        cls.javac = str(configured / ('javac' + suffix)) if (configured / ('javac' + suffix)).is_file() else shutil.which('javac')
        cls.java = str(configured / ('java' + suffix)) if (configured / ('java' + suffix)).is_file() else shutil.which('java')
        if not cls.javac or not cls.java:
            raise unittest.SkipTest('JDK required for the production i18n engine')

    def compile(self, work, catalogs):
        classes = Path(work) / 'classes'
        classes.mkdir()
        sources = [SOURCE / 'I18n.java', SOURCE / 'LanguagePrefs.java', ROOT / 'test/I18nTest.java', *catalogs]
        result = subprocess.run([self.javac, '-encoding', 'UTF-8', '-d', str(classes), *map(str, sources)],
                                capture_output=True, text=True, encoding='utf-8', timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return classes

    def run_engine(self, classes, *args):
        result = subprocess.run([self.java, '-cp', str(classes), 'dev.pgs.I18nTest', *map(str, args)],
                                capture_output=True, text=True, encoding='utf-8', timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS I18n', result.stdout)
        print(result.stdout.strip())

    def test_real_engine_with_controlled_faults_and_new_process(self):
        with tempfile.TemporaryDirectory(prefix='pgs-i18n-engine-') as work:
            fixture = Path(work) / 'I18nCatalog.java'
            fixture.write_text(CATALOG_FIXTURE, encoding='utf-8')
            classes = self.compile(work, [fixture])
            self.run_engine(classes, 'fixture')
            # A genuinely fresh JVM proves the next process can apply another saved selection.
            self.run_engine(classes, 'restart', 'de')

    def test_all_real_generated_catalogs_round_trip(self):
        dispatcher = SOURCE / 'I18nCatalog.java'
        source_json = ROOT / 'i18n/en.json'
        if not dispatcher.is_file() or not source_json.is_file():
            self.skipTest('Generated catalogs have not been installed yet; tools/check.py requires them')
        catalogs = sorted(SOURCE.glob('I18nCatalog*.java'))
        languages = ('en', 'de', 'es', 'fr', 'pt-BR', 'ru', 'it', 'zh-Hant', 'nl', 'th', 'ko')
        master = json.loads(source_json.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory(prefix='pgs-i18n-real-catalogs-') as work:
            rows = []
            for language in languages:
                values = json.loads((ROOT / 'i18n' / (language + '.json')).read_text(encoding='utf-8'))
                self.assertEqual(set(master), set(values), language)
                for key, value in values.items():
                    encoded = [base64.b64encode(text.encode('utf-8')).decode('ascii') for text in (key, value)]
                    rows.append(language + '\t' + '\t'.join(encoded))
            expected = Path(work) / 'expected.tsv'
            expected.write_text('\n'.join(rows) + '\n', encoding='utf-8')
            classes = self.compile(work, catalogs)
            self.run_engine(classes, 'catalogs', expected)


if __name__ == '__main__':
    unittest.main()
