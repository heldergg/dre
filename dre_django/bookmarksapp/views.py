# -*- coding: utf-8 -*-

# Global Imports:
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist


# Local Imports
from models import Bookmark

##
# Add bookmark
##

def get_bookmark( user, obj ):
    content_type = ContentType.objects.get_for_model(obj)
    try: 
        bookmark = Bookmark.objects.get( user = user,
                                         object_id  = obj.id,
                                         content_type = content_type ) 
        return bookmark 
    except ObjectDoesNotExist:
        return False 

def add_bookmark( user, obj ):
    bookmark = Bookmark( user=user, 
                         content_object=obj) 
    bookmark.save()
    return bookmark


@login_required
def toggle_bookmark( request, ctype_id, object_id ):
    user = request.user
    content_type = ContentType.objects.get(id=ctype_id)

    try:
        obj = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        raise Http404

    redirect_to = request.REQUEST.get('next', '')

    bookmark = get_bookmark( user, obj )

    if bookmark: 
        # Only the owner of the bookmark can delete it
        if bookmark.user != request.user:
            raise Http404
        bookmark.delete()
    else:
        bookmark = add_bookmark( user, obj )

    if redirect_to:
        return redirect(redirect_to)
    else:
        return HttpResponse('<h1>Bookmark toggled</h1>') 

 
@login_required
def toggle_public( request, ctype_id, object_id ):
    user = request.user
    content_type = ContentType.objects.get(id=ctype_id)

    try:
        obj = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        raise Http404

    redirect_to = request.REQUEST.get('next', '')

    bookmark = get_bookmark( user, obj )

    if not bookmark: 
        raise Http404
    if bookmark.user != request.user:
        # Only the owner of the bookmark can change its status 
        raise Http404

    # Toggle the public flag
    bookmark.public = not bookmark.public
    bookmark.save()

    if redirect_to:
        return redirect(redirect_to)
    else:
        return HttpResponse('<h1>Bookmark status toggled</h1>') 
