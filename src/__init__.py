"""
twobitreader

Licensed under Perl Artistic License 2.0
No warranty is provided, express or implied
"""
from array import array
from bisect import bisect_right
from errno import ENOENT, EACCES
from os import R_OK, access
try:
    from os import strerror
except ImportError:
    strerror = lambda: 'strerror not supported'
from os.path import exists
from itertools import izip

def true_long_type():
    """
    OS X uses an 8-byte long, so make sure L (long) is the right size
    and switch to I (int) if needed
    """
    for type_ in ['L', 'I']:
        test_array = array(type_, [0])
        long_size = test_array.itemsize
        if long_size == 4: return type_
    raise ImportError("Couldn't determine a valid 4-byte long type to use \
as equivalent to LONG")
LONG = true_long_type()

def byte_to_bases(x):
    """convert one byte to the four bases it encodes"""
    c = (x >> 4) & 0xf
    f = x & 0xf
    cc = (c >> 2) & 0x3
    cf = c & 0x3
    fc = (f >> 2) & 0x3
    ff = f & 0x3
    return map(bits_to_base, (cc, cf, fc, ff))

def bits_to_base(x):
    """convert integer representation of two bits to correct base"""
    if x is 0: return 'T'
    if x is 1: return 'C'
    if x is 2: return 'A'
    if x is 3: return 'G'

def base_to_bin(x):
    """
    provided for user convenience
    convert a nucleotide to its bit representation 
    """
    if x == 'T': return '00'
    if x == 'C': return '01'
    if x == 'A': return '10'
    if x == 'G': return '11'

def create_byte_table():
    """create BYTE_TABLE"""
    d = {}
    for x in xrange(2**8):
        d[x] = byte_to_bases(x)
    return d

def split16(x):
    """
    split a 16-bit number into integer representation
    of its course and fine parts in binary representation
    """
    c = (x >> 8) & 0xff
    f = x & 0xff
    return c, f

def create_twobyte_table():
    """create TWOBYTE_TABLE"""
    d = {}
    for x in xrange(2**16):
        c, f = split16(x)
        d[x] = byte_to_bases(c) + byte_to_bases(f)
    return d

BYTE_TABLE = create_byte_table()
TWOBYTE_TABLE = create_twobyte_table()

def longs_to_char_array(longs, first_base_offset, last_base_offset, array_size):
    """
    takes in a iterable of longs and converts them to bases in a char array
    returns a ctypes string buffer
    """
    longs_len = len(longs)
    # dna = ctypes.create_string_buffer(array_size)
    dna = array('c', 'N' * longs_len)
    # translate from 32-bit blocks to bytes
    # this method ensures correct endianess (byteswap as neeed)
    bytes = array('B')
    bytes.fromstring(longs.tostring())
    # first block
    first_block = ''.join([''.join(BYTE_TABLE[bytes[x]]) for x in range(4)])
    i = 16 - first_base_offset
    if array_size < i: i = array_size
    dna[0:i] = array('c', first_block[first_base_offset:first_base_offset + i])
    if longs_len == 1: return dna
    # middle blocks (implicitly skipped if they don't exist)
    for byte in bytes[4:-4]:
        dna[i:i + 4] = array('c', BYTE_TABLE[byte])
        i += 4
    # last block
    last_block = array('c', ''.join([''.join(BYTE_TABLE[bytes[x]]) for x in range(-4,0)]))
    dna[i:i + last_base_offset] = last_block[0:last_base_offset]
    return dna

