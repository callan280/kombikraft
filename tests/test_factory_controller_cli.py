"""Explicit optional startup choice; no local firmware needed."""
from contextlib import redirect_stderr,redirect_stdout
import io
import unittest
from unittest.mock import Mock,patch
from kombikraft.cli import main


class ControllerCliTests(unittest.TestCase):
    def test_check_control_requires_local_manifest_pair(self):
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as raised:
            main(['serve','--check-control'])
        self.assertEqual(raised.exception.code,2)

    def test_explicit_flag_constructs_one14_bank_machine(self):
        source=Mock();server=Mock();server.origin='http://127.0.0.1:12345'
        server.__enter__=Mock(return_value=server);server.__exit__=Mock(return_value=False)
        server.serve_forever.side_effect=KeyboardInterrupt
        with patch('kombikraft.factory.worker.SourceControllerProcess',return_value=source) as create, \
             patch('kombikraft.server.ViewerServer',return_value=server) as serve,redirect_stdout(io.StringIO()):
            self.assertEqual(main(['serve','--check-control','--firmware-manifest','input.json','--firmware-root','banks']),0)
        create.assert_called_once_with('input.json','banks',check_control=True)
        source.initialize.assert_not_called();source.close.assert_called_once_with()
        self.assertTrue(serve.call_args.kwargs['check_control'])


if __name__=='__main__':unittest.main()
