# -*- coding: utf-8 -*-
"""
Analysis models.
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from app import db
from app.utils.datetime import now_local as now_mn
from app.models.mixins import FLOAT_EPSILON

class AnalysisResult(db.Model):
    """
    Шинжилгээний үр дүнгийн модель (ISO 17025 compliance).

    Нэг дээжний нэг шинжилгээний үр дүн, анхны өгөгдөл, статус,
    буцаалтын мэдээллийг хадгална. Audit trail-тэй.

    Attributes:
        id (int): Primary key
        sample_id (int): Foreign key → Sample
        user_id (int): Foreign key → User (шинжилгээ хийсэн хүн)
        analysis_code (str): Шинжилгээний код (ж: "Mad", "Aad", "CV")
        final_result (float): Эцсийн үр дүн (тоон утга)
        raw_data (str): Анхны өгөгдөл (JSON string)
        reason (str): Тайлбар, шалтгаан
        status (str): Төлөв ('pending_review', 'approved', 'rejected', 'reanalysis')
        rejection_category (str): Буцаалтын ангилал (ISO 17025)
        rejection_subcategory (str): Буцаалтын дэд ангилал
        rejection_comment (str): Буцаалтын тайлбар
        error_reason (str): Алдааны шалтгаан (KPI шинжилгээнд)
        created_at (datetime): Үүсгэсэн огноо (Монгол цаг)
        updated_at (datetime): Сүүлд засварласан огноо (Монгол цаг)

    Relationships:
        sample: Many-to-one → Sample (backref)
        logs: One-to-many → AnalysisResultLog (audit trail)

    Status values:
        - pending_review: Шалгалт хүлээж байна
        - approved: Баталгаажсан
        - rejected: Буцаагдсан
        - reanalysis: Дахин шинжилгээ хийх

    Example:
        >>> result = AnalysisResult(
        ...     sample_id=1,
        ...     analysis_code='Mad',
        ...     final_result=8.5,
        ...     status='pending_review'
        ... )
        >>> result.set_raw_data({'m1': 50.0, 'm2': 45.9})
    """
    __tablename__ = "analysis_result"

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("sample.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    analysis_code = db.Column(db.String(50), index=True, nullable=False)
    final_result = db.Column(db.Numeric(12, 4))
    raw_data = db.Column(db.Text)
    reason = db.Column(db.Text, nullable=True)  # Тайлбар

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

    # 🛑 KPI Алдааны шалтгаан
    error_reason = db.Column(db.String(50), nullable=True)

    # CH-3: Optimistic locking — concurrent edit detection
    version_id = db.Column(db.Integer, nullable=False, default=1)

    # Монгол цаг
    created_at = db.Column(db.DateTime, index=True, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    # CH-1: UNIQUE constraint — нэг дээжинд нэг шинжилгээний код давхардахгүй
    # Composite indexes - түгээмэл query-уудыг хурдасгах
    __table_args__ = (
        UniqueConstraint('sample_id', 'analysis_code', name='uq_sample_analysis_code'),
        CheckConstraint(
            "status IN ('pending_review','approved','rejected','reanalysis')",
            name="ck_analysis_result_status",
        ),
        db.Index('ix_analysis_result_sample_status', 'sample_id', 'status'),
        db.Index('ix_analysis_result_code_status', 'analysis_code', 'status'),
        db.Index('ix_analysis_result_user_code', 'user_id', 'analysis_code'),
    )

    __mapper_args__ = {
        'version_id_col': version_id
    }

    logs = db.relationship(
        "AnalysisResultLog",
        back_populates="result",
        lazy="select",
        cascade="save-update, merge",
        passive_deletes=True,
        order_by="desc(AnalysisResultLog.timestamp)",
    )

    # User relationship (шинжилгээ хийсэн хүн)
    user = db.relationship("User", foreign_keys=[user_id], backref="analysis_results")

    # Note: sample relationship нь Sample.results backref-ээс ирнэ

    def set_raw_data(self, data_dict: Dict[str, Any]) -> None:
        """
        Анхны өгөгдлийг JSON болгож хадгална.

        Args:
            data_dict (dict): Анхны өгөгдөл (жишээ: {'m1': 50.0, 'm2': 45.9})

        Example:
            >>> result.set_raw_data({'m1': 50.0, 'm2': 45.9, 'm_dry': 8.5})
        """
        self.raw_data = json.dumps(data_dict)

    def get_raw_data(self) -> Dict[str, Any]:
        """
        JSON string-ийг Python dict болгож буцаана.

        Returns:
            dict: Анхны өгөгдөл. Алдаа гарвал хоосон dict {}.

        Example:
            >>> data = result.get_raw_data()
            >>> m1 = data.get('m1')
        """
        if self.raw_data:
            try:
                return json.loads(self.raw_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def __repr__(self) -> str:
        return f"<AnalysisResult {self.id}>"


# -------------------------
# ШИНЖИЛГЭЭНИЙ ТӨРӨЛ
# -------------------------
class AnalysisType(db.Model):
    """
    Шинжилгээний төрлүүдийн бүртгэл.

    Системд ашиглагдах шинжилгээнүүдийн жагсаалт, дараалал,
    шаардагдах эрхийг хадгална.

    Attributes:
        id (int): Primary key
        code (str): Шинжилгээний өвөрмөц код (ж: "Mad", "Aad", "CV")
        name (str): Шинжилгээний нэр (ж: "Чийг (агаарын)")
        order_num (int): Жагсаалт дахь дараалал (default: 100)
        required_role (str): Шаардлагатай эрх (default: "chemist")

    Example:
        >>> analysis = AnalysisType(
        ...     code='Mad',
        ...     name='Чийг (агаарын)',
        ...     order_num=10,
        ...     required_role='chemist'
        ... )
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order_num = db.Column(db.Integer, default=100)
    required_role = db.Column(
        db.String(64), default="chemist", index=True, nullable=False
    )
    lab_type = db.Column(db.String(20), default='coal', index=True)  # 'coal', 'petrography', 'water'

    def __repr__(self) -> str:
        return f"<AnalysisType {self.name}>"


