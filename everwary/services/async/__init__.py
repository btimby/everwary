try:
    import cPickle as pickle
except ImportError:
    import pickle

from gearman import DataEncoder
from gearman.client import GearmanClient as BaseGearmanClient

from django.conf import settings


class PickleDataEncoder(DataEncoder):
    @classmethod
    def encode(cls, obj):
        return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def decode(cls, encoded):
        return pickle.loads(encoded)


class GearmanClient(BaseGearmanClient):
    data_encoder = PickleDataEncoder


GEARMAN = GearmanClient(getattr(settings, 'GEARMAN_SERVERS', ['localhost']))