class TwoBitFile(dict):
    """
python-level reader for .2bit files (i.e., from UCSC genome browser)
(note: no writing support)

TwoBitFile inherits from dict
You may access sequences by name, e.g.
>>> genome = TwoBitFile('hg18.2bit')
>>> chr20 = genome['chr20']

Sequences are returned as TwoBitSequence objects
You may access intervals by slicing or using str() to dump the entire entry
e.g.
>>> chr20[100100:100200]
'ttttcctctaagataatttttgccttaaatactattttgttcaatactaagaagtaagataacttccttttgttggtat
ttgcatgttaagtttttttcc'
>>> whole_chr20 = str(chr20)

Fair warning: dumping the entire chromosome requires a lot of memory

See TwoBitSequence for more info
    """
    
    def __init__(self, foo):
        super(dict, self).__init__(self)
        if not exists(foo):
            raise IOError(ENOENT, strerror(ENOENT), foo)
        if not access(foo, R_OK):
            raise IOError(EACCES, strerror(EACCES), foo)
        self._filename = foo
        self._file_handle = open(foo, 'rb')
        self._load_header()
        self._load_index()
        for name, offset in self._offset_dict.iteritems():
            self[name] = TwoBitSequence(self._file_handle, offset,
                                        self._byteswapped)
        return        
        
    def _load_header(self):
        file_handle = self._file_handle
        header = array(LONG)
        header.fromfile(file_handle, 4)
        # check signature -- must be 0x1A412743
        # if not, swap bytes
        byteswapped = False
        (signature, version, sequence_count, reserved) = header
        if not signature == 0x1A412743:
            byteswapped = True
            header.byteswap()
            (signature, version, sequence_count, reserved) = header
            if not signature == 0x1A412743:
                raise TwoBitFileError('Signature in header should be 0x1A412743.')
        if not version == 0: 
            raise TwoBitFileError('File version in header should be 0.')
        if not reserved == 0: 
            raise TwoBitFileError('Reserved field in header should be 0.')
        self._byteswapped = byteswapped
        self._sequence_count = sequence_count
        
    def _load_index(self):
        file_handle = self._file_handle
        byteswapped = self._byteswapped
        remaining = self._sequence_count
        sequence_offsets = []
        file_handle.seek(16)
        while True:
            if remaining == 0: break
            name_size = array('B')
            name_size.fromfile(file_handle, 1)
            if byteswapped: name_size.byteswap()
            name = array('c')
            if byteswapped: name.byteswap()
            name.fromfile(file_handle, name_size[0])
            offset = array(LONG)
            offset.fromfile(file_handle, 1)
            if byteswapped: offset.byteswap()
            sequence_offsets.append((name.tostring(), offset[0]))
            remaining -= 1
        self._sequence_offsets = sequence_offsets
        self._offset_dict = dict(sequence_offsets)

    def sequence_sizes(self):
        """returns a dictionary with the sizes of each sequence"""
        d = {}
        file_handle = self._file_handle
        byteswapped = self._byteswapped
        for name, offset in self._offset_dict.iteritems():
            file_handle.seek(offset)
            dna_size = array(LONG)
            dna_size.fromfile(file_handle, 1)
            if byteswapped: dna_size.byteswap()
            d[name] = dna_size[0]
        return d

class TwoBitSequence(object):
    """
A TwoBitSequence object refers to an entry in a TwoBitFile

You may access intervals by slicing or using str() to dump the entire entry
e.g.
>>> genome = TwoBitFile('hg18.2bit')
>>> chr20 = genome['chr20']
>>> chr20[100100:100200] # slicing returns a string
'ttttcctctaagataatttttgccttaaatactattttgttcaatactaagaagtaagataacttccttttgttggtat
ttgcatgttaagtttttttcc'
>>> whole_chr20 = str(chr20) # get whole chr as string

Fair warning: dumping the entire chromosome requires a lot of memory
 
Note that we follow python/UCSC conventions:
Coordinates are 0-based, end-open
(Note: The UCSC web-based genome browser uses 1-based closed coordinates)
If you attempt to access a slice past the end of the sequence,
it will be truncated at the end.

Your computer probably doesn't have enough memory to load a whole genome
but if you want to string-ize your TwoBitFile, here's a recipe:

x = TwoBitFile('my.2bit')
d = x.dict()
for k,v in d.iteritems(): d[k] = str(v)
    """
    def __init__(self, file_handle, offset, byteswapped=False):
        self._file_handle = file_handle
        self._original_offset = offset
        self._byteswapped = byteswapped
        file_handle.seek(offset)
        header = array(LONG)
        header.fromfile(file_handle, 2)
        if byteswapped: header.byteswap()
        dna_size, n_block_count = header
        self._dna_size = dna_size
        self._packed_dna_size = (dna_size + 15) / 16 # this is 32-bit fragments
        n_block_starts = array(LONG)
        n_block_sizes = array(LONG)
        n_block_starts.fromfile(file_handle, n_block_count)
        if byteswapped: n_block_starts.byteswap()
        n_block_sizes.fromfile(file_handle, n_block_count)
        if byteswapped: n_block_sizes.byteswap()
        self._n_block_starts = n_block_starts
        self._n_block_sizes= n_block_sizes
        mask_rawc = array(LONG)
        mask_rawc.fromfile(file_handle, 1)
        if byteswapped: mask_rawc.byteswap()
        mask_block_count = mask_rawc[0]
        mask_block_starts = array(LONG)
        mask_block_starts.fromfile(file_handle, mask_block_count)
        if byteswapped: mask_block_starts.byteswap()
        mask_block_sizes = array(LONG)
        mask_block_sizes.fromfile(file_handle, mask_block_count)
        if byteswapped: mask_block_sizes.byteswap()
        self._mask_block_starts = mask_block_starts
        self._mask_block_sizes = mask_block_sizes
        file_handle.read(4)
        self._offset = file_handle.tell()

    def __len__(self):
        return self._dna_size

    def __getslice__(self, min, max=None):
        return self.get_slice(min, max)

    def get_slice(self, min, max=None):
        """
        get_slice returns only a sub-sequence
        """
        # handle negative coordinates
        dna_size = self._dna_size
        if max < 0:
            if max < -dna_size: raise IndexError('index out of range')
            max = dna_size + 1 + max
        if min < 0:
            if max < -dna_size: raise IndexError('index out of range')
            min = dna_size + 1 + min
        # make sure there's a proper range
        if min > max and max is not None: return ''
        if max == 0: return ''
        # load all the data
        if max > dna_size: max = dna_size
        file_handle = self._file_handle
        byteswapped = self._byteswapped
        n_block_starts = self._n_block_starts
        n_block_sizes = self._n_block_sizes
        mask_block_starts = self._mask_block_starts
        mask_block_sizes = self._mask_block_sizes
        offset = self._offset
        packed_dna_size = self._packed_dna_size

        # region_size is how many bases the region is       
        if max is None: region_size = dna_size - min
        else: region_size = max - min
        
        # start_block, end_block are the first/last 32-bit blocks we need
        # note: end_block is not read
        # blocks start at 0
        start_block = min / 16
        end_block = (max - 1) / 16
        # don't read past seq end
        if end_block >= packed_dna_size: end_block = packed_dna_size - 1
        # +1 we still need to read block
        blocks_to_read = end_block - start_block + 1
        
        # jump directly to desired file location
        local_offset = offset + start_block * 4
        file_handle.seek(local_offset)
        
        # note we won't actually read the last base
        # this is a python slice first_base_offset:16*blocks+last_base_offset
        first_base_offset = min % 16
        last_base_offset = max % 16
        
        fourbyte_dna = array(LONG)
        fourbyte_dna.fromfile(file_handle, blocks_to_read)
        if byteswapped: fourbyte_dna.byteswap()
        string_as_array = longs_to_char_array(fourbyte_dna, first_base_offset,
                                              last_base_offset, region_size)
        for start, size in izip(n_block_starts, n_block_sizes):
            end = start + size
            if end <= min: continue
            if start > max: break
            if start < min: start = min
            if end > max: end = max 
            start -= min
            end -= min
            string_as_array[start:end] = 'N'*(end-start)
        lower = str.lower
        first_masked_region = max(0,
                                  bisect_right(mask_block_starts, min) - 1)
        last_masked_region = min(len(masked_block_starts),
                                 1 + bisect_right(mask_block_starts, max,
                                                  lo=first_masked_region))
        for start, size in izip(mask_block_starts[first_masked_region:last_masked_region],
                                mask_block_sizes[first_masked_region:last_masked_region]):
            end = start + size
            if end <= min: continue
            if start > max: break
            if start < min: start = min
            if end > max: end = max 
            start -= min
            end -= min
            string_as_array[start:end] = array('c', lower(string_as_array[start:end].tostring()))
        return string_as_array.tostring()

    def __str__(self):
        """
        returns the entire chromosome
        """
        return self.__getslice__(0, None)
    
