# -*- coding: utf-8 -*-

# Global Imports:
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

# Local Imports:
import dreapp.index
from bookmarksapp.models import Bookmark
from dreapp.forms import QueryForm
from dreapp.models import Document

def search(request):
    context = {}

    query = ''
    results = []

    new_data = request.GET.copy()
    form = QueryForm(new_data)

    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1

    if form.is_valid():
        query = form.cleaned_data['q']
        indexer = Document.indexer
        results = indexer.search(query)
        context['result_count'] = results.count()
    else:
        form = QueryForm()

    context['form'] = form
    if query:
        context['query'] = '?q=%s' % query
    else:
        context['query'] = ''

    # Setting the pagination
    paginator = Paginator(results, settings.RESULTS_PER_PAGE, orphans=settings.ORPHANS)
    if page < 1:
        page = 1
    if page > paginator.num_pages:
        page = paginator.num_pages

    context['page'] = paginator.page(page)

    object_list = []

    for obj in context['page'].object_list:
        obj.instance.docid = obj.docid
        object_list.append(obj.instance)

    context['page'].object_list = object_list

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
    results = Document.objects.filter( date__exact = datetime.date( year, month, day ))

    # Pagination
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1

    paginator = Paginator(results, settings.RESULTS_PER_PAGE, orphans=settings.ORPHANS)
    if page < 1:
        page = 1
    if page > paginator.num_pages:
        page = paginator.num_pages

    context['page'] = paginator.page(page)
    context['query'] = '?'

    return render_to_response('browse_day.html', context,
                context_instance=RequestContext(request))

def document_display( request, docid ):
    context = {}

    document = get_object_or_404(Document, pk=docid )

    context['document'] = document

    return render_to_response('document_display.html', context,
                context_instance=RequestContext(request))

def bookmark_display( request, userid ):
    context = {}
    user = get_object_or_404(User, pk=userid)

    # Select the bookmarks
    results = Bookmark.objects.filter(user__exact = user) 

    # Pagination
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1

    paginator = Paginator(results, settings.RESULTS_PER_PAGE, orphans=settings.ORPHANS)
    if page < 1:
        page = 1
    if page > paginator.num_pages:
        page = paginator.num_pages

    context['page'] = paginator.page(page)
    context['query'] = '?'

    return render_to_response('bookmark_display.html', context,
                context_instance=RequestContext(request))
