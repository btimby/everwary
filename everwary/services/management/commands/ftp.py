import os
import mimetypes

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from pyftpdlib.handlers import FTPHandler as BaseFTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.filesystems import AbstractedFS
from pyftpdlib.authorizers import AuthenticationFailed

from main.models import Camera
from main.models import Image
from main.models import Event

from services.async import GEARMAN


# Allow:
#  * Directory creation (m)
#  * Directory navigation (e)
#  * Uploading (w)
FTP_PERMISSIONS = 'mew'


class FTPAuth(object):
    """Simple class to perform authentication and authorization for FTP
    clients."""
    def has_user(self, username):
        return Camera.objects.filter(id=username).exists()

    def has_perm(self, username, perm, path=None):
        return perm in FTP_PERMISSIONS

    def get_perms(self, username):
        return FTP_PERMISSIONS

    def validate_authentication(self, username, password, handler):
        if Camera.objects.authenticate(username, password):
            return True
        raise AuthenticationFailed()

    def get_home_dir(self, username):
        return os.path.join(settings.ALARM_IMAGE_DIR, username)

    def get_msg_login(selfself, username):
        return 'Login successful.'

    def get_msg_quit(self, username):
        return 'Goodbye.'

    def impersonate_user(self, username, password):
        pass

    def terminate_impersonation(self, username):
        pass


class FTPImageStorageFS(AbstractedFS):
    """pyftpdlib.filesystems.AbstractedFS subclass that allows images to be
    uploaded."""
    def chdir(self, path):
        # Fake it, there are not any directories here.
        pass

    def open(self, filename, mode):
        mime, enc = mimetypes.guess_type(filename)
        c = Camera.objects.get(auth=self.cmd_channel.username)
        i = Image.objects.create(camera=c, mime=mime)
        return i.open(mode)


class FTPHandler(BaseFTPHandler):
    """pyftpdlib.handlers.FTPHandler subclass that fires off motion events
    when an image is uploaded."""
    def on_file_received(self, filename):
        fn = os.path.basename(filename)
        fn = os.path.splitext(fn)[0]
        try:
            image = Image.objects.get(id=fn)
        except Image.DoesNotExist:
            return
        m = image.camera.events.create(event=Event.CAMERA_EVENT_MOTION, image=image)
        GEARMAN.submit_job('motion', data={'args': (m, ), 'kwargs':
                           {}}, background=True, wait_until_complete=False)


class Command(BaseCommand):
    help = 'Runs FTP daemon that accepts still images from cameras when motion is detected.'

    option_list = BaseCommand.option_list + (
        make_option('--port',
                    type='int',
                    default=21,
                    help='TCP port to bind'),
        make_option('--addr',
                    type='string',
                    default='0.0.0.0',
                    help='IP address to bind'),
    )

    def handle(self, *args, **kwargs):
        handler = FTPHandler
        handler.authorizer = FTPAuth()
        handler.abstracted_fs = FTPImageStorageFS
        handler.banner = 'Camden FTP server'

        server = FTPServer((kwargs["addr"], kwargs['port']), handler)
        server.serve_forever()
