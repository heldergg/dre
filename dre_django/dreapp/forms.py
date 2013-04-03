# -*- coding: utf-8 -*-

"""Project forms"""

# Global imports:
from django import forms

# Local imports:
from tagsapp.models import Tag

class QueryForm(forms.Form):
    """
    General Xapian Query
    """
    q = forms.CharField(
        required=True,
        max_length=1000,)

class BookmarksFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user =  kwargs['tags_user']
        public_only = kwargs['public_only']
        del kwargs['tags_user']
        del kwargs['public_only']
        super(BookmarksFilterForm, self).__init__(*args, **kwargs)

        tags = Tag.objects.user_tags( user, public_only )
        tag_choices = [ (tag.id,tag.name) for tag in tags ]
        self.fields['tags'].choices = tag_choices

        self.fields['order'].choices = [
            (1, 'Data do marcador'),
            (2, 'Data do documento'),
            ]

    order = forms.TypedChoiceField(
        coerce = int,
        label = 'Ordenar por:',
        required=False )

    invert = forms.BooleanField(
        label = 'Inverter?',
        required=False )

    query = forms.CharField(
        label = 'Procurar texto',
        required=False,
        max_length=1000,)    

    start_date = forms.DateTimeField(
        label = 'Data inicial:',
        required=False )

    end_date = forms.DateTimeField(
        label = 'Data final:',
        required=False )

    tags = forms.MultipleChoiceField(
        label = 'Etiquetas:',
        required=False,
        widget = forms.SelectMultiple(attrs = {'title':'Filtro por tags'}))    
