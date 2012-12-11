# -*- coding: utf-8 -*-

# Global imports:
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError
from django.db import IntegrityError
from django.db.transaction import commit_on_success
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.db.models.signals import pre_delete
from django.db.models.signals import Signal

# Local imports:
from tagsapp.forms import TagEditForm, TagForm
from tagsapp.models import Tag, TaggedItem, del_tagged_item, delete_tag

from decorators import is_ajax

##
# Signals 
##

def check_object_deleted_tags(sender, **kwargs):
    '''Each object that gets deleted is checked for association with tags. If
    this associations exist they are deleted'''

    # Get the tagged items list 
    obj = kwargs['instance']
    content_type = ContentType.objects.get_for_model(obj)
    try:
        tag_list = TaggedItem.objects.filter( content_type__exact = content_type,
                                          object_id__exact = obj.id )
    except AttributeError:
        # The django session onjects have no id attribute
        return

    # Delete the tags
    for tagged_item in tag_list:
        del_tagged_item(tagged_item)

pre_delete.connect(check_object_deleted_tags)


##
# Tagging objects
##

def get_tag_from_request(request):
    if request.method != 'POST':
        raise PermissionDenied

    user = request.user
    form = TagForm(request.POST)
 
    if form.is_valid():
        name = form.cleaned_data['name']
        try:
            tag = Tag.objects.get( user=user, name=name ) 
        except ObjectDoesNotExist:
            tag = Tag( user=user, name=name )
            tag.save()
    else:
        tag = None

    return tag

@login_required
@commit_on_success
@is_ajax(template = 'tags_ops.html', referer = True )
def tag_object(request, ctype_id, object_id ):
    context = {}

    # Get the tag
    tag = get_tag_from_request(request)
    if not tag:
        context['success'] = False
        context['message'] = 'Não consegui obter a etiqueta'
        return context

    # Get the object
    content_type = ContentType.objects.get(id=ctype_id)
    try:
        obj = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        context['success'] = False
        context['message'] = 'O objecto para aplicar a etiqueta já não existe.'
        return context

    try:
        # Associate the tag with the object
        tagged_item = TaggedItem( tag=tag, content_object=obj )
        tagged_item.save()
    except IntegrityError:
        context['success'] = False
        context['message'] = 'Etiqueta repetida!'
        return context

    context['success'] = False
    context['message'] = 'Etiqueta aplicada!'
    return context


@login_required
@commit_on_success
@is_ajax(template = 'tags_ops.html', referer = True )
def untag_object(request, item_id ):
    context = {}

    tagged_item = get_object_or_404(TaggedItem, pk = item_id)
    user = tagged_item.tag.user

    if request.user != user:
        raise PermissionDenied 

    del_tagged_item( tagged_item )

    context['success'] = True
    context['message'] = 'Tag removed from object'
    return context

##
# Tag Management
##

def create_edit( request, tag_edit=None ):
    context = {}
    context['title'] = 'Editar Etiqueta' if tag_edit else 'Criar Etiqueta'
    redirect_to = request.REQUEST.get('next', '')
    
    if request.method == 'POST':
        form = ( TagEditForm(request.POST, instance=tag_edit) 
                 if tag_edit else 
                 TagEditForm(request.POST) )

        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            try:
                tag.save()

                if redirect_to:
                    return redirect( redirect_to )
                else:
                    return HttpResponse('<h1>Etiqueta modificada</h1>' 
                                    if tag_edit else
                                    '<h1>Etiqueta criada</h1>' ) 
            except IntegrityError:
                form.errors['__all__'] = '<span class="error">A etiqueta está duplicada!</span>'
    else:
        form = TagEditForm(instance=tag_edit) if tag_edit else TagEditForm()
    
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
        raise PermissionDenied 

    return create_edit(request, tag )

@login_required
def delete( request, tag_id ):
    context = {}
    redirect_to = request.REQUEST.get('next', '')

    tag = get_object_or_404(Tag, pk = tag_id)
    user = tag.user

    if request.user != user:
        raise PermissionDenied 

    delete_tag( tag )

    context['success'] = True
    context['message'] = 'Tag removed from object'

    if redirect_to:
        return redirect( redirect_to )
    else:
        return HttpResponse('<h1>Etiqueta apagada</h1>')
    

@login_required
def display( request ):
    context = {}

    context['tag_list'] = Tag.objects.filter(user__exact = request.user)
    
    return render_to_response('display.html', context,
                context_instance=RequestContext(request))
