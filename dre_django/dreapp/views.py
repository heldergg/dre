# -*- coding: utf-8 -*-

# Global Imports:
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

# Local Imports:
from dreapp.models import Document

def browse( request ):
    context = {}

    return render_to_response('browse.html', context,
                context_instance=RequestContext(request))


def document_display( request, claint ):
    context = {}

    document = get_object_or_404(Document, claint=claint )

    context['document'] = document

    return render_to_response('document_display.html', context,
                context_instance=RequestContext(request))
