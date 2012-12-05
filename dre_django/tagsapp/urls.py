# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('tagsapp.views',
    # Create tag
    url( r'create/$', 'create', name= 'create_tag' ),

    # Edit tag
    url( r'edit/(?P<tag_id>\d+)/$', 'edit', name= 'edit_tag' ),

    # Delete tag
    url( r'delete/(?P<tag_id>\d+)/$', 'delete', name= 'delete_tag' ),

    # Tag Object
    url( r'object/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$',
         'tag_object',
         name= 'tag_object' ),
    
    # Untag object
    url( r'object/remove/(?P<item_id>\d+)/$',
         'untag_object',
         name= 'untag_object' ),

    
    )

