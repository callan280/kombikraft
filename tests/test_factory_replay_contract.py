"""Optional original-code integration test; user-supplied local imports only."""
import os
import unittest

class FactoryReplayTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("KOMBIKRAFT_FIRMWARE_MANIFEST") and
                         os.environ.get("KOMBIKRAFT_FIRMWARE_ROOT"),
                         "Local firmware inputs are not supplied")
    def test_original_initialized_receiver_replay(self):
        from kombikraft.factory.inputs import load_banks
        from kombikraft.factory.backend import OriginalControllerBackend
        from kombikraft.factory.replay import replay
        banks = load_banks(os.environ["KOMBIKRAFT_FIRMWARE_MANIFEST"],
                           os.environ["KOMBIKRAFT_FIRMWARE_ROOT"])
        backend = OriginalControllerBackend(banks)
        self.assertEqual(backend.status()["readiness"], {"rte": 0, "hmi": 0, "api": 0})
        report = replay(backend)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 24)
        self.assertEqual(report["status"]["readiness"], {"rte": 2, "hmi": 1, "api": 1})
        self.assertFalse(report["status"]["fullFactoryStartup"])
        self.assertFalse(report["status"]["physicalTransport"])
        self.assertFalse(report["status"]["factoryGraphics"])
        self.assertEqual(len(backend.kernel_semaphores), 6)
        self.assertEqual([(r["address"], r["value"], r["originalPc"])
                          for r in backend.gate_writes],
                         [("0x7ad25f5", 1, "0x2af99f6"),
                          ("0x795e510", 2, "0x2248a40"),
                          ("0x56dafe4", 1, "0x2197889")])

if __name__ == "__main__":
    unittest.main()
