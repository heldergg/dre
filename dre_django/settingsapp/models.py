# -*- coding: utf-8 -*-

# Global imports

import pickle

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

# Local imports
from exceptions import UserSettingsError

USER_SETTINGS = getattr(settings, 'USER_SETTINGS', None)

class Settings(models.Model):
    user =  models.ForeignKey(User)
    name = models.CharField( max_length = 128 )
    value = models.CharField( max_length = 1024 )

    class Meta:
        unique_together = ('user', 'name')

def get_setting( user, name ):
    try:
        value = Settings.objects.get( user = user, name = name ).value
        value = pickle.loads(value)
    except ObjectDoesNotExist:
        settings = dict( ( (xi['name'], xi) for xi in USER_SETTINGS ) )
        if name in settings:
            value = settings[name]['default']
        else:
            raise UserSettingsError('Unknown setting: %s' % name )
    return value

def set_setting( user, name, value ):
    value = pickle.dumps(value)
    try:
        setting = Settings.objects.get( user = user, name = name )
        setting.value = value
    except ObjectDoesNotExist:
        setting = Settings(user = user, name = name, value = value )
    setting.save()
