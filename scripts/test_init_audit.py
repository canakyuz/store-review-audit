"""Regression tests for creating honest audit skeletons."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from init_audit import make_audit
from validate_audit import validate

class InitTests(unittest.TestCase):
    def test_apple_starts_incomplete(self):
        d=make_audit("apple","com.example.test","42",["en-GB"],["GB"])
        self.assertEqual(len(d["controls"]),23)
        self.assertEqual(validate(d)["verdict"],"INCOMPLETE")
        self.assertFalse(d["evidence"])
    def test_google_starts_incomplete(self):
        d=make_audit("google","com.example.test","42",["en-GB"],["GB"])
        self.assertEqual(len(d["controls"]),24)
        self.assertEqual(validate(d)["verdict"],"INCOMPLETE")
    def test_unknowns_not_false(self):
        d=make_audit("apple","com.example.test","42",["en-GB","en-GB"],["GB"])
        self.assertTrue(all(v["value"] is None for v in d["features"].values()))
        self.assertEqual(d["scope"]["locales"],["en-GB"])
        self.assertTrue(all(c["status"]=="UNKNOWN" for c in d["controls"]))
    def test_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"audit.json"
            p.write_text("KEEP")
            result=subprocess.run([sys.executable,str(Path(__file__).with_name("init_audit.py")),
                "--platform","apple","--app-id","com.example.test","--build","42",
                "--locales","en-GB","--territories","GB","--output",str(p)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertEqual(p.read_text(),"KEEP")

if __name__ == "__main__":
    unittest.main()
