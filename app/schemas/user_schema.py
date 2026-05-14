# app/schemas/user_schema.py
# -*- coding: utf-8 -*-
"""
Хэрэглэгчийн Marshmallow schema

User моделийн validation, serialization.
app/models/core.py-тай sync.
"""

import re

from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError,
    pre_load,
)


ALLOWED_ROLES = ["prep", "chemist", "senior", "manager", "admin"]
ALLOWED_LANGUAGES = ["en", "mn"]
ALLOWED_LABS = ["coal", "petrography", "water_chemistry", "microbiology"]


class UserSchema(Schema):
    """
    User моделийн schema — app/models/core.py-тай sync

    Хэрэглээ:
        schema = UserSchema()
        errors = schema.validate(data)
    """

    # --- dump_only ---
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # --- Заавал талбарууд ---
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=64),
        error_messages={
            "required": "Хэрэглэгчийн нэр шаардлагатай",
            "invalid": "Хэрэглэгчийн нэр текст байх ёстой",
        },
    )

    password = fields.Str(
        load_only=True,
        validate=validate.Length(min=10),
        error_messages={
            "invalid": "Нууц үг текст байх ёстой",
            "length": "Нууц үг хамгийн багадаа 10 тэмдэгт байх ёстой",
        },
    )

    role = fields.Str(
        required=True,
        validate=validate.OneOf(ALLOWED_ROLES),
        error_messages={
            "required": "Эрх шаардлагатай",
            "validator_failed": "Эрх буруу (prep/chemist/senior/manager/admin)",
        },
    )

    # --- Заавал биш талбарууд ---
    email = fields.Email(
        allow_none=True,
        error_messages={"invalid": "И-мэйл хаяг буруу байна"},
    )

    full_name = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    phone = fields.Str(
        validate=validate.Length(max=20),
        allow_none=True,
    )

    position = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    is_active = fields.Boolean(load_default=True)

    language = fields.Str(
        validate=validate.OneOf(ALLOWED_LANGUAGES),
        load_default="en",
    )

    allowed_labs = fields.List(
        fields.Str(validate=validate.OneOf(ALLOWED_LABS)),
        load_default=["coal"],
    )

    @pre_load
    def strip_username(self, data, **kwargs):
        """username хоосон зай арилгах"""
        if isinstance(data, dict) and "username" in data:
            val = data["username"]
            if isinstance(val, str):
                data["username"] = val.strip()
        return data

    @validates("username")
    def validate_username(self, value, **kwargs):
        """Хэрэглэгчийн нэр — зөвхөн үсэг, тоо, доогуур зураас"""
        if not value or not value.strip():
            raise ValidationError("Хэрэглэгчийн нэр хоосон байж болохгүй")
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValidationError(
                "Хэрэглэгчийн нэр зөвхөн үсэг, тоо, доогуур зураас агуулна"
            )

    @validates("password")
    def validate_password(self, value, **kwargs):
        """
        Нууц үгний бодлого — Model.set_password()-тай sync:
        - 10+ тэмдэгт
        - Том үсэг
        - Жижиг үсэг
        - Тоо
        """
        if not value:
            return

        errors = []
        if len(value) < 10:
            errors.append("хамгийн багадаа 10 тэмдэгт")
        if not any(c.isupper() for c in value):
            errors.append("том үсэг агуулах ёстой")
        if not any(c.islower() for c in value):
            errors.append("жижиг үсэг агуулах ёстой")
        if not any(c.isdigit() for c in value):
            errors.append("тоо агуулах ёстой")

        if errors:
            raise ValidationError("Нууц үг: " + ", ".join(errors))

    class Meta:
        ordered = True
        unknown = "exclude"


class UserListSchema(Schema):
    """Олон хэрэглэгчийн schema"""

    users = fields.List(fields.Nested(UserSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()

    class Meta:
        ordered = True
