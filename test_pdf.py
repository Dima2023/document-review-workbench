import csv
import io
from contextlib import redirect_stdout
from unittest.mock import patch
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from review import extract_pdf,parse_mock,validate
class PDFTests(unittest.TestCase):
 def test_real_digital_pdfs(self):
  for name in ['invoice-1.pdf','invoice-2.pdf']:
   p=Path(__file__).parent/'examples'/name
   before=p.read_bytes(); pages=extract_pdf(p)
   fields=parse_mock(pages)
   self.assertEqual(validate(fields),[]); self.assertEqual(p.read_bytes(),before)
   expected=({'invoice':'DEMO-001','date':'2026-10-01','subtotal':'100.00','tax':'20.00','total':'120.00','currency':'USD','source_page':'1'} if name=='invoice-1.pdf' else {'invoice':'DEMO-002','date':'2026-10-02','subtotal':'50.00','tax':'0.00','total':'50.00','currency':'EUR','source_page':'1'})
   self.assertEqual(fields,expected)
 def test_cli_human_gate_and_no_overwrite(self):
  source=Path(__file__).parent/'examples/invoice-1.pdf'
  script=Path(__file__).parent/'review.py'
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/'out.csv'
   cmd=[sys.executable,str(script),str(source),'--output',str(target)]
   r=subprocess.run(cmd,input='\n'*6+'NO\n',capture_output=True,text=True)
   self.assertEqual(r.returncode,2); self.assertFalse(target.exists())
   r=subprocess.run(cmd,input='\n'*6+'APPROVE\n',capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr); before=target.read_bytes()
   self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(),target.read_text())
   r=subprocess.run(cmd,input='\n'*6+'APPROVE\n',capture_output=True,text=True)
   self.assertEqual(r.returncode,2); self.assertEqual(target.read_bytes(),before)
 def test_source_replaced_after_parser_opens_keeps_matching_digest(self):
  import pypdf
  import review
  fixtures=Path(__file__).parent/'examples'
  original=(fixtures/'invoice-1.pdf').read_bytes()
  replacement=(fixtures/'invoice-2.pdf').read_bytes()
  real_reader=pypdf.PdfReader
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.pdf'; source.write_bytes(original)
   target=Path(tmp)/'result.csv'
   def replace_after_open(*args, **kwargs):
    reader=real_reader(*args, **kwargs)
    swapped=Path(tmp)/'replacement.pdf'; swapped.write_bytes(replacement)
    swapped.replace(source)
    return reader
   with patch('pypdf.PdfReader',side_effect=replace_after_open), patch('sys.argv',['review.py',str(source),'--output',str(target)]), patch('builtins.input',side_effect=['']*6+['APPROVE']), redirect_stdout(io.StringIO()):
    self.assertEqual(review.main(),0)
   row=next(csv.DictReader(io.StringIO(target.read_text())))
   self.assertEqual(row['invoice'],'DEMO-001')
   self.assertEqual(source.read_bytes(),replacement)
   self.assertEqual(row['source_sha256'],hashlib.sha256(original).hexdigest())
 def test_snapshot_rejects_oversized_input(self):
  from review import read_snapshot, MAX_PDF_BYTES
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'large.pdf'; source.write_bytes(b'x'*(MAX_PDF_BYTES+1))
   with self.assertRaisesRegex(ValueError,'exceeds 2 MiB'):
    read_snapshot(source)
 def test_malformed_pdf(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'broken.pdf'; path.write_bytes(b'not a PDF')
   with self.assertRaises(ValueError): extract_pdf(path)
if __name__=='__main__': unittest.main()
