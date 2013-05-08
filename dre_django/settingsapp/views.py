# -*- coding: utf-8 -*-

# Global imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

# Local imports
from forms import SettingsForm
from models import get_setting, set_setting

USER_SETTINGS = getattr(settings, 'USER_SETTINGS', None)

def settings_form( request, template = 'settings_form.html' ):
    context = {}
    user = request.user

    if request.method == 'POST':
        form = SettingsForm(request.POST.copy())
        if form.is_valid():
            # Cycle through the settings and save them
            data = form.cleaned_data
            for setting in USER_SETTINGS:
                name = setting['name']
                set_setting(user, name, data[name])
            context['saved'] = True
    else:
        # Read user settings and build the form
        settings = {}
        for setting in USER_SETTINGS:
            name = setting['name']
            settings[name] = get_setting(user, name)
        form = SettingsForm(settings)

    context['form'] = form

    return render_to_response(template,
        context, context_instance=RequestContext(request))
