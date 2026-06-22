# Some of this test code is specific to 2.7
import sys

sys.path.insert(0, "..")
import unittest
import twobitreader
import os
import pickle
import struct
import tempfile

if sys.version_info < (3,):
    from cStringIO import StringIO
else:
    from io import BytesIO as StringIO


BASE_TO_BITS = {
    "T": 0,
    "C": 1,
    "A": 2,
    "G": 3,
    "N": 0,
}


def pack_sequence(seq):
    packed = bytearray()
    for block_start in range(0, len(seq), 4):
        byte = 0
        block = seq[block_start : block_start + 4]
        for index, base in enumerate(block):
            byte |= BASE_TO_BITS[base.upper()] << (6 - index * 2)
        packed.append(byte)
    while len(packed) % 4:
        packed.append(0)
    return bytes(packed)


def twobit_record(seq, n_blocks=(), mask_blocks=()):
    n_starts = [start for start, _ in n_blocks]
    n_sizes = [size for _, size in n_blocks]
    mask_starts = [start for start, _ in mask_blocks]
    mask_sizes = [size for _, size in mask_blocks]
    return b"".join(
        [
            struct.pack("<I", len(seq)),
            struct.pack("<I", len(n_blocks)),
            b"".join(struct.pack("<I", start) for start in n_starts),
            b"".join(struct.pack("<I", size) for size in n_sizes),
            struct.pack("<I", len(mask_blocks)),
            b"".join(struct.pack("<I", start) for start in mask_starts),
            b"".join(struct.pack("<I", size) for size in mask_sizes),
            struct.pack("<I", 0),
            pack_sequence(seq),
        ]
    )


def write_twobit_file(path, sequences):
    names = list(sequences)
    index_size = sum(1 + len(name.encode("ascii")) + 4 for name in names)
    offset = 16 + index_size
    index = []
    records = []
    for name in names:
        encoded_name = name.encode("ascii")
        data = sequences[name]
        body = twobit_record(data["seq"], data.get("n_blocks", ()), data.get("mask_blocks", ()))
        index.append(struct.pack("B", len(encoded_name)) + encoded_name + struct.pack("<I", offset))
        records.append(body)
        offset += len(body)
    with open(path, "wb") as handle:
        handle.write(
            b"".join(
                [
                    struct.pack("<IIII", 0x1A412743, 0, len(names), 0),
                    b"".join(index),
                    b"".join(records),
                ]
            )
        )


class HasLongTypeTestCase(unittest.TestCase):
    def test_has_long_type(self):
        self.assertTrue(twobitreader.true_long_type() in ["L", "I"])


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
        self.assertEqual(bt[0], ["T", "T", "T", "T"])
        self.assertEqual(bt[85], ["C", "C", "C", "C"])
        self.assertEqual(bt[170], ["A", "A", "A", "A"])
        self.assertEqual(bt[255], ["G", "G", "G", "G"])

    def test_twobyte_table(self):
        self.assertEqual(len(twobitreader.TWOBYTE_TABLE), 2**16)
        self.assertEqual(twobitreader.TWOBYTE_TABLE[0], ["T"] * 8)
        self.assertEqual(twobitreader.TWOBYTE_TABLE[0xFFFF], ["G"] * 8)


class SimpleBytesTestCase(unittest.TestCase):
    def test_bits_to_base(self):
        self.assertEqual(twobitreader.bits_to_base(0), "T")
        self.assertEqual(twobitreader.bits_to_base(1), "C")
        self.assertEqual(twobitreader.bits_to_base(2), "A")
        self.assertEqual(twobitreader.bits_to_base(3), "G")
        self.assertRaises(ValueError, twobitreader.bits_to_base, 4)

    def test_base_to_bin(self):
        self.assertEqual(twobitreader.base_to_bin("T"), "00")
        self.assertEqual(twobitreader.base_to_bin("C"), "01")
        self.assertEqual(twobitreader.base_to_bin("A"), "10")
        self.assertEqual(twobitreader.base_to_bin("G"), "11")


