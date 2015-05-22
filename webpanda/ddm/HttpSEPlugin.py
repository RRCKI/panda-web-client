import os
from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class HttpSEPlugin():
    def __init__(self, params=None):
        pass

    def get(self, url, dest):
        _logger.debug('HTTP: Try to get file from %s to %s' % (url, dest))
        try:
            import urllib2

            file_name = url.split('/')[-1]
            u = urllib2.urlopen(url)
            f = open(os.path.join(dest, file_name), 'wb')
            meta = u.info()
            file_size = int(meta.getheaders("Content-Length")[0])
            print "Downloading: %s Bytes: %s" % (file_name, file_size)

            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break

                file_size_dl += len(buffer)
                f.write(buffer)
                status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                status = status + chr(8)*(len(status)+1)
                print status,

            f.close()
        except:
            _logger.error('Unable to download:%s to %s' % (url, dest))


    def put(self, src, dest):
        _logger.debug('HTTP: Try to put file from %s to %s' % (src, dest))
        pass