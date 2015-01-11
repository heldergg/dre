# -*- coding: utf-8 -*-

"""Project forms"""

# Global imports:
from django import forms

# Local imports:
from models import Document
from tagsapp.models import Tag

class DateInput(forms.widgets.TextInput):
    '''This widget uses the <input type="date" ... > from html5
    '''
    input_type = 'date'

class QueryForm(forms.Form):
    """
    General Xapian Query
    """
    q = forms.CharField(
        required=True,
        max_length=1000,)

class ChooseDateForm(forms.Form):
    date = forms.DateTimeField(
        label = 'Indique a data:',
        required=True,
        widget = DateInput(),
        help_text = "Use o formato AAAA-MM-DD" )

class BrowseDayFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        date =  kwargs['date']
        del kwargs['date']
        super(BrowseDayFilterForm, self).__init__(*args, **kwargs)

        doc_type_choices = [ x['doc_type'] for x in Document.objects.filter(
            date__exact = date ).values('doc_type'
            ).order_by('doc_type').distinct() ]

        self.fields['doc_type'].choices = list(enumerate(doc_type_choices))
        self.document_types = dict(self.fields['doc_type'].choices)

        self.fields['series'].choices = [
            (1, 'Série I'),
            (2, 'Série II'),
            (3, 'Ambas as séries'),
            ]

    series = forms.TypedChoiceField(
        coerce = int,
        label = 'Série:',
        required=True )

    query = forms.CharField(
        label = 'Procurar texto',
        required=False,
        max_length=1000,)

    doc_type = forms.MultipleChoiceField(
        label = 'Tipo documento:',
        required=False,
        widget = forms.SelectMultiple(attrs = {'title':'Filtrar por tipo'}))

    date = forms.DateTimeField(
        label = 'Mudar data:',
        required=False,
        widget = DateInput() )

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
        required=False,
        widget = DateInput() )

    end_date = forms.DateTimeField(
        label = 'Data final:',
        required=False,
        widget = DateInput() )

    tags = forms.MultipleChoiceField(
        label = 'Etiquetas:',
        required=False,
        widget = forms.SelectMultiple(attrs = {'title':'Filtro por tags'}))
