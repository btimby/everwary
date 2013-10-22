import os
import glob
import importlib


BACKEND_PATTERN = '*.py'


def iter_backends():
    """Iterates over all camera backend modules."""
    # Get a directory listing of all the backends
    for n in glob.glob('%s/%s' % (os.path.dirname(__file__), BACKEND_PATTERN)):
        # Remove the leading directory name
        n = os.path.basename(n)
        # Skip __init__.py and it's ilk.
        if n.startswith('__'):
            continue
        # Remove the extension
        n = os.path.splitext(n)[0]
        yield importlib.import_module('%s.%s' % (__name__, n))


def get_backend(camera):
    """Finds a camera backend that supports the given make/model."""
    # Asks each available backend if this make/model is supported.
    for b in iter_backends():
        try:
            if b.supports(camera.model.make.name, camera.model.name):
                return b.Camera(camera)
        except AttributeError:
            # AttributeError signifies a code module that is not
            # a backend. It is OK to ignore this exception.
            continue
    raise NotSupportedError(camera)


class NotSupportedError(Exception):
    """Raised when no backend supporting the given camera can be found."""
    def __init__(self, camera):
        super(NotSupportedError, self).__init__('No backend available for %s' % camera)