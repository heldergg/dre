# -*- coding: utf-8 -*-

# Global imports:
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

# Local imports:
from tagsapp.forms import TagForm
from tagsapp.models import Tag

def create_edit( request, tag_edit=None ):
    context = {}
    context['title'] = 'Editar Etiqueta' if tag_edit else 'Criar Etiqueta'
    
    if request.method == 'POST':
        form = ( TagForm(request.POST, instance=tag_edit) 
                 if tag_edit else 
                 TagForm(request.POST) )

        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            try:
                tag.save()
                return HttpResponse('<h1>Etiqueta modificada</h1>' 
                                    if tag_edit else
                                    '<h1>Etiqueta criada</h1>' ) 
            except IntegrityError:
                form.errors['__all__'] = '<span class="error">A etiqueta está duplicada!</span>'
    else:
        form = TagForm(instance=tag_edit) if tag_edit else TagForm()
    
    context['form'] = form
    return render_to_response('create.html', context,
                context_instance=RequestContext(request))

@login_required
def create( request ):
    return create_edit(request)

@login_required
def edit( request, tag_id ):
    tag = get_object_or_404(Tag, id=tag_id)
    
    if tag.user != request.user:
        raise Http404

    return create_edit(request, tag )

def delete( request ):
    pass

def show( request ):
    pass
