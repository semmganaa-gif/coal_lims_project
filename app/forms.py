# app/forms.py
# -*- coding: utf-8 -*-
"""
WTForms формуудын тодорхойлолт.

Flask-WTF ашиглан бүх вэб формуудыг тодорхойлно:
- Нэвтрэх/хэрэглэгч удирдлага
- Дээж бүртгэл
- Шинжилгээний тохиргоо
- Тайлангийн шүүлтүүр
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    BooleanField,
    PasswordField,
    SelectField,
    DateField,
    TextAreaField,
    RadioField,
    IntegerField,
    SelectMultipleField,
    HiddenField, # ✅ Нэмэгдсэн
    widgets,
)
from wtforms.validators import DataRequired, Optional, Regexp, NumberRange, Email, ValidationError
import re


def latin_only(form, field):
    """Allow only Latin letters, numbers, spaces, and common punctuation"""
    if field.data:
        # Latin letters, numbers, spaces, common punctuation
        if not re.match(r'^[A-Za-z0-9\s\.\,\-\_\(\)\']+$', field.data):
            raise ValidationError('Only Latin characters are allowed')


# --- Helper class for multi-select checkboxes ---
# (Used for selecting multiple analyses in Analysis Config)
class MultiCheckboxField(SelectMultipleField):
    """Multi-select checkbox field."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# ==============================================================================
# 1. LOGIN AND USER MANAGEMENT FORMS
# ==============================================================================
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
    # Laboratory permissions
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
    # Profile information (used for Email signature)
    full_name = StringField("Full Name (Latin)", validators=[Optional(), latin_only])
    email = StringField("Work Email", validators=[Optional(), Email(message="Please enter a valid email address")])
    phone = StringField("Phone", validators=[Optional()])
    position = StringField("Position (Latin)", validators=[Optional(), latin_only])
    submit = SubmitField("Save")


class UserProfileForm(FlaskForm):
    """User profile settings form (Email signature)"""
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


# ==============================================================================
# 2. SAMPLE REGISTRATION FORM (AddSampleForm)
# ==============================================================================
class AddSampleForm(FlaskForm):
    """New sample registration form."""
    client_name = RadioField(
        "Submitting Unit",
        choices=[
            ("CHPP", "CHPP"),
            ("UHG-Geo", "UHG-Geo"),
            ("BN-Geo", "BN-Geo"),
            ("QC", "QC"),
            ("Proc", "Proc"),
            ("WTL", "WTL"),
            ("LAB", "LAB"),
        ],
        validators=[DataRequired(message="Please select a unit.")],
    )

    sample_type = RadioField(
        "Sample Type",
        choices=[],  # Dynamically set from JS + route
        validators=[DataRequired(message="Please select a sample type.")],
    )

    sample_condition = RadioField(
        "Sample Condition",
        choices=[
            ("Хуурай", "Хуурай"),
            ("Чийгтэй", "Чийгтэй"),
            ("Шингэн", "Шингэн"),
        ],
        validators=[DataRequired(message="Please select a condition.")],
    )

    sample_date = DateField(
        "Sample Date",
        validators=[DataRequired(message="Please select a date.")],
    )

    return_sample = BooleanField("Return Sample")

    retention_period = SelectField(
        "Retention Period",
        choices=[
            ("7", "7 days"),
            ("14", "14 days"),
            ("30", "1 month"),
            ("730", "2 years"),
            ("1825", "5 years"),
        ],
        default="30",
    )

    delivered_by = StringField(
        "Delivered By",
        validators=[
            DataRequired(message="Please enter a name."),
            Regexp(
                r"^[A-Za-z0-9_.\s-]*$",
                message="Only Latin letters, numbers, and spaces are allowed.",
            ),
        ],
    )

    prepared_date = DateField(
        "Prepared Date",
        validators=[DataRequired(message="Please select a date.")],
    )

    prepared_by = StringField(
        "Prepared By",
        validators=[
            DataRequired(message="Please enter a name."),
            Regexp(
                r"^[A-Za-z0-9_.\s-]*$",
                message="Only Latin letters, numbers, and spaces are allowed.",
            ),
        ],
    )

    notes = TextAreaField(
        "Notes",
        validators=[
            Optional(),
            Regexp(
                r"^[A-Za-z0-9_.\s-]*$",
                message="Only Latin letters and numbers are allowed.",
            ),
        ],
    )

    # --- CHPP 2 hourly ---
    chpp_2h_mod1 = BooleanField("PF211 (MOD I)")
    chpp_2h_mod2 = BooleanField("PF221 (MOD II)")
    chpp_2h_mod3 = BooleanField("PF231 (MOD III)")
    chpp_2h_tc_missing = BooleanField("TC sample not received")

    # --- CHPP 4 hourly ---
    chpp_4h_timeslot = SelectField(
        "Time Slot",
        choices=[
            ("", ""),
            ("10:00", "10:00"),
            ("14:00", "14:00"),
            ("18:00", "18:00"),
            ("22:00", "22:00"),
            ("02:00", "02:00"),
            ("06:00", "06:00"),
        ],
        validators=[Optional()],
    )
    chpp_4h_mod1 = BooleanField("MOD I")
    chpp_4h_mod2 = BooleanField("MOD II")
    chpp_4h_mod3 = BooleanField("MOD III")

    # --- CHPP 12 hourly ---
    chpp_12h_mod1 = BooleanField("MOD I")
    chpp_12h_mod2 = BooleanField("MOD II")
    chpp_12h_mod3 = BooleanField("MOD III")

    # --- UHG/BN/QC/Proc multi-generator ---
    location = StringField(
        "Location",
        validators=[
            Optional(),
            Regexp(
                "^[A-Za-z0-9_-]*$",
                message="Only Latin letters, numbers, -, _ are allowed.",
            ),
        ],
    )

    sample_count = IntegerField(
        "Sample Count",
        validators=[
            Optional(),
            NumberRange(min=1, message="Must be at least 1."),
        ],
    )

    product = StringField(
        "Product",
        validators=[
            Optional(),
            Regexp(
                "^[A-Za-z0-9_-]*$",
                message="Only Latin letters, numbers, -, _ are allowed.",
            ),
        ],
    )

    # --- WTL ---
    lab_number = StringField(
        "Lab Number",
        validators=[
            Optional(),
            Regexp(
                r"^[A-Za-z0-9_#/-]*$",
                message="Only Latin letters, numbers, #, _, /, - are allowed.",
            ),
        ],
    )

    # Manual sample_code for WTL (MG/Test) and other cases
    sample_code = StringField("Sample name", validators=[Optional()])

    submit = SubmitField("Register")


