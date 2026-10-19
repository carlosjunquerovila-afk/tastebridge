import json
import os
import subprocess
import unittest
from unittest.mock import patch
from qloo_adapter import QlooAdapter

KEY = 'SYNTHETIC_TEST_ONLY'
ID = '11111111-1111-4111-8111-111111111111'

class AdapterSecurityTests(unittest.TestCase):
    @patch.dict(os.environ, {'QLOO_API_KEY': KEY, 'QLOO_BASE_URL': 'https://wrong.invalid',
                            'QLOO_TRUSTED_BASE_URL': 'https://wrong.invalid',
                            'OPENAI_API_KEY': 'UNRELATED', 'NODE_OPTIONS': '--inspect'})
    def test_exact_origin_and_minimal_environment(self):
        def run(args, **kw):
            env = kw['env']
            self.assertEqual(env['QLOO_BASE_URL'], 'https://hackathon.api.qloo.com')
            self.assertEqual(env['QLOO_TRUSTED_BASE_URL'], env['QLOO_BASE_URL'])
            self.assertNotIn('OPENAI_API_KEY', env)
            self.assertNotIn('NODE_OPTIONS', env)
            self.assertNotIn(KEY, args)
            kw['stdout'].write(b'[]')
            return subprocess.CompletedProcess(args, 0)
        with patch('subprocess.run', side_effect=run):
            self.assertEqual(QlooAdapter().search('Jazz', 'artist')['status'], 'no_match')

    @patch.dict(os.environ, {'QLOO_API_KEY': KEY})
    def test_successful_payload_cannot_echo_key(self):
        raw = json.dumps([{'entity_id': ID, 'name': KEY}])
        escaped = raw.replace(KEY, ''.join('\\u%04x' % ord(c) for c in KEY))
        for payload in (raw, escaped):
            def run(args, **kw):
                kw['stdout'].write(payload.encode())
                return subprocess.CompletedProcess(args, 0)
            with self.subTest(payload=payload), patch('subprocess.run', side_effect=run):
                result = QlooAdapter().search('Jazz', 'artist')
                self.assertEqual(result['reason'], 'unsafe_response')
                self.assertNotIn(KEY, json.dumps(result))

    @patch.dict(os.environ, {'QLOO_API_KEY': '   '})
    def test_whitespace_key_never_executes(self):
        with patch('subprocess.run') as run:
            self.assertEqual(QlooAdapter().search('Jazz', 'artist')['reason'], 'credential_missing')
            run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
  
