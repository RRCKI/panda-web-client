import os
import ftplib
from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class FtpSEPlugin():
    def __init__(self, params=None):
        self.anonymode = True
        self.login = 'anonymous'
        self.password = ''
        if 'login' in params.keys() and 'password' in params.keys():
            self.anonymode = False
            self.login = params['login']
            self.password = params['password']

    def get(self, url, dest):
        _logger.debug('FTP: Try to get file from %s to %s' % (url, dest))
        try:
            url = url.split('ftp://')[-1]
            host = url.split('/')[0]
            path = '/'.join(url.split('/')[1:-1])
            fname = url.split('/')[-1]
            destfile = os.path.join(dest, fname)

            ftp = self.connect(host, self.login, self.password)
            ftp.cwd(path)

            f = open(destfile, "wb")
            ftp.retrbinary("RETR " + fname, f.write, 8*1024)
            f.close()

        except:
            _logger.error('Unable to download:%s to %s' % (url, dest))


    def put(self, src, dest):
        _logger.debug('FTP: Try to put file from %s to %s' % (src, dest))
        try:
            dest = dest.split('ftp://')[-1]
            host = dest.split('/')[0]
            path = '/'.join(dest.split('/')[1:])
            fname = src.split('/')[-1]

            ftp = self.connect(host, self.login, self.password)
            ftp.cwd(path)

            f = open(src, "wb")
            ftp.storbinary("STOR " + fname, f)
            f.close()

        except:
            _logger.error('Unable to download:%s to %s' % (src, dest))

    def connect(self, host, login, password):
        ftp = ftplib.FTP(host)
        if self.anonymode:
            ftp.login()
        else:
            ftp.login(login, password)
        return ftp