import base64
import socket
import logging
import asyncore

from email.parser import Parser

import smtpd
from smtpd import NEWLINE
from smtpd import EMPTYSTRING
from smtpd import SMTPChannel as BaseSMTPChannel
from smtpd import SMTPServer as BaseSMTPServer

from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from main.models import Camera
from main.models import Image
from main.models import Event
from services.async import GEARMAN


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())


class SMTPLogger(object):
    """Simple class that logs via logging module."""
    def write(self, message):
        LOGGER.debug(message)


# Cause smtpd module to log via logging module
smtpd.DEBUGSTREAM = SMTPLogger()


class SMTPAuth(object):
    """Simple class that performs authentication of a camera."""
    def validate(self, username, password):
        if Camera.objects.authenticate(unicode(username), unicode(password)):
            return True


class SMTPChannel(BaseSMTPChannel):
    """smtpd.SMTPChannel subclass that supports AUTH."""
    def __init__(self, *args, **kwargs):
        self.username = None
        self.password = None
        self.authenticator = kwargs.pop('authenticator', None)
        self.authenticated = False
        self.authenticating = False
        BaseSMTPChannel.__init__(self, *args, **kwargs)

    def found_terminator(self):
        line = EMPTYSTRING.join(self.__line)
        print >> smtpd.DEBUGSTREAM, 'Data:', repr(line)
        self.__line = []
        if self.__state == self.COMMAND:
            if not line:
                self.push('500 Error: bad syntax')
                return
            method = None
            i = line.find(' ')
            # If we are in authentication mode, and the line is NOT a valid
            # SMTP verb, then assume it is the password.
            if ((self.authenticating and not
                 callable(getattr(self, 'smtp_' + line.upper(), None)))):
                arg = line.strip()
                command = 'AUTH'
            elif i < 0:
                command = line.upper()
                arg = None
            else:
                command = line[:i].upper()
                arg = line[i + 1:].strip()
            # White list of operations that are allowed prior to AUTH.
            if not command in ['AUTH', 'EHLO', 'HELO', 'NOOP', 'RSET', 'QUIT']:
                if self.authenticator and not self.authenticated:
                    self.push('530 Authentication required')
                    return
            method = getattr(self, 'smtp_' + command, None)
            if not method:
                self.push('502 Error: command "%s" not implemented' % command)
                return
            method(arg)
            return
        else:
            if self.__state != self.DATA:
                self.push('451 Internal confusion')
                return
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 821, Section 4.5.2.
            data = []
            for text in line.split('\r\n'):
                if text and text[0] == '.':
                    data.append(text[1:])
                else:
                    data.append(text)
            self.__data = NEWLINE.join(data)
            status = self.__server.process_message(self.username,
                                                   self.__peer,
                                                   self.__mailfrom,
                                                   self.__rcpttos,
                                                   self.__data)
            self.__rcpttos = []
            self.__mailfrom = None
            self.__state = self.COMMAND
            self.set_terminator('\r\n')
            if not status:
                self.push('250 Ok')
            else:
                self.push(status)

    def smtp_EHLO(self, arg):
        if not arg:
            self.push('501 Syntax: HELO hostname')
            return
        if self.__greeting:
            self.push('503 Duplicate HELO/EHLO')
        else:
            self.push('250-%s Hello %s' % (self.__fqdn, arg))
            self.push('250-AUTH LOGIN')
            self.push('250 EHLO')

    def smtp_AUTH(self, arg):
        if 'LOGIN' in arg:
            self.authenticating = True
            split_args = arg.split(' ')

            # Some implmentations of 'LOGIN' seem to provide the username
            # along with the 'LOGIN' stanza, hence both situations are
            # handled.
            if len(split_args) == 2:
                self.username = base64.b64decode(arg.split(' ')[1])
                self.push('334 ' + base64.b64encode('Username'))
            else:
                self.push('334 ' + base64.b64encode('Username'))

        elif not self.username:
            self.username = base64.b64decode(arg)
            self.push('334 ' + base64.b64encode('Password'))
        else:
            self.authenticating = False
            self.password = base64.b64decode(arg)
            if self.authenticator and self.authenticator.validate(self.username, self.password):
                self.authenticated = True
                self.push('235 Authentication successful.')
            else:
                self.push('454 Temporary authentication failure.')


class SMTPServer(BaseSMTPServer):
    """smtpd.SMTPServer subclass that supports AUTH and processes images
    from message bodies."""
    def __init__(self, address_or_socket, authenticator=SMTPAuth()):
        if callable(getattr(address_or_socket, 'listen', None)):
            asyncore.dispatcher.__init__(self)
            address_or_socket.setblocking(0)
            self.set_socket(address_or_socket)
        else:
            BaseSMTPServer.__init__(self, address_or_socket, None)
        self.authenticator = authenticator
        self.parser = Parser()

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            print >> smtpd.DEBUGSTREAM, 'Incoming connection from %s' % repr(addr)
            SMTPChannel(self, conn, addr, authenticator=self.authenticator)

    def process_message(self, username, peer, mailfrom, rcpttos, data):
        """Parses the message body, then saves the first encountered image.
        Other images are ignored."""
        m = self.parser.parsestr(data)
        for p in m.walk():
            if p.get_content_maintype() == 'multipart':
                continue
            mime = p.get_content_type()
            if not mime.startswith('image/'):
                continue
            camera = Camera.objects.get(auth=username)
            image = Image.objects.create(camera=camera, mime=mime)
            image.write(p.get_payload(decode=True))
            m = camera.events.create(event=Event.CAMERA_EVENT_MOTION,
                                     image=image)
            GEARMAN.submit_job('motion', data={'args': (m, ), 'kwargs':
                               {}}, background=True, wait_until_complete=False)
            break

    def start(self):
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            return

    def stop(self):
        self.close()


class Command(BaseCommand):
    help = 'Runs SMTP daemon that accepts still images from cameras when motion is detected.'

    option_list = BaseCommand.option_list + (
        make_option('--port',
                    type='int',
                    help='TCP port to bind'),
        make_option('--addr',
                    type='string',
                    help='IP address to bind'),
        make_option('--fd',
                    type='int',
                    help='File descriptor of open listening socket'),
    )

    def handle(self, *args, **kwargs):
        if kwargs.get('fd'):
            sock = socket.fromfd(kwargs['fd'], socket.AF_INET, socket.SOCK_STREAM)
        elif kwargs.get('addr') and kwargs.get('port'):
            sock = (kwargs["addr"], kwargs['port'])
        else:
            raise CommandError('Must specify addr/port or fd for listening')

        server = SMTPServer(sock)
        server.start()
