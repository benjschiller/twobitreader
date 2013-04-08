# Some of this test code is specific to 2.7
import unittest
import twobitreader


class ByteTableTestCase(unittest.TestCase):
    def setUp(self):
        self.byte_table = twobitreader.create_byte_table()

    def test_module_table(self):
        self.assertTrue(type(twobitreader.BYTE_TABLE) is dict)
        self.assertEquals(len(twobitreader.BYTE_TABLE), 256)
        self.assertEquals(twobitreader.BYTE_TABLE, self.byte_table)

    def test_has_all_keys(self):
        bt = self.byte_table
        for i in range(256):
            self.assertTrue(i in bt)

    def test_polyNs(self):
        bt = self.byte_table
        self.assertEquals(bt[0], ['T', 'T', 'T', 'T'])
        self.assertEquals(bt[85], ['C', 'C', 'C', 'C'])
        self.assertEquals(bt[170], ['A', 'A', 'A', 'A'])
        self.assertEquals(bt[255], ['G', 'G', 'G', 'G'])


class SimpleBytesTestCase(unittest.TestCase):
    def test_bits_to_base(self):
        pass
