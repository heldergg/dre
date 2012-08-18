# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^$', 'dreapp.views.browse', name='browse'),

    # About:
    url(r'^about', 
        TemplateView.as_view(template_name='about.html'),
        name='about'),

    # Not implemented:
    url(r'^not_implemented', 
        TemplateView.as_view(template_name='not_implemented.html'),
        name='not_implemented'),

    # Examples:
    # url(r'^$', 'dre_django.views.home', name='home'),
    # url(r'^dre_django/', include('dre_django.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
