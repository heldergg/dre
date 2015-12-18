# -*- coding: utf-8 -*-

"""Utility django snippets
"""

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
import json

def is_ajax( template = 'is_ajax_template.html', referer = False ):
    '''Decorator that checks if the request is an AJAX one, if it is returns
    the constructed context as json. If the request is not AJAX it will try
    to find a page to redirect to, if it doesn't find it it will render a
    named template.

    If it tries to redirect it will check if there ia a 'next' defined on the
    request, if it's not it will try to redirecto to the referer page. If you
    don't want to redirect to the referer, use referer = False.
    '''
    def wrapper( f ):
        def inner_wrapper( request, **karg ):
            is_ajax = request.is_ajax()
            context = f( request, **karg )
            redirect_to = request.GET.get('next', '')
            if is_ajax:
                return HttpResponse(json.dumps(context),
                            content_type='application/json')
            elif redirect_to:
                # Redirect to a 'next' page
                return redirect( redirect_to )
            elif referer and request.META.has_key('HTTP_REFERER'):
                # Redirect to the referer
                return redirect( request.META['HTTP_REFERER'] )
            else:
                # Go to the template page
                return render_to_response(template, context,
                    context_instance=RequestContext(request))

        return inner_wrapper
    return wrapper

def only_ajax(f):
    '''Raises a permission denied if the request isn't an AJAX one.
    TODO: Test this decorator
    '''
    def wrapper(request, **karg ):
        if not request.is_ajax():
            raise PermissionDenied
        return f(request, **karg )
    return wrapper
