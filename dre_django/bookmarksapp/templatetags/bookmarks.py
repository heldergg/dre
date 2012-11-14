# -*- coding: utf-8 -*-

'''
To use the tags defined on this module you must load them to your template with:

{% load bookmarks %}

The following tags are defined:

{% toggle_bookmark <object> %} - url to toggle a bookmarks on an object. 
                                 The user must be logged on the system. 

{% bookmark_icon <object> %}   - returns the bookmark icon (on or off).
'''

# Global imports
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django import template
from django.core.exceptions import ObjectDoesNotExist

# Local imports
from bookmarksapp.models import Bookmark

register = template.Library()

# Configuration
STATIC_URL = getattr(settings, 'STATIC_URL', '/static/')
BOOKMARK_ON_ICON = getattr( settings, 'BOOKMARK_ON_ICON', 
                            '%simg/bookmark_on.png' % STATIC_URL)
BOOKMARK_OFF_ICON = getattr( settings, 'BOOKMARK_OFF_ICON', 
                             '%simg/bookmark_off.png' % STATIC_URL)

##
# Tags

class BookmarkNode(template.Node):
    def __init__(self, object_name):
        self.obj = template.Variable(object_name)

    def resolve_object(self, context):
        obj = self.obj.resolve(context)
        content_type = ContentType.objects.get_for_model(obj)
        return obj, content_type


class ToggleBookmarkNode(BookmarkNode):
    def render(self, context):
        try:
            obj, content_type = self.resolve_object(context)

            return reverse( 'toggle_bookmark',
                          kwargs={ 'ctype_id': content_type.id,
                                   'object_id': obj.id })
        except template.VariableDoesNotExist:
            return ''

class BookmarkIconNode(BookmarkNode):
    def render(self, context):
        img = '<img width=16 height=16 src="%s" title="%s">'
        try:
            obj, content_type = self.resolve_object(context)
            user = context['request'].user 
            
            try: 
                bookmark = Bookmark.objects.get( user = user,
                                                 object_id  = obj.id,
                                                 content_type = content_type ) 
                return img % ( BOOKMARK_ON_ICON, 'Remover marcador' ) 
            except ObjectDoesNotExist:
                return img % ( BOOKMARK_OFF_ICON, 'Criar marcador' ) 
        except template.VariableDoesNotExist:
            return ''

@register.tag(name="toggle_bookmark")
def do_toggle_bookmark(parser, token):
    try:
        tag_name, object_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return ToggleBookmarkNode(object_name)

@register.tag(name="bookmark_icon")
def do_toggle_bookmark(parser, token):
    try:
        tag_name, object_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return BookmarkIconNode(object_name)
