from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import review

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.target=self.root/'out.csv'
 def test_success_and_no_overwrite(self):
  review.publish(self.target,b'a,b\n1,2\n');self.assertEqual(self.target.read_bytes(),b'a,b\n1,2\n')
  with self.assertRaises(OSError):review.publish(self.target,b'changed')
  self.assertEqual(self.target.read_bytes(),b'a,b\n1,2\n')
 def test_fsync_failure_publishes_nothing(self):
  with patch.object(review.os,'fsync',side_effect=OSError('synthetic disk error')):
   with self.assertRaises(OSError):review.publish(self.target,b'complete CSV')
  self.assertFalse(self.target.exists());self.assertEqual(list(self.root.iterdir()),[])
 def test_partial_write_failure_publishes_nothing(self):
  original=review.tempfile.NamedTemporaryFile
  class Partial:
   def __init__(self,*args,**kwargs):self.file=original(*args,**kwargs);self.name=self.file.name
   def __enter__(self):self.file.__enter__();return self
   def __exit__(self,*args):return self.file.__exit__(*args)
   def write(self,data):self.file.write(data[:3]);raise OSError('synthetic disk full')
  with patch.object(review.tempfile,'NamedTemporaryFile',Partial):
   with self.assertRaises(OSError):review.publish(self.target,b'complete CSV')
  self.assertFalse(self.target.exists());self.assertEqual(list(self.root.iterdir()),[])
 def test_dangling_symlink_is_preserved(self):
  self.target.symlink_to(self.root/'missing')
  with self.assertRaises(OSError):review.publish(self.target,b'complete CSV')
  self.assertTrue(self.target.is_symlink())
if __name__=='__main__':unittest.main()
