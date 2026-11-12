import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from kombikraft.assets import AssetPack, AssetError

class AssetTests(unittest.TestCase):
    def make_pack(self, root, **changes):
        content=b"ordinary synthetic test data"
        Path(root,"glyph.txt").write_bytes(content)
        entry={"route":"/design/assets/test.txt","file":"glyph.txt","sha256":hashlib.sha256(content).hexdigest()}
        entry.update(changes)
        Path(root,"manifest.json").write_text(json.dumps({"schema":"kombikraft-local-assets-v1","entries":[entry]}))
        return entry

    def test_hash_checked_at_admission_and_read(self):
        with tempfile.TemporaryDirectory() as root:
            entry=self.make_pack(root)
            pack=AssetPack(root)
            self.assertEqual(pack.read(entry["route"]),b"ordinary synthetic test data")
            Path(root,"glyph.txt").write_bytes(b"changed after admission")
            with self.assertRaises(AssetError):pack.read(entry["route"])

    def test_path_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ("../escape.txt","/tmp/escape.txt","folder/../glyph.txt"):
                self.make_pack(root,file=name)
                with self.assertRaises(AssetError):AssetPack(root)
            Path(root,"link.txt").symlink_to(Path(root,"glyph.txt"))
            self.make_pack(root,file="link.txt")
            with self.assertRaises(AssetError):AssetPack(root)

    def test_reserved_route_and_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            self.make_pack(root,route="/api/control")
            with self.assertRaises(AssetError):AssetPack(root)
            entry=self.make_pack(root)
            Path(root,"manifest.json").write_text(json.dumps({"schema":"kombikraft-local-assets-v1","entries":[entry,entry]}))
            with self.assertRaises(AssetError):AssetPack(root)

if __name__=="__main__":unittest.main()
