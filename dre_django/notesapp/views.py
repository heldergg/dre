# -*- coding: utf-8 -*-

# Global imports:
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models.signals import pre_delete
from django.db.transaction import commit_on_success

# Local imports:
from decorators import is_ajax
from notesapp.models import Note
from notesapp.forms import NoteForm

##
# Signals
##

@commit_on_success
def check_object_deleted_notes(sender, **kwargs):
    '''Each object that gets deleted is checked for association with notes. If
    this association exist they are deleted'''

    # Get the tagged items list
    obj = kwargs['instance']
    content_type = ContentType.objects.get_for_model(obj)
    try:
        note_list = Note.objects.filter( content_type__exact = content_type,
                                          object_id__exact = obj.id )
    except AttributeError:
        # The django session objects have no id attribute
        return

    # Delete the notes 
    for note in note_list:
        note.delete()

pre_delete.connect(check_object_deleted_notes)


##
# Apply notes
##

@login_required
@is_ajax(template = 'notes_ops.html', referer = True )
def manage(request, ctype_id, object_id ):
    context = {}
    context['success'] = False


    # Get the object
    content_type = ContentType.objects.get(id=ctype_id)
    try:
        obj = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        context['message'] = 'O objecto para aplicar a nota já não existe.'
        return context

    # Check if there's a note associated to the object    
    try:
        note = Note.objects.get( user = request.user, 
                                 content_type = content_type,
                                 object_id = obj.id )
    except ObjectDoesNotExist:
        note = None

    # Process the form
    form = NoteForm(request.POST) 
    if form.is_valid():
        txt = form.cleaned_data['txt']
        public = form.cleaned_data['public']

        if not txt.strip() and not note:
            context['message'] = 'Nota vazia. Não vou criar uma nota vazia'
            return context
        elif not txt.strip() and note:
            # Delete the note:
            note.delete()
            context['success'] = True
            context['html'] = '' 
            context['message'] = 'Nota apagada'
            return context

        if note:
            note.txt = txt
            note.public = public
            context['message'] = 'Nota editada'
        else:
            note = Note( user = request.user,
                         content_object = obj,
                         txt = txt ,
                         public = public)
            context['message'] = 'Nota criada para o objecto'
        note.save()

        context['success'] = True
        context['html'] = note.html()
        return context

    context['message'] = 'Input inválido. Não vou criar a nota.'
    if note:
        context['html'] = note.html()
    return context
    
