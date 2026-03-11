# app/forms/reports.py
"""Report filter forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField
from wtforms.validators import Optional, Length


class KPIReportFilterForm(FlaskForm):
    """KPI report filter form."""
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

    unit = SelectField(
        "Нэгж (client_name)",
        choices=[("all", "Бүх нэгж")],
        default="all",
        validators=[Optional()],
    )

    sample_type = SelectField(
        "Төрөл",
        choices=[("all", "Бүх төрөл")],
        default="all",
        validators=[Optional()],
    )

    analysis_code = StringField(
        "Шинжилгээний код",
        validators=[Optional(), Length(max=50)],
    )

    user_name = StringField(
        "Хэрэглэгч",
        validators=[Optional(), Length(max=100)],
    )

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
