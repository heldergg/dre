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
                        help_text = setting.get( 'help_text', None ),
                        )
                continue
            elif setting['type'].lower() == 'integer':
                self.fields[setting['name']] = forms.IntegerField(
                        label = setting['label'],
                        required = False,
                        max_value = setting.get( 'max_value', None ),
                        min_value = setting.get( 'min_value', None ),
                        help_text = setting.get( 'help_text', None ),
                        )
                continue
            elif setting['type'].lower() == 'char':
                self.fields[setting['name']] = forms.CharField(
                        label = setting['label'],
                        required = False,
                        max_length = setting.get( 'max_length', None ),
                        min_length = setting.get( 'min_length', None ),
                        help_text  = setting.get( 'help_text',  None ),
                        )
                continue

            raise UserSettingsError('Unknown setting type')
