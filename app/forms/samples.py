# app/forms/samples.py
"""Sample registration form."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, BooleanField, SelectField,
    DateField, TextAreaField, RadioField, IntegerField,
)
from wtforms.validators import DataRequired, Optional, Regexp, NumberRange, Length


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
        choices=[],
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

    # --- WTL MG ---
    wtl_module = SelectField(
        "Module",
        choices=[("MODI", "MOD I"), ("MODII", "MOD II"), ("MODIII", "MOD III")],
        validators=[Optional()],
    )
    wtl_supplier = StringField("Supplier", validators=[Optional(), Length(max=255)])
    wtl_vehicle = StringField("Vehicle Number", validators=[Optional(), Length(max=100)])

    # Manual sample_code for WTL (MG/Test) and other cases
    sample_code = StringField("Sample name", validators=[Optional(), Length(max=255)])

    submit = SubmitField("Register")
