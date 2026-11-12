"""Optional original-code integration; exact user-supplied local banks only."""
import os
import struct
import unittest


class CheckControlReplayTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('KOMBIKRAFT_CC_MANIFEST') and
                         os.environ.get('KOMBIKRAFT_FIRMWARE_ROOT'),
                         'Local 14-bank Check Control inputs are not supplied')
    def test_interleaved_source_commands_and_counter_only_refresh(self):
        from kombikraft.factory.check_control import OriginalCcControllerBackend,load_check_control_banks
        banks,auxiliary=load_check_control_banks(os.environ['KOMBIKRAFT_CC_MANIFEST'],
                                                os.environ['KOMBIKRAFT_FIRMWARE_ROOT'])
        backend=OriginalCcControllerBackend(banks,auxiliary);backend.initialize()
        self.assertEqual(backend.command({'signal':'bc','raw':1})['events'],[0x98])
        first=backend.command({'signal':'checkControl','raw':{'ccid':2051}})
        self.assertEqual(first['selected']['textLines'],['Emissions failure.',''])
        self.assertEqual(backend.command({'signal':'leftLamp','raw':1})['events'],[0x13d])
        duplicate=backend.command({'signal':'checkControl','raw':{'ccid':2051}})
        self.assertEqual(duplicate['payloadConsumerCalls'],0)
        self.assertEqual(first['selected'],duplicate['selected'])
        native=struct.pack('<8H',2051,11,22,33,44,55,66,77)+bytes(range(46))+bytes(4)
        selected=backend.command({'signal':'checkControl','raw':{'record66Hex':native.hex()}})
        refreshed=native[:64]+b'\x71\xe9'
        counter=backend.command({'signal':'checkControl','raw':{'record66Hex':refreshed.hex()}})
        self.assertEqual(counter['native66Hex'],refreshed.hex())
        self.assertEqual(counter['payloadConsumerCalls'],0)
        self.assertEqual(selected['selected'],counter['selected'])
        self.assertEqual(backend.command({'signal':'rightLamp','raw':1})['events'],[0x13f])
        mode=backend.command({'signal':'checkControl','raw':{'ccid':2051,'mode':2}})
        self.assertEqual(mode['selected']['selectedCcid'],34)
        clear=backend.command({'signal':'checkControl','raw':{'ccid':0,'mode':0}})['selected']
        self.assertEqual(clear['textLines'],[None,None]);self.assertIsNone(clear['primaryIcon'])
        self.assertEqual((clear['iconSelector'],clear['textSelector']),(255,255))
        self.assertEqual((clear['sourceVariantIndex'],clear['sourceCollectionBankOrdinal'],
                          clear['sourceLanguageOrdinal']),(1,1,2))
        self.assertFalse(clear['originalGraphicsReady'])
        self.assertFalse(clear['masterArbitrationVerified'])
        self.assertFalse(clear['physicalCanMappingVerified'])


if __name__=='__main__':unittest.main()
