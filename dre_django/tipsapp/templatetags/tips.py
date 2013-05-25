# -*- coding: utf-8 -*-

'''
To show the tips, simply load this tags with:

{% load tips %}

And then place the following on your template:

{% show_tips %}

'''

# Global imports
import random
from django.conf import settings
from django import template

register = template.Library()

# Local imports
from settingsapp.models import get_setting

# Configuration
TIPS = getattr(settings, 'TIPS', [])

##
# Tips
##

class TipNode(template.Node):
    def render(self, context):
        user = context['request'].user

        print "#" * 80
        print user

        if not user.is_authenticated() or get_setting( user, 'show_tips'):
            print [random.choice(TIPS)]
            return '<div class="tip">%s</div>' % random.choice(TIPS)
        else:
            return ''

@register.tag(name="show_tips")
def do_note_form(parser, token):
    try:
        note_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r has no arguments," % token.contents.split()[0]

    return TipNode()
