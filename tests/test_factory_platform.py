import struct
import unittest
from kombikraft.factory.platform import FixedClock, PlatformBoundaryError, TrackedMutexes

class FactoryPlatformTests(unittest.TestCase):
    def test_clock_fixed_point_and_unknown_handle(self):
        clock = FixedClock(7)
        for raw in (0, 1, 999, 1000, 999999, 1000000, 123456789):
            clock.microseconds = raw
            seconds, fraction = struct.unpack("<qI", clock.read(7))
            self.assertEqual(seconds * 1_000_000 + (fraction * 1_000_000 >> 32), raw)
        with self.assertRaises(PlatformBoundaryError):
            clock.read(8)

    def test_tracked_ownership_and_lifetime(self):
        mutex = TrackedMutexes()
        self.assertEqual(mutex.initialize(0, 0, b""), 0x16)
        with self.assertRaises(PlatformBoundaryError):
            mutex.acquire(16)
        mutex.initialize(16, 0, bytes(32))
        mutex.acquire(16)
        with self.assertRaises(PlatformBoundaryError):
            mutex.acquire(16)
        mutex.release(16)
        with self.assertRaises(PlatformBoundaryError):
            mutex.release(16)
        with self.assertRaises(PlatformBoundaryError):
            mutex.initialize(16, 0, bytes(32))

if __name__ == "__main__":
    unittest.main()
