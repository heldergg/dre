# -*- coding: utf-8 -*-

# Global imports:
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

# Local imports:
from decorators import is_ajax
from notesapp.models import Notes
from notesapp.forms import NoteForm


##
# Apply notes
##

@login_required
@is_ajax(template = 'notes_ops.html', referer = True )
def create(request, ctype_id, object_id ):
    context = {}
    context['success'] = False

    # Get the object
    content_type = ContentType.objects.get(id=ctype_id)
    try:
        obj = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        context['message'] = 'O objecto para aplicar a nota já não existe.'
        return context

    # Process the form
    form = NoteForm(request.POST) 
    if form.is_valid():
        txt = form.cleaned_data['txt']
        if not txt.strip():
            context['message'] = 'Nota vazia. Não vou criar uma nota vazia'
            return context

        note = Notes( user = request.user,
                      content_object = obj,
                      txt = txt )
        note.save()

        context['success'] = True
        context['message'] = 'Nota criada para o objecto'
        return context

    context['message'] = 'Input inválido. Não vou criar a nota.'
    return context
    

@login_required
@is_ajax(template = 'notes_ops.html', referer = True )
def edit(request, note_id):
    context = {}
    context['success'] = False

    # Get the note
    try:
        note = Notes.objects.get( id = int(note_id) )
    except ValueError:
        context['message'] = 'Nota inválida.'
        return context
    except ObjectDoesNotExist:
        context['message'] = 'A nota não existe.'
        return context

    # Check the user
    if request.user != note.user:    
        raise PermissionDenied

    # Get and process the form:
    form = NoteForm(request.POST) 
    if form.is_valid():
        txt = form.cleaned_data['txt']

        # Delete the note
        if not txt.strip():
            note.delete()
            context['success'] = True
            context['message'] = 'Nota apagada'
            return context

        # Save changes
        note.txt = txt
        note.save()

        context['success'] = True
        context['message'] = 'Nota editada'
        return context

def delete(request):
    pass

