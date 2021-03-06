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
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django import template
from django.middleware import csrf

register = template.Library()

# Local imports
from notesapp.models import Note
from settingsapp.models import get_setting

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
            edit = True

            # Try to get the note for this object:
            try:
                note = Note.objects.get( user = user,
                                          content_type = content_type,
                                          object_id = obj.id )
                public = 'on' if note.public else 'off'
                checked = 'checked' if note.public else ''
                note = note.txt
            except ObjectDoesNotExist:
                note = ''
                edit = False
                public = 'on' if get_setting(user, 'profile_public') else 'off'
                checked = 'checked' if get_setting(user, 'profile_public') else ''

            form_view = reverse( 'manage_note', kwargs={
                                 'ctype_id': content_type.id,
                                 'object_id': obj.id })

            form = '''
            <div class="add_note noprint">
            <form method="POST" action="%(form_view)s">
              <input type='hidden' name='csrfmiddlewaretoken' value='%(csrf)s' />
              <textarea class="note_name_input" type="text" name="txt" maxlength="20480">%(note)s</textarea>
              <input type="checkbox" name="public" id="id_public" value="%(public)s" %(checked)s /> Nota p&uacute;blica |
              <button type="submit" value="Submit">Aplicar</button>
            </form></div>
            ''' % { 'form_view': form_view,
                    'csrf': csrf.get_token(context['request']),
                    'note': note,
                    'public': public,
                    'checked': checked, }

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
                note = Note.objects.get( user=user,
                                          content_type=content_type,
                                          object_id=obj.id)
            except ObjectDoesNotExist:
                # No object to display
                return '<div class="user_notes"></div>'

            if not render_remove and not note.public:
                # Do not show private notes to third parties
                return ''

            return '<div class="user_notes">%s</div>' % note.html()
        except template.VariableDoesNotExist:
            return ''

class ShowPublicNotesNode(template.Node):
    def __init__(self, object_name):
        self.obj = template.Variable(object_name)

    def resolve_vars(self, context):
        obj = self.obj.resolve(context)
        content_type = ContentType.objects.get_for_model(obj)
        return obj, content_type

    def render(self, context):
        try:
            obj, content_type = self.resolve_vars(context)
            remote_user = context['request'].user

            if remote_user.is_authenticated():
                note_list = Note.objects.filter( content_type__exact=content_type,
                                             object_id__exact=obj.id
                                           ).filter( public__exact=True
                                           ).exclude(user__exact = remote_user
                                           ).order_by('timestamp')
            else:
                note_list = Note.objects.filter( content_type__exact=content_type,
                                             object_id__exact=obj.id
                                           ).filter( public__exact=True
                                           ).order_by('timestamp')

            # This sets the context vairable 'note_list' on the template
            context['note_list'] = note_list
            return ''

        except template.VariableDoesNotExist:
            context['note_list'] = []
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

@register.tag(name="show_public_notes")
def do_show_public_notes(parser, token):
    user = None
    try:
        note_name, object_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r this tag must have only one argument" % token.contents.split()[0]

    return ShowPublicNotesNode(object_name)