# -------------------------
# ПРОФАЙЛ (simple / pattern)
# -------------------------
class AnalysisProfile(db.Model):
    """
    Шинжилгээний профайл (автомат шинжилгээ сонгох).

    Дээжний client_name + sample_type эсвэл sample_code pattern-аар
    автоматаар шинжилгээ сонгох тохиргоо.

    Attributes:
        id (int): Primary key
        profile_type (str): Төрөл ('simple' эсвэл 'pattern')
        client_name (str): Захиалагч (simple тохиргоонд)
        sample_type (str): Дээжний төрөл (simple тохиргоонд)
        pattern (str): Regex загвар (pattern тохиргоонд, ж: "^CC_.*")
        analyses_json (str): Шинжилгээний жагсаалт (JSON string)
        priority (int): Эрэмбэлэх ач холбогдол (default: 50)
        match_rule (str): Давхцах дүрэм ('merge' эсвэл 'replace')

    Profile Types:
        - simple: Client name + Sample type таарах (ж: CHPP + 2 hourly)
        - pattern: Regex sample_code-той таарах (ж: ^CC_.* → CC дээжнүүд)

    Match Rules:
        - merge: Одоо байгаа шинжилгээнүүдтэй нэмж нэгтгэх
        - replace: Бүрэн солих

    Example:
        >>> # Simple profile
        >>> profile = AnalysisProfile(
        ...     profile_type='simple',
        ...     client_name='CHPP',
        ...     sample_type='2 hourly',
        ...     match_rule='replace'
        ... )
        >>> profile.set_analyses(['Mad', 'Aad', 'Vad', 'CV'])
        >>>
        >>> # Pattern profile
        >>> profile2 = AnalysisProfile(
        ...     profile_type='pattern',
        ...     pattern='^CC_.*',
        ...     priority=100
        ... )
    """
    __tablename__ = "analysis_profiles"

    id = db.Column(db.Integer, primary_key=True)

    # Төрөл: 'simple' (Энгийн матриц) эсвэл 'pattern' (Regex)
    profile_type = db.Column(
        db.String(50), nullable=False, index=True, default="simple"
    )

    # Simple тохиргоонд ашиглана
    client_name = db.Column(db.String(200), index=True, nullable=True)
    sample_type = db.Column(db.String(100), index=True, nullable=True)

    # Pattern тохиргоонд ашиглана
    pattern = db.Column(db.String(255), index=True, nullable=True)

    # ✅ analyses_json
    analyses_json = db.Column(db.Text, default="[]")

    priority = db.Column(db.Integer, nullable=True, default=50)

    # match_rule: 'merge' (нэмэх) эсвэл 'replace' (солих)
    match_rule = db.Column(db.String(50), nullable=True, default="merge")

    def set_analyses(self, analysis_codes: List[str]) -> None:
        """
        List-ийг JSON болгож хадгалах.

        Args:
            analysis_codes (list): Шинжилгээний кодуудын жагсаалт
        """
        if isinstance(analysis_codes, list):
            self.analyses_json = json.dumps(analysis_codes)
        else:
            self.analyses_json = "[]"

    def get_analyses(self) -> List[str]:
        """
        JSON string-ийг Python list болгож буцаана.

        Returns:
            list: Шинжилгээний кодуудын жагсаалт
        """
        if not self.analyses_json:
            return []
        try:
            return json.loads(self.analyses_json)
        except (json.JSONDecodeError, TypeError):
            return []

    def __repr__(self) -> str:
        if self.profile_type == "simple":
            return f"<Profile Simple: {self.client_name} - {self.sample_type}>"
        else:
            return f"<Profile Pattern: {self.pattern}>"


