# app/models/worksheets.py
# -*- coding: utf-8 -*-
"""
Усны лабораторийн ажлын хуудасны модель (Water Lab Worksheet).

ISO 17025 шаардлагын дагуу blank/control/duplicate/spike дээж бүртгэх,
QC bracketing, reagent lot холбох боломжийг хангана.
"""

from app import db
from app.utils.datetime import now_local as now_mn


class WaterWorksheet(db.Model):
    """
    Усны лабораторийн шинжилгээний ажлын хуудас.

    Нэг batch шинжилгээ (≤20 дээж) -ийг нэг worksheet болгон
    бүртгэж, QC статусыг хянана.

    Status values:
        open       — химич нэмэж буй, дуусаагүй
        submitted  — химич хадгалсан, ахлах хянаж буй
        approved   — ахлах батлагаажуулсан
        rejected   — ахлах буцаасан
    """
    __tablename__ = 'water_worksheet'

    id = db.Column(db.Integer, primary_key=True)
    method_code = db.Column(db.String(50), nullable=False, index=True)
    # e.g. 'NH4', 'CL_W', 'TDS', 'SFT', 'MICRO_WATER'

    analysis_date = db.Column(db.Date, nullable=False, default=lambda: now_mn().date())
    analyst_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    status = db.Column(
        db.String(20),
        nullable=False,
        default='open',
        index=True,
    )
    # Batch размер — EPA SW-846: ≤20 тоот дээж нэг batch
    batch_size = db.Column(db.Integer, default=0)

    # Ашигласан урвалжийн lot (гол урвалж)
    primary_reagent_lot_id = db.Column(
        db.Integer, db.ForeignKey('chemical.id'), nullable=True
    )

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_mn)
    updated_at = db.Column(db.DateTime, default=now_mn, onupdate=now_mn)

    # Батлах хүн (ахлах химич)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_comment = db.Column(db.String(500), nullable=True)

    # Relationships
    analyst = db.relationship(
        'User', foreign_keys=[analyst_id],
        backref=db.backref('worksheets_created', passive_deletes=True),
    )
    reviewer = db.relationship(
        'User', foreign_keys=[reviewer_id],
        backref=db.backref('worksheets_reviewed', passive_deletes=True),
    )
    primary_reagent = db.relationship('Chemical', foreign_keys=[primary_reagent_lot_id])
    rows = db.relationship('WorksheetRow', back_populates='worksheet', cascade='all, delete-orphan',
                           order_by='WorksheetRow.position')

    __table_args__ = (
        db.Index('ix_ws_analyst_date', 'analyst_id', 'analysis_date'),
        db.Index('ix_ws_method_date', 'method_code', 'analysis_date'),
    )

    def __repr__(self):
        return f'<WaterWorksheet id={self.id} method={self.method_code} status={self.status}>'

    @property
    def unknown_count(self):
        return sum(1 for r in self.rows if r.row_type == 'unknown')

    @property
    def qc_pass_rate(self):
        qc_rows = [r for r in self.rows if r.row_type != 'unknown']
        if not qc_rows:
            return None
        passed = sum(1 for r in qc_rows if r.qc_status == 'pass')
        return round(passed / len(qc_rows) * 100, 1)


class WorksheetRow(db.Model):
    """
    Ажлын хуудасны нэг мөр.

    row_type утгууд:
        unknown    — шинжилгээний дээж (хэмжих зорилготой)
        blank      — method blank (лабын бохирдол шалгана)
        control    — LCS — мэдэгдэх концентрацийн стандарт
        duplicate  — тохирох дээжийн давхардал (RPD тооцоолно)
        spike      — matrix spike (матрицын нөлөөг шалгана)
        msd        — matrix spike duplicate

    qc_status утгууд:
        pending    — үнэлэгдээгүй
        pass       — хүлээн зөвшөөрөгдсөн
        warn       — анхааруулга (хяналтын хязгаарт ойролцоо)
        fail       — хяналтын хязгаараас гарсан
    """
    __tablename__ = 'worksheet_row'

    id = db.Column(db.Integer, primary_key=True)
    worksheet_id = db.Column(
        db.Integer, db.ForeignKey('water_worksheet.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    position = db.Column(db.Integer, nullable=False)  # мөрийн дараалал

    row_type = db.Column(db.String(20), nullable=False, default='unknown')

    # Дээжтэй холбоо (unknown/duplicate/spike дээж)
    sample_id = db.Column(
        db.Integer, db.ForeignKey('sample.id', ondelete='SET NULL'), nullable=True
    )

    # Шинжилгээний үр дүн
    analysis_result_id = db.Column(
        db.Integer, db.ForeignKey('analysis_result.id', ondelete='SET NULL'), nullable=True
    )

    # QC тооцоолол
    expected_value = db.Column(db.Float)      # хяналтын стандартын мэдэгдэх утга
    result_value = db.Column(db.Float)        # хэмжсэн утга
    recovery_pct = db.Column(db.Float)        # % Recovery = (result / expected) × 100
    rpd_pct = db.Column(db.Float)             # RPD = |r1-r2| / avg × 100

    qc_status = db.Column(db.String(10), nullable=False, default='pending')

    # Ашигласан урвалжийн lot — lot-д асуудал гарвал бүх холбогдох үр дүнг тэмдэглэнэ
    reagent_lot_id = db.Column(
        db.Integer, db.ForeignKey('chemical.id'), nullable=True
    )

    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=now_mn)

    # Relationships
    worksheet = db.relationship('WaterWorksheet', back_populates='rows')
    sample = db.relationship('Sample')
    analysis_result = db.relationship('AnalysisResult')
    reagent_lot = db.relationship('Chemical')

    __table_args__ = (
        db.Index('ix_wr_worksheet_pos', 'worksheet_id', 'position'),
        db.Index('ix_wr_sample', 'sample_id'),
    )

    def __repr__(self):
        return f'<WorksheetRow id={self.id} type={self.row_type} qc={self.qc_status}>'

    def evaluate_qc(self, limits: dict):
        """
        QC статус тооцоолох.

        Args:
            limits: {'recovery_min': 80, 'recovery_max': 120, 'rpd_max': 20}
        """
        if self.row_type == 'unknown':
            return

        self.qc_status = 'pending'

        if self.row_type == 'blank':
            mdl = limits.get('mdl')
            if self.result_value is not None and mdl is not None:
                self.qc_status = 'pass' if self.result_value < mdl else 'fail'

        elif self.row_type in ('control', 'spike', 'msd'):
            if self.result_value is not None and self.expected_value:
                self.recovery_pct = round(self.result_value / self.expected_value * 100, 1)
                lo = limits.get('recovery_min', 80)
                hi = limits.get('recovery_max', 120)
                warn_margin = limits.get('warn_margin', 5)
                if lo <= self.recovery_pct <= hi:
                    if (self.recovery_pct < lo + warn_margin or
                            self.recovery_pct > hi - warn_margin):
                        self.qc_status = 'warn'
                    else:
                        self.qc_status = 'pass'
                else:
                    self.qc_status = 'fail'

        elif self.row_type == 'duplicate':
            if self.rpd_pct is not None:
                rpd_max = limits.get('rpd_max', 20)
                rpd_warn = limits.get('rpd_warn', 15)
                if self.rpd_pct <= rpd_warn:
                    self.qc_status = 'pass'
                elif self.rpd_pct <= rpd_max:
                    self.qc_status = 'warn'
                else:
                    self.qc_status = 'fail'
