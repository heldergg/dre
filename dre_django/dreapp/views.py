# -*- coding: utf-8 -*-

# Global Imports:
import datetime
import re
import urllib

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.db.models import Q

# Local Imports:
import dreapp.index
from bookmarksapp.models import Bookmark
from tagsapp.models import Tag
from dreapp.forms import QueryForm, BookmarksFilterForm
from dreapp.models import Document, doc_ref_re

abreviation_list = (
    ('dl', 'decreto-lei'),
)

def search(request):
    context = {}
    context['success'] = True
    context['query_modified'] = False

    query = ''
    results = []

    new_data = request.GET.copy()
    form = QueryForm(new_data)

    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1

    # Try to optimize the user's query?
    mquery = request.GET.get('m','T')

    if form.is_valid():
        query = form.cleaned_data['q']
        indexer = Document.indexer

        # Query optimization
        if mquery == 'T':
            query = query.lower()

            # Expand normal abreviations
            for abr, expanded in abreviation_list:
                query = re.sub( r'(?:^|\s+)' + abr + r'(?:$|\s+)', ' ' + expanded + ' ', query)
            query = re.sub(r'\s\s+', ' ', query).strip()

            # Try to optimize the query
            mod_query = doc_ref_re.sub( ur'tipo:"\2" número:\3', query.lower())

            if mod_query.lower() == query.lower():
                # No optimization
                results = indexer.search(query)
            else:
                # The query string was modified
                results = indexer.search(mod_query)

                if results.count(): # Did we get results?
                    # Yap
                    context['query_modified'] = query
                else:
                    # Nope, will try to get results with the user's query string
                    results = indexer.search(query)
        else:
            results = indexer.search(query)

        context['result_count'] = results.count()
        if not context['result_count']:
            context['success'] = False
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

    # Bookmark Filter Form
    f = context['filter_form'] = BookmarksFilterForm(request.GET, tags_user = user,
            public_only = user != request.user )

    ##
    # Select the bookmarks
    if user != request.user:
        results = Document.objects.filter( Q(bookmarks__user__exact = user) &
                                           Q(bookmarks__public__exact = True))
    else:
        results = Document.objects.filter(bookmarks__user__exact = user)

    if f.is_valid():
        # Filter the results
        order      = f.cleaned_data['order']
        invert     = f.cleaned_data['invert']
        query      = f.cleaned_data['query']
        start_date = f.cleaned_data['start_date']
        end_date   = f.cleaned_data['end_date']
        tags       = [ Tag.objects.get(pk=int(tag_id)) for tag_id in f.cleaned_data['tags'] ]

        # Date filter
        if start_date:
            results = results.filter(date__gte = start_date)
        if end_date:
            results = results.filter(date__lte = end_date)

        # Query filter
        if query:
            results = results.filter(
                    Q(number__icontains = query ) |
                    Q(doc_type__icontains = query ) |
                    Q(emiting_body__icontains = query ) |
                    Q(source__icontains = query ) |
                    Q(dre_key__icontains = query ) |
                    Q(notes__icontains = query )
                    )

        # Tag filter
        if tags:
            results = results.filter( tags__tag__in = tags )

        # Order:
        sign = '' if invert else '-'

        if order:
            results = results.order_by('%s%s' % ( sign,
                'bookmarks__timestamp' if order == 1 else 'date') )
        else:
            results = results.order_by('-bookmarks__timestamp')


    results = results.distinct()

    ##
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

    # Get the bookmark objects:
    results = list(paginator.page(page).object_list)
    for doc in results:
        doc.bm = doc.bookmark( user )

    # Finish the context:
    context['page'] = paginator.page(page)
    context['results'] = results
    context['query'] = '?'
    context['bookmarks_user'] = user

    return render_to_response('bookmark_display.html', context,
                context_instance=RequestContext(request))
