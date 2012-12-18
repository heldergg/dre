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
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django import template
from django.middleware import csrf

register = template.Library()

# Local imports
from tagsapp.models import TaggedItem

# Configuration
STATIC_URL = getattr(settings, 'STATIC_URL', '/static/')

# NOTE: this is not made to be a configuration option because then, we'd need
# to generate the JavaScript having this in mind. It's too much trouble for
# little gain.

REMOVE_TAG_ICON = '%simg/remove-active.png' % STATIC_URL
REMOVE_TAG_INACTIVE_ICON = '%simg/remove-inactive.png' % STATIC_URL
ADD_TAG_ICON = '%simg/add-tag.png' % STATIC_URL
REMOVE_TAG_ICON =  '%simg/remove-tag.png' % STATIC_URL

##
# Tags
##

class TagNode(template.Node):
    def __init__(self, object_name, user):
        self.obj = template.Variable(object_name)
        self.user = template.Variable(user)

    def resolve_vars(self, context):
        obj = self.obj.resolve(context)
        content_type = ContentType.objects.get_for_model(obj)
        user = self.user.resolve(context)
        return obj, content_type, user
        

class TagFormNode(TagNode):
    def render(self, context):
        try:
            obj, content_type, user = self.resolve_vars(context)

            form_view = reverse( 'tag_object', kwargs={ 
                                 'ctype_id': content_type.id,
                                 'object_id': obj.id })

            form = '''
            <div id="add_tag_%(object_id)d" class="add_tag">
            <form method="POST" action="%(form_view)s">
              <input type='hidden' name='csrfmiddlewaretoken' value='%(csrf)s' />
              <input class="tag_name_input" type="text" name="name" maxlength="128" /> 
              <button type="submit" value="Submit">Adicionar Etiqueta</button>
            </form></div>
            ''' % { 'form_view': form_view, 
                    'object_id': obj.id,
                    'csrf':csrf.get_token(context['request']) }

            return form
        except template.VariableDoesNotExist:
            return ''

class ShowTagsNode(TagNode):
    def render(self, context):
        try:
            obj, content_type, user = self.resolve_vars(context)

            tag_list = TaggedItem.objects.filter( tag__user__exact = user,
                                          content_type__exact = content_type,
                                          object_id__exact = obj.id )
                                          
            remote_user = context['request'].user

            html_list = []
            render_remove = remote_user == user
            for item in tag_list:        
                remove_link = ''
                if render_remove:
                    remove_link = '<span class="tag_remove"><a href="%(remove_tag)s"><img class="remove_tag_img" hight="16" width="16" src="%(icon)s"></a></span>' % {
                        'icon': REMOVE_TAG_INACTIVE_ICON, 
                        'remove_tag': reverse('untag_object', kwargs={
                                              'item_id': item.id }) } 
                html =  ('<span class="tag" style="%(style)s">%(remove_link)s<span class="tag_name">%(tag_name)s</span></span>' %       
                        { 'style': item.tag.style(), 
                          'tag_name': item.tag.name,
                          'remove_link': remove_link,
                        } )
                if render_remove or item.tag.public:
                    html_list.append(html)        

            tag_list = '<span class="tag_list">%s</span>' % '\n'.join(html_list)
            if render_remove:
                tag_list += '<span class="tag_control"><img src="%s"></span>' % ADD_TAG_ICON

            return tag_list 
        except template.VariableDoesNotExist:
            return ''


@register.tag(name="tag_object")
def do_tag_object(parser, token):
    try:
        tag_name, object_name, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return TagFormNode(object_name, user)
    
@register.tag(name="show_tags")
def do_show_tags(parser, token):
    try:
        tag_name, object_name, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    return ShowTagsNode(object_name, user)
