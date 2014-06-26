import unittest
from pysftpserver import *
import os
import os.path
import struct
import random


def _sftpstring(s):
    return struct.pack('>I', len(s)) + s

def _sftpint(n):
    return struct.pack('>I', n)

def _sftpint64(n):
    return struct.pack('>Q', n)

def _sftpcmd(cmd, *args):
    msg = struct.pack('>BI', cmd, random.randrange(1, 0xffffffff) )
    for arg in args:
        msg += arg
    return _sftpint(len(msg)) + msg

def _sftphandle(blob):
    slen, = struct.unpack('>I', blob[9:13])
    return blob[13:13+slen]

basedir = os.getcwd()

class ServerTest(unittest.TestCase):

    def setUp(self):
        global basedir
        os.chdir(basedir)
        self.home = 'testhome'
        if not os.path.isdir(self.home):        
            os.mkdir(self.home)
        self.server = SFTPServer(self.home, raise_on_error=True)
        if os.path.exists('foo'):
            os.rmdir('foo')
    
    def test_mkdir(self):
        self.server.input_queue = _sftpcmd(SSH2_FXP_MKDIR, _sftpstring('foo'), _sftpint(0))
        self.server.process()
        self.server.input_queue = _sftpcmd(SSH2_FXP_MKDIR, _sftpstring('foo'), _sftpint(0))
        self.assertRaises(SFTPException, self.server.process)

    def test_mkdir_notfound(self):
        self.server.input_queue = _sftpcmd(SSH2_FXP_MKDIR, _sftpstring('bad/ugly'), _sftpint(0))
        self.assertRaises(SFTPNotFound, self.server.process)

    def test_rmdir_notfound(self):
        self.server.input_queue = _sftpcmd(SSH2_FXP_RMDIR, _sftpstring('bad/ugly'), _sftpint(0))
        self.assertRaises(SFTPNotFound, self.server.process)

    def test_copy_services(self):
        self.server.input_queue = _sftpcmd(SSH2_FXP_OPEN, _sftpstring('services'), _sftpint(SSH2_FXF_CREAT), _sftpint(0))
        self.server.process()
        handle = _sftphandle(self.server.output_queue)
        # reset output queue
        self.server.output_queue = ''
        etc_services = open('/etc/services').read()
        self.server.input_queue = _sftpcmd(SSH2_FXP_WRITE, _sftpstring(handle), _sftpint64(0), _sftpstring(etc_services))
        self.server.process()
        # reset output queue
        self.server.output_queue = ''
        self.server.input_queue = _sftpcmd(SSH2_FXP_CLOSE, _sftpstring(handle))
        self.server.process()
        self.assertEqual(etc_services, open('services').read())


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)

if __name__ == "__main__":
    unittest.main()
