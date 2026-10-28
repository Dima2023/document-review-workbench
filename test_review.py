import unittest
from review import parse_mock, validate, export_csv
class Tests(unittest.TestCase):
 def test_two_layouts(self):
  for text in ['Invoice: DEMO-001\nDate: 2026-10-01\nSubtotal: 100.00\nTax: 20.00\nTotal: 120.00\nCurrency: USD', 'Invoice number | DEMO-002\nIssue date | 2026-10-02\nNet amount | 50.00\nTax amount | 0.00\nAmount due | 50.00\nCurrency | EUR']:
   fields=parse_mock([text]); self.assertEqual(validate(fields),[]); self.assertEqual(fields['source_page'],'1')
 def test_missing_and_mismatch(self):
  fields=parse_mock(['Invoice: X']); self.assertTrue(validate(fields))
  fields.update(date='2026-02-30',subtotal='1.00',tax='2.00',total='4.00',currency='USD')
  errors=validate(fields); self.assertIn('Invalid date',errors); self.assertIn('Subtotal plus tax must equal total',errors)
 def test_export_requires_approval(self):
  fields=parse_mock(['Invoice: DEMO-001\nDate: 2026-10-01\nSubtotal: 1.00\nTax: 0.00\nTotal: 1.00\nCurrency: USD'])
  with self.assertRaises(ValueError): export_csv(fields,'example.pdf','abc',False)
  self.assertIn('DEMO-001',export_csv(fields,'example.pdf','abc',True))
 def test_bad_amounts_and_formula(self):
  fields={'invoice':'=BAD','date':'2026-10-01','subtotal':'NaN','tax':'-1','total':'0','currency':'USD','source_page':'1'}
  self.assertTrue(validate(fields))
 def test_ambiguous_duplicates(self):
  with self.assertRaises(ValueError): parse_mock(['Invoice: ONE\nInvoice: TWO'])
if __name__=='__main__': unittest.main()
