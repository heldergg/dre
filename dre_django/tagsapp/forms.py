# -*- coding: utf-8 -*-

'''Tags forms'''

from django import forms

from tagsapp.models import Tag

class TagEditForm(forms.ModelForm):
    class Meta:
        model = Tag 
        fields = ('name', 'public', 'note', 'color', 'background')

class TagForm(forms.Form):
    name = forms.CharField(
        required=False,
        max_length=128)
