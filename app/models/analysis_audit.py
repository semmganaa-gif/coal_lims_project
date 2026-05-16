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

    # SET NULL: User устсан ч audit history үлдэнэ (ISO 17025 immutable trail).
    # Архивлагдсан user тэмдэглэгээ original_user_id-д хэвээр хадгалагдана.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user = db.relationship(
        "User", foreign_keys=[user_id],
        backref=db.backref("logs", lazy="select", passive_deletes=True),
    )

    # SET NULL: Sample устахад log үлдэнэ
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", ondelete="SET NULL"),
        index=True,
        nullable=True,  # NULL болох боломжтой
    )
    # SET NULL: Result устахад log үлдэнэ
    analysis_result_id = db.Column(
        db.Integer,
        db.ForeignKey("analysis_result.id", ondelete="SET NULL"),
        index=True,
        nullable=True,  # NULL болох боломжтой
    )
    analysis_code = db.Column(db.String(50), index=True, nullable=False)

    # Анхны хадгалсан химичийн ID (хэзээ ч өөрчлөгдөхгүй).
    # SET NULL: User устсан ч анхны бүртгэлийн контекст үлдэнэ.
    original_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    original_user = db.relationship("User", foreign_keys=[original_user_id])

    # Анхны хадгалсан цаг (хэзээ ч өөрчлөгдөхгүй)
    original_timestamp = db.Column(db.DateTime, nullable=True)

    # Дээжний код хадгалах (sample устсан ч харагдах)
    sample_code_snapshot = db.Column(db.String(100), nullable=True)

    # Hash checksum (өөрчлөгдсөн эсэхийг шалгах)
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

    # KPI алдааны шалтгаан
    error_reason = db.Column(db.String(50), nullable=True)

    # ISO 17025: Хэн хаанаас хийсэн бүртгэл
    ip_address = db.Column(db.String(50), nullable=True)        # Хэрэглэгчийн IP
    source_endpoint = db.Column(db.String(200), nullable=True)  # API endpoint / route

    # Before/after — өмнөх утга (ChatGPT зөвлөмж #4)
    previous_value = db.Column(db.Float, nullable=True)  # Өөрчлөлтийн өмнөх final_result

    # Status transition tracking (ChatGPT P0: old/new status)
    old_status = db.Column(db.String(50), nullable=True)   # Өмнөх status
    new_status = db.Column(db.String(50), nullable=True)   # Шинэ status

    # Composite indexes - audit log query-уудыг хурдасгах
    __table_args__ = (
        db.Index('ix_result_log_code_timestamp', 'analysis_code', 'timestamp'),
        db.Index('ix_result_log_sample_timestamp', 'sample_id', 'timestamp'),
        db.Index('ix_result_log_user_timestamp', 'user_id', 'timestamp'),
    )

    def _get_hash_data(self) -> str:
        """HashableMixin: Return data string for hashing.

        ChatGPT P0: Бүх critical metadata hash-д оруулах ёстой.
        Өмнө зөвхөн 6 талбар байсан → одоо 14 талбар.
        """
        ts = self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f') if self.timestamp else ''
        ots = self.original_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f') if self.original_timestamp else ''
        return (
            f"{self.user_id}|{self.sample_id}|{self.analysis_code}|{self.action}|"
            f"{self.raw_data_snapshot}|{self.final_result_snapshot}|{ts}|"
            f"{self.reason}|{self.error_reason}|{self.rejection_category}|"
            f"{self.rejection_subcategory}|{self.sample_code_snapshot}|"
            f"{self.original_user_id}|{ots}|{self.ip_address}|{self.source_endpoint}|"
            f"{self.previous_value}|{self.old_status}|{self.new_status}"
        )

    def __repr__(self) -> str:
        return f"<AnalysisResultLog {self.id}: {self.action}>"


# ──────────────────────────────────────────
# Append-only enforcement (ChatGPT P2)
# ──────────────────────────────────────────
# SQLAlchemy event listeners: UPDATE/DELETE хориглох
from sqlalchemy import event


def _block_audit_update(mapper, connection, target):
    """AnalysisResultLog бичлэгийг UPDATE хийхийг хориглоно."""
    raise RuntimeError(
        f"AUDIT INTEGRITY: AnalysisResultLog #{target.id} cannot be modified. "
        "Audit records are append-only."
    )


def _block_audit_delete(mapper, connection, target):
    """AnalysisResultLog бичлэгийг DELETE хийхийг хориглоно."""
    raise RuntimeError(
        f"AUDIT INTEGRITY: AnalysisResultLog #{target.id} cannot be deleted. "
        "Audit records are append-only."
    )


event.listen(AnalysisResultLog, "before_update", _block_audit_update)
event.listen(AnalysisResultLog, "before_delete", _block_audit_delete)


# -------------------------
# БОРТОГО (ПИКНОМЕТР) ТОГТМОЛ
# -------------------------
# TRD шинжилгээнд хэрэглэдэг бортогоны (пикнометр) тогтмолууд.
# Улирал бүр 3 хэмжилтээр хоосон тодорхойлолт хийж, дундаж массыг
# тогтмол болгон хадгална (MNS GB/T 217, 7.4.1–7.4.8).
#
# Моделиуд:  app/models/bottles.py → Bottle, BottleConstant
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
