# -*- coding: utf-8 -*-

# Global Imports:
import datetime
import re
import urllib
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q, Max, Min
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.db import connections

# Local Imports:
import dreapp.index
from bookmarksapp.models import Bookmark
from djapian.resultset import ResultSet
from dreapp.forms import BrowseDayFilterForm
from dreapp.forms import QueryForm, BookmarksFilterForm, ChooseDateForm
from dreapp.models import Document, doc_ref_optimize_re
from settingsapp.models import get_setting
from tagsapp.models import Tag

# Settings
SITE_URL = getattr(settings, 'SITE_URL', 'http://dre.tretas.org')

abreviation_list = (
    # Use lower case abreviations and expansions
    # ( <abreviation>, <expansion> )
    (r'd\.?l\.?', 'decreto-lei'),
    (r'dec\.?\s*lei\.?', 'decreto-lei'),
    (r'd\.?\s*lei\.?', 'decreto-lei'),
    (r'dec\s*lei', 'decreto-lei'),
    (r'decreto\s*lei', 'decreto-lei'),
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

    order = request.GET.get('order', None)
    if order not in ('date', '-date'):
        order = None
    context['order'] = order

    # Try to optimize the user's query?
    mquery = request.GET.get('m','T')
    if mquery not in ('T','F'):
        mquery = 'T'
    context['mquery'] = mquery

    if form.is_valid():
        query = form.cleaned_data['q']
        indexer = Document.indexer

        # Query optimization
        if mquery == 'T':
            query = query.lower()

            # Expand normal abreviations
            for abr, expanded in abreviation_list:
                query = re.sub( r'(?:^|\s+)' + abr + r'(?:$|\s+)', ' ' + expanded + ' ', query)
            # Remove extra spaces:
            query = re.sub(r'\s\s+', ' ', query).strip()

            # Try to optimize the query
            mod_query = doc_ref_optimize_re.sub( ur'tipo:"\1" número:\2', query.lower())

            if mod_query.lower() == query.lower():
                # No optimization
                results = ResultSet(indexer, query, parse_query=True) # .order_by('-date')
            else:
                # The query string was modified
                results = ResultSet(indexer, mod_query, parse_query=True)

                if results.count(): # Did we get results?
                    # Yap
                    context['query_modified'] = query
                else:
                    # Nope, will try to get results with the user's query string
                    results = ResultSet(indexer, query, parse_query=True)
        else:
            results = ResultSet(indexer, query, parse_query=True)

        if order:
            results = results.order_by(order)

        spell_correction = results.spell_correction()
        spell_correction = spell_correction.get_corrected_query_string()
        context['spell_correction'] = spell_correction.strip()

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

def related( request, docid ):
    '''
    Returns a related set of search results to a given document.
    '''
    # Select the related documents:
    document = get_object_or_404( Document, id = docid )
    results = Document.indexer.related( document.plain_txt() )

    # Setting the pagination
    context = {}
    context['document'] = document
    context['query'] = '?'
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

    object_list = []

    for obj in context['page'].object_list:
        obj.instance.docid = obj.docid
        object_list.append(obj.instance)

    context['page'].object_list = object_list

    return render_to_response('related.html', context,
                context_instance=RequestContext(request))

def browse( request ):
    context = {}

    if request.method == 'POST':
        form = ChooseDateForm( request.POST )
        if form.is_valid():
            date = form.cleaned_data['date']
            return redirect( reverse('browse_day',
                kwargs= { 'year': date.year,
                          'month': date.month,
                          'day': date.day } ))
    else:
        form = ChooseDateForm()

    context['form'] = form

    return render_to_response('browse.html', context,
                context_instance=RequestContext(request))

def today_results( request ):
    date = datetime.date.today()

    return redirect( reverse('browse_day',
        kwargs= { 'year': date.year,
                  'month': date.month,
                  'day': date.day } ))

def browse_day( request, year, month, day ):
    context = {}

    try:
        date = datetime.date( int(year), int(month), int(day) )
    except ValueError:
        raise Http404

    ##
    # Filter form
    f = BrowseDayFilterForm( request.GET,  date=date )
    context['filter_form'] = f

    order = 1
    invert = False
    query = ''
    doc_type_choices = []
    series = 1
    fdate = date

    if f.is_valid():
        # Filter the results
        query = f.cleaned_data['query']
        doc_type_choices   = [ int(i) for i in f.cleaned_data['doc_type']]
        series = f.cleaned_data['series']
        try:
            fdate = f.cleaned_data['date'].date()
        except AttributeError:
            pass

        if fdate != date:
            return redirect( '%s%s' % ( reverse('browse_day',
                kwargs= { 'year': fdate.year,
                          'month': fdate.month,
                          'day': fdate.day } ),
                re.sub(r'&page=\d+', '', '?%s' % request.META['QUERY_STRING'] ) ))

    ##
    # Query the document table
    results = Document.objects.filter( date__exact = date )

    if series == 1:
        results = results.filter( series__exact = 1 )
    elif series == 2:
        results = results.filter( series__exact = 2 )

    if doc_type_choices:
        t = [ f.document_types[ i ] for i in doc_type_choices ]
        results = results.filter( doc_type__in = t )

    if query:
        results = results.filter(
                Q(number__icontains = query ) |
                Q(doc_type__icontains = query ) |
                Q(emiting_body__icontains = query ) |
                Q(source__icontains = query ) |
                Q(dre_key__icontains = query ) |
                Q(notes__icontains = query )
                )

    results = results.order_by('timestamp')

    ##
    # Dates
    context['prev_date'] = Document.objects.filter( date__lt = date
            ).aggregate(Max('date'))['date__max']
    context['next_date'] = Document.objects.filter( date__gt = date
            ).aggregate(Min('date'))['date__min']
    context['date'] = date

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
    context['query'] = re.sub(r'&page=\d+', '', '?%s' % request.META['QUERY_STRING'] )
    context['query_date'] = re.sub(r'&date=\d+-\d+-\d+', '', '?%s' % request.META['QUERY_STRING'] )

    return render_to_response('browse_day.html', context,
                context_instance=RequestContext(request))

def document_display( request, docid ):
    context = {}

    document = get_object_or_404(Document, pk=docid )

    if document.no_index():
        return redirect(reverse( 'forgetme'))


    context['document'] = document
    context['url'] = urllib.quote_plus( SITE_URL + reverse( 'document_display',
            kwargs = { 'docid': docid }) )
    context['text'] =  urllib.quote_plus( document.title().encode('utf-8')  )

    if request.user.is_authenticated():
        context['show_user_notes'] = get_setting(request.user, 'show_user_notes')

    return render_to_response('document_display.html', context,
                context_instance=RequestContext(request))

def document_org_pdf( request, docid ):
    document = get_object_or_404(Document, pk=docid )

    if not document.dre_pdf:
        raise Http404
#    elif 'getpdf.asp' in document.dre_pdf:
#        url = document.dre_pdf.replace('dig', 'rss')
    elif 'https://dre.pt/application/file/' in document.dre_pdf:
        url = document.dre_pdf
    else:
        url = document.dre_pdf_url()

    return redirect( url )


def document_json( request, docid ):
    document = get_object_or_404(Document, pk=docid )


    return HttpResponse(json.dumps(document.dict_repr()),
            content_type='application/json')

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
    context['query'] = re.sub(r'&page=\d+', '', '?%s' % request.META['QUERY_STRING'] )
    context['bookmarks_user'] = user

    return render_to_response('bookmark_display.html', context,
                context_instance=RequestContext(request))

def top( request ):
    context = {}

    ##
    # Period to show

    # 0 - statistics since the begining
    # 1 - last month
    # 2 - last week
    # 3 - last year
    period = request.GET.get('period', 2)
    try:
        period = int(period)
    except:
        period = 2
    if period not in (1,2,3):
        period = 2
    context['period'] = period

    if period == 1:
        min_date = datetime.datetime.now() - datetime.timedelta(1)
    elif period == 2:
        min_date = datetime.datetime.now() - datetime.timedelta(7)
    else:
        min_date = datetime.datetime.now() - datetime.timedelta(30)

    ##
    # Get the results
    cursor = connections['stats'].cursor()
    query = '''
        select
            count(1) as hits,
            request_path
        from
            statsapp_logline
        where
            response_status = 200 and
            timestamp >= %s and
            request_path ~ '^/dre/[0-9]+/$'
        group by
            request_path
        order by hits desc
        limit 10
    '''
    cursor.execute( query, [ min_date ] )

    results = []
    for hit in cursor.fetchall():
        doc_id = int(hit[1].split('/')[2])
        try:
            results.append(Document.objects.get( pk = doc_id ))
        except ObjectDoesNotExist:
            # This might happen if a document is deleted
            pass

    context['results'] = results

    return render_to_response('top.html', context,
            context_instance=RequestContext(request))

def last( request ):
    '''Shows the last 300 documents for the search engine benefict
    '''
    context = {}

    results = Document.objects.all().order_by('-date')[:300]

    context['results'] = results
    return render_to_response('last.html', context,
            context_instance=RequestContext(request))
