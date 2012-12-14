# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('tagsapp.views',
    ##
    # Tag management

    # Create tag
    url( r'create/$', 'create', name= 'create_tag' ),

    # Edit tag
    url( r'edit/(?P<tag_id>\d+)/$', 'edit', name= 'edit_tag' ),

    # Delete tag
    url( r'delete/(?P<tag_id>\d+)/$', 'delete', name= 'delete_tag' ),

    # Show tag list
    url( r'display/$', 'display', name= 'tag_display' ),

    # Autocomplete suggestions (AJAX only)
    url( r'suggest/$', 'suggest', name= 'tag_suggest'),


    ##
    # Associate tags with objects

    # Tag Object
    url( r'object/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$',
         'tag_object',
         name= 'tag_object' ),

    # Untag object
    url( r'object/remove/(?P<item_id>\d+)/$',
         'untag_object',
         name= 'untag_object' ),
    
    )

