# Some of this test code is specific to 2.7
import unittest
import twobitreader
import os
import sys

class HasLongTypeTestCase(unittest.TestCase):
    def test_has_long_type(self):
        self.assertTrue(twobitreader.true_long_type() in ['L', 'I'])

        
class ByteTableTestCase(unittest.TestCase):
    def setUp(self):
        self.byte_table = twobitreader.create_byte_table()

    def test_module_table(self):
        self.assertTrue(type(twobitreader.BYTE_TABLE) is dict)
        self.assertEqual(len(twobitreader.BYTE_TABLE), 256)
        self.assertEqual(twobitreader.BYTE_TABLE, self.byte_table)

    def test_has_all_keys(self):
        bt = self.byte_table
        for i in range(256):
            self.assertTrue(i in bt)

    def test_polyNs(self):
        bt = self.byte_table
        self.assertEqual(bt[0], ['T', 'T', 'T', 'T'])
        self.assertEqual(bt[85], ['C', 'C', 'C', 'C'])
        self.assertEqual(bt[170], ['A', 'A', 'A', 'A'])
        self.assertEqual(bt[255], ['G', 'G', 'G', 'G'])


class SimpleBytesTestCase(unittest.TestCase):
    def test_bits_to_base(self):
        self.assertEqual(twobitreader.bits_to_base(0), 'T')
        self.assertEqual(twobitreader.bits_to_base(1), 'C')
        self.assertEqual(twobitreader.bits_to_base(2), 'A')
        self.assertEqual(twobitreader.bits_to_base(3), 'G')
        self.assertRaises(ValueError, twobitreader.bits_to_base, 4)
        
    def test_base_to_bin(self):
        self.assertEqual(twobitreader.base_to_bin('T'), '00')
        self.assertEqual(twobitreader.base_to_bin('C'), '01')
        self.assertEqual(twobitreader.base_to_bin('A'), '10')
        self.assertEqual(twobitreader.base_to_bin('G'), '11')


class SimpleLongsToCharTest(unittest.TestCase):
    def setUp(self):
        from array import array
        self.longs_array = array(twobitreader.LONG, [683102738, 3396552641,
                                                     3797081033, 1243780212])
        self.as_string = \
         'TCTACCTAAGCGTAATGTTCCTCGCGTGGTAAGTACGCAGCCTAGATACGCTACCTTATACTAA'
        self.chars_array = array(twobitreader._CHAR_CODE,
            'TCTACCTAAGCGTAATGTTCCTCGCGTGGTAAGTACGCAGCCTAGATACGCTACCTTATACTAA')
    
    def test_longs_to_char(self):
        self.assertEqual(twobitreader.longs_to_char_array(self.longs_array,
                                                          0, 16, 64),
                         self.chars_array)
        
    def test_longs_to_string(self):
        as_string = twobitreader.safe_tostring(twobitreader.longs_to_char_array(self.longs_array,
                                                                                0, 16, 64))
        self.assertEqual(as_string, self.as_string)
        
    def test_string_length(self):
        for length in range(65):
            char_array = twobitreader.longs_to_char_array(self.longs_array,
                                                          0, 16, length)
            self.assertEqual(len(char_array), length,
               'Longs to character array conversion failed at length %d' %
               length)
    
    def test_first_base_with_offsets(self):
        for offset in range(16):
            first_base = twobitreader.longs_to_char_array(self.longs_array,
                                                          offset, 16, 1)[0]
            self.assertEqual(first_base, self.chars_array[offset])
            self.assertEqual(first_base, self.as_string[offset])
            
            
    def test_first_base_with_offsets(self):
        for offset in range(16):
            first_base = twobitreader.longs_to_char_array(self.longs_array,
                                                          offset, 16, 1)[0]
            self.assertEqual(first_base, self.chars_array[offset],
                             "Failed at offset %d" % offset)
            self.assertEqual(first_base, self.as_string[offset],
                             "Failed at offset %d" % offset)
            
    def test_last_base_with_offsets(self):
        for offset in reversed(range(1, 17)):
            last_base = twobitreader.longs_to_char_array(
                            self.longs_array,
                            0, offset, 64 - (16 - offset)
                        )[-1]
            self.assertEqual(last_base, self.chars_array[-1 + (offset - 16)])
            self.assertEqual(last_base, self.as_string[-1 + (offset - 16)])

class BadTwoBitFileTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.t = tempfile.mkstemp()
        self.file_handle = os.fdopen(self.t[0], 'w')
    
    def tearDown(self):
        self.file_handle.close()
        os.remove(self.t[1])
    
    def test_open_bad_file(self):
        self.file_handle.write('Writing some garbage to a file\n' * 10)
        self.file_handle.flush()
        self.file_handle.close()
        self.assertRaises(twobitreader.TwoBitFileError,
                          twobitreader.TwoBitFile,
                          self.t[1])
        
    def test_open_empty_file(self):
        self.assertRaises(EOFError,
                          twobitreader.TwoBitFile,
                          self.t[1])
        
    def test_open_not_a_file(self):
        self.assertRaises(IOError,
                          twobitreader.TwoBitFile,
                          'notreallyafile')
        
class CheckTestTwoBitFileTest(unittest.TestCase):
    def setUp(self):
        # not sure how to get the path more robustly
        this_dir = os.path.join(os.path.dirname(__file__))
        self.filename = os.path.join(this_dir, 'test.2bit')
        
    def test_testfile_can_be_opened(self):
        #with open(self.filename) as f:
        #    pass
        f = open(self.filename)
        f.close()
        
    def test_open_twobit_file_and_delete_object(self):
        t = twobitreader.TwoBitFile(self.filename)
        self.assertTrue(isinstance(t, twobitreader.TwoBitFile))
        del t
        
    def test_twobit_file_has_chrs(self):
        """make sure file has chr1 - chr10"""
        t = twobitreader.TwoBitFile(self.filename)
        self.assertEqual(set(t.keys()),
                         set(['chr%d' % x for x in range(1,11)]))
        
    def test_twobit_file_has_sequences(self):
        """make sure file has chr1 - chr10"""
        t = twobitreader.TwoBitFile(self.filename)
        for sequence in t.values():
            self.assertTrue(isinstance(sequence, twobitreader.TwoBitSequence))
    
    def test_twobit_sequence_lengths(self):
        t = twobitreader.TwoBitFile(self.filename)
        self.assertEqual(t.sequence_sizes()['chr1'], 75)
        for i in range(2, 11):
            self.assertEqual(t.sequence_sizes()['chr%d' % i], 50)
    
    def test_twobit_chr1_sequence(self):
        t = twobitreader.TwoBitFile(self.filename)
        chr1 = str(t['chr1'])
        self.assertEqual(chr1, 'GAACATGTACAACCTGACCTTCCACgaacatgtacaacctgaccttccacNNNNATGTACAACCTGACCTTCCAC')
    
    def test_twobit_chr10_sequence(self):
        t = twobitreader.TwoBitFile(self.filename)
        chr10 = str(t['chr10'])
        self.assertEqual(chr10,
                         'gaaagggaactccctgaccccttgtgaaagggaactccctgaccccttgt')

    def test_twobitsequence_getitem_key(self):
        t = twobitreader.TwoBitFile(self.filename)
        keys = [(0,'g'),
                (10,'t'),
                (-10,'g'),
                 (-1,'t'),
               ]
        for key, expected in keys:
            found = t["chr10"].__getitem__(key)
            msg = "__getitem__[%s] failed. Expected %s, got %s" % (key,expected,found)
            self.assertEqual(found,expected,msg)

    def test_twobitsequence_getitem_slice(self):
        t = twobitreader.TwoBitFile(self.filename)
        slices = [(0,10,'gaaagggaac'),
                  (5,10,'ggaac'),
                  (5,None,'ggaactccctgaccccttgtgaaagggaactccctgaccccttgt'),
                  (None,None,'gaaagggaactccctgaccccttgtgaaagggaactccctgaccccttgt'),
                  (-10,-5,'gaccc'),
                  (-5,None,'cttgt'),
                  ]

        for start, end, expected in slices:
            found = t["chr10"][start:end]
            self.assertEqual(found,expected,"__getitem__ failed on [%s:%s]. Expected %s, got %s" % (start,end,expected,found))





