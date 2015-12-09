# -*- coding: utf-8 -*-

"""Authentication forms"""

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.forms.utils import ErrorList
from django import forms
from middleware import threadlocals

# Local
from recaptcha_newforms import RecaptchaFieldPlaceholder, RecaptchaField, RecaptchaForm

class AuthFormPersistent(AuthenticationForm):
    def __init__(self, *args, **kargs):
        show_captcha = False
        if kargs.has_key('show_captcha'):
            show_captcha = kargs['show_captcha']
            del kargs['show_captcha']

        if show_captcha:
            self.base_fields['captcha'] = RecaptchaFieldPlaceholder(label='Humano?')
            remote_ip = threadlocals.get_remote_ip()
            self.base_fields['captcha'] = RecaptchaField(remote_ip,
                        *self.base_fields['captcha'].args,
                        **self.base_fields['captcha'].kwargs)
        else:
            if 'captcha' in self.base_fields:
                del self.base_fields['captcha']

        super(AuthFormPersistent, self).__init__(*args, **kargs)


    autologin = forms.BooleanField(
        label = 'Login automatico?',
        required=False )

# Registration forms

ALLOWEDCHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRTSUVWXYZ0123456789'

class RegistrationForm(RecaptchaForm):
    '''Registration form for a new user
    '''
    username = forms.CharField(
        label = 'Nome de utilizador',
        required=True,
        max_length=30,)
    email = forms.EmailField(
        label = 'Email',
        required=False,
        help_text = 'Não é obrigatório')
    password_1 = forms.CharField(
        widget = forms.PasswordInput(render_value=False),
        label = 'Senha',
        required=True)
    password_2 = forms.CharField(
        widget = forms.PasswordInput(render_value=False),
        label = 'Confirmar senha',
        required=True)

    # The validation battery
    def clean_username(self):
        username = self.cleaned_data.get('username')
        for c in username:
            if c not in ALLOWEDCHARS:
                raise forms.ValidationError('O nome de utilizador não admite '
                    'espaços, ou caracteres com acentos.')
        return username

    def clean(self):
        cleaned_data = self.cleaned_data

        password_1 = cleaned_data.get('password_1')
        password_2 = cleaned_data.get('password_2')

        if not self._errors.has_key('password_2'):
            if password_1 != password_2:
                msg = u'As senhas não coincidem.'
                self._errors['password_2'] = ErrorList([msg])
            if len(password_1) < settings.PASSWORD_MIN_SIZE:
                msg = u'A senha é muito curta (minimo %s).' % settings.PASSWORD_MIN_SIZE
                self._errors['password_2'] = ErrorList([msg])
            if len(password_1) > settings.PASSWORD_MAX_SIZE:
                msg = u'A senha é muito longa (maximo %s).' % settings.PASSWORD_MAX_SIZE
                self._errors['password_2'] = ErrorList([msg])

        return cleaned_data

class PersonalDataForm(forms.Form):
    '''Change user's personal data
    '''
    first_name = forms.CharField(
        label = 'Primeiro nome',
        required=False,
        max_length=30,)
    last_name = forms.CharField(
        label = 'Último nome',
        required=False,
        max_length=30,)
    email = forms.EmailField(
        label = 'Email',
        required=False, )
