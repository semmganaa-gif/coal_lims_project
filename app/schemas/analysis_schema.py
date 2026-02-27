# app/schemas/analysis_schema.py
# -*- coding: utf-8 -*-
"""
Шинжилгээний үр дүнгийн Marshmallow schema
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, validates_schema


class AnalysisResultSchema(Schema):
    """
    AnalysisResult моделийн schema

    API /save_results endpoint-д ашиглана
    """
    # Зөвхөн унших талбарууд (dump_only)
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_id = fields.Int(dump_only=True)

    # Заавал талбарууд
    sample_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "Дээжний ID шаардлагатай",
            "invalid": "Дээжний ID тоо байх ёстой",
            "range": "Дээжний ID эерэг тоо байх ёстой"
        }
    )

    analysis_code = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            "required": "Шинжилгээний код шаардлагатай"
        }
    )

    # Заавал биш талбарууд
    raw_data = fields.Str(allow_none=True)  # JSON текст

    final_result = fields.Float(
        allow_none=True,
        error_messages={
            "invalid": "Үр дүн тоо байх ёстой"
        }
    )

    unit = fields.Str(
        validate=validate.Length(max=50),
        allow_none=True
    )

    status = fields.Str(
        validate=validate.OneOf([
            "pending_review",
            "approved",
            "rejected",
            "draft"
        ]),
        load_default="pending_review",
        error_messages={
            "validator_failed": "Статус буруу (pending_review/approved/rejected/draft)"
        }
    )

    notes = fields.Str(allow_none=True)

    equipment_id = fields.Int(
        validate=validate.Range(min=1),
        allow_none=True,
        error_messages={
            "invalid": "Хэрэгслийн ID тоо байх ёстой",
            "range": "Хэрэгслийн ID эерэг тоо байх ёстой"
        }
    )

    reviewed_by_id = fields.Int(allow_none=True)
    reviewed_at = fields.DateTime(allow_none=True)

    @validates("analysis_code")
    def validate_analysis_code(self, value, **kwargs):
        """Шинжилгээний код validation — whitelist regex"""
        if not value or not value.strip():
            raise ValidationError("Шинжилгээний код хоосон байж болохгүй")

        import re
        if not re.match(r'^[A-Za-z0-9_]+$', value.strip()):
            raise ValidationError("Шинжилгээний код зөвхөн үсэг, тоо, доогуур зураас агуулна")

        return value

    @validates("final_result")
    def validate_final_result(self, value, **kwargs):
        """
        Эцсийн үр дүн validation

        - NaN, Infinity шалгах
        - Range-ийн шалгалт (analysis code-оос хамаарна)
        """
        if value is not None:
            # NaN эсвэл Infinity шалгах
            import math
            if math.isnan(value) or math.isinf(value):
                raise ValidationError("Үр дүн NaN эсвэл Infinity байж болохгүй")

        return value

    @validates_schema
    def validate_schema(self, data, **kwargs):
        """
        Schema түвшний validation

        - final_result болон raw_data хоёрын аль нэг байх ёстой
        """
        final_result = data.get("final_result")
        raw_data = data.get("raw_data")

        if final_result is None and not raw_data:
            raise ValidationError({
                "_schema": "final_result эсвэл raw_data заавал байх ёстой"
            })

    class Meta:
        """Schema тохиргоо"""
        ordered = True
        unknown = "exclude"


class AnalysisResultListSchema(Schema):
    """Олон шинжилгээний үр дүнгийн schema"""
    results = fields.List(fields.Nested(AnalysisResultSchema))

    class Meta:
        """Schema тохиргоо"""
        ordered = True
