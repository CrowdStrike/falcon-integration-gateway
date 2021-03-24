from . import api


class APIDataError(Exception):
    pass


class AssetNotFound(APIDataError):
    pass


__all__ = ['api', 'APIDataError', 'AssetNotFound']
