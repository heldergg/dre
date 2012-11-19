# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('tagsapp.views',
    # Create tag
    url( r'create_tag/$',
         'create_tag',
         name= 'create_tag' ),
    )

