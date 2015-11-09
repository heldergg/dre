# -*- coding: utf-8 -*-

from django.conf import settings

def site(request):
    context = {
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://dre.tretas.org'),
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Diários da República')
    }
    return context
