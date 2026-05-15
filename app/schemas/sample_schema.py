# app/schemas/sample_schema.py
# -*- coding: utf-8 -*-
"""
Дээжний Marshmallow schema

Sample моделийн validation, serialization.
app/models/core.py-тай sync.
"""

from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError,
    pre_load,
)


# DB CHECK constraint-аас авсан зөвшөөрөгдсөн утгууд
ALLOWED_CLIENT_NAMES = [
    "CHPP", "UHG-Geo", "BN-Geo", "QC", "WTL", "Proc", "LAB",
    "uutsb", "negdsen_office", "tsagaan_khad", "tsetsii", "naymant",
    "naimdai", "malchdyn_hudag", "hyanalt", "tsf", "uarp",
    "shine_camp", "busad", "dotood_air", "dotood_swab", "naimdain",
    "maiga", "sum", "uurhaichin", "gallerey", "sbutsb",
]

# Enum-аас гаргасан жагсаалтууд — single source of truth
from app.constants import SampleStatus, LabKey

ALLOWED_STATUSES = SampleStatus.values()
ALLOWED_LAB_TYPES = LabKey.values()


class SampleSchema(Schema):
    """
    Sample моделийн schema — app/models/core.py-тай sync

    Хэрэглээ:
        schema = SampleSchema()
        errors = schema.validate(request_data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400
        data = schema.load(request_data)
    """

    # --- dump_only ---
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # --- Заавал талбарууд ---
    sample_code = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={
            "required": "Дээжний код шаардлагатай",
            "invalid": "Дээжний код текст байх ёстой",
        },
    )

    client_name = fields.Str(
        required=True,
        validate=validate.OneOf(
            ALLOWED_CLIENT_NAMES,
            error="Захиалагчийн нэр буруу. Зөвшөөрөгдсөн: {choices}",
        ),
        error_messages={"required": "Захиалагчийн нэр шаардлагатай"},
    )

    sample_type = fields.Str(
        required=True,
        validate=validate.Length(max=100),
        error_messages={"required": "Дээжний төрөл шаардлагатай"},
    )

    received_date = fields.DateTime(
        required=True,
        error_messages={
            "required": "Хүлээн авсан огноо шаардлагатай",
            "invalid": "Огнооны формат буруу",
        },
    )

    # --- Заавал биш талбарууд ---
    lab_type = fields.Str(
        validate=validate.OneOf(ALLOWED_LAB_TYPES),
        load_default="coal",
    )

    status = fields.Str(
        validate=validate.OneOf(ALLOWED_STATUSES),
        allow_none=True,
        load_default="new",
    )

    sample_date = fields.Date(allow_none=True)

    sample_condition = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    weight = fields.Float(
        validate=validate.Range(min=0.001, max=10000),
        allow_none=True,
        error_messages={
            "invalid": "Жин тоо байх ёстой",
        },
    )

    notes = fields.Str(allow_none=True)

    return_sample = fields.Boolean(load_default=False)

    delivered_by = fields.Str(
        validate=validate.Length(max=200),
        allow_none=True,
    )

    prepared_by = fields.Str(
        validate=validate.Length(max=200),
        allow_none=True,
    )

    prepared_date = fields.Date(allow_none=True)

    location = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    hourly_system = fields.Str(
        validate=validate.Length(max=50),
        allow_none=True,
    )

    shift_time = fields.Str(
        validate=validate.Length(max=50),
        allow_none=True,
    )

    product = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    analyses_to_perform = fields.Str(
        allow_none=True,
    )

    mass_ready = fields.Boolean(allow_none=True)
    mass_ready_at = fields.DateTime(allow_none=True, dump_only=True)
    mass_ready_by_id = fields.Int(allow_none=True, dump_only=True)

    # --- Water Lab ---
    chem_lab_id = fields.Str(
        validate=validate.Length(max=20),
        allow_none=True,
    )

    micro_lab_id = fields.Str(
        validate=validate.Length(max=20),
        allow_none=True,
    )

    # --- ISO 17025 Chain of Custody ---
    sampled_by = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    sampling_date = fields.DateTime(allow_none=True)

    sampling_location = fields.Str(
        validate=validate.Length(max=200),
        allow_none=True,
    )

    sampling_method = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    custody_log = fields.Str(allow_none=True)  # JSON

    retention_date = fields.Date(allow_none=True)
    disposal_date = fields.Date(allow_none=True)

    disposal_method = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True,
    )

    @pre_load
    def strip_sample_code(self, data, **kwargs):
        """sample_code хоосон зай арилгах"""
        if isinstance(data, dict) and "sample_code" in data:
            val = data["sample_code"]
            if isinstance(val, str):
                data["sample_code"] = val.strip()
        return data

    @validates("sample_code")
    def validate_sample_code(self, value, **kwargs):
        """Дээжний код — хоосон биш, зөвшөөрөгдсөн тэмдэгтүүд"""
        if not value or not value.strip():
            raise ValidationError("Дээжний код хоосон байж болохгүй")

    class Meta:
        ordered = True
        unknown = "exclude"


class SampleListSchema(Schema):
    """DataTables-д зориулсан дээжний жагсаалт schema"""

    draw = fields.Int(required=True)
    recordsTotal = fields.Int(required=True)
    recordsFiltered = fields.Int(required=True)
    data = fields.List(fields.Dict())

    class Meta:
        ordered = True
