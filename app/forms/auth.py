# app/forms/auth.py
"""Authentication and user management forms."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    SelectField, SelectMultipleField, widgets,
)
from wtforms.validators import DataRequired, Optional, Email
from app.forms.common import latin_only


class LoginForm(FlaskForm):
    """User login form."""
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class UserManagementForm(FlaskForm):
    """User create/edit form."""
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField(
        "Password (Enter to create new or change)",
        validators=[Optional()],
    )
    role = SelectField(
        "Role",
        choices=[
            ("prep", "Sample Preparation"),
            ("chemist", "Chemist"),
            ("senior", "Senior Chemist"),
            ("manager", "Manager"),
            ("admin", "Admin (edit existing only)"),
        ],
        validators=[DataRequired()],
    )
    allowed_labs = SelectMultipleField(
        "Allowed Laboratories",
        choices=[
            ('coal', 'Coal Laboratory'),
            ('petrography', 'Petrography Laboratory'),
            ('water', 'Water Laboratory'),
            ('microbiology', 'Microbiology Laboratory'),
        ],
        validators=[Optional()],
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
    )
    full_name = StringField("Full Name (Latin)", validators=[Optional(), latin_only])
    email = StringField("Work Email", validators=[Optional(), Email(message="Please enter a valid email address")])
    phone = StringField("Phone", validators=[Optional()])
    position = StringField("Position (Latin)", validators=[Optional(), latin_only])
    submit = SubmitField("Save")


class UserProfileForm(FlaskForm):
    """User profile settings form (Email signature)."""
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Please enter your name"), latin_only],
        render_kw={"placeholder": "e.g. GANTULGA Ulziibuyan"}
    )
    email = StringField(
        "Work Email",
        validators=[DataRequired(message="Please enter your email"), Email(message="Please enter a valid email address")],
        render_kw={"placeholder": "e.g. gantulga.u@mmc.mn"}
    )
    phone = StringField(
        "Phone Number",
        validators=[Optional()],
        render_kw={"placeholder": "e.g. 80872013"}
    )
    position = StringField(
        "Position",
        validators=[Optional(), latin_only],
        render_kw={"placeholder": "e.g. Senior Chemist, Laboratory"}
    )
    submit = SubmitField("Save")
