# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('authapp.views',
    # Authentication
    url(r'^login/$', 'do_login',
        {'template_name': 'login.html'}, name='login'),

    url(r'^logout/$', 'do_logout', name='logout'),

    # Registration urls
    url(r'^register/$', 'registration', name='registration'),

    # Personal data
    url(r'^personal_data/$', 'personal_data', name='personal_data'),
)

urlpatterns += patterns('django.contrib.auth.views',
    # Change password
    url(r'^password_change/$', 'password_change',
        kwargs={ 'template_name': 'password_change_form.html', },
        name='password_change'),
    url(r'^password_change/done/$', 'password_change_done',
        kwargs={ 'template_name': 'password_change_done.html' },
        name='password_change_done'),

    # Password reset
    url(r'^password_reset/$', 'password_reset',
        kwargs={ 'template_name': 'password_reset.html',
                 'email_template_name': 'password_reset_email.txt',
                 'subject_template_name': 'password_reset_subject.txt', },
        name='password_reset'),
    url(r'^password_reset_done/done/$', 'password_reset_done',
        kwargs={ 'template_name': 'password_reset_done.html' },
        name='password_reset_done'),
    url(r'^password_reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'password_reset_confirm',
        kwargs={ 'template_name': 'password_reset_confirm.html' },
        name='password_reset_confirm' ),
    url(r'^password_reset/complete/$', 'password_reset_complete',
        kwargs={ 'template_name': 'password_reset_complete.html' },
        name='password_reset_complete' ),

    )
