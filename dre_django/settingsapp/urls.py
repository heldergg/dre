# -*- coding: utf-8 -*-

# Global Imports
from django.conf.urls import url

# Local Imports
from settingsapp import views

urlpatterns = [
    # Settings configuration
    url(r'^$', views.settings_form, name='settings_form'),
    ]