class TwoBitFileError(StandardError):
    """
    Base exception for TwoBit module
    """
    def __init__(self, msg):
        errtext = 'Invalid 2-bit file. ' + msg
        return super(TwoBitFileError, self).__init__(errtext)

def print_specification():
    """
    Prints the twoBit file format specification I got from the Internet.
    This is only here for reference
    """
    return """
From http://www.its.caltech.edu/~alok/reviews/blatSpecs.html

.2bit files

A .2bit file can store multiple DNA sequence (up to 4 gig total) in a compact \
randomly accessible format. The two bit files contain masking information as \
well as the DNA itself. The file begins with a 16 byte header containing the \
following fields:

signature - the number 0x1A412743 in the architecture of the machine that \
created the file.
version - zero for now. Readers should abort if they see a version number \
higher than 0.
sequenceCount - the number of sequences in the file
reserved - always zero for now.
All fields are 32 bits unless noted. If the signature value is not as given, \
the reader program should byte swap the signature and see if the swapped \
version matches. If so all multiple-byte entities in the file will need to be \
byte-swapped. This enables these binary files to be used unchanged on \
different architectures.

The header is followed by a file index. There is one entry in the index for \
each sequence. Each index entry contains three fields:

nameSize - a byte containing the length of the name field
name - this contains the sequence name itself, and is variable length \
depending on nameSize.
offset - 32 bit offset of the sequence data relative to the start of the file

The index is followed by the sequence records. These contain 9 fields:

dnaSize - number of bases of DNA in the sequence.
nBlockCount - the number of blocks of N's in the file (representing unknown \
sequence).
nBlockStarts - a starting position for each block of N's
nBlockSizes - the size of each block of N's
maskBlockCount - the number of masked (lower case) blocks
maskBlockStarts - starting position for each masked block
maskBlockSizes - the size of each masked block
packedDna - the dna packed to two bits per base as so: 00 - T, 01 - C, 10 - A, \
11 - G. The first base is in the most significant 2 bits byte, and the last \
base in the least significant 2 bits, so that the sequence TCAG would be \
represented as 00011011. The packedDna field will be padded with 0 bits as \

necessary so that it takes an even multiple of 32 bit in the file, as this \
improves i/o performance on some machines.
.nib files
"""