# -*- coding: utf-8 -*-

'''Taken from:

http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser

This is necessary to check if the articles are bookmarked
'''

# threadlocals middleware
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_remote_ip():
    return getattr(_thread_locals, 'remote_ip', None)

class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.remote_ip = request.META['REMOTE_ADDR']

