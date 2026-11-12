from pathlib import Path
import hashlib,importlib.util,json,sys,tempfile,unittest
N=Path(__file__).resolve().parents[1];sys.path.insert(0,str(N));from build import validate_data,confined
from generate_f97 import RoutePack
class NativeInputTests(unittest.TestCase):
 def test_current_visual_profile(self):
  m=validate_data(N/'data/v12');self.assertEqual(len(m['files']),202);self.assertEqual(m['footerBand'],[0,680,1920,720]);self.assertFalse(m['firmwareBinariesIncluded'])
 def test_latest_v13_visual_profile(self):
  m=validate_data(N/'data/v13');self.assertEqual(len(m['files']),204);self.assertEqual(m['visualRevision'],13);self.assertEqual(m['miniBands']['fixedCrossover'],[.35,.65]);self.assertFalse(m['miniBands']['adjustable']);self.assertEqual(m['boostIconScale'],1.68)
 def test_path_escape_and_symlink_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder)/'pack';root.mkdir();other=Path(folder)/'other';other.write_text('external');(root/'link').symlink_to(other)
   for name in ['../other',str(other),'link']:
    with self.assertRaises(ValueError):confined(root,name)
 def test_data_tamper_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder);(root/'table.inc').write_text('bad');m={'schema':'kombikraft-native-visual-inputs-v1','wireCompositionVersion':10,'layoutRevision':12,'files':[{'file':'table.inc','sha256':hashlib.sha256(b'good').hexdigest(),'bytes':3,'kind':'generated-visual-table'}]};(root/'manifest.json').write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'hash mismatch'):validate_data(root)
 def test_public_route_wrong_hash_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder);(root/'mesh.json').write_text('{}');(root/'manifest.json').write_text(json.dumps({'schema':'kombikraft-local-assets-v1','entries':[{'route':'/mesh.json','file':'mesh.json','sha256':'0'*64}]}));pack=RoutePack(root)
   with self.assertRaisesRegex(ValueError,'hash mismatch'):pack.read('/mesh.json')
 def test_authored_source_has_no_private_machine_paths(self):
  for p in (N/'source').iterdir():
   if p.is_file():self.assertNotIn('/Users/',p.read_text(),p.name)
if __name__=='__main__':unittest.main()
