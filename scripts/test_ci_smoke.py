"""Exercise the exact CI smoke block, including a failing CLI (no YAML dependency)."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest


class CiSmokeTest(unittest.TestCase):
    def run_smoke(self, exit_code):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/ci.yml').read_text()
        block = workflow.split('      - name: Verify CLI Binary\n        run: |\n', 1)[1]
        command = '\n'.join(line[10:] for line in block.splitlines() if line.startswith('          '))
        with tempfile.TemporaryDirectory(prefix='doc-engine-ci-', dir=os.environ.get('TMPDIR')) as tmp:
            work = Path(tmp)
            binary = work / 'zig-out/bin/doc-engine'
            binary.parent.mkdir(parents=True)
            binary.write_text(f'#!/bin/sh\nexit {exit_code}\n')
            binary.chmod(0o755)
            library = work / 'zig-out/lib/libdocengine.a'
            library.parent.mkdir(parents=True)
            library.touch()
            return subprocess.run(['bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c', command], cwd=work, capture_output=True).returncode

    def test_cli_failure_fails_ci(self):
        self.assertEqual(self.run_smoke(23), 23)

    def test_cli_success_passes_ci(self):
        self.assertEqual(self.run_smoke(0), 0)


if __name__ == '__main__':
    unittest.main()
