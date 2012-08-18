# -*- coding: utf-8 -*-

# Global Imports:
from django.shortcuts import render_to_response
from django.template import RequestContext

# Local Imports:
from dreapp.models import Document

def browse( request ):
    context = {}

    return render_to_response('browse.html', context,
                context_instance=RequestContext(request))
