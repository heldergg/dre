# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('bookmarksapp.views',
    # Toggle bookmark on an object
    url( r'toggle/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$', 
         'toggle_bookmark', 
         name= 'toggle_bookmark' ),

    # Toggle public status in a bookmark
    url( r'toggle_public/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$', 
         'toggle_public', 
         name= 'toggle_public' ),
    )
