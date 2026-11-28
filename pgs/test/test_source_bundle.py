import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

SPEC=importlib.util.spec_from_file_location('source_bundle',Path(__file__).resolve().parents[2]/'tools/source_bundle.py')
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class SourceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.git('init','-q')

    def git(self,*args):
        subprocess.run(['git',*args],cwd=self.root,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    def write(self,name,text='source'):
        path=self.root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding='utf-8')
        return path

    def test_main_creates_pgs_archive_with_tracked_source(self):
        self.write('README.md','PGS source')
        self.write('native/example.cpp','example source')
        self.git('add','.')
        with mock.patch.object(MODULE,'ROOT',self.root):
            MODULE.main([])
        output=self.root/'dist/PGS-source-tools.zip'
        self.assertTrue(output.is_file())
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.namelist(),['README.md','native/example.cpp'])
            self.assertEqual(archive.read('README.md'),b'PGS source')
            self.assertEqual(archive.read('native/example.cpp'),b'example source')

    def test_ci_upload_matches_pgs_archive_name(self):
        workflow=(Path(__file__).resolve().parents[2]/'.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn('name: PGS-source-tools\n',workflow)
        self.assertIn('path: dist/PGS-source-tools.zip\n',workflow)

    def test_tracked_deletion_does_not_resurrect_source(self):
        old=self.write('old.js')
        self.write('README.md')
        self.git('add','.')
        old.unlink()
        self.assertEqual([name for _,name in MODULE.select_files(self.root)],['README.md'])

    def test_explicit_untracked_allowlist_excludes_ignored_and_private_inputs(self):
        self.write('README.md')
        self.write('.gitignore','pgs/native/ignored.cpp\n')
        self.git('add','.')
        self.write('pgs/native/new.cpp')
        self.write('pgs/native/shared_metadata_gifts.inc')
        self.write('pgs/native/schema/routes.json')
        self.write('pgs/native/ignored.cpp')
        self.write('notes-handoff.md')
        self.write('pgs/input/original.apk')
        with self.assertRaisesRegex(ValueError,'--include-working-tree'):
            MODULE.select_files(self.root)
        names=[name for _,name in MODULE.select_files(self.root,True)]
        self.assertIn('pgs/native/new.cpp',names)
        self.assertIn('pgs/native/shared_metadata_gifts.inc',names)
        self.assertIn('pgs/native/schema/routes.json',names)
        for name in ('notes-handoff.md','pgs/input/original.apk','pgs/native/ignored.cpp'):
            self.assertNotIn(name,names)

    def test_secret_inside_allowlist_and_tracked_key_fail_closed(self):
        secret=self.write('pgs/native/credentials.json')
        with self.assertRaisesRegex(ValueError,'Private/generated'):
            MODULE.select_files(self.root,True)
        secret.unlink()
        self.write('signing.key')
        self.git('add','.')
        with self.assertRaisesRegex(ValueError,'Private/generated'):
            MODULE.select_files(self.root)

    def test_named_build_tools_are_included_but_arbitrary_tools_are_not(self):
        self.write('pgs/native_build.py')
        self.write('tools/native_routes_schema.py')
        self.write('tools/my_notes.py')
        names=[name for _,name in MODULE.select_files(self.root,True)]
        self.assertEqual(names,['pgs/native_build.py','tools/native_routes_schema.py'])

    def test_path_escape_is_rejected(self):
        for name in ('../outside.cpp','C:/outside.cpp','native\\file.cpp'):
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                MODULE.validate(self.root,name)

    def test_parent_symlink_is_rejected(self):
        real=self.root/'real'
        real.mkdir()
        (real/'file.cpp').write_text('source')
        try:
            (self.root/'alias').symlink_to(real,target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks requires platform privileges')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            MODULE.validate(self.root,'alias/file.cpp')

if __name__=='__main__': unittest.main()
