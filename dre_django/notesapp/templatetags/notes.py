# -*- coding: utf-8 -*-

'''
To use the notes defined on this module you must load them to your template with:

{% load notes %}

The following notes are defined:

{% show_note <object> <user object> %} - show the user notes of a given object    

'''

# Global imports
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django import template
from django.middleware import csrf
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

# Local imports
from notesapp.models import Notes

# Configuration
STATIC_URL = getattr(settings, 'STATIC_URL', '/static/')

# NOTE: this is not made to be a configuration option because then, we'd need
# to generate the JavaScript having this in mind. It's too much trouble for
# little gain.

TAG_ICON =  '%simg/remove-note.png' % STATIC_URL

##
# Notes
##

class NoteNode(template.Node):
    def __init__(self, object_name, user):
        self.obj = template.Variable(object_name)
        self.user = template.Variable(user)

    def resolve_vars(self, context):
        obj = self.obj.resolve(context)
        content_type = ContentType.objects.get_for_model(obj)
        user = self.user.resolve(context)
        return obj, content_type, user
        

class NoteFormNode(NoteNode):
    def render(self, context):
        try:
            obj, content_type, user = self.resolve_vars(context)

            form_view = reverse( 'create_note', kwargs={ 
                                 'ctype_id': content_type.id,
                                 'object_id': obj.id })

            form = '''
            <div id="add_note_%(object_id)d" class="add_note">
            <form method="POST" action="%(form_view)s">
              <input type='hidden' name='csrfmiddlewaretoken' value='%(csrf)s' />
              <textarea class="note_name_input" type="text" name="txt" maxlength="20480"></textarea>
              <button type="submit" value="Submit">Adicionar Nota</button>
            </form></div>
            ''' % { 'form_view': form_view, 
                    'object_id': obj.id,
                    'csrf': csrf.get_token(context['request']) }

            return form
        except template.VariableDoesNotExist:
            return ''

class ShowNotesNode(NoteNode):
    def render(self, context):
        try:
            obj, content_type, user = self.resolve_vars(context)
            remote_user = context['request'].user
            render_remove = remote_user == user
            try:
                note = Notes.objects.get( user=user,
                                          content_type=content_type,
                                          object_id=obj.id)
            except ObjectDoesNotExist:
                # No object to display
                return ''

            if not render_remove and note.private:
                # Do not show private notes to third parties
                return ''

            html_list = []
            note_txt = '<div class="user_notes">Notas:<p>%s</p></div>' % note.txt

            return note_txt
        except template.VariableDoesNotExist:
            return ''


@register.tag(name="create_note")
def do_note_form(parser, token):
    try:
        note_name, object_name, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r note requires exactly two arguments" % token.contents.split()[0]

    return NoteFormNode(object_name, user)
    
@register.tag(name="show_note")
def do_show_notes(parser, token):
    try:
        note_name, object_name, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r note requires exactly two arguments" % token.contents.split()[0]

    return ShowNotesNode(object_name, user)

