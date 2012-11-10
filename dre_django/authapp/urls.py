# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('authapp.views',
    # Authentication
    url(r'^login/$', 'do_login',
        {'template_name': 'login.html'}, name='login'),

    url(r'^logout/$', 'do_logout', name='logout'),

    # Registration urls
    url(r'^register/$', 'registration', name='registration'),
    )
