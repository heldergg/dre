# -*- coding: utf-8 -*-

# Global Imports
from django.conf.urls import patterns, url

# Local Imports
from tagsapp import views

urlpatterns = [
    ##
    # Tag management

    # Create tag
    url( r'create/$', views.create, name= 'create_tag' ),

    # Edit tag
    url( r'edit/(?P<tag_id>\d+)/$', views.edit, name= 'edit_tag' ),

    # Delete tag
    url( r'delete/(?P<tag_id>\d+)/$', views.delete, name= 'delete_tag' ),

    # Show tag list
    url( r'display/$', views.display, name= 'tag_display' ),

    # Autocomplete suggestions (AJAX only)
    url( r'suggest/$', views.suggest, name= 'tag_suggest'),


    ##
    # Associate tags with objects

    # Tag Object
    url( r'object/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$',
         views.tag_object,
         name= 'tag_object' ),

    # Untag object
    url( r'object/remove/(?P<item_id>\d+)/$',
         views.untag_object,
         name= 'untag_object' ),
    ]

