const { spawn } = require('child_process');

const pyCode = [
  'import unittest',
  'import sys',
  'from backend.tests import test_endpoints as te',
  '',
  'class ApiTests(unittest.TestCase):',
  '    @classmethod',
  '    def setUpClass(cls):',
  '        cls.client = te._make_client()',
  '    @classmethod',
  '    def tearDownClass(cls):',
  '        try:',
  '            cls.client.close()',
  '        except Exception:',
  '            pass',
  '    def test_api_players(self):',
  '        te.test_api_players(self.client)',
  '    def test_api_teams(self):',
  '        te.test_api_teams(self.client)',
  '    def test_api_fdr(self):',
  '        te.test_api_fdr(self.client)',
  '    def test_pages_render(self):',
  '        te.test_pages_render(self.client)',
  '',
  'suite = unittest.defaultTestLoader.loadTestsFromTestCase(ApiTests)',
  'res = unittest.TextTestRunner(verbosity=2).run(suite)',
  'sys.exit(0 if res.wasSuccessful() else 1)'
].join('\n');

const child = spawn('python3', ['-c', pyCode], { stdio: 'inherit' });
child.on('close', (code) => process.exit(code));


