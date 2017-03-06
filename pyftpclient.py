"""Python FTP multithread downloader.

This is Fork from https://github.com/keepitsimple/pyFTPclient

This version of pyFTPclient will download all files containig in remote directory.
"""

__author__ = 'Roman Podlinov, Nauris Dorbe'

import argparse
import ftplib
import logging
import os
import socket
import threading
import time

parser = argparse.ArgumentParser(description='Python FTP multithread downloader.')

parser.add_argument('--host', type=str, default='', help='FTP Host name/IP address.')
parser.add_argument('--usr', type=str, default='', help='FTP server username.')
parser.add_argument('--psw', type=str, default='', help='FTP server password.')

parser.add_argument('--local_dir', type=str, default='',
                    help='Local directory where to save downloaded files. Will be created.')
parser.add_argument('--remote_dir', type=str, default='',
                    help='If files is in remote directory then passing this argument will switch directories.')

args = parser.parse_args()


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """Print iterations progress.

    Call in a loop to create terminal progress bar.
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def setInterval(interval, times=-1):
    """Decorator, with fixed interval and times parameter."""
    def outer_wrap(function):
        # This will be the function to be
        # called
        def wrap(*args, **kwargs):
            stop = threading.Event()

            # This is another function to be executed
            # in a different thread to simulate setInterval
            def inner_wrap():
                i = 0
                while i != times and not stop.isSet():
                    stop.wait(interval)
                    function(*args, **kwargs)
                    i += 1

            t = threading.Timer(0, inner_wrap)
            t.daemon = True
            t.start()
            return stop
        return wrap
    return outer_wrap


class PyFTPclient(object):
    """FTP Client."""

    def __init__(self, host, port, login, passwd, monitor_interval=30):
        """Initializee class variables."""
        self.host = host
        self.port = port
        self.login = login
        self.passwd = passwd
        self.monitor_interval = monitor_interval
        self.ptr = None
        self.max_attempts = 15
        self.waiting = True

    def DownloadFile(self, dst_filename):
        """Download File."""
        res = ''
        with open('models/' + dst_filename, 'w+b') as f:
            self.ptr = f.tell()

            @setInterval(self.monitor_interval)
            def monitor():
                if not self.waiting:
                    i = f.tell()
                    if self.ptr < i:
                        logging.debug("%d  -  %0.1f Kb/s" % (i, (i - self.ptr) / (1024 * self.monitor_interval)))
                        self.ptr = i
                    else:
                        ftp.close()

            def connect():
                ftp.connect(self.host, self.port)
                ftp.login(self.login, self.passwd)
                ftp.cwd("models")
                # optimize socket params for download task
                ftp.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                ftp.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 75)
                ftp.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)

            ftp = ftplib.FTP()

            connect()
            ftp.voidcmd('TYPE I')
            dst_filesize = ftp.size(dst_filename)

            mon = monitor()
            while dst_filesize > f.tell():
                try:
                    connect()
                    self.waiting = False
                    # retrieve file from position where we were disconnected
                    res = ftp.retrbinary('RETR %s' % dst_filename, f.write) if f.tell() == 0 else \
                              ftp.retrbinary('RETR %s' % dst_filename, f.write, rest=f.tell())

                except Exception:
                    self.max_attempts -= 1
                    if self.max_attempts == 0:
                        mon.set()
                        logging.exception('')
                        raise
                    self.waiting = True
                    logging.info('waiting 30 sec...')
                    time.sleep(30)
                    logging.info('reconnect')

            mon.set()  # stop monitor
            self.waiting = True
            ftp.close()

            if not res.startswith('226 Transfer complete'):
                logging.error('Downloaded file {0} is not full.'.format(dst_filename))
                # os.remove(local_filename)
                return None

            return 1


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)

    if args.local_dir != '':
        logging.info('Creating {} directory'.format(args.local_dir))
        if not os.path.exists(args.local_dir):
            os.makedirs(args.local_dir)

    logging.info('Connecting to FTP server')
    ftp = ftplib.FTP(args.host)
    ftp.login(args.usr, args.psw)
    ftp.cwd(args.remote_dir)
    filenames = ftp.nlst()
    file_count = len(filenames)
    ftp.close()

    logging.info('Downloading {} files. Grab a tea, this may take awhile.'.format(file_count))
    obj = PyFTPclient(args.host, 21, args.usr, args.psw)

    i = 0
    printProgressBar(i, file_count, prefix='Progress:', suffix='Full downloaded files', length=50)
    for fname in filenames:
        obj.DownloadFile(fname)
        i += 1
        printProgressBar(i, file_count, prefix='Progress:', suffix='Full downloaded files', length=50)