# ==============================================================================
# 3. ANALYSIS CONFIG FORMS
# ==============================================================================

# Simple profile (Simple Matrix)
class SimpleProfileForm(FlaskForm):
    """Simple analysis profile form (Simple Matrix)."""
    submit_simple = SubmitField("Save simple config")


# Pattern profile (Regex Rules)
class PatternProfileForm(FlaskForm):
    """Pattern-based analysis profile form."""
    pattern = StringField(
        "Name Pattern",
        validators=[DataRequired(message="Please enter a pattern.")],
    )

    analyses = MultiCheckboxField(
        "Analyses",
        choices=[],  # Populated from DB in __init__
        coerce=str,
        validators=[DataRequired(message="Please select at least one analysis.")],
    )

    priority = HiddenField('Priority', default=50)
    rule = HiddenField('Rule', default='merge')

    submit_pattern = SubmitField("Add new pattern")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Load from DB only when application is running
            from app.models import AnalysisType
            items = AnalysisType.query.order_by(AnalysisType.order_num).all()
            self.analyses.choices = [
                (a.code, f"{a.order_num:02d} — {a.name} ({a.code})") for a in items
            ]
        except (RuntimeError, ImportError):
            # No error when DB connection is unavailable (e.g. migrations)
            self.analyses.choices = []


# ==============================================================================
# 4. KPI / SHIFT ТАЙЛАН ФОРМ
# ==============================================================================
class KPIReportFilterForm(FlaskForm):
    """KPI тайлангийн шүүлтүүр форм."""
    # Огнооны интервал
    start_date = DateField(
        "Эхлэх огноо",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
    end_date = DateField(
        "Дуусах огноо",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    # Аль timestamp дээр тулж KPI тооцох вэ?
    time_base = SelectField(
        "Огнооны суурь",
        choices=[
            ("received", "Хүлээн авсан (received_date)"),
            ("prepared", "Бэлтгэсэн (prepared_date)"),
            ("mass", "Масс бэлэн (mass_ready_at)"),
        ],
        default="received",
        validators=[Optional()],
    )

    # Ямар KPI тоолох вэ?
    kpi_target = SelectField(
        "KPI төрөл",
        choices=[
            ("samples_received", "Хүлээн авсан дээжийн тоо"),
            ("samples_prepared", "Бэлтгэсэн дээжийн тоо"),
            ("mass_ready", "Масс бэлэн болсон дээжийн тоо"),
        ],
        default="samples_received",
        validators=[Optional()],
    )

    # Ээлжийн сонголтууд
    shift_team = SelectField(
        "Ээлж (A/B/C)",
        choices=[
            ("all", "Бүх ээлж"),
            ("A", "A ээлж"),
            ("B", "B ээлж"),
            ("C", "C ээлж"),
        ],
        default="all",
        validators=[Optional()],
    )

    shift_type = SelectField(
        "Shift (өдөр/шөнө)",
        choices=[
            ("all", "Өдөр + Шөнө"),
            ("day", "Зөвхөн өдөр"),
            ("night", "Зөвхөн шөнө"),
        ],
        default="all",
        validators=[Optional()],
    )

    # Нэмэлт фильтрүүд
    unit = SelectField(
        "Нэгж (client_name)",
        choices=[("all", "Бүх нэгж")],  # View-ээс динамикаар бөглөх боломжтой
        default="all",
        validators=[Optional()],
    )

    sample_type = SelectField(
        "Төрөл",
        choices=[("all", "Бүх төрөл")],  # View-ээс динамикаар бөглөнө
        default="all",
        validators=[Optional()],
    )

    analysis_code = StringField(
        "Шинжилгээний код",
        validators=[Optional()],
    )

    user_name = StringField(
        "Хэрэглэгч",
        validators=[Optional()],
    )

    # GROUP BY сонголт – KPI хүснэгтийн баруун талын багана
    group_by = SelectField(
        "Бүлэглэлт",
        choices=[
            ("shift", "Зөвхөн ээлж (A/B/C + өдөр/шөнө)"),
            ("unit", "Нэгжээр (client_name)"),
            ("sample_state", "Дээжийн байдлаар"),
            ("storage", "Хадгалалтаар"),
            ("person", "Хүнээр (ирээдүйд өргөтгөнө)"),
        ],
        default="shift",
        validators=[Optional()],
    )
