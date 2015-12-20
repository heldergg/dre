# -*- coding: utf-8 -*-

# Global Imports
from django.conf.urls import url

# Local Imports
from notesapp import views

urlpatterns = [
    ##
    # Notes management

    # Create note
    url( r'manage/(?P<ctype_id>\d+)/(?P<object_id>\d+)/$',
        views.manage, name= 'manage_note' ),
    ]

