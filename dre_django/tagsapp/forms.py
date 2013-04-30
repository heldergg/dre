# -*- coding: utf-8 -*-

'''Tags forms'''

from django import forms
from django.core.exceptions import ValidationError
from django.core import validators

from tagsapp.models import Tag

class ColorInput(forms.widgets.TextInput):
    '''This widget uses the <input type="color" ... > from html5, on the
    chrome browser a color picker widget will be displayed.
    '''
    input_type = 'color'

class HtmlColorField(forms.fields.IntegerField):
    '''Html color field, it will accept integers in hex format preceeded by a #
    from 0x0 to 0xFFFFFF. The value returned to the database will be an integer
    '''
    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super(HtmlColorField, self).__init__(*args, **kwargs)

        self.validators.append(validators.MaxValueValidator(int('0xFFFFFF', 16)))
        self.validators.append(validators.MinValueValidator(0))

    def prepare_value(self, value):
        return '#%06x' % value

    def to_python(self, value):
        try:
            value = int(value[1:], 16)
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'])
        value = super(HtmlColorField, self).to_python(value)
        return value

class TagEditForm(forms.ModelForm):
    color      = HtmlColorField(label = 'Color', widget      = ColorInput())
    background = HtmlColorField(label = 'Background', widget = ColorInput())
    class Meta:
        model = Tag
        fields = ('name', 'public', 'color', 'background')

class TagForm(forms.Form):
    name = forms.CharField(
        required=False,
        max_length=128)
