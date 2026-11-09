"""Strict JSON and content round trips through a real isolated CLI database."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'zig-out/bin/doc-engine'


class JsonOutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe_tmp = tempfile.TemporaryDirectory(prefix='doc-engine-c-api-', dir=os.environ.get('TMPDIR'))
        cls.addClassCleanup(cls.probe_tmp.cleanup)
        source = Path(cls.probe_tmp.name) / 'probe.c'
        cls.probe = source.with_suffix('')
        source.write_text('''#include "doc_engine.h"
#include <stdio.h>
int main(int argc, char **argv) {
    if (argc != 4) return 1;
    DocEngineHandle handle = doc_engine_open(argv[1], true);
    if (!handle) return 2;
    char *json = doc_engine_search_json(handle, "needle", argv[2], 5);
    if (!json) return 3;
    puts(json);
    doc_engine_free_string(json);
    json = doc_engine_search_json_ver(handle, "needle", argv[2], argv[3], 5);
    if (!json) return 4;
    puts(json);
    doc_engine_free_string(json);
    doc_engine_close(handle);
    return 0;
}
''')
        sqlite_flags = ['-lsqlite3']
        if shutil.which('pkg-config'):
            flags = subprocess.run(['pkg-config', '--libs', 'sqlite3'], capture_output=True, text=True)
            if flags.returncode == 0:
                sqlite_flags = shlex.split(flags.stdout)
        build = subprocess.run(['cc', str(source), '-I', str(ROOT / 'include'),
                                str(ROOT / 'zig-out/lib/libdocengine.a'), *sqlite_flags,
                                '-lpthread', '-lm', '-o', str(cls.probe)], capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='doc-engine-json-', dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        (self.home / '.hermes/docs/db').mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.home))
        self.path = self.home / 'fixture"\\.md'
        self.content = 'needle first line\nsecond "quoted" \\path\t한글\r\nend\b\f\x01\n'
        self.path.write_bytes(self.content.encode())
        self.lib = 'fixture"\\\nlib'
        self.title = 'title"\\\nvalue'
        self.category = 'cat"\\\tvalue'
        self.version = 'ver"\\\rvalue'
        self.run_cli('index-file', '--lib', self.lib, '--title', self.title,
                     '--category', self.category, '--version', self.version, '--path', str(self.path))

    def run_cli(self, *args):
        return subprocess.run([str(BINARY), *args], env=self.env, check=True,
                              capture_output=True).stdout

    def test_search_and_get_round_trip(self):
        rows = json.loads(self.run_cli('search', 'needle', '--lib', self.lib, '--ver', self.version))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        for key, expected in [('id', self.lib + ':' + self.title), ('lib_id', self.lib),
                              ('title', self.title), ('category', self.category),
                              ('version', self.version), ('path', str(self.path))]:
            self.assertEqual(row[key], expected)
        self.assertEqual(row['snippet'], self.content.replace('needle', '<b>needle</b>'))
        self.assertEqual(self.run_cli('get', row['id']), self.content.encode())

    def test_c_api_search_round_trip(self):
        output = subprocess.run([str(self.probe), str(self.home / '.hermes/docs/db/docs.db'),
                                 self.lib, self.version], check=True, capture_output=True).stdout
        responses = output.splitlines()
        self.assertEqual(len(responses), 2)
        expected = json.loads(self.run_cli('search', 'needle', '--lib', self.lib, '--ver', self.version))
        self.assertEqual(len(expected), 1)
        for response in responses:
            self.assertEqual(json.loads(response), expected)

    def test_list_round_trip(self):
        rows = json.loads(self.run_cli('list'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['lib_id'], self.lib)
        self.assertEqual(rows[0]['category'], self.category)
        self.assertEqual(rows[0]['version'], self.version)
        self.assertEqual(rows[0]['doc_count'], 1)
        self.assertEqual(rows[0]['total_bytes'], len(self.content.encode()))


if __name__ == '__main__':
    unittest.main()
