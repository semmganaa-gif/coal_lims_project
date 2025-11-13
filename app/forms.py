# app/forms.py
# --- БҮХ ФОРМЫГ НЭГ ДОР ТОДОРХОЙЛСОН ФАЙЛ ---

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, BooleanField, PasswordField, SelectField,
    DateField, TextAreaField, RadioField, IntegerField, SelectMultipleField, widgets
)
from wtforms.validators import DataRequired, Optional, Regexp, NumberRange


# --- Checkbox-той олон сонголт хийхэд зориулсан туслах класс ---
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# ===========================
#  ЛОГИН, ХЭРЭГЛЭГЧИЙН ФОРМУУД
# ===========================
class LoginForm(FlaskForm):
    username = StringField('Нэвтрэх нэр', validators=[DataRequired()])
    password = PasswordField('Нууц үг', validators=[DataRequired()])
    remember_me = BooleanField('Намайг сана')
    submit = SubmitField('Нэвтрэх')


class UserManagementForm(FlaskForm):
    username = StringField('Нэвтрэх нэр', validators=[DataRequired()])
    password = PasswordField(
        'Нууц үг (Шинээр оруулах эсвэл солих бол бичнэ үү)',
        validators=[Optional()]
    )
    role = SelectField(
        'Эрхийн түвшин',
        choices=[
            ('beltgegch', 'Дээж бэлтгэгч'),
            ('himich', 'Химич'),
            ('ahlah', 'Ахлах химич'),
            ('admin', 'Админ')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Хадгалах')


# ===========================
#      ДЭЭЖ БҮРТГЭХ ФОРМ
# ===========================
class AddSampleForm(FlaskForm):
    client_name = RadioField(
        'Хүлээлгэн өгсөн нэгж',
        choices=[
            ('CHPP', 'CHPP'),
            ('UHG-Geo', 'UHG-Geo'),
            ('BN-Geo', 'BN-Geo'),
            ('QC', 'QC'),
            ('Proc', 'Proc'),   # 🛑 ШИНЭ: Proc нэмэгдсэн
            ('WTL', 'WTL'),
            ('LAB', 'LAB'),
        ],
        validators=[DataRequired(message="Нэгжийг сонгоно уу.")]
    )

    sample_type = RadioField(
        'Дээжний төрөл',
        choices=[],   # JS + route дээрээс динамикаар тохируулна
        validators=[DataRequired(message="Дээжний төрлийг сонгоно уу.")]
    )

    sample_condition = RadioField(
        'Дээжийн төлөв байдал',
        choices=[
            ('Хуурай', 'Хуурай'),
            ('Чийгтэй', 'Чийгтэй'),
            ('Шингэн', 'Шингэн'),
        ],
        validators=[DataRequired(message="Төлөв байдал сонгоно уу.")]
    )

    sample_date = DateField(
        'Дээж авсан огноо',
        validators=[DataRequired(message="Огноо сонгоно уу.")]
    )

    return_sample = BooleanField('Дээжийг буцаах эсэх')

    delivered_by = StringField(
        'Хүлээлгэн өгсөн ажилтны нэр',
        validators=[
            DataRequired(message="Нэр оруулна уу."),
            Regexp('^[A-Za-z0-9_.]*$', message='Зөвхөн латин үсэг, тоо ашиглана уу.')
        ]
    )

    prepared_date = DateField(
        'Бэлдсэн он сар өдөр',
        validators=[DataRequired(message="Огноо сонгоно уу.")]
    )

    prepared_by = StringField(
        'Бэлтгэсэн ажилтан',
        validators=[
            DataRequired(message="Нэр оруулна уу."),
            Regexp('^[A-Za-z0-9_.]*$', message='Зөвхөн латин үсэг, тоо ашиглана уу.')
        ]
    )

    notes = TextAreaField(
        'Тайлбар',
        validators=[
            Optional(),
            Regexp(
                r'^[A-Za-z0-9_.\s-]*$',
                message='Зөвхөн латин үсэг, тоо ашиглана уу.'
            )
        ]
    )

    # --- CHPP 2 цаг тутмын ---
    chpp_2h_mod1 = BooleanField('PF211 (MOD I)')
    chpp_2h_mod2 = BooleanField('PF221 (MOD II)')
    chpp_2h_mod3 = BooleanField('PF231 (MOD III)')
    chpp_2h_tc_missing = BooleanField('TC дээж ирээгүй')

    # --- CHPP 4 цаг тутмын ---
    chpp_4h_timeslot = SelectField(
        'Цагийн бүс',
        choices=[
            ('', ''),
            ('10:00', '10:00'),
            ('14:00', '14:00'),
            ('18:00', '18:00'),
            ('22:00', '22:00'),
            ('02:00', '02:00'),
            ('06:00', '06:00'),
        ],
        validators=[Optional()]
    )
    chpp_4h_mod1 = BooleanField('MOD I')
    chpp_4h_mod2 = BooleanField('MOD II')
    chpp_4h_mod3 = BooleanField('MOD III')

    # --- CHPP 12 цаг тутмын ---
    chpp_12h_mod1 = BooleanField('MOD I')
    chpp_12h_mod2 = BooleanField('MOD II')
    chpp_12h_mod3 = BooleanField('MOD III')

    # --- UHG/BN/QC/Proc олон үүсгэгч ---
    location = StringField(
        'Location',
        validators=[
            Optional(),
            Regexp(
                '^[A-Za-z0-9_-]*$',
                message='Зөвхөн латин үсэг, тоо, -, _ ашиглана уу.'
            )
        ]
    )

    sample_count = IntegerField(
        'Дээжний тоо',
        validators=[
            Optional(),
            NumberRange(min=1, message='Ядаж 1 байх ёстой.')
        ]
    )

    product = StringField(
        'Бүтээгдэхүүн',
        validators=[
            Optional(),
            Regexp(
                '^[A-Za-z0-9_-]*$',
                message='Зөвхөн латин үсэг, тоо, -, _ ашиглана уу.'
            )
        ]
    )

    # --- WTL ---
    lab_number = StringField(
        'Лаб дугаар',
        validators=[
            Optional(),
            Regexp(
                r'^[A-Za-z0-9_#/-]*$',
                message='Зөвхөн латин үсэг, тоо, #, _, /, - ашиглана уу.'
            )
        ]
    )

    # WTL (MG/Test) болон бусад үед гараар өгөх нэр
    sample_code = StringField('Sample name', validators=[Optional()])

    submit = SubmitField('Бүртгэх')


# ===========================
#  ШИНЖИЛГЭЭНИЙ ПРОФАЙЛ ФОРМУУД
# ===========================

# 🧩 Энгийн профайл (client_name + sample_type → analyses list)
class SimpleProfileForm(FlaskForm):
    client_name = SelectField(
        'Хүлээлгэн өгсөн нэгж',
        choices=[
            ('CHPP', 'CHPP'),
            ('UHG-Geo', 'UHG-Geo'),
            ('BN-Geo', 'BN-Geo'),
            ('QC', 'QC'),
            ('Proc', 'Proc'),
            ('WTL', 'WTL'),
            ('LAB', 'LAB'),
        ],
        validators=[DataRequired(message="Нэгжийг сонгоно уу.")]
    )

    sample_type = StringField(
        'Дээжний төрөл',
        validators=[DataRequired(message="Дээжний төрлийг оруулна уу.")]
    )

    analyses = MultiCheckboxField(
        'Шинжилгээнүүд',
        choices=[],            # __init__ дотор DB-ээс дүүргэнэ
        coerce=str,
        validators=[DataRequired(message="Ядаж нэг шинжилгээ сонгоно уу.")]
    )

    submit_simple = SubmitField('Энгийн тохиргоог хадгалах')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Анализын жагсаалтыг DB-ээс уншаад сонголтуудыг бүрдүүлнэ
        try:
            from app.models import AnalysisType
            items = AnalysisType.query.order_by(AnalysisType.order_num).all()
            self.analyses.choices = [
                (a.code, f"{a.order_num:02d} — {a.name} ({a.code})")
                for a in items
            ]
        except Exception:
            # app context байхгүй үед (миграци гэх мэт) эвдэрчихгүйн тулд
            self.analyses.choices = []


# 🧩 Pattern профайл (нэрний ПАТТЕРН → analyses list)
class PatternProfileForm(FlaskForm):
    pattern = StringField(
        'Нэрний бүтэц (Pattern)',
        validators=[DataRequired(message="Бүтэц оруулна уу.")]
    )

    analyses = MultiCheckboxField(
        'Шинжилгээнүүд',
        choices=[],            # __init__ дотор DB-ээс дүүргэнэ
        coerce=str,
        validators=[DataRequired(message="Ядаж нэг шинжилгээ сонгоно уу.")]
    )

    submit_pattern = SubmitField('Шинэ бүтэц нэмэх')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from app.models import AnalysisType
            items = AnalysisType.query.order_by(AnalysisType.order_num).all()
            self.analyses.choices = [
                (a.code, f"{a.order_num:02d} — {a.name} ({a.code})")
                for a in items
            ]
        except Exception:
            self.analyses.choices = []