class SampleCalculations:
    """
    Нүүрсний шинжилгээний тооцоолол хийх класс.

    Дээжний үр дүнгүүдээс (MT, Mad, Aad гэх мэт) өөр өөр нөхцлийн
    үзүүлэлтүүдийг тооцоолно:
    - Air-dried (ad) → Dry basis (d)
    - Air-dried (ad) → As-received (ar)
    - Dry basis (d) → Dry ash-free (daf)

    Parameters:
        sample (Sample): Тооцоолол хийх дээж

    Attributes:
        inputs (dict): {analysis_code: final_result} dictionary
        mt (float): Total moisture (Нийт чийг)
        mad (float): Moisture air-dried (Агаарын чийг)
        aad (float): Ash air-dried (Үнс air-dried)
        vad (float): Volatile matter air-dried
        cv_ad (float): Calorific value air-dried (Дулааны чанар)
        ts_ad (float): Total sulfur air-dried (Нийт хүхэр)
        trd_ad (float): True relative density
        p_ad (float): Phosphorus (Фосфор)
        csn (float): Crucible swelling number
        gi (float): Gray-King index
        x (float), y (float): Нэмэлт үзүүлэлт
        h_ad (float): Hydrogen (Устөрөгч)

    Methods:
        Олон @property методууд:
        - ash_dry, ash_ar: Үнс (dry/ar)
        - volatiles_dry, volatiles_ar, volatiles_daf: Дэгдэмхий бодис
        - fc_ad, fc_dry, fc_ar: Fixed carbon (Баттай нүүрстөрөгч)
        - cv_dry, cv_ar, cv_daf: Calorific value
        - ts_dry, ts_ar: Total sulfur
        - trd_dry, trd_ar: True relative density
        - p_dry, p_ar: Phosphorus

    Example:
        >>> calc = sample.get_calculations()
        >>> ash_dry = calc.ash_dry  # Үнс (dry basis)
        >>> cv_ar = calc.cv_ar      # Дулааны чанар (as-received)
        >>> fc_dry = calc.fc_dry    # Fixed carbon (dry)

    Notes:
        - FLOAT_EPSILON ашиглан нарийвчлалтай харьцуулалт хийнэ
        - Тооцоолол боломжгүй бол None буцаана
        - Lazy loading: sample.get_calculations() ашиглан дуудна
    """

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
        self.fm = self.inputs.get("FM")

    def _calculate_conversion(self, param_code: str, conversion_type: str) -> Optional[float]:
        """
        Нөхцлийн хувиргалт хийх (ad → dry, ad → ar).

        Args:
            param_code (str): Параметрийн код (Aad, Vad, CV, TS, TRD, P)
            conversion_type (str): Хувиргалтын төрөл ('dry' эсвэл 'ar')

        Returns:
            float, optional: Хувиргасан утга. Тооцоолох боломжгүй бол None.
        """
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
            if abs(100 - self.mad) < FLOAT_EPSILON:
                return None
            return param_ad * (100 / (100 - self.mad))
        if conversion_type == "ar":
            if self.mt is None:
                return None
            if abs(100 - self.mad) < FLOAT_EPSILON:
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
        if abs(100 - a_dry) < FLOAT_EPSILON:
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
        if abs(100 - ash_dry_val) < FLOAT_EPSILON:
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
