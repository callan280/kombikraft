"""The offline gallery serves only files confined to an explicit library root."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from kombikraft.server import ViewerServer


class LibraryServerTests(unittest.TestCase):
    def test_gallery_and_confinement(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);library=root/'gallery';library.mkdir()
            (library/'index.html').write_text('<h1>Offline library</h1>')
            (library/'catalog.js').write_text('const catalog=[];')
            (root/'outside.txt').write_text('PRIVATE OUTSIDE ROOT')
            (library/'outside.json').symlink_to(root/'outside.txt')
            server=ViewerServer(0,library=library)
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                with urllib.request.urlopen(server.origin+'/library/') as response:
                    self.assertIn(b'Offline library',response.read())
                with urllib.request.urlopen(server.origin+'/api/toolkit/status') as response:
                    self.assertTrue(json.load(response)['visualLibraryAvailable'])
                for path in ['/library/../outside.txt','/library/%2e%2e/outside.txt','/library/outside.json']:
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(server.origin+path)
                    self.assertEqual(error.exception.code,404);error.exception.close()
            finally:server.shutdown();server.server_close();worker.join()


if __name__=='__main__':unittest.main()
