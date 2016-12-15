# pylint: skip-file
"""Provide BaseView class and register_versions decorator for easier
handling of different api versions.
"""

import inspect

from flask import jsonify, abort
from flask.views import MethodView

VERSIONS = ['v1', 'v2', 'v3', 'v4', 'v5']


def register_versions(role, versions=None):
    """Decorator for connecting methods in the views to api versions.

    Example:

        class MyView(BaseView):

            @register_versions('fetch', ['v1', 'v2', 'v3'])
            def _get_data(self, param1, param2):
                ...

            @register_versions('return', ['v1', 'v2', 'v3'])
            def _reurn_data(self, data, param1, param2):
                ...

    Args:
       role (string): The role of the method, for example 'fetch' for fetching
         data and 'return' for deciding the return format.
      versions (list): List of versions to register this method for. Default
         is all available versions.
    """
    def decorator(method):
        method._role = role
        method._versions = versions or VERSIONS
        return method
    return decorator


class BaseView(MethodView):
    """Basic view

    Add methods for fetching and formatting data and register them for the
    correct versions.

    Example:

        class ScanData(BaseView):
            SUPPORTED_VERSIONS = ['v1', 'v2', 'v3', 'v4']

            @register_versions('fetch', ['v1', 'v2', 'v3'])
            def _get_data(self, version, date, backend, freqmode, scanno):
                print('In _get_data')

            @register_versions('fetch', ['v4'])
            def _get_data_v4(self, version, date, backend, freqmode, scanno):
                print('In _get_data_v4')

            @register_versions('return', SUPPORTED_VERSIONS)
            def _return_data(self, version, data, *args):
                print('In _return_data')


        class ScanDataNoBackend(ScanData):
            SUPPORTED_VERSIONS = ['v5']

            @register_versions('fetch', SUPPORTED_VERSIONS)
            def _get_data_v5(self, version, date, freqmode, scanno):
                print('In _get_data_v5')
                backend = 'AC2'
                return self._get_data_v4(
                    version, date, backend, freqmode, scanno)

            @register_versions('return', SUPPORTED_VERSIONS)
            def _return_data_v5(self, version, data, *args):
                print('In _return_data_v5')
    """
    # Versions supported by this view (other versions will result in 404):
    SUPPORTED_VERSIONS = VERSIONS

    def __new__(cls, *args, **kwargs):
        """Class constructor, map api versions to view methods."""
        cls.VERSION_TO_FETCHDATA = {}
        cls.VERSION_TO_RETURNDATA = {}
        for method_name, method in inspect.getmembers(
                cls, predicate=inspect.ismethod):
            if hasattr(method, '_role'):
                if method._role == 'fetch':
                    lookup = cls.VERSION_TO_FETCHDATA
                elif method._role == 'return':
                    lookup = cls.VERSION_TO_RETURNDATA
                else:
                    raise ValueError(
                        'Unsupported method role: %r' % method._role)
                for version in method._versions:
                    if version in lookup:
                        raise ValueError((
                            'Version {} has already been registered for '
                            'role {} in method {}').format(
                                version, repr(method._role), lookup[version]))
                    lookup[version] = method_name
        return MethodView.__new__(cls)

    def get(self, version, *args, **kwargs):
        if version not in self.SUPPORTED_VERSIONS:
            abort(404)
        if (version not in self.VERSION_TO_FETCHDATA or
                version not in self.VERSION_TO_RETURNDATA):
            abort(404)
        # TODO: Might want to add more method roles?
        data = getattr(self, self.VERSION_TO_FETCHDATA[version])(
            version, *args, **kwargs)
        # Assume that we always want to return json and 200
        return jsonify(
            getattr(self, self.VERSION_TO_RETURNDATA[version])(
                version, data, *args, **kwargs))
