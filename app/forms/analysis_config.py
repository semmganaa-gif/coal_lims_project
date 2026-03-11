# app/forms/analysis_config.py
"""Analysis configuration forms (Simple Matrix, Pattern Rules)."""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired
from app.forms.common import MultiCheckboxField


class SimpleProfileForm(FlaskForm):
    """Simple analysis profile form (Simple Matrix)."""
    submit_simple = SubmitField("Save simple config")


class PatternProfileForm(FlaskForm):
    """Pattern-based analysis profile form."""
    pattern = StringField(
        "Name Pattern",
        validators=[DataRequired(message="Please enter a pattern.")],
    )

    analyses = MultiCheckboxField(
        "Analyses",
        choices=[],
        coerce=str,
        validators=[DataRequired(message="Please select at least one analysis.")],
    )

    priority = HiddenField('Priority', default=50)
    rule = HiddenField('Rule', default='merge')

    submit_pattern = SubmitField("Add new pattern")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from app.models import AnalysisType
            items = AnalysisType.query.order_by(AnalysisType.order_num).all()
            self.analyses.choices = [
                (a.code, f"{a.order_num:02d} — {a.name} ({a.code})") for a in items
            ]
        except (RuntimeError, ImportError):
            self.analyses.choices = []
