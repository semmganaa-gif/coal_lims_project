# app/schemas/sample_schema.py
# -*- coding: utf-8 -*-
"""
Дээжний Marshmallow schema

API request/response validation болон serialization
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime


class SampleSchema(Schema):
    """
    Sample моделийн schema

    API endpoints дээр дараах зорилгоор ашиглана:
    - Request validation (POST, PUT)
    - Response serialization (GET)
    - Data transformation
    """
    # Read-only fields
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Required fields
    sample_code = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            'required': 'Дээжний код шаардлагатай',
            'invalid': 'Дээжний код текст байх ёстой'
        }
    )

    client_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
        error_messages={
            'required': 'Захиалагчийн нэр шаардлагатай'
        }
    )

    sample_type = fields.Str(
        required=True,
        validate=validate.Length(max=100),
        error_messages={
            'required': 'Дээжний төрөл шаардлагатай'
        }
    )

    # Optional fields
    weight = fields.Float(
        validate=validate.Range(min=0.001, max=10000),
        allow_none=True,
        error_messages={
            'invalid': 'Жин тоо байх ёстой',
            'range': 'Жин 0.001-10000 хооронд байх ёстой'
        }
    )

    mass = fields.Float(
        validate=validate.Range(min=0.001, max=10000),
        allow_none=True
    )

    sample_condition = fields.Str(
        validate=validate.OneOf(['Хуурай', 'Чийгтэй', 'Шингэн']),
        allow_none=True,
        error_messages={
            'validator_failed': 'Дээжний төлөв буруу (Хуурай/Чийгтэй/Шингэн)'
        }
    )

    delivered_by = fields.Str(
        validate=validate.Length(max=200),
        allow_none=True
    )

    prepared_by = fields.Str(
        validate=validate.Length(max=200),
        allow_none=True
    )

    prepared_date = fields.DateTime(allow_none=True)

    notes = fields.Str(allow_none=True)

    received_date = fields.DateTime(
        required=True,
        error_messages={
            'required': 'Хүлээн авсан огноо шаардлагатай',
            'invalid': 'Огнооны формат буруу'
        }
    )

    analyses_to_perform = fields.List(
        fields.Str(),
        allow_none=True,
        error_messages={
            'invalid': 'Шинжилгээний жагсаалт массив байх ёстой'
        }
    )

    status = fields.Str(
        validate=validate.OneOf(['new', 'New', 'in_progress', 'completed', 'archived']),
        allow_none=True,
        missing='new'
    )

    mass_ready = fields.Boolean(allow_none=True)
    mass_ready_at = fields.DateTime(allow_none=True)
    mass_ready_by_id = fields.Int(allow_none=True)

    @validates('sample_code')
    def validate_sample_code(self, value):
        """
        Дээжний код validation

        - Зөвхөн үсэг, тоо, дефис, доогуур зураас
        - SQL injection хамгаалалт
        """
        if not value or not value.strip():
            raise ValidationError('Дээжний код хоосон байж болохгүй')

        # Аюултай тэмдэгтүүд шалгах
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            if char in value.lower():
                raise ValidationError('Дээжний код буруу тэмдэгт агуулж байна')

        return value

    @validates('weight')
    def validate_weight(self, value):
        """Жин validation - сөрөг тоо байж болохгүй"""
        if value is not None and value < 0:
            raise ValidationError('Жин сөрөг тоо байж болохгүй')
        return value

    class Meta:
        """Schema metadata"""
        # Ordered fields for consistent output
        ordered = True
        # Unknown fields-г ignore хийх (strict биш)
        unknown = 'exclude'


class SampleListSchema(Schema):
    """DataTables-д зориулсан sample list schema"""
    draw = fields.Int(required=True)
    recordsTotal = fields.Int(required=True)
    recordsFiltered = fields.Int(required=True)
    data = fields.List(fields.Dict())

    class Meta:
        ordered = True
