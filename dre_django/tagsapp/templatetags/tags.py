# -*- coding: utf-8 -*-

'''
To use the tags defined on this module you must load them to your template with:

{% load tags %}

The following tags are defined:

{% tag_form <object> %}     - creates a form to add a tag to the object. 
{% show_tags <object> %}    - shows the tags for the object

PROBLEM - we resolve the user name from the context, if we are
'''

# Global imports
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django import template
from django.middleware import csrf

register = template.Library()

# Local imports
from tagsapp.models import TaggedItem

# Configuration

##
# Tags
##

class TagNode(template.Node):
    def __init__(self, object_name):
        self.obj = template.Variable(object_name)

    def resolve_object(self, context):
        obj = self.obj.resolve(context)
        content_type = ContentType.objects.get_for_model(obj)
        return obj, content_type

class TagFormNode(TagNode):
    def render(self, context):
        try:
            obj, content_type = self.resolve_object(context)

            form_view = reverse( 'tag_object', kwargs={ 
                                 'ctype_id': content_type.id,
                                 'object_id': obj.id })

            form = '''<p class="object_tags"><form method="POST" action="%(form_view)s">
            <div><input type='hidden' name='csrfmiddlewaretoken' value='%(csrf)s' /></div>
            <input id="id_name" type="text" name="name" maxlength="128" /> 
            <button type="submit" value="Submit">Adicionar Etiqueta</button>
            </form></p>
            ''' % { 'form_view': form_view, 
                    'csrf':csrf.get_token(context['request']) }

            return form
        except template.VariableDoesNotExist:
            return ''

class ShowTagsNode(TagNode):
    def render(self, context):
        try:
            obj, content_type = self.resolve_object(context)
            user = context['request'].user

            tag_list = TaggedItem.objects.filter( tag__user__exact = user,
                                          content_type__exact = content_type,
                                          object_id__exact = obj.id )

            return ''.join([ '<span class="tag" style="%s"><span class="tag_remove"><a>x</a></span> %s</span>' % 
                            (item.tag.style(), item.tag.name) 
                            for item in tag_list]) 
        except template.VariableDoesNotExist:
            return ''


@register.tag(name="tag_object")
def do_tag_object(parser, token):
    try:
        tag_name, object_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return TagFormNode(object_name)
    
@register.tag(name="show_tags")
def do_tag_object(parser, token):
    try:
        tag_name, object_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return ShowTagsNode(object_name)
