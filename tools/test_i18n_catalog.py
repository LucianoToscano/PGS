"""Offline catalog validation/generation regression tests; no translation service or Android needed."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import i18n_catalog as catalog


class PlaceholderTests(unittest.TestCase):
    def test_only_explicit_arguments_may_move(self):
        compatible = catalog.compatible_placeholders
        self.assertTrue(compatible('%1$s: %2$d', '%2$d — %1$s'))
        self.assertTrue(compatible('%1$.2f%% / %2$s / %1$.2f', '%2$s / %1$.2f / %1$.2f%%'))
        self.assertTrue(compatible('%1$tF %1$tT%n%2$s', '%2$s%n%1$tT %1$tF'))
        self.assertTrue(compatible('%s %d', '%s %d'))
        self.assertFalse(compatible('%s %d', '%d %s'))
        self.assertFalse(compatible('%s %2$d', '%2$d %s'))
        self.assertFalse(compatible('%1$s %<s %2$d', '%2$d %1$s %<s'))

    def test_indexes_types_precision_and_multiplicity_stay_exact(self):
        for source, translated in (
                ('%1$s %2$s', '%1$s %3$s'),
                ('%1$s %2$d', '%1$d %2$s'),
                ('%1$.1f', '%1$.2f'),
                ('%1$,d', '%1$d'),
                ('%1$s %1$s', '%1$s'),
                ('%1$s', '%1$s %2$s'),
                ('%d%%', '%d'),
                ('%1$s%n', '%1$s'),
                ('%1$s', '%0$s'),
                ('%1$s', '%1$s %q'),
                ('%1$s', '%1$s 100% chance'),
                ('%1$s %%', '%1$s %')):
            with self.subTest(source=source, translated=translated):
                self.assertFalse(catalog.compatible_placeholders(source, translated))

    def test_literal_percentages_and_real_java_formats(self):
        self.assertEqual([], catalog.placeholders('Perfect (100% IV)'))
        self.assertEqual([], catalog.placeholders('Keep 0% IV (0/0/0)'))
        self.assertEqual(['%,d', '%.6f', '%%', '%1$s', '%2$d'],
                         catalog.placeholders('%,d XP / %.6f / %% / %1$s %2$d'))
        self.assertTrue(catalog.compatible_placeholders('Perfect (100% IV)', 'Perfekt (100% IV)'))
        self.assertTrue(catalog.compatible_placeholders('100%% %1$s', '%1$s 100%%'))
        self.assertFalse(catalog.compatible_placeholders('100%% %1$s', '%1$s 100%'))


class CatalogTests(unittest.TestCase):
    SOURCE = {
        'Close': 'Close',
        'Pair %1$s / %2$d': 'Pair %1$s / %2$d',
        'Rate %.1f%%': 'Rate %.1f%%',
        'Perfect (100% IV)': 'Perfect (100% IV)',
        'Quote " and slash \\ and\nline': 'Quote " and slash \\ and\nline',
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pgs-catalog-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'catalog'
        self.java = self.root / 'java'
        self.folder.mkdir()
        self.java.mkdir()
        for language in catalog.LANGUAGES:
            self.write(language, dict(self.SOURCE))
        for attribute, value in (('CATALOG', self.folder), ('JAVA', self.java), ('ROOT', self.root)):
            setting = patch.object(catalog, attribute, value)
            setting.start()
            self.addCleanup(setting.stop)

    def write(self, language, messages):
        (self.folder / (language + '.json')).write_text(
            json.dumps(messages, ensure_ascii=False), encoding='utf-8')

    def test_all_languages_and_exact_master_keys(self):
        data = catalog.catalogs()
        self.assertEqual(set(catalog.LANGUAGES), set(data))
        for messages in data.values():
            self.assertEqual(set(self.SOURCE), set(messages))

    def test_missing_and_extra_keys_fail(self):
        for changed in ({k: v for k, v in self.SOURCE.items() if k != 'Close'},
                        dict(self.SOURCE, extra='extra')):
            self.write('fr', changed)
            with self.assertRaisesRegex(ValueError, 'fr: .*missing.*extra'):
                catalog.catalogs()

    def test_non_object_empty_null_and_duplicate_translations_fail(self):
        self.write('fr', list(self.SOURCE))
        with self.assertRaisesRegex(ValueError, 'catalog must be an object'):
            catalog.catalogs()
        for value in ('', '   ', '\x00', None, 1):
            self.write('fr', dict(self.SOURCE, Close=value))
            with self.assertRaisesRegex(ValueError, 'empty or invalid'):
                catalog.catalogs()
        (self.folder / 'fr.json').write_text('{"Close":"Fermer","Close":"Autre"}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate message key'):
            catalog.catalogs()

    def test_english_is_canonical_and_nonempty(self):
        for value in ({}, [], {'Close': 'Fermer'}, {'': ''}):
            with self.subTest(value=value):
                self.write('en', value)
                with self.assertRaises(ValueError):
                    catalog.catalogs()

    def test_index_reordering_validates_but_type_change_fails(self):
        values = dict(self.SOURCE)
        values['Pair %1$s / %2$d'] = '%2$d puis %1$s'
        self.write('fr', values)
        self.assertEqual('%2$d puis %1$s', catalog.catalogs()['fr']['Pair %1$s / %2$d'])
        values['Pair %1$s / %2$d'] = '%2$s puis %1$s'
        self.write('fr', values)
        with self.assertRaisesRegex(ValueError, 'changed formatting placeholders'):
            catalog.catalogs()

    def test_generation_is_sorted_chunked_utf8_and_resource_independent(self):
        messages = {'Key %03d' % i: 'Français น้ำ 繁體中文 한국어 " \\ \n %03d' % i for i in range(257)}
        data = {language: messages for language in catalog.LANGUAGES}
        first = catalog.generated(data)
        reversed_data = {language: dict(reversed(list(messages.items()))) for language in catalog.LANGUAGES}
        self.assertEqual(first, catalog.generated(reversed_data))
        self.assertEqual(len(catalog.LANGUAGES), len(first))
        french = first[self.java / 'I18nCatalog_fr.java']
        self.assertEqual(257, french.count('values.put('))
        self.assertIn('fill0(values);', french)
        self.assertIn('fill1(values);', french)
        self.assertIn('fill2(values);', french)
        self.assertNotIn('fill3(values);', french)
        self.assertIn('Français น้ำ 繁體中文 한국어', french)
        self.assertIn('\\"', french)
        self.assertIn('\\\\', french)
        self.assertIn('\\n', french)
        self.assertNotIn('android.', french)
        dispatch = first[self.java / 'I18nCatalog.java']
        self.assertIn('case "pt-BR": return I18nCatalog_pt_BR.load();', dispatch)
        self.assertIn('case "zh-Hant": return I18nCatalog_zh_Hant.load();', dispatch)

    def test_check_rejects_missing_and_stale_generated_files(self):
        with patch('sys.argv', ['i18n_catalog.py', '--check']), redirect_stdout(StringIO()):
            with self.assertRaisesRegex(ValueError, 'Stale generated'):
                catalog.main()
        with patch('sys.argv', ['i18n_catalog.py']), redirect_stdout(StringIO()):
            catalog.main()
        with patch('sys.argv', ['i18n_catalog.py', '--check']), redirect_stdout(StringIO()):
            catalog.main()
        target = self.java / 'I18nCatalog_fr.java'
        target.write_text(target.read_text(encoding='utf-8') + '// changed\n', encoding='utf-8')
        with patch('sys.argv', ['i18n_catalog.py', '--check']), redirect_stdout(StringIO()):
            with self.assertRaisesRegex(ValueError, 'Stale generated'):
                catalog.main()


if __name__ == '__main__':
    unittest.main()
