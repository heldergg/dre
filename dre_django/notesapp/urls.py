# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('notesapp.views',
    ##
    # Notes management

    # Create note
    url( r'manage/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$', 'manage', name= 'manage_note' ),
    
    )

