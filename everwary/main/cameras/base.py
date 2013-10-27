from main.models import Video


MODELS = {
}


class BaseCamera(object):
    mime = 'video/x-msvideo'
    make = None
    models = MODELS.keys()

    def __init__(self, camera):
        self.camera = camera

    def get_video(self):
        return Video.objects.create(camera=self.camera, mime=self.mime)

    def health(self):
        """Performs a camera health check."""
        raise NotImplemented()

    def capture(self):
        """Captures a still image."""
        raise NotImplemented()

    def record(self):
        """Starts recording video."""
        raise NotImplemented()

    def stop(self):
        """Stops recording video."""
        raise NotImplemented()

    def configure(self):
        """Auto-configures the camera."""
        raise NotImplemented()
