# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('dreapp.views',
    # Browsing index:
    url(r'^data/$', 'browse', name='browse'),

    # Today's results:
    url(r'^data/hoje/$', 'today_results', name='today_results'),

    # Browse by day:
    url(r'^data/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'browse_day', name='browse_day'),

    # Document display
    url(r'^(?P<docid>\d+)/$', 'document_display', name='document_display'),

    # Document display (JSON)
    url(r'^(?P<docid>\d+).json$', 'document_json', name='document_json'),

    # Document display (Original PDF)
    url(r'^(?P<docid>\d+).dre.pdf$', 'document_org_pdf', name='document_org_pdf'),

    # Related documents search result
    url(r'^(?P<docid>\d+)/related/$', 'related', name='related_document'),

    # Display the bookmarked documents
    url(r'^marcador/(?P<userid>\d+)/$','bookmark_display', name='bookmark_display'),

    # Top documents
    url(r'^top/$','top', name='top'),

    # Last documents
    url(r'^last/$','last', name='last'),

    # Forget me page
    url(r'^forgetme$',
        TemplateView.as_view(template_name='forgetme.html'),
        name='forgetme'),
    )

##
# Feeds
##

from dreapp.syndication import LatestEntriesFeed

urlpatterns += patterns('',
    # Latest feeds
    url(r'^rss/$', LatestEntriesFeed(), name='rss'),

    # Feed help page:
    url(r'^rss/help/$',
        TemplateView.as_view(template_name='rss_help.html'),
        name='rss_help'),
    )
