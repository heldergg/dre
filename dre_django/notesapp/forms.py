# -*- coding: utf-8 -*-

'''Notes forms'''

from django import forms

from notesapp.models import Note

class NoteForm(forms.Form):
    public = forms.BooleanField(required=False)
    txt = forms.CharField(
        required=False,
        max_length=20480,
        widget=forms.Textarea )