class SimpleLongsToCharTest(unittest.TestCase):
    def setUp(self):
        from array import array

        self.longs_array = array(twobitreader.LONG, [683102738, 3396552641, 3797081033, 1243780212])
        self.as_string = "TCTACCTAAGCGTAATGTTCCTCGCGTGGTAAGTACGCAGCCTAGATACGCTACCTTATACTAA"
        self.chars_array = list("TCTACCTAAGCGTAATGTTCCTCGCGTGGTAAGTACGCAGCCTAGATACGCTACCTTATACTAA")

    def test_longs_to_char(self):
        chars = twobitreader.longs_to_char_array(self.longs_array, 0, 16, 64)
        self.assertEqual(chars, self.chars_array)
        self.assertTrue(isinstance(chars, list))

    def test_longs_to_string(self):
        as_string = twobitreader.safe_tostring(twobitreader.longs_to_char_array(self.longs_array, 0, 16, 64))
        self.assertEqual(as_string, self.as_string)

    def test_string_length(self):
        for length in range(65):
            char_array = twobitreader.longs_to_char_array(self.longs_array, 0, 16, length)
            self.assertEqual(len(char_array), length, "Longs to character array conversion failed at length %d" % length)

    def test_first_base_with_offsets(self):
        for offset in range(16):
            first_base = twobitreader.longs_to_char_array(self.longs_array, offset, 16, 1)[0]
            self.assertEqual(first_base, self.chars_array[offset])
            self.assertEqual(first_base, self.as_string[offset])

    def test_first_base_with_offsets(self):
        for offset in range(16):
            first_base = twobitreader.longs_to_char_array(self.longs_array, offset, 16, 1)[0]
            self.assertEqual(first_base, self.chars_array[offset], "Failed at offset %d" % offset)
            self.assertEqual(first_base, self.as_string[offset], "Failed at offset %d" % offset)

    def test_last_base_with_offsets(self):
        for offset in reversed(range(1, 17)):
            last_base = twobitreader.longs_to_char_array(self.longs_array, 0, offset, 64 - (16 - offset))[-1]
            self.assertEqual(last_base, self.chars_array[-1 + (offset - 16)])
            self.assertEqual(last_base, self.as_string[-1 + (offset - 16)])


class BadTwoBitFileTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.t = tempfile.mkstemp()
        self.file_handle = os.fdopen(self.t[0], "w")

    def tearDown(self):
        self.file_handle.close()
        os.remove(self.t[1])

    def test_open_bad_file(self):
        self.file_handle.write("Writing some garbage to a file\n" * 10)
        self.file_handle.flush()
        self.file_handle.close()
        self.assertRaises(twobitreader.TwoBitFileError, twobitreader.TwoBitFile, self.t[1])

    def test_open_empty_file(self):
        self.assertRaises(EOFError, twobitreader.TwoBitFile, self.t[1])

    def test_open_not_a_file(self):
        self.assertRaises(IOError, twobitreader.TwoBitFile, "notreallyafile")


class GeneratedTwoBitFileTest(unittest.TestCase):
    def setUp(self):
        fd, self.filename = tempfile.mkstemp(suffix=".2bit")
        os.close(fd)

    def tearDown(self):
        os.remove(self.filename)

    def test_short_last_chromosome_slices(self):
        write_twobit_file(
            self.filename,
            {
                "FIRST_CHR": {
                    "seq": "ACGTACGTACGTACGTACGTACGTACGTA",
                },
                "LAST_CHR": {
                    "seq": "AAAGGGGGGC",
                },
            },
        )
        with twobitreader.TwoBitFile(self.filename) as reader:
            self.assertEqual(reader["LAST_CHR"][0:9], "AAAGGGGGG")
            self.assertEqual(reader["LAST_CHR"][5:6], "G")
            self.assertEqual(reader["LAST_CHR"][6:9], "GGG")
            self.assertEqual(reader["LAST_CHR"][0:10], "AAAGGGGGGC")
            self.assertEqual(reader["LAST_CHR"][:], "AAAGGGGGGC")

    def test_n_and_mask_blocks_are_applied_to_overlapping_slices(self):
        write_twobit_file(
            self.filename,
            {
                "chr1": {
                    "seq": "ACGTACGTACGTACGTACGTACGTACGTACGT",
                    "n_blocks": [(4, 3), (20, 5)],
                    "mask_blocks": [(10, 4), (24, 4)],
                },
            },
        )
        with twobitreader.TwoBitFile(self.filename) as reader:
            self.assertEqual(reader["chr1"][0:12], "ACGTNNNTACgt")
            self.assertEqual(reader["chr1"][18:29], "GTNNNNncgtA")


