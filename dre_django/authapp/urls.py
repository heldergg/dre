# -*- coding: utf-8 -*-

# Global Imports
from django.conf.urls import url
from django.contrib.auth import views as auth_views

# Local Imports:
from authapp import views as authapp_views

urlpatterns = [
    # Authentication
    url(r'^login/$', authapp_views.do_login,
        {'template_name': 'login.html'}, name='login'),

    url(r'^logout/$', authapp_views.do_logout, name='logout'),

    # Registration urls
    url(r'^register/$', authapp_views.registration, name='registration'),

    # Personal data
    url(r'^personal_data/$', authapp_views.personal_data, name='personal_data'),
    ]

urlpatterns += [
    # Change password
    url(r'^password_change/$', auth_views.password_change,
        kwargs={ 'template_name': 'password_change_form.html', },
        name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done,
        kwargs={ 'template_name': 'password_change_done.html' },
        name='password_change_done'),

    # Password reset
    url(r'^password_reset/$', auth_views.password_reset,
        kwargs={ 'template_name': 'password_reset.html',
                 'email_template_name': 'password_reset_email.txt',
                 'subject_template_name': 'password_reset_subject.txt', },
        name='password_reset'),
    url(r'^password_reset_done/done/$', auth_views.password_reset_done,
        kwargs={ 'template_name': 'password_reset_done.html' },
        name='password_reset_done'),
    url(r'^password_reset/confirm/(?P<uidb64>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        kwargs={ 'template_name': 'password_reset_confirm.html' },
        name='password_reset_confirm' ),
    url(r'^password_reset/complete/$', auth_views.password_reset_complete,
        kwargs={ 'template_name': 'password_reset_complete.html' },
        name='password_reset_complete' ),
    ]
