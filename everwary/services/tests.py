import ftplib
import smtplib
import asyncore
import threading

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.test import TransactionTestCase

from main.models import Image
from main.models import Camera

from services.management.commands.ftp import FTPAuth
from services.management.commands.ftp import FTPServer
from services.management.commands.ftp import FTPHandler
from services.management.commands.ftp import FTPImageStorageFS
from services.management.commands.smtp import SMTPServer


TEST_USERNAME = '8f55a2ea-4b9d-4133-b89b-d5874d652544'
TEST_PASSWORD = '67b2e671-4673-4b75-b8d2-b07fef05e8ea'
TEST_MULTIPART = '''Subject: Example Email
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="MixedBoundaryString"

--MixedBoundaryString
Content-Type: multipart/related; boundary="RelatedBoundaryString"

--RelatedBoundaryString
Content-Type: multipart/alternative; boundary="AlternativeBoundaryString"

--AlternativeBoundaryString
Content-Type: text/plain;charset="utf-8"
Content-Transfer-Encoding: quoted-printable

This is the plain text part of the email.

--RelatedBoundaryString
Content-Type: image/png;name="logo.png"
Content-Transfer-Encoding: base64
Content-Disposition: inline;filename="logo.png"
Content-ID: <logo.png@qcode.co.uk>

amtsb2hiaXVvbHJueXZzNXQ2XHVmdGd5d2VoYmFmaGpremxidTh2b2hydHVqd255aHVpbnRyZnhu
dWkgb2l1b3NydGhpdXRvZ2hqdWlyb2h5dWd0aXJlaHN1aWhndXNpaHhidnVqZmtkeG5qaG5iZ3Vy
...
...
a25qbW9nNXRwbF0nemVycHpvemlnc3k5aDZqcm9wdHo7amlodDhpOTA4N3U5Nnkwb2tqMm9sd3An
LGZ2cDBbZWRzcm85eWo1Zmtsc2xrZ3g=

--MixedBoundaryString--
'''
TEST_IMAGE = '''amtsb2hiaXVvbHJueXZzNXQ2XHVmdGd5d2VoYmFmaGpremxidTh2b2hydHVqd255aHVpbnRyZnhu
dWkgb2l1b3NydGhpdXRvZ2hqdWlyb2h5dWd0aXJlaHN1aWhndXNpaHhidnVqZmtkeG5qaG5iZ3Vy
...
...
a25qbW9nNXRwbF0nemVycHpvemlnc3k5aDZqcm9wdHo7amlodDhpOTA4N3U5Nnkwb2tqMm9sd3An
LGZ2cDBbZWRzcm85eWo1Zmtsc2xrZ3g='''


class ThreadedSMTPServer(SMTPServer):
    def __init__(self, *args, **kwargs):
        SMTPServer.__init__(self, *args, **kwargs)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=asyncore.loop,
                                       kwargs={'timeout': 0.1,
                                               'use_poll': True})
        self.thread.start()

    def stop(self):
        SMTPServer.stop(self)
        self.thread.join()


class SMTPTest(TransactionTestCase):
    fixtures = ('unittest', )

    def setUp(self):
        self.server = ThreadedSMTPServer(('127.0.0.1', 0))
        self.server.start()
        self.client = smtplib.SMTP('127.0.0.1', self.server.socket.getsockname()[1])

    def tearDown(self):
        try:
            self.client.quit()
        except smtplib.SMTPServerDisconnected:
            # Ignore this, we are already disconnnected.
            pass
        self.server.stop()

    def test_auth(self):
        """Ensure a valid username and password logs in properly."""
        self.client.login(TEST_USERNAME, TEST_PASSWORD)

    def test_authfail(self):
        """Ensure a valid username or password logs in properly."""
        self.assertRaises(smtplib.SMTPAuthenticationError, self.client.login,
                          TEST_USERNAME, '')

    def test_disabled(self):
        Camera.objects.all().update(disabled=True)
        self.assertRaises(smtplib.SMTPAuthenticationError, self.client.login,
                          TEST_USERNAME, TEST_PASSWORD)

    def test_send(self):
        """Ensure an image attachment is properly saved."""
        try:
            self.client.login(TEST_USERNAME, TEST_PASSWORD)
        except smtplib.SMTPAuthenticationError:
            self.fail('Could not send email due to authentication failure')
        self.client.sendmail('unittest@example.org', ['unittest@example.org'],
                             '')

    def test_sendfail(self):
        """Ensure authentication is required to send."""
        self.assertRaises(smtplib.SMTPSenderRefused, self.client.sendmail,
                          'unittest@example.org', ['unittest@example.org'],
                          '')

    def test_attachment(self):
        """Ensure an image attachment is properly saved."""
        try:
            self.client.login(TEST_USERNAME, TEST_PASSWORD)
        except smtplib.SMTPAuthenticationError:
            self.fail('Could not send email due to authentication failure')
        self.client.sendmail('unittest@example.org', ['unittest@example.org'],
                             TEST_MULTIPART)
        self.assertGreater(Image.objects.all().count(), 0)


class ThreadedFTPServer(threading.Thread):
    "Threaded FTP server for running unit tests."
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.server.handler._auth_failed_timeout = 0.1
        self.host, self.port = self.server.socket.getsockname()[:2]
        self.daemon = True
        self.running = True
        self.start()

    def run(self):
        while self.running:
            self.server.serve_forever(timeout=0.001, blocking=False)
        self.server.close_all()

    def stop(self):
        self.running = False
        self.join()


class FTPTest(TransactionTestCase):
    fixtures = ('unittest', )

    def setUp(self):
        handler = FTPHandler
        handler.authorizer = FTPAuth()
        handler.abstracted_fs = FTPImageStorageFS
        handler.banner = 'Camden FTP server'
        self.server = ThreadedFTPServer(FTPServer(('127.0.0.1', 0), handler))
        self.client = ftplib.FTP()
        self.client.connect('127.0.0.1', port=self.server.port)

    def tearDown(self):
        try:
            self.client.quit()
        except EOFError:
            pass
        self.server.stop()
        self.server.join()

    def test_auth(self):
        self.client.login(TEST_USERNAME, TEST_PASSWORD)

    def test_authfail(self):
        self.assertRaises(ftplib.error_perm, self.client.login, TEST_USERNAME,
                          '')

    def test_disabled(self):
        Camera.objects.all().update(disabled=True)
        self.assertRaises(ftplib.error_perm, self.client.login, TEST_USERNAME,
                          TEST_PASSWORD)

    def test_upload(self):
        try:
            self.client.login(TEST_USERNAME, TEST_PASSWORD)
        except ftplib.error_perm:
            self.fail('Could not upload due to authentication failure')
        self.client.storbinary('STOR example.jpg', StringIO(TEST_IMAGE))
        self.assertGreater(Image.objects.all().count(), 0)
