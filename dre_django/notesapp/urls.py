# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('notesapp.views',
    ##
    # Notes management

    # Create note
    url( r'create/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$', 'create', name= 'create_note' ),

    # Edit note
    url( r'edit/(?P<note_id>\d+)/$', 'edit', name= 'edit_note' ),

    # Delete note
    url( r'delete/(?P<note_id>\d+)/$', 'delete', name= 'delete_note' ),
    
    )

