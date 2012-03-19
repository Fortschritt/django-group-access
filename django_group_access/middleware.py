# Copyright 2012 Canonical Ltd.
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_storage = local()


def get_access_control_user():
    return getattr(_storage, 'access_control_user', None)


class DjangoGroupAccessMiddleware(object):
    """
    Stores and clears the currently logged in user in
    thread local storage.
    """
    def process_request(self, request):
        _storage.access_control_user = getattr(request, 'user', None)
        return None

    def process_response(self, request, response):
        _storage.access_control_user = None
        return response
