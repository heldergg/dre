# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import url
from django.views.generic import TemplateView

# Local Imports
from dreapp import views

urlpatterns = [
    # Browsing index:
    url(r'^data/$', views.browse, name='browse'),

    # Today's results:
    url(r'^data/hoje/$', views.today_results, name='today_results'),

    # Browse by day:
    url(r'^data/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$',
        views.browse_day, name='browse_day'),

    # Document display
    url(r'^(?P<docid>\d+)/[a-zA-Z0-9\-/_]+$',
        views.document_display, name='document_display'),
    url(r'^(?P<docid>\d+)/$',
        views.document_redirect, name='document_redirect'),

    # Document display (JSON)
    url(r'^(?P<docid>\d+)\.json$', views.document_json, name='document_json'),

    # Document display (Original PDF)
    url(r'^(?P<docid>\d+)\.dre\.pdf$',
        views.document_org_pdf, name='document_org_pdf'),

    # Related documents search result
    url(r'^(?P<docid>\d+)\.related$', views.related, name='related_document'),

    # Display the bookmarked documents
    url(r'^marcador/(?P<userid>\d+)/$',
        views.bookmark_display, name='bookmark_display'),

    # Top documents
    url(r'^top/$',views.top, name='top'),

    # Last documents
    url(r'^last/$',views.last, name='last'),

    # Generate dynamic JS
    url(r'^view_js\.js', views.view_js, name='view_js'),
    ]

##
# Feeds
##

from dreapp.syndication import LatestEntriesFeed

urlpatterns += [
    # Latest feeds
    url(r'^rss/$', LatestEntriesFeed(), name='rss'),

    # Feed help page:
    url(r'^rss/help/$',
        TemplateView.as_view(template_name='rss_help.html'),
        name='rss_help'),
    ]
