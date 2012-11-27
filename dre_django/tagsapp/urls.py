# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('tagsapp.views',
    # Create tag
    url( r'create/$', 'create', name= 'create_tag' ),

    # Edit tag
    url( r'edit/(?P<tag_id>\d+)/$', 'edit', name= 'edit_tag' ),

    # Delete tag
    url( r'delete/(?P<tag_id>\d+)/$', 'delete', name= 'delete_tag' ),
    )

