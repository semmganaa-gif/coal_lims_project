# app/schemas/analysis_schema.py
# -*- coding: utf-8 -*-
"""
Шинжилгээний үр дүнгийн Marshmallow schema

AnalysisResult моделийн validation, serialization.
/api/save_results endpoint-д ашиглана.
"""

import math
import re

from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    validates_schema,
    ValidationError,
    pre_load,
)

from app.utils.validators import ANALYSIS_VALUE_RANGES, DEFAULT_RANGE


class AnalysisResultSchema(Schema):
    """
    AnalysisResult моделийн schema — app/models/analysis.py-тай sync

    Хэрэглээ:
        # Нэг item validation
        schema = AnalysisResultSchema()
        errors = schema.validate(data)

        # Олон item validation
        schema = AnalysisResultSchema(many=True)
        errors = schema.validate(data_list)
    """

    # --- dump_only (response-д буцаана, request-д хүлээн авахгүй) ---
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # --- Заавал талбарууд ---
    sample_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=2147483647),
        error_messages={
            "required": "Дээжний ID шаардлагатай",
            "invalid": "Дээжний ID тоо байх ёстой",
        },
    )

    analysis_code = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            "required": "Шинжилгээний код шаардлагатай",
        },
    )

    # --- Заавал биш талбарууд ---
    user_id = fields.Int(dump_only=True)

    final_result = fields.Float(
        allow_none=True,
        error_messages={"invalid": "Үр дүн тоо байх ёстой"},
    )

    raw_data = fields.Str(allow_none=True)  # JSON текст

    reason = fields.Str(allow_none=True)

    status = fields.Str(
        validate=validate.OneOf(
            ["pending_review", "approved", "rejected", "reanalysis"]
        ),
        load_default="pending_review",
        error_messages={
            "validator_failed": "Статус буруу (pending_review/approved/rejected/reanalysis)"
        },
    )

    rejection_category = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    rejection_subcategory = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    rejection_comment = fields.Str(
        validate=validate.Length(max=255),
        allow_none=True,
    )

    error_reason = fields.Str(
        validate=validate.Length(max=50),
        allow_none=True,
    )

    notes = fields.Str(allow_none=True)

    equipment_id = fields.Int(
        validate=validate.Range(min=1),
        allow_none=True,
        error_messages={
            "invalid": "Хэрэгслийн ID тоо байх ёстой",
        },
    )

    reviewed_by_id = fields.Int(allow_none=True, dump_only=True)
    reviewed_at = fields.DateTime(allow_none=True, dump_only=True)

    @pre_load
    def strip_analysis_code(self, data, **kwargs):
        """analysis_code хоосон зай арилгах"""
        if isinstance(data, dict) and "analysis_code" in data:
            val = data["analysis_code"]
            if isinstance(val, str):
                data["analysis_code"] = val.strip()
        return data

    @validates("analysis_code")
    def validate_analysis_code(self, value, **kwargs):
        """Шинжилгээний код — зөвхөн үсэг, тоо, таслал, доогуур зураас"""
        if not value or not value.strip():
            raise ValidationError("Шинжилгээний код хоосон байж болохгүй")
        if not re.match(r"^[A-Za-z0-9,_\s]+$", value.strip()):
            raise ValidationError(
                "Шинжилгээний код зөвхөн үсэг, тоо, таслал агуулна"
            )

    @validates("final_result")
    def validate_final_result(self, value, **kwargs):
        """NaN, Infinity шалгах"""
        if value is not None:
            if math.isnan(value) or math.isinf(value):
                raise ValidationError("Үр дүн NaN эсвэл Infinity байж болохгүй")

    @validates_schema
    def validate_result_or_raw(self, data, **kwargs):
        """final_result эсвэл raw_data аль нэг байх ёстой"""
        final_result = data.get("final_result")
        raw_data = data.get("raw_data")
        if final_result is None and not raw_data:
            raise ValidationError(
                {"_schema": ["final_result эсвэл raw_data заавал байх ёстой"]}
            )

    class Meta:
        ordered = True
        unknown = "exclude"


class AnalysisResultListSchema(Schema):
    """Олон шинжилгээний үр дүнгийн schema (batch save)"""

    results = fields.List(
        fields.Nested(AnalysisResultSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    class Meta:
        ordered = True
