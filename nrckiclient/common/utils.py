import hashlib
import zlib


def adler32(fname):
        """Compute the adler32 checksum of the file, with seed value 1"""
        BLOCKSIZE = 4096 * 1024
        f = open(fname,'r')
        checksum = 1 #Important - dCache uses seed of 1 not 0
        while True:
            data = f.read(BLOCKSIZE)
            if not data:
                break
            checksum = zlib.adler32(data, checksum)
        f.close()
        # Work around problem with negative checksum
        if checksum < 0:
            checksum += 2**32
        return hex(checksum)[2:10].zfill(8).lower()

def md5sum(self, fname):
        BLOCKSIZE = 4096 * 1024
        f = open(fname,'r')
        checksum = hashlib.md5()
        while True:
            data = f.read(BLOCKSIZE)
            if not data:
                break
            checksum.update(data)
        f.close()
        return checksum.hexdigest().lower()