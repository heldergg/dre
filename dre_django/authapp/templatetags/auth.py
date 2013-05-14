# -*- coding: utf-8 -*-

'''
To use these tags you have to load them with:

{% load auth %}

The tags defined are:

{% gravatar <email> %} - url for the email gravatar

'''

# Global imports
from django.conf import settings
from django import template
import hashlib
import urllib

register = template.Library()

# Configuration
DEFAULT_GRAVATAR = getattr(settings, 'DEFAULT_GRAVATAR', 'identicon' )

##
# Gravatar
##

class GravatarNode(template.Node):
    def __init__(self, email):
        self.email = template.Variable(email)

    def hash(self, context):
        try:
            email = self.email.resolve(context)
            return hashlib.md5(email.lower()).hexdigest()
        except template.VariableDoesNotExist:
            return ''

    def render(self, context):
        return self.hash(context)

class AvatarNode(GravatarNode):
    def __init__(self,  email, size ):
        GravatarNode.__init__(self, email)
        self.size = template.Variable(size)

    def render(self, context):
        try:
            size = self.size.resolve(context)
            gravatar_url = 'http://www.gravatar.com/avatar/' + self.hash( context ) + "?"
            gravatar_url += urllib.urlencode({'d':DEFAULT_GRAVATAR, 's':str(size)})
            return gravatar_url
        except template.VariableDoesNotExist:
            return ''


@register.tag(name='gravatar')
def do_avatar(parser, token):
    try:
        tag_name, email = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r gravatar requires exactly one arguments" % token.contents.split()[0]

    return GravatarNode(email)

@register.tag(name='avatar')
def do_avatar(parser, token):
    try:
        tag_name, email, size = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r gravatar requires exactly two arguments" % token.contents.split()[0]

    return AvatarNode(email, size)

