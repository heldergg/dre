# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.contrib.auth.views import password_change, password_change_done

urlpatterns = patterns('authapp.views',
    # Authentication
    url(r'^login/$', 'do_login',
        {'template_name': 'login.html'}, name='login'),

    url(r'^logout/$', 'do_logout', name='logout'),

    # Registration urls
    url(r'^register/$', 'registration', name='registration'),

    # Change password
    url(r'^password_change/$', password_change,
        kwargs={ 'template_name': 'password_change_form.html', },
        name='password_change'),
    url(r'^password_change/done/$', password_change_done,
        kwargs={ 'template_name': 'password_change_done.html' },
        name='password_change_done'),

    # Personal data
    url(r'^personal_data/$', 'personal_data', name='personal_data'),
    )
