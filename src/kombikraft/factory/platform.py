"""Restricted deterministic single-thread platform adapters, not an RTOS."""
import struct

class PlatformBoundaryError(RuntimeError):
    pass

class TrackedMutexes:
    def __init__(self):
        self.objects = {}
        self.events = []

    def initialize(self, address, attrs, raw):
        if not address:
            return 0x16
        if attrs or len(raw) != 32 or address in self.objects:
            raise PlatformBoundaryError("Unadmitted mutex initialization or lifetime")
        self.objects[address] = False
        self.events.append(("initialize", address))
        return 0

    def acquire(self, address):
        if address not in self.objects or self.objects[address]:
            raise PlatformBoundaryError("Uninitialized or already owned mutex")
        self.objects[address] = True
        self.events.append(("acquire", address))
        return 0

    def release(self, address):
        if address not in self.objects or not self.objects[address]:
            raise PlatformBoundaryError("Uninitialized or unowned mutex release")
        self.objects[address] = False
        self.events.append(("release", address))
        return 0

class FixedClock:
    def __init__(self, admitted_handle):
        self.handle = admitted_handle
        self.microseconds = 1_000_000
        self.reads = 0

    def read(self, handle):
        if handle != self.handle:
            raise PlatformBoundaryError("Unadmitted clock handle")
        seconds, remainder = divmod(self.microseconds, 1_000_000)
        fraction = (remainder * (1 << 32) + 999_999) // 1_000_000
        self.microseconds += 1000
        self.reads += 1
        return struct.pack("<qI", seconds, fraction)
