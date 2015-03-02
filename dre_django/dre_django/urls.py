# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.conf import settings

# Local Imports:
from dre_django.sitemap import StaticViewSitemap
from dreapp.sitemap import DocumentSitemap

urlpatterns = patterns('',
    # Index:
    url(r'^$', 'dreapp.views.search'),

    # About:
    url(r'^about/',
        TemplateView.as_view(template_name='about.html'),
        name='about'),

    # Help:
    url(r'^help/',
        TemplateView.as_view(template_name='help.html'),
        name='help'),

    # Not implemented:
    url(r'^not_implemented/',
        TemplateView.as_view(template_name='not_implemented.html'),
        name='not_implemented'),

    # Authentication and registration
    (r'^auth/', include('authapp.urls')),

    # Bookmarks
    (r'^bookmark/', include('bookmarksapp.urls')),

    # Tags
    (r'^tag/', include('tagsapp.urls')),

    # Notes
    (r'^notes/', include('notesapp.urls')),

    # Settings
    (r'settings/', include('settingsapp.urls')),

    # dreapp
    (r'^dre/', include('dreapp.urls')),

    # Examples:
    # url(r'^$', 'dre_django.views.home', name='home'),
    # url(r'^dre_django/', include('dre_django.foo.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

sitemaps = {
        'static': StaticViewSitemap,
        'documents': DocumentSitemap,
        }

urlpatterns += patterns('django.contrib.sitemaps.views',
        url(r'^sitemap\.xml$', 'index', {'sitemaps': sitemaps}),
        url(r'^sitemap-(?P<section>.+)\.xml$', 'sitemap', {'sitemaps': sitemaps}),
        )


if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
