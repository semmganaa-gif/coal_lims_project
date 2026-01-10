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
    """Зөвхөн латин үсэг, тоо, зай, цэг тэмдэгт зөвшөөрнө"""
    if field.data:
        # Latin letters, numbers, spaces, common punctuation
        if not re.match(r'^[A-Za-z0-9\s\.\,\-\_\(\)\']+$', field.data):
            raise ValidationError('Зөвхөн латин үсэг ашиглана уу (Latin characters only)')


# --- Checkbox-той олон сонголт хийхэд зориулсан туслах класс ---
# (Analysis Config дээр олон шинжилгээ сонгоход ашиглана)
class MultiCheckboxField(SelectMultipleField):
    """Олон сонголттой checkbox field."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# ==============================================================================
# 1. ЛОГИН, ХЭРЭГЛЭГЧИЙН УДИРДЛАГЫН ФОРМУУД
# ==============================================================================
class LoginForm(FlaskForm):
    """Хэрэглэгч нэвтрэх форм."""
    username = StringField("Нэвтрэх нэр", validators=[DataRequired()])
    password = PasswordField("Нууц үг", validators=[DataRequired()])
    remember_me = BooleanField("Намайг сана")
    submit = SubmitField("Нэвтрэх")


class UserManagementForm(FlaskForm):
    """Хэрэглэгч үүсгэх/засах форм."""
    username = StringField("Нэвтрэх нэр", validators=[DataRequired()])
    password = PasswordField(
        "Нууц үг (Шинээр оруулах эсвэл солих бол бичнэ үү)",
        validators=[Optional()],
    )
    role = SelectField(
        "Эрхийн түвшин",
        choices=[
            ("prep", "Дээж бэлтгэгч (Sample Preparation)"),
            ("chemist", "Химич (Chemist)"),
            ("senior", "Ахлах химич (Senior Chemist)"),
            ("manager", "Менежер (Manager)"),
            ("admin", "Админ"),
        ],
        validators=[DataRequired()],
    )
    # Профайл мэдээлэл (Email signature-д ашиглана)
    full_name = StringField("Бүтэн нэр (Latin)", validators=[Optional(), latin_only])
    email = StringField("Ажлын имэйл", validators=[Optional(), Email(message="Зөв имэйл хаяг оруулна уу")])
    phone = StringField("Утас", validators=[Optional()])
    position = StringField("Албан тушаал (Latin)", validators=[Optional(), latin_only])
    submit = SubmitField("Хадгалах")


class UserProfileForm(FlaskForm):
    """Хэрэглэгчийн профайл тохиргооны форм (Email signature)"""
    full_name = StringField(
        "Бүтэн нэр",
        validators=[DataRequired(message="Нэрээ оруулна уу"), latin_only],
        render_kw={"placeholder": "e.g. GANTULGA Ulziibuyan"}
    )
    email = StringField(
        "Ажлын имэйл",
        validators=[DataRequired(message="Имэйл оруулна уу"), Email(message="Зөв имэйл хаяг оруулна уу")],
        render_kw={"placeholder": "e.g. gantulga.u@mmc.mn"}
    )
    phone = StringField(
        "Утасны дугаар",
        validators=[Optional()],
        render_kw={"placeholder": "e.g. 80872013"}
    )
    position = StringField(
        "Албан тушаал",
        validators=[Optional(), latin_only],
        render_kw={"placeholder": "e.g. Senior Chemist, Laboratory"}
    )
    submit = SubmitField("Хадгалах")


# ==============================================================================
# 2. ДЭЭЖ БҮРТГЭХ ФОРМ (AddSampleForm)
# ==============================================================================
class AddSampleForm(FlaskForm):
    """Шинэ дээж бүртгэх форм."""
    client_name = RadioField(
        "Хүлээлгэн өгсөн нэгж",
        choices=[
            ("CHPP", "CHPP"),
            ("UHG-Geo", "UHG-Geo"),
            ("BN-Geo", "BN-Geo"),
            ("QC", "QC"),
            ("Proc", "Proc"),
            ("WTL", "WTL"),
            ("LAB", "LAB"),
        ],
        validators=[DataRequired(message="Нэгжийг сонгоно уу.")],
    )

    sample_type = RadioField(
        "Дээжний төрөл",
        choices=[],  # JS + route дээрээс динамикаар тохируулна
        validators=[DataRequired(message="Дээжний төрлийг сонгоно уу.")],
    )

    sample_condition = RadioField(
        "Дээжийн төлөв байдал",
        choices=[
            ("Хуурай", "Хуурай"),
            ("Чийгтэй", "Чийгтэй"),
            ("Шингэн", "Шингэн"),
        ],
        validators=[DataRequired(message="Төлөв байдал сонгоно уу.")],
    )

    sample_date = DateField(
        "Дээж авсан огноо",
        validators=[DataRequired(message="Огноо сонгоно уу.")],
    )

    return_sample = BooleanField("Дээжийг буцаах эсэх")

    retention_period = SelectField(
        "Хадгалах хугацаа",
        choices=[
            ("7", "7 хоног"),
            ("14", "14 хоног"),
            ("30", "1 сар"),
            ("730", "2 жил"),
            ("1825", "5 жил"),
        ],
        default="30",
    )

    delivered_by = StringField(
        "Хүлээлгэн өгсөн ажилтны нэр",
        validators=[
            DataRequired(message="Нэр оруулна уу."),
            Regexp(
                "^[A-Za-z0-9_.]*$",
                message="Зөвхөн латин үсэг, тоо ашиглана уу.",
            ),
        ],
    )

    prepared_date = DateField(
        "Бэлдсэн он сар өдөр",
        validators=[DataRequired(message="Огноо сонгоно уу.")],
    )

    prepared_by = StringField(
        "Бэлтгэсэн ажилтан",
        validators=[
            DataRequired(message="Нэр оруулна уу."),
            Regexp(
                "^[A-Za-z0-9_.]*$",
                message="Зөвхөн латин үсэг, тоо ашиглана уу.",
            ),
        ],
    )

    notes = TextAreaField(
        "Тайлбар",
        validators=[
            Optional(),
            Regexp(
                r"^[A-Za-z0-9_.\s-]*$",
                message="Зөвхөн латин үсэг, тоо ашиглана уу.",
            ),
        ],
    )

    # --- CHPP 2 цаг тутмын ---
    chpp_2h_mod1 = BooleanField("PF211 (MOD I)")
    chpp_2h_mod2 = BooleanField("PF221 (MOD II)")
    chpp_2h_mod3 = BooleanField("PF231 (MOD III)")
    chpp_2h_tc_missing = BooleanField("TC дээж ирээгүй")

    # --- CHPP 4 цаг тутмын ---
    chpp_4h_timeslot = SelectField(
        "Цагийн бүс",
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

    # --- CHPP 12 цаг тутмын ---
    chpp_12h_mod1 = BooleanField("MOD I")
    chpp_12h_mod2 = BooleanField("MOD II")
    chpp_12h_mod3 = BooleanField("MOD III")

    # --- UHG/BN/QC/Proc олон үүсгэгч ---
    location = StringField(
        "Location",
        validators=[
            Optional(),
            Regexp(
                "^[A-Za-z0-9_-]*$",
                message="Зөвхөн латин үсэг, тоо, -, _ ашиглана уу.",
            ),
        ],
    )

    sample_count = IntegerField(
        "Дээжний тоо",
        validators=[
            Optional(),
            NumberRange(min=1, message="Ядаж 1 байх ёстой."),
        ],
    )

    product = StringField(
        "Бүтээгдэхүүн",
        validators=[
            Optional(),
            Regexp(
                "^[A-Za-z0-9_-]*$",
                message="Зөвхөн латин үсэг, тоо, -, _ ашиглана уу.",
            ),
        ],
    )

    # --- WTL ---
    lab_number = StringField(
        "Лаб дугаар",
        validators=[
            Optional(),
            Regexp(
                r"^[A-Za-z0-9_#/-]*$",
                message="Зөвхөн латин үсэг, тоо, #, _, /, - ашиглана уу.",
            ),
        ],
    )

    # WTL (MG/Test) болон бусад үед гараар өгөх нэр
    sample_code = StringField("Sample name", validators=[Optional()])

    submit = SubmitField("Бүртгэх")


# ==============================================================================
# 3. ШИНЖИЛГЭЭНИЙ ТОХИРГООНЫ ФОРМУУД (ANALYSIS CONFIG) - ✅ ШИНЭЧЛЭГДСЭН
# ==============================================================================

# 🧩 Энгийн профайл (Simple Matrix)
class SimpleProfileForm(FlaskForm):
    """Энгийн шинжилгээний профайл форм (Simple Matrix)."""
    # Matrix хүснэгт нь HTML талаас loop хийж өгөгдлөө илгээдэг тул
    # энд зөвхөн Submit товчлуур байхад хангалттай.
    submit_simple = SubmitField("Энгийн тохиргоог хадгалах")


# 🧩 Pattern профайл (Regex Rules)
class PatternProfileForm(FlaskForm):
    """Pattern-д суурилсан шинжилгээний профайл форм."""
    pattern = StringField(
        "Нэрний бүтэц (Pattern)",
        validators=[DataRequired(message="Бүтэц оруулна уу.")],
    )

    analyses = MultiCheckboxField(
        "Шинжилгээнүүд",
        choices=[],  # __init__ дотор DB-ээс дүүргэнэ
        coerce=str,
        validators=[DataRequired(message="Ядаж нэг шинжилгээ сонгоно уу.")],
    )

    # ✅ ШИНЭЧЛЭЛ: admin_routes.py дээрх логиктой уялдуулан эдгээрийг нэмэв
    priority = HiddenField('Priority', default=50)
    rule = HiddenField('Rule', default='merge')

    submit_pattern = SubmitField("Шинэ бүтэц нэмэх")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Аппликейшн ажиллаж байх үед л DB-ээс татна
            from app.models import AnalysisType
            items = AnalysisType.query.order_by(AnalysisType.order_num).all()
            self.analyses.choices = [
                (a.code, f"{a.order_num:02d} — {a.name} ({a.code})") for a in items
            ]
        except (RuntimeError, ImportError):
            # DB холболт байхгүй үед (миграци г.м) алдаа өгөхгүй байх
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