class CheckTestTwoBitFileTest(unittest.TestCase):
    def setUp(self):
        # not sure how to get the path more robustly
        this_dir = os.path.join(os.path.dirname(__file__))
        self.filename = os.path.join(this_dir, "test.2bit")

    def test_testfile_can_be_opened(self):
        # with open(self.filename) as f:
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
        self.assertEqual(set(t.keys()), set(["chr%d" % x for x in range(1, 11)]))
        t.close()

    def test_twobit_file_has_sequences(self):
        """make sure file has chr1 - chr10"""
        t = twobitreader.TwoBitFile(self.filename)
        for sequence in t.values():
            self.assertTrue(isinstance(sequence, twobitreader.TwoBitSequence))
        t.close()

    def test_twobit_sequence_lengths(self):
        t = twobitreader.TwoBitFile(self.filename)
        self.assertEqual(t.sequence_sizes()["chr1"], 75)
        for i in range(2, 11):
            self.assertEqual(t.sequence_sizes()["chr%d" % i], 50)
        t.close()

    def test_twobit_chr1_sequence(self):
        t = twobitreader.TwoBitFile(self.filename)
        chr1 = str(t["chr1"])
        self.assertEqual(chr1, "GAACATGTACAACCTGACCTTCCACgaacatgtacaacctgaccttccacNNNNATGTACAACCTGACCTTCCAC")
        t.close()

    def test_twobit_chr10_sequence(self):
        t = twobitreader.TwoBitFile(self.filename)
        chr10 = str(t["chr10"])
        self.assertEqual(chr10, "gaaagggaactccctgaccccttgtgaaagggaactccctgaccccttgt")
        t.close()

    def test_twobitsequence_getitem_key(self):
        t = twobitreader.TwoBitFile(self.filename)
        keys = [
            (0, "g"),
            (10, "t"),
            (-10, "g"),
            (-1, "t"),
        ]
        for key, expected in keys:
            found = t["chr10"].__getitem__(key)
            msg = "__getitem__[%s] failed. Expected %s, got %s" % (key, expected, found)
            self.assertEqual(found, expected, msg)
        t.close()

    def test_twobitsequence_getitem_slice(self):
        t = twobitreader.TwoBitFile(self.filename)
        slices = [
            (0, 10, "gaaagggaac"),
            (5, 10, "ggaac"),
            (5, None, "ggaactccctgaccccttgtgaaagggaactccctgaccccttgt"),
            (None, None, "gaaagggaactccctgaccccttgtgaaagggaactccctgaccccttgt"),
            (-10, -5, "gaccc"),
            (-5, None, "cttgt"),
        ]

        for start, end, expected in slices:
            found = t["chr10"][start:end]
            self.assertEqual(
                found, expected, "__getitem__ failed on [%s:%s]. Expected %s, got %s" % (start, end, expected, found)
            )
        t.close()

    def test_twobitsequence_slice_starting_past_end(self):
        t = twobitreader.TwoBitFile(self.filename)
        sequence = t["chr10"]
        length = len(sequence)
        self.assertEqual(sequence[length:], "")
        self.assertEqual(sequence[length + 1 :], "")
        self.assertEqual(sequence[length:100], "")
        self.assertEqual(sequence[length + 1 : 100], "")
        self.assertEqual(sequence[length - 1 : 100], "t")
        t.close()

    def test_twobit_reader_skips_invalid_start(self):
        t = twobitreader.TwoBitFile(self.filename)
        output = []
        with self.assertLogs(level="WARNING") as logs:
            twobitreader.twobit_reader(t, input_stream=["chr1 nope 4"], write=output.append)
        self.assertEqual(output, [])
        self.assertTrue(any("Invalid start" in message for message in logs.output))
        t.close()

    def test_pickle(self):
        t = twobitreader.TwoBitFile(self.filename)
        buf = StringIO()
        pickle.dump(t, buf)
        buf.seek(0)
        t2 = pickle.load(buf)
        self.assertListEqual(sorted(t.keys()), sorted(t2.keys()))
        for k in t:
            self.assertEqual(str(t[k]), str(t2[k]))
        t.close()

    def test_context_manager(self):
        with twobitreader.TwoBitFile(self.filename) as t:
            chr10 = str(t["chr10"])
            self.assertEqual(chr10, "gaaagggaactccctgaccccttgtgaaagggaactccctgaccccttgt")

    def test_closed_file(self):
        t = twobitreader.TwoBitFile(self.filename)
        t.close()
        with self.assertRaises(ValueError):
            chr1 = str(t["chr1"])


if __name__ == "__main__":
    unittest.main()
