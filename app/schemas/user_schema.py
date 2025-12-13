# app/schemas/user_schema.py
# -*- coding: utf-8 -*-
"""
Хэрэглэгчийн Marshmallow schema
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class UserSchema(Schema):
    """
    User моделийн schema

    Admin endpoints дээр хэрэглэгч үүсгэх, засахад ашиглана
    """
    # Read-only
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # Required fields
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=64),
        error_messages={
            'required': 'Хэрэглэгчийн нэр шаардлагатай',
            'invalid': 'Хэрэглэгчийн нэр текст байх ёстой',
            'length': 'Хэрэглэгчийн нэр 3-64 тэмдэгт байх ёстой'
        }
    )

    # Load only (нууц үг зөвхөн request-д)
    password = fields.Str(
        load_only=True,
        validate=validate.Length(min=8),
        error_messages={
            'invalid': 'Нууц үг текст байх ёстой',
            'length': 'Нууц үг хамгийн багадаа 8 тэмдэгт байх ёстой'
        }
    )

    role = fields.Str(
        required=True,
        validate=validate.OneOf(['prep', 'chemist', 'senior', 'manager', 'admin']),
        error_messages={
            'required': 'Эрх шаардлагатай',
            'validator_failed': 'Эрх буруу (prep/chemist/senior/manager/admin)'
        }
    )

    # Optional fields
    email = fields.Email(
        allow_none=True,
        error_messages={
            'invalid': 'И-мэйл хаяг буруу байна'
        }
    )

    full_name = fields.Str(
        validate=validate.Length(max=200),
        allow_none=True
    )

    is_active = fields.Boolean(load_default=True)

    @validates('username')
    def validate_username(self, value, **kwargs):
        """
        Username validation

        - Зөвхөн үсэг, тоо, доогуур зураас
        - SQL injection хамгаалалт
        """
        if not value or not value.strip():
            raise ValidationError('Хэрэглэгчийн нэр хоосон байж болохгүй')

        # Only alphanumeric and underscore
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError(
                'Хэрэглэгчийн нэр зөвхөн үсэг, тоо, доогуур зураас агуулна'
            )

        # SQL injection хамгаалалт
        dangerous = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        value_upper = value.upper()
        for word in dangerous:
            if word in value_upper:
                raise ValidationError('Хэрэглэгчийн нэр буруу тэмдэгт агуулж байна')

        return value

    @validates('password')
    def validate_password(self, value, **kwargs):
        """
        Нууц үгний validation

        Шаардлага:
        - Хамгийн багадаа 8 тэмдэгт
        - Том үсэг
        - Жижиг үсэг
        - Тоо
        """
        if not value:
            # Password optional during update
            return value

        errors = []

        if len(value) < 8:
            errors.append('хамгийн багадаа 8 тэмдэгт')

        if not any(c.isupper() for c in value):
            errors.append('том үсэг агуулах ёстой')

        if not any(c.islower() for c in value):
            errors.append('жижиг үсэг агуулах ёстой')

        if not any(c.isdigit() for c in value):
            errors.append('тоо агуулах ёстой')

        if errors:
            raise ValidationError(f"Нууц үг: {', '.join(errors)}")

        return value

    class Meta:
        ordered = True
        unknown = 'exclude'


class UserListSchema(Schema):
    """Multiple users schema"""
    users = fields.List(fields.Nested(UserSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()

    class Meta:
        ordered = True
