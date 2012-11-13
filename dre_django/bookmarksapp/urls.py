# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('bookmarksapp.views',
    url( r'toggle/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$', 
         'toggle_bookmark', 
         name= 'toggle_bookmark' ),
    )
