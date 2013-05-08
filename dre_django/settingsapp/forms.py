# -*- coding: utf-8 -*-

'''Settings form'''

# Global
from django.conf import settings
from django import forms

# Local
from exceptions import UserSettingsError

USER_SETTINGS = getattr(settings, 'USER_SETTINGS', None)

# USER_SETTINGS = [
#         { 'name'    : 'profile_public',
#           'label'   : 'Quer o seu perfil público por omissão?',
#           'group'   : 'privacy',
#           'default' : True,
#           'type'    : 'boolean'
#         },
#         ]

class SettingsForm(forms.Form):
    def __init__( self, *args, **kwargs ):
        super(SettingsForm, self).__init__(*args, **kwargs)

        if not USER_SETTINGS:
            raise UserSettingsError('User settings not defined')

        for setting in USER_SETTINGS:
            if setting['type'].lower() == 'boolean':
                self.fields[setting['name']] = forms.BooleanField(
                        label = setting['label'],
                        required = False,
                        )
                continue
            elif setting['type'].lower() == 'integer':
                self.fields[setting['name']] = forms.IntegerField(
                        label = setting['label'],
                        required = False,
                        max_value = getattr( setting, 'max_value', None ),
                        min_value = getattr( setting, 'min_value', None ),
                        )
                continue
            elif setting['type'].lower() == 'char':
                self.fields[setting['name']] = forms.CharField(
                        label = setting['label'],
                        required = False,
                        max_length = getattr( setting, 'max_length', None ),
                        min_length = getattr( setting, 'min_length', None ),
                        )
                continue

            raise UserSettingsError('Unknown setting type')
