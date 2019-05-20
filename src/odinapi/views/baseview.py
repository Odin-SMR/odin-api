"""Provide BaseView class and register_versions decorator for easier
handling of different api versions.
"""

import inspect
from threading import Lock

from flask import jsonify, Response
from flask.views import MethodView

NEW_BASEVIEW_LOCK = Lock()
VERSIONS = ['v4', 'v5']


def register_versions(role, versions=None):
    """Decorator for connecting methods in the views to api versions.

    Example:

        class MyView(BaseView):

            @register_versions('fetch', ['v4', 'v5'])
            def _get_data(self, param1, param2):
                ...

            @register_versions('return', ['v4', 'v5'])
            def _return_data(self, data, param1, param2):
                ...

    Args:
       role (string): The role of the method, for example 'fetch' for fetching
         data and 'return' for deciding the return format.
      versions (list): List of versions to register this method for. Default
         is all available versions.
    """
    def decorator(method):
        method._role = role
        method._versions = versions
        return method
    return decorator


def inspect_predicate(obj):
    return inspect.ismethod(obj) or inspect.isfunction(obj)


class BadRequest(Exception):
    pass


class BaseView(MethodView):
    """Basic view

    Add methods for fetching and formatting data and register them for the
    correct versions.

    Example:

        class ScanData(BaseView):
            SUPPORTED_VERSIONS = ['v4', 'v5']

            @register_versions('fetch', ['v5'])
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
        with NEW_BASEVIEW_LOCK:
            cls.VERSION_TO_FETCHDATA = {}
            cls.VERSION_TO_RETURNDATA = {}
            cls.VERSION_TO_SWAGGERSPEC = {}
            for method_name, method in inspect.getmembers(
                cls, predicate=inspect_predicate
            ):
                if hasattr(method, '_role'):
                    if method._role == 'fetch':
                        lookup = cls.VERSION_TO_FETCHDATA
                    elif method._role == 'return':
                        lookup = cls.VERSION_TO_RETURNDATA
                    elif method._role == 'swagger':
                        lookup = cls.VERSION_TO_SWAGGERSPEC
                    else:
                        raise ValueError(
                            'Unsupported method role: %r' % method._role)
                    for version in method._versions or cls.SUPPORTED_VERSIONS:
                        if version in lookup:
                            raise ValueError((
                                'Could not register version {} to method {} '
                                'in class {}, it has already been registered '
                                'for role {} in method {}').format(
                                    version, method_name, cls.__name__,
                                    repr(method._role), lookup[version]))
                        lookup[version] = method_name
            return MethodView.__new__(cls)

    def get(self, version, *args, **kwargs):
        if version not in self.SUPPORTED_VERSIONS:
            return jsonify({
                'Error': 'Version {} not supported only {}'.format(
                    version, self.SUPPORTED_VERSIONS,
                ),
            }), 404
        if (version not in self.VERSION_TO_FETCHDATA or
                version not in self.VERSION_TO_RETURNDATA):
            return jsonify({
                'Error':
                'Version {} not supported only {} (restriction {})'.format(
                    version,
                    self.VERSION_TO_FETCHDATA
                    if version not in self.VERSION_TO_FETCHDATA
                    else self.VERSION_TO_RETURNDATA,
                    'fetch data' if version not in self.VERSION_TO_FETCHDATA
                    else 'return data'
                ),
            }), 404
        # TODO: Might want to add more method roles?
        try:
            data = getattr(self, self.VERSION_TO_FETCHDATA[version])(
                version, *args, **kwargs)
        except BadRequest as err:
            return jsonify({'Error': str(err)}), 400
        if isinstance(data, Response):
            return data, 400
        elif isinstance(data, tuple):
            data, status, headers = data
        else:
            status, headers = 200, {}
        # Assume that we always want to return json and 200
        return jsonify(
            getattr(self, self.VERSION_TO_RETURNDATA[version])(
                version, data, *args, **kwargs)), status, headers

    def swagger_spec(self, version):
        """Return GET swagger spec for this view.

        Register the method to use like this:

            @register_versions('swagger', ['v5'])
            def _swagger_spec(self, version):
               ...
        """
        if version not in self.SUPPORTED_VERSIONS:
            return
        if version in self.VERSION_TO_SWAGGERSPEC:
            return getattr(self, self.VERSION_TO_SWAGGERSPEC[version])(version)
