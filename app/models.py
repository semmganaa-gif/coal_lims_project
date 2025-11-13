# app/models.py
# -*- coding: utf-8 -*-

from app import db
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.types import Date, Text
from sqlalchemy import CheckConstraint
import json

# Монгол цаг
from app.utils.datetime import now_local as now_mn


# -------------------------
# ХЭРЭГЛЭГЧ
# -------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(64), index=True, default="beltgegch")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# -------------------------
# ДЭЭЖ
# -------------------------
class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_code = db.Column(db.String(100), index=True, unique=True)

    # UTC биш, Монгол
    received_date = db.Column(db.DateTime, index=True, default=now_mn)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_sample_user_id"))

    # Танайд өмнө нь "new" жижиг үсгээр явдаг тул хэвээр нь үлдээв
    status = db.Column(db.String(64), default="new", index=True)

    # өмнө нь Date байсан мөртлөө utcnow өгдөг байсан → өдөр л хадгалъя
    sample_date = db.Column(Date, default=lambda: now_mn().date())

    sample_condition = db.Column(db.String(100))
    client_name = db.Column(db.String(200))   # ← CHECK энэ талбарт үйлчилнэ
    sample_type = db.Column(db.String(100))
    analyses_to_perform = db.Column(db.String(500))
    notes = db.Column(Text)
    weight = db.Column(db.Float)
    return_sample = db.Column(db.Boolean, default=False)
    delivered_by = db.Column(db.String(200))
    prepared_by = db.Column(db.String(200))
    prepared_date = db.Column(Date)
    location = db.Column(db.String(100))
    hourly_system = db.Column(db.String(50))
    shift_time = db.Column(db.String(50))
    product = db.Column(db.String(100))

    # 🛑 ШИНЭ: Mass gate талбарууд
    mass_ready = db.Column(db.Boolean, nullable=False, default=False, index=True)
    mass_ready_at = db.Column(db.DateTime, nullable=True)
    mass_ready_by_id = db.Column(db.Integer, nullable=True)  # FK дараа нь хүсвэл нэмэж болно

    # ✅ CHECK CONSTRAINT: Proc нэмэгдсэн хувилбар (SQLite/MySQL/Postgres дээр ажиллана)
    __table_args__ = (
        CheckConstraint(
            "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')",
            name="ck_sample_client_name",
        ),
    )

    results = db.relationship(
        "AnalysisResult",
        backref="sample",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # 🛑 ШИНЭ: Туслах property
    @property
    def is_mass_ready(self) -> bool:
        return bool(self.mass_ready)

    def get_calculations(self):
        if not hasattr(self, "_calculations_cache"):
            self._calculations_cache = SampleCalculations(self)
        return self._calculations_cache

    def __repr__(self):
        return f"<Sample {self.sample_code}>"


# -------------------------
# ҮР ДҮН
# -------------------------
class AnalysisResult(db.Model):
    __tablename__ = "analysis_result"
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("sample.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    analysis_code = db.Column(db.String(50), index=True, nullable=False)
    final_result = db.Column(db.Float)
    raw_data = db.Column(db.Text)

    status = db.Column(
        db.String(50),
        server_default="pending_review",
        index=True,
        nullable=False,
    )

    # ISO буцаалт
    rejection_category = db.Column(db.String(100))
    rejection_subcategory = db.Column(db.String(100))
    rejection_comment = db.Column(db.String(255))

    # Монгол цаг
    created_at = db.Column(db.DateTime, index=True, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    logs = db.relationship(
        "AnalysisResultLog",
        back_populates="result",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisResultLog.timestamp)",
    )

    def set_raw_data(self, data_dict):
        self.raw_data = json.dumps(data_dict)

    def get_raw_data(self):
        if self.raw_data:
            try:
                return json.loads(self.raw_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def __repr__(self):
        return f"<AnalysisResult {self.id}>"


# -------------------------
# ШИНЖИЛГЭЭНИЙ ТӨРӨЛ
# -------------------------
class AnalysisType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order_num = db.Column(db.Integer, default=100)
    required_role = db.Column(
        db.String(64), default="himich", index=True, nullable=False
    )

    def __repr__(self):
        return f"<AnalysisType {self.name}>"


# -------------------------
# ПРОФАЙЛ (simple / pattern)
# -------------------------
class AnalysisProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_type = db.Column(db.String(50), nullable=False, index=True)
    client_name = db.Column(db.String(200), index=True)
    sample_type = db.Column(db.String(100), index=True)
    pattern = db.Column(db.String(200), index=True)
    analyses = db.Column(Text, default="[]")

    def set_analyses(self, analysis_codes):
        self.analyses = json.dumps(analysis_codes)

    def get_analyses(self):
        return json.loads(self.analyses)

    def __repr__(self):
        if self.profile_type == "simple":
            return f"<Profile {self.client_name} - {self.sample_type}>"
        else:
            return f"<Profile Pattern: {self.pattern}>"


# -------------------------
# ТООЦООЛОЛ
# -------------------------
class SampleCalculations:
    def __init__(self, sample):
        self.inputs = {res.analysis_code: res.final_result for res in sample.results}
        self.mt = self.inputs.get("MT")
        self.mad = self.inputs.get("Mad")
        self.aad = self.inputs.get("Aad")
        self.vad = self.inputs.get("Vad")
        self.cv_ad = self.inputs.get("CV")
        self.ts_ad = self.inputs.get("TS")
        self.trd_ad = self.inputs.get("TRD")
        self.p_ad = self.inputs.get("P")
        self.csn = self.inputs.get("CSN")
        self.gi = self.inputs.get("Gi")
        self.x = self.inputs.get("X")
        self.y = self.inputs.get("Y")
        self.h_ad = self.inputs.get("Had")

    def _calculate_conversion(self, param_code, conversion_type):
        param_value_map = {
            "Aad": self.aad,
            "Vad": self.vad,
            "CV": self.cv_ad,
            "TS": self.ts_ad,
            "TRD": self.trd_ad,
            "P": self.p_ad,
        }
        param_ad = param_value_map.get(param_code)
        if param_ad is None or self.mad is None:
            return None
        if conversion_type == "dry":
            if (100 - self.mad) == 0:
                return None
            return param_ad * (100 / (100 - self.mad))
        if conversion_type == "ar":
            if self.mt is None:
                return None
            if (100 - self.mad) == 0:
                return None
            return param_ad * ((100 - self.mt) / (100 - self.mad))
        return None

    @property
    def ash_dry(self):
        return self._calculate_conversion("Aad", "dry")

    @property
    def ash_ar(self):
        return self._calculate_conversion("Aad", "ar")

    @property
    def volatiles_dry(self):
        return self._calculate_conversion("Vad", "dry")

    @property
    def volatiles_ar(self):
        return self._calculate_conversion("Vad", "ar")

    @property
    def volatiles_daf(self):
        v_dry = self.volatiles_dry
        a_dry = self.ash_dry
        if v_dry is None or a_dry is None:
            return None
        if (100 - a_dry) == 0:
            return None
        return v_dry * (100 / (100 - a_dry))

    @property
    def fc_ad(self):
        if self.aad is None or self.vad is None:
            return None
        return 100 - self.aad - self.vad

    @property
    def fc_dry(self):
        a_dry = self.ash_dry
        v_dry = self.volatiles_dry
        if a_dry is None or v_dry is None:
            return None
        return 100 - a_dry - v_dry

    @property
    def fc_ar(self):
        if self.mt is None or self.ash_ar is None or self.volatiles_ar is None:
            return None
        return 100 - self.mt - self.ash_ar - self.volatiles_ar

    @property
    def cv_dry(self):
        return self._calculate_conversion("CV", "dry")

    @property
    def cv_ar(self):
        return self._calculate_conversion("CV", "ar")

    @property
    def cv_daf(self):
        cv_dry_val = self.cv_dry
        ash_dry_val = self.ash_dry
        if cv_dry_val is None or ash_dry_val is None:
            return None
        if (100 - ash_dry_val) == 0:
            return None
        return cv_dry_val * (100 / (100 - ash_dry_val))

    @property
    def qnet_ar(self):
        return None

    @property
    def ts_dry(self):
        return self._calculate_conversion("TS", "dry")

    @property
    def ts_ar(self):
        return self._calculate_conversion("TS", "ar")

    @property
    def trd_dry(self):
        return self._calculate_conversion("TRD", "dry")

    @property
    def trd_ar(self):
        return self._calculate_conversion("TRD", "ar")

    @property
    def p_dry(self):
        return self._calculate_conversion("P", "dry")

    @property
    def p_ar(self):
        return self._calculate_conversion("P", "ar")


# -------------------------
# ҮР ДҮН – ЛОГ
# -------------------------
class AnalysisResultLog(db.Model):
    __tablename__ = "analysis_result_log"
    id = db.Column(db.Integer, primary_key=True)

    # Монгол цаг
    timestamp = db.Column(db.DateTime, index=True, default=now_mn, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("logs", lazy="dynamic"))

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_result_id = db.Column(
        db.Integer,
        db.ForeignKey("analysis_result.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_code = db.Column(db.String(50), index=True, nullable=False)

    result = db.relationship(
        "AnalysisResult",
        back_populates="logs",
        foreign_keys=[analysis_result_id],
    )

    action = db.Column(db.String(50), index=True, nullable=False)
    raw_data_snapshot = db.Column(db.Text)
    final_result_snapshot = db.Column(db.Float, nullable=True)

    rejection_category = db.Column(db.String(100))
    rejection_subcategory = db.Column(db.String(100))
    reason = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<AnalysisResultLog {self.id}: {self.action}>"


# -------------------------
# 🆕 БОРТОГО / ТОГТМОЛ
# -------------------------
class Bottle(db.Model):
    __tablename__ = "bottle"
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(64), unique=True, index=True, nullable=False)  # ж: PY-001
    label = db.Column(db.String(64))                                               # ж: "#1" (заавал биш)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("1"))

    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    constants = db.relationship(
        "BottleConstant", backref="bottle", lazy="dynamic", cascade="all, delete-orphan"
    )


class BottleConstant(db.Model):
    __tablename__ = "bottle_constant"
    id = db.Column(db.Integer, primary_key=True)
    bottle_id = db.Column(db.Integer, db.ForeignKey("bottle.id"), index=True, nullable=False)

    trial_1 = db.Column(db.Float, nullable=False)
    trial_2 = db.Column(db.Float, nullable=False)
    # 🆕 optional болгосон (хуучин миграци дээр nullable=False байсан бол дараагийн миграциар өөрчилнө)
    trial_3 = db.Column(db.Float, nullable=True)
    avg_value = db.Column(db.Float, nullable=False, index=True)

    temperature_c = db.Column(db.Float, nullable=False, server_default="20")
    effective_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    effective_to = db.Column(db.DateTime)

    remarks = db.Column(db.String(255))
    approved_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    approved_at = db.Column(db.DateTime)

    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def is_active_now(self, ref=None):
        from datetime import datetime as _dt
        ref = ref or _dt.utcnow()
        if self.effective_to is not None and ref >= self.effective_to:
            return False
        return self.effective_from <= ref and self.approved_at is not None

    def __repr__(self):
        return f"<BottleConst b#{self.bottle_id} avg={self.avg_value:.5f} @ {self.temperature_c}°C>"
