# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('settingsapp.views',
    # Settings configuration
    url(r'^$', 'settings_form', name='settings_form'),

    )
