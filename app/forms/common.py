# app/forms/common.py
"""Shared form utilities: validators and custom fields."""

import re
from wtforms import SelectMultipleField, widgets
from wtforms.validators import ValidationError


def latin_only(form, field):
    """Allow only Latin letters, numbers, spaces, and common punctuation."""
    if field.data:
        if not re.match(r'^[A-Za-z0-9\s\.\,\-\_\(\)\']+$', field.data):
            raise ValidationError('Only Latin characters are allowed')


class MultiCheckboxField(SelectMultipleField):
    """Multi-select checkbox field."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
