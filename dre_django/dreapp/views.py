# -*- coding: utf-8 -*-

# Global Imports:
import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

# Local Imports:
from dreapp.models import Document

def search(request):
    context = {}

    return render_to_response('search.html', context,
                context_instance=RequestContext(request))

def browse( request ):
    context = {}

    return render_to_response('browse.html', context,
                context_instance=RequestContext(request))

def browse_day( request, year, month, day ):
    context = {}
    year, month, day = int(year), int(month), int(day) 
    context['query_date'] = '%d,%d,%d' % ( year, month-1, day )

    # Query the document table
    docs = Document.objects.filter( date__exact = datetime.date( year, month, day ))

    context['docs'] = docs

    return render_to_response('browse_day.html', context,
                context_instance=RequestContext(request))

def document_display( request, claint ):
    context = {}

    document = get_object_or_404(Document, claint=claint )

    context['document'] = document

    return render_to_response('document_display.html', context,
                context_instance=RequestContext(request))
