"""OpenAI extractor tests with a faked HTTP layer: no network, no key needed."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import openai_provider
import review
from openai_provider import OpenAIExtractor

EXAMPLES = Path(__file__).parent / 'examples'
GOOD = {'invoice': 'INV-2026-0147', 'date': '2026-10-14', 'subtotal': '1240.00', 'tax': '248.00',
        'total': '1488.00', 'currency': 'GBP', 'source_page': '1'}


class FakeResponse:
    def __init__(self, status=200, content=None, refusal=None, body=None):
        self.status_code = status
        self._body = body if body is not None else {
            'choices': [{'message': {'content': json.dumps(content) if isinstance(content, dict) else content,
                                     'refusal': refusal}}]}

    def json(self):
        return self._body


class ExtractorTests(unittest.TestCase):
    def call(self, response):
        with patch.object(openai_provider.requests, 'post', return_value=response) as post:
            result = OpenAIExtractor(model='test-model', key='sk-test').extract(['page one', 'page two'])
        return result, post

    def test_request_shape_and_result(self):
        result, post = self.call(FakeResponse(content=GOOD))
        self.assertEqual(result, GOOD)
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['model'], 'test-model')
        self.assertTrue(payload['response_format']['json_schema']['strict'])
        self.assertIn('=== PAGE 2 ===', payload['messages'][1]['content'])
        self.assertIn('untrusted', payload['messages'][0]['content'])
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer sk-test')

    def test_refusal_invalid_json_and_schema_drift(self):
        for response in [FakeResponse(refusal='cannot help'), FakeResponse(content='not json'),
                         FakeResponse(content={**GOOD, 'extra': 'x'}), FakeResponse(content={**GOOD, 'total': 5})]:
            with self.assertRaises(ValueError):
                self.call(response)

    def test_api_error_does_not_leak_key(self):
        with self.assertRaises(ValueError) as caught:
            self.call(FakeResponse(status=401, body={'error': {'message': 'Incorrect API key'}}))
        self.assertIn('401', str(caught.exception))
        self.assertNotIn('sk-test', str(caught.exception))

    def test_key_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            key_file = Path(tmp) / 'key'
            key_file.write_text('sk-from-file\n')
            with patch.dict(os.environ, {'OPENAI_API_KEY': '', 'OPENAI_API_KEY_FILE': str(key_file)}):
                self.assertEqual(openai_provider.load_key(), 'sk-from-file')
            with patch.dict(os.environ, {'OPENAI_API_KEY': '', 'OPENAI_API_KEY_FILE': ''}):
                with self.assertRaises(ValueError):
                    openai_provider.load_key()


class CliTests(unittest.TestCase):
    def run_cli(self, fields, answers):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'out.csv'
            argv = ['review.py', str(EXAMPLES / 'invoice-3.pdf'), '--output', str(target), '--extractor', 'openai']
            out = io.StringIO()
            with patch.object(OpenAIExtractor, 'extract', return_value=fields), patch('sys.argv', argv), \
                    patch('builtins.input', side_effect=answers), redirect_stdout(out):
                code = review.main()
            return code, out.getvalue(), target.read_text() if target.exists() else None

    def test_offline_rules_cannot_read_new_layout(self):
        pages = review.extract_pdf(EXAMPLES / 'invoice-3.pdf')
        self.assertFalse(any(review.parse_mock(pages).values()))

    def test_openai_path_exports_with_mode(self):
        code, out, csv_text = self.run_cli(dict(GOOD), [''] * 6 + ['APPROVE'])
        self.assertEqual(code, 0, out)
        self.assertIn('Extraction: openai:', out)
        self.assertIn('INV-2026-0147', csv_text)
        self.assertIn(',openai:', csv_text)

    def test_validation_still_guards_model_output(self):
        bad = dict(GOOD, total='1500.00')  # does not add up
        code, out, csv_text = self.run_cli(bad, [''] * 6)
        self.assertEqual(code, 2)
        self.assertIn('Subtotal plus tax must equal total', out)
        self.assertIsNone(csv_text)

    def test_nonexistent_source_page_rejected(self):
        code, out, _ = self.run_cli(dict(GOOD, source_page='7'), [''] * 6)
        self.assertEqual(code, 2)
        self.assertIn('source page', out)


if __name__ == '__main__':
    unittest.main()
