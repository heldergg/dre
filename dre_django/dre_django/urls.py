# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.conf import settings

# Local Imports:
from dre_django.sitemap import StaticViewSitemap
from dreapp.sitemap import DocumentSitemap

from dreapp import views

urlpatterns = [
    # Index:
    url(r'^$', views.search),

    # About:
    url(r'^about/',
        TemplateView.as_view(template_name='about.html'),
        name='about'),

    # Help:
    url(r'^help/',
        TemplateView.as_view(template_name='help.html'),
        name='help'),

    # FAQ:
    url(r'^faq/',
        TemplateView.as_view(template_name='faq.html'),
        name='faq'),

    # Not implemented:
    url(r'^not_implemented/',
        TemplateView.as_view(template_name='not_implemented.html'),
        name='not_implemented'),

    # Authentication and registration
    url(r'^auth/', include('authapp.urls')),

    # Bookmarks
    url(r'^bookmark/', include('bookmarksapp.urls')),

    # Tags
    url(r'^tag/', include('tagsapp.urls')),

    # Notes
    url(r'^notes/', include('notesapp.urls')),

    # Settings
    url(r'settings/', include('settingsapp.urls')),

    # dreapp
    url(r'^dre/', include('dreapp.urls')),
    ]


sitemaps = {
        'static': StaticViewSitemap,
        'documents': DocumentSitemap,
        }

from django.contrib.sitemaps import views
urlpatterns += [
        url(r'^sitemap\.xml$', views.index, {'sitemaps': sitemaps}),
        url(r'^sitemap-(?P<section>.+)\.xml$', views.sitemap, {'sitemaps': sitemaps}),
        ]


if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
