# -*- coding: utf-8 -*-

# Global Imports
from django.conf.urls import url

# Local Imports
from bookmarksapp import views

urlpatterns = [
    # Toggle bookmark on an object
    url( r'toggle/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$',
         views.toggle_bookmark,
         name= 'toggle_bookmark' ),

    # Toggle public status in a bookmark
    url( r'toggle_public/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$',
         views.toggle_public,
         name= 'toggle_public' ),
    ]
