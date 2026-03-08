# -*- coding: utf-8 -*-
"""
Analysis audit models.
"""

from app import db
from app.models.mixins import HashableMixin
from app.utils.datetime import now_local as now_mn

class AnalysisResultLog(HashableMixin, db.Model):
    """
    Шинжилгээний үр дүнгийн түүх/лог (Audit trail - ISO 17025).

    Үр дүн өөрчлөгдөх бүрийн түүх, хэн юу хийсэн, хэзээ хийсэн,
    буцаалтын шалтгааныг бүртгэнэ. Өөрчлөлтийг буцаах боломжгүй.

    Attributes:
        id (int): Primary key
        timestamp (datetime): Үйлдэл хийсэн огноо/цаг (Монгол цаг)
        user_id (int): Foreign key → User (хэн хийсэн)
        sample_id (int): Foreign key → Sample
        analysis_result_id (int): Foreign key → AnalysisResult
        analysis_code (str): Шинжилгээний код
        action (str): Үйлдэл ('created', 'updated', 'approved', 'rejected', 'reanalysis')
        raw_data_snapshot (str): Анхны өгөгдлийн snapshot (JSON)
        final_result_snapshot (float): Үр дүнгийн snapshot
        rejection_category (str): Буцаалтын ангилал
        rejection_subcategory (str): Буцаалтын дэд ангилал
        reason (str): Шалтгаан, тайлбар
        error_reason (str): Алдааны шалтгаан (KPI)

    Relationships:
        user: Many-to-one → User
        result: Many-to-one → AnalysisResult

    Action values:
        - created: Шинээр үүсгэсэн
        - updated: Засварласан
        - approved: Баталгаажуулсан
        - rejected: Буцаасан
        - reanalysis: Дахин шинжилгээ

    Example:
        >>> log = AnalysisResultLog(
        ...     user_id=current_user.id,
        ...     sample_id=sample.id,
        ...     analysis_result_id=result.id,
        ...     analysis_code='Mad',
        ...     action='approved'
        ... )

    Security:
        - Бүртгэл устгах, засах боломжгүй (audit trail)
        - SET NULL: Sample эсвэл Result устахад log үлдэнэ (sample_id, analysis_result_id = NULL)
        - Hash checksum: Өөрчлөгдсөн эсэхийг шалгах боломжтой
    """
    __tablename__ = "analysis_result_log"

    id = db.Column(db.Integer, primary_key=True)

    # Монгол цаг
    timestamp = db.Column(db.DateTime, index=True, default=now_mn, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("logs", lazy="select"))

    # ✅ SET NULL: Sample устахад log үлдэнэ
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", ondelete="SET NULL"),
        index=True,
        nullable=True,  # NULL болох боломжтой
    )
    # ✅ SET NULL: Result устахад log үлдэнэ
    analysis_result_id = db.Column(
        db.Integer,
        db.ForeignKey("analysis_result.id", ondelete="SET NULL"),
        index=True,
        nullable=True,  # NULL болох боломжтой
    )
    analysis_code = db.Column(db.String(50), index=True, nullable=False)

    # ✅ ШИНЭ: Анхны хадгалсан химичийн ID (хэзээ ч өөрчлөгдөхгүй)
    original_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    original_user = db.relationship("User", foreign_keys=[original_user_id])

    # ✅ ШИНЭ: Анхны хадгалсан цаг (хэзээ ч өөрчлөгдөхгүй)
    original_timestamp = db.Column(db.DateTime, nullable=True)

    # ✅ ШИНЭ: Дээжний код хадгалах (sample устсан ч харагдах)
    sample_code_snapshot = db.Column(db.String(100), nullable=True)

    # ✅ ШИНЭ: Hash checksum (өөрчлөгдсөн эсэхийг шалгах)
    data_hash = db.Column(db.String(64), nullable=True)  # SHA-256

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

    # 🛑 ШИНЭ: Алдаа гарч байсан хэсэг
    error_reason = db.Column(db.String(50), nullable=True)

    # Composite indexes - audit log query-уудыг хурдасгах
    __table_args__ = (
        db.Index('ix_result_log_code_timestamp', 'analysis_code', 'timestamp'),
        db.Index('ix_result_log_sample_timestamp', 'sample_id', 'timestamp'),
        db.Index('ix_result_log_user_timestamp', 'user_id', 'timestamp'),
    )

    def _get_hash_data(self) -> str:
        """HashableMixin: Return data string for hashing."""
        return (
            f"{self.sample_id}|{self.analysis_code}|{self.action}|"
            f"{self.raw_data_snapshot}|{self.final_result_snapshot}|{self.timestamp}"
        )

    def __repr__(self) -> str:
        return f"<AnalysisResultLog {self.id}: {self.action}>"


# -------------------------
# БОРТОГО (ПИКНОМЕТР) ТОГТМОЛ
# -------------------------
# TRD шинжилгээнд хэрэглэдэг бортогоны (пикнометр) тогтмолууд.
# Улирал бүр 3 хэмжилтээр хоосон тодорхойлолт хийж, дундаж массыг
# тогтмол болгон хадгална (MNS GB/T 217, 7.4.1–7.4.8).
#
# Моделиуд:  app/models/quality.py → Bottle, BottleConstant
# Routes:    app/routes/settings/routes.py → /settings/bottles/*
# Tolerance: app/constants.py → BOTTLE_TOLERANCE = 0.0015g
# API:       /settings/api/bottle/<serial_no>/active → идэвхтэй тогтмол

# -------------------------
# ТОГТМОЛУУД
# -------------------------

# Audit log action утгууд
AUDIT_ACTIONS = (
    'CREATED',          # Шинээр үүсгэсэн
    'UPDATED',          # Засварласан
    'APPROVED',         # Баталгаажуулсан
    'REJECTED',         # Буцаасан
    'PENDING_REVIEW',   # Хянагдаж буй
    'REANALYSIS',       # Дахин шинжилгээ
)

# Буцаалтын шалтгаан (fallback — DB-д SystemSetting category='error_reason' байхгүй үед)
# Бодит утгууд: SystemSetting.query.filter_by(category='error_reason') → app/utils/settings.py
DEFAULT_ERROR_REASONS = {
    'sample_prep':          '1. Дээж бэлтгэлийн алдаа (Бутлалт/Хуваалт)',
    'measurement':          '2. Шинжилгээний гүйцэтгэлийн алдаа',
    'qc_fail':              '3. QC / Стандарт дээжийн зөрүү',
    'equipment':            '4. Тоног төхөөрөмж / Орчны нөхцөл',
    'data_entry':           '5. Өгөгдөл шивэлт / Тооцооллын алдаа',
    'method':               '6. Арга аргачлал зөрчсөн (SOP)',
    'sample_mixup':         '7. Дээж солигдсон / Буруу дээж',
    'customer_complaint':   '8. Санал гомдол / Хяналтын шинжилгээ',
}
