import time
import signal
import urllib
import urlparse

from sh import ffmpeg

from django.utils import timezone

from main.models import Video


def supports(make, model=None):
    return make.lower() == 'foscam'


class Camera(object):
    def __init__(self, camera):
        self.camera = camera
        self.recording = None

    def build_url(self, type):
        # Set stream type
        # * Note I am not sure why this is necessary or what it does. Another
        # way to capture a stream would be nice.
        # http://192.168.1.89:88/CGIProxy.fcgi?usr=admin&pwd=12345&cmd=setSubStreamFormat&format=1
        # Capture stream
        # http://192.168.1.87:88/cgi-bin/CGIStream.cgi?cmd=GetMJStream\&usr=admin\&pwd=12345
        urlp = urlparse.urlsplit(self.camera.url)
        params = {
            'usr': self.camera.username,
            'pwd': self.camera.password,
        }
        if type == 'setup':
            path = '/CGIProxy.fcgi'
            params.update({'cmd': 'setSubStreamFormat', 'format': '1'})
        elif type == 'stream':
            path = '/cgi-bin/CGIStream.cgi'
            params['cmd'] = 'GetMJStream'
        else:
            raise Exception('Invalid URL type %s' % type)
        return urlparse.SplitResult(urlp.scheme, urlp.netloc,
                                    path, urllib.urlencode(params),
                                    urlp.fragment).geturl()

    def get_video(self):
        return Video.objects.create(camera=self.camera, mime='video/x-msvideo')

    def health(self):
        """Performs a camera health check."""
        pass

    def capture(self):
        """Captures a still image."""
        pass

    def record(self):
        """Records video."""
        v = self.get_video()
        p = ffmpeg('-f', 'mjpeg', '-i', self.build_url('stream'), v.get_path(),
                   _bg=True)
        self.recording = (p, v)

    def stop(self):
        """Stop recording."""
        if self.recording is None:
            return
        p, v = self.recording
        # Ask ffmpeg nicely to stop recording
        p.process.signal(signal.SIGINT)
        timestamp = time.time()
        while p.process.alive:
            # Wait 15 seconds then yell at ffmpeg
            if time.time() - timestamp >= 15:
                p.process.terminate()
            # Wait 30 seconds then fucking stab ffmpeg
            if time.time() - timestamp >= 30:
                p.process.kill()
            # Wait 45 seconds then go nuclear on ffmpeg
            if time.time() - timestamp >= 45:
                raise Exception('Runaway recording process')
            time.sleep(0.01)
        self.recording = None
        v.duration = (timezone.now()-v.created).seconds
        v.save()
        return v
