# -*- coding: utf-8 -*-
"""
Quality management records.
"""

import json

from sqlalchemy import CheckConstraint, event
from app import db
from app.constants import CorrectiveActionStatus, CorrectiveActionSeverity
from app.models.mixins import HashableMixin
from app.utils.datetime import now_local as now_mn

class CorrectiveAction(db.Model):
    """
    Засвар арга хэмжээ (Corrective and Preventive Actions).

    ISO 17025 - Clause 8.7: Бүх зөрчил, гомдол, дотоод хяналтын үр дүнд
    засвар арга хэмжээ авах шаардлагатай.
    """
    __tablename__ = "corrective_action"

    id = db.Column(db.Integer, primary_key=True)
    ca_number = db.Column(db.String(50), unique=True, nullable=False, index=True)  # CA-2025-001

    # Асуудлын мэдээлэл
    issue_date = db.Column(db.Date, nullable=False, default=now_mn)
    issue_source = db.Column(db.String(100))  # Internal audit, Customer complaint, PT, Equipment
    issue_description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='Minor')  # Critical, Major, Minor

    # Шалтгааны шинжилгээ
    root_cause = db.Column(db.Text)  # 5 Why, Fishbone analysis
    root_cause_method = db.Column(db.String(100))  # 5 Whys, Fishbone, Pareto

    # Арга хэмжээ
    corrective_action = db.Column(db.Text)  # Засах үйлдэл
    preventive_action = db.Column(db.Text)  # Урьдчилан сэргийлэх
    responsible_person_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    target_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)

    # Баталгаажуулалт (хуучин - хэрэглэгдэхгүй ч DB-д үлдэнэ)
    verification_method = db.Column(db.Text)
    verification_date = db.Column(db.Date)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    effectiveness = db.Column(db.String(20))

    # ═══ Хэсэг 2: Хяналт (Техникийн менежер) - LAB.02.00.04 ═══
    completed_on_time = db.Column(db.Boolean)               # Цаг хугацаандаа хийсэн эсэх
    fully_resolved = db.Column(db.Boolean)                   # Бүрэн шийдэгдсэн эсэх
    residual_risk_exists = db.Column(db.Boolean)             # Үлдэгдэл эрсдэл байгаа эсэх
    management_change_needed = db.Column(db.Boolean)         # Удирдлагын тогтолцооны өөрчлөлт шаардлагатай эсэх
    control_notes = db.Column(db.Text)
    control_date = db.Column(db.Date)
    technical_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Төлөв
    status = db.Column(db.String(20), default='open', index=True)  # open, in_progress, reviewed, closed
    notes = db.Column(db.Text)

    __table_args__ = (
        CheckConstraint(
            CorrectiveActionStatus.check_constraint("status"),
            name="ck_corrective_action_status",
        ),
        CheckConstraint(
            CorrectiveActionSeverity.check_constraint("severity"),
            name="ck_corrective_action_severity",
        ),
    )

    # Relationships
    responsible_person = db.relationship('User', foreign_keys=[responsible_person_id], backref='assigned_capas')
    verified_by = db.relationship('User', foreign_keys=[verified_by_id], backref='verified_capas')
    technical_manager = db.relationship('User', foreign_keys=[technical_manager_id], backref='reviewed_capas')

    def __repr__(self):
        return f"<CorrectiveAction {self.ca_number} - {self.status}>"


# -------------------------
# ЧАДАМЖИЙН ШАЛГАЛТ (Proficiency Testing)
# -------------------------
class ProficiencyTest(HashableMixin, db.Model):
    """
    Чадамжийн шалгалт (Proficiency Testing).

    ISO 17025 - Clause 7.7.2: Лаборатори PT программд оролцож,
    үр дүнгээ гадны байгууллагатай харьцуулж чадвараа батлах.

    Append-only: UPDATE/DELETE хориглосон (хадгалагдсан PT result-ийг өөрчлөх
    боломжгүй; шинэ test шалгалт нь шинэ row).
    """
    __tablename__ = "proficiency_test"

    id = db.Column(db.Integer, primary_key=True)

    # PT мэдээлэл
    pt_provider = db.Column(db.String(150))  # ASTM, ISO LEAP, NIST
    pt_program = db.Column(db.String(100))  # Coal PT-2025
    round_number = db.Column(db.String(50))
    sample_code = db.Column(db.String(100))  # PT дээжний код

    # Үр дүн
    analysis_code = db.Column(db.String(50), index=True)
    our_result = db.Column(db.Float)
    assigned_value = db.Column(db.Float)  # Зөвт утга
    uncertainty = db.Column(db.Float)
    z_score = db.Column(db.Float)  # Performance indicator

    # Үнэлгээ
    performance = db.Column(db.String(30))  # satisfactory, questionable, unsatisfactory

    # Огноо
    received_date = db.Column(db.Date)
    test_date = db.Column(db.Date, index=True)
    report_date = db.Column(db.Date)

    # Хавсралт
    certificate_file = db.Column(db.String(255))
    notes = db.Column(db.Text)

    # Хэн шинжилсэн
    tested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    tested_by = db.relationship('User', backref='pt_tests')

    # ISO 17025: Audit log integrity hash
    data_hash = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<PT {self.pt_program} - {self.analysis_code} Z={self.z_score}>"

    def _get_hash_data(self) -> str:
        td = self.test_date.isoformat() if self.test_date else ''
        return (
            f"{self.pt_provider}|{self.pt_program}|{self.round_number}|"
            f"{self.sample_code}|{self.analysis_code}|{self.our_result}|"
            f"{self.assigned_value}|{self.z_score}|{self.performance}|"
            f"{td}|{self.tested_by_id}"
        )


# -------------------------
# ОРЧНЫ НӨХЦЛИЙН ХЯНАЛТ
# -------------------------
class EnvironmentalLog(HashableMixin, db.Model):
    """
    Орчны нөхцлийн бүртгэл (Environmental Monitoring).

    ISO 17025 - Clause 6.3.3: Лабораторийн орчны нөхцөл
    (температур, чийг) үр дүнд нөлөөлж болох тул хянах.

    Append-only: UPDATE/DELETE хориглосон.
    """
    __tablename__ = "environmental_log"

    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.DateTime, default=now_mn, index=True)

    # Байршил
    location = db.Column(db.String(100))  # Sample storage, Analysis room, Furnace room

    # Хэмжилт
    temperature = db.Column(db.Float)  # °C
    humidity = db.Column(db.Float)  # %
    pressure = db.Column(db.Float)  # kPa (optional)

    # Хэвийн хязгаар
    temp_min = db.Column(db.Float)  # Доод хязгаар
    temp_max = db.Column(db.Float)  # Дээд хязгаар
    humidity_min = db.Column(db.Float)
    humidity_max = db.Column(db.Float)

    # Хэвийн эсэх
    within_limits = db.Column(db.Boolean, default=True)

    # Бүртгэсэн хүн
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    recorded_by = db.relationship('User', backref='env_logs')

    notes = db.Column(db.Text)

    # ISO 17025: Audit log integrity hash
    data_hash = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<EnvLog {self.location} T={self.temperature}°C RH={self.humidity}%>"

    def _get_hash_data(self) -> str:
        ld = self.log_date.strftime('%Y-%m-%d %H:%M:%S.%f') if self.log_date else ''
        return (
            f"{ld}|{self.location}|{self.temperature}|{self.humidity}|"
            f"{self.pressure}|{self.within_limits}|{self.recorded_by_id}"
        )


# -------------------------
# ЧАНАРЫН ХЯНАЛТЫН ГРАФИК (Control Chart)
# -------------------------
class QCControlChart(HashableMixin, db.Model):
    """
    Чанарын хяналтын график өгөгдөл.

    ISO 17025 - Clause 7.7.1: QC дээж тогтмол шинжлэж,
    control chart-аар системийн чанарыг хянах.

    Append-only: UPDATE/DELETE хориглосон (QC measurement-ийг өөрчлөх боломжгүй).
    """
    __tablename__ = "qc_control_chart"

    id = db.Column(db.Integer, primary_key=True)

    # QC дээж
    analysis_code = db.Column(db.String(50), index=True)
    qc_sample_name = db.Column(db.String(100))  # QC Coal Standard A

    # Хяналтын хязгаар
    target_value = db.Column(db.Float)  # Зорилтот утга
    ucl = db.Column(db.Float)  # Upper control limit (target + 2*sd)
    lcl = db.Column(db.Float)  # Lower control limit (target - 2*sd)
    usl = db.Column(db.Float)  # Upper spec limit (optional)
    lsl = db.Column(db.Float)  # Lower spec limit

    # Хэмжилт
    measurement_date = db.Column(db.Date, index=True)
    measured_value = db.Column(db.Float)
    in_control = db.Column(db.Boolean, default=True)  # UCL/LCL дотор уу?

    # Operator
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    operator = db.relationship('User', backref='qc_measurements')

    # Тэмдэглэл
    notes = db.Column(db.Text)

    # ISO 17025: Audit log integrity hash
    data_hash = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<QC {self.analysis_code} - {self.qc_sample_name} = {self.measured_value}>"

    def _get_hash_data(self) -> str:
        md = self.measurement_date.isoformat() if self.measurement_date else ''
        return (
            f"{self.analysis_code}|{self.qc_sample_name}|{self.target_value}|"
            f"{self.ucl}|{self.lcl}|{md}|{self.measured_value}|"
            f"{self.in_control}|{self.operator_id}"
        )


# ──────────────────────────────────────────
# Append-only enforcement (ISO 17025 audit trail)
# ──────────────────────────────────────────

def _block_quality_log_update(mapper, connection, target):
    raise RuntimeError(
        f"AUDIT INTEGRITY: {type(target).__name__} #{target.id} cannot be modified. "
        "Quality audit records are append-only (ISO 17025)."
    )


def _block_quality_log_delete(mapper, connection, target):
    raise RuntimeError(
        f"AUDIT INTEGRITY: {type(target).__name__} #{target.id} cannot be deleted. "
        "Quality audit records are append-only (ISO 17025)."
    )


event.listen(ProficiencyTest, "before_update", _block_quality_log_update)
event.listen(ProficiencyTest, "before_delete", _block_quality_log_delete)
event.listen(EnvironmentalLog, "before_update", _block_quality_log_update)
event.listen(EnvironmentalLog, "before_delete", _block_quality_log_delete)
event.listen(QCControlChart, "before_update", _block_quality_log_update)
event.listen(QCControlChart, "before_delete", _block_quality_log_delete)


# -------------------------
# ҮЙЛЧЛҮҮЛЭГЧИЙН ГОМДОЛ
# -------------------------
class CustomerComplaint(db.Model):
    """
    Санал гомдлын бүртгэл (LAB.02.00.01).

    ISO 17025 - Clause 7.9: Бүх санал гомдлыг бүртгэж, шалтгааныг
    олж, шийдвэрлэх ёстой.
    """
    __tablename__ = "customer_complaint"

    id = db.Column(db.Integer, primary_key=True)
    complaint_no = db.Column(db.String(50), unique=True, index=True)  # COMP-2025-001
    complaint_date = db.Column(db.Date, nullable=False, default=now_mn)

    # ═══ Хэсэг 1: Санал гомдол гаргагч ═══
    complainant_name = db.Column(db.String(200))          # Овог, нэр, албан тушаал
    complainant_department = db.Column(db.String(200))     # Хэсэг, нэгж
    complaint_content = db.Column(db.Text)                 # Агуулга, тайлбар, баримт
    complainant_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)  # Гарын үсэг

    # ═══ Хэсэг 2: Хүлээн авагч ═══
    receiver_name = db.Column(db.String(200))              # Овог, нэр, албан тушаал
    action_taken = db.Column(db.Text)                      # Хэрэгжүүлсэн арга хэмжээ
    receiver_documentation = db.Column(db.Text)            # Баримтжуулсан материал
    is_justified = db.Column(db.Boolean)                   # Үндэслэлтэй эсэх
    response_detail = db.Column(db.Text)                   # Хариу өгсөн байдал
    receiver_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)  # Гарын үсэг

    # ═══ Хэсэг 3: Хяналт (Чанарын менежер) ═══
    action_corrective = db.Column(db.Boolean, default=False)       # Залруулах
    action_improvement = db.Column(db.Boolean, default=False)      # Сайжруулах
    action_partial_audit = db.Column(db.Boolean, default=False)    # Хэсэгчилсэн аудит
    quality_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # ═══ Дахин шинжилгээ ═══
    reanalysis_codes = db.Column(db.Text)               # JSON list: ["Mad", "Aad"]
    original_results_snapshot = db.Column(db.Text)       # JSON dict: {"Mad": {"final_result": 8.5, "analysis_result_id": 123}}

    # Legacy fields (хуучин өгөгдөлд зориулсан)
    client_name = db.Column(db.String(200))
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))
    complaint_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    related_sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete="SET NULL"), index=True)
    investigated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    investigation_findings = db.Column(db.Text)
    resolution = db.Column(db.Text)
    resolution_date = db.Column(db.Date)
    customer_notified = db.Column(db.Boolean, default=False)
    customer_satisfied = db.Column(db.Boolean)
    capa_created = db.Column(db.Boolean, default=False)
    capa_id = db.Column(db.Integer, db.ForeignKey('corrective_action.id'), index=True)

    # Төлөв
    status = db.Column(db.String(20), default='draft', index=True)
    # draft → received → resolved → closed

    # Relationships
    complainant_user = db.relationship('User', foreign_keys=[complainant_user_id], backref='filed_complaints')
    receiver_user = db.relationship('User', foreign_keys=[receiver_user_id], backref='received_complaints')
    quality_manager = db.relationship('User', foreign_keys=[quality_manager_id], backref='signed_complaints')
    investigated_by = db.relationship('User', foreign_keys=[investigated_by_id])
    related_sample = db.relationship('Sample', backref='complaints')
    related_capa = db.relationship('CorrectiveAction', backref='source_complaints')

    def get_reanalysis_codes(self):
        if self.reanalysis_codes:
            try:
                return json.loads(self.reanalysis_codes)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_reanalysis_codes(self, codes):
        self.reanalysis_codes = json.dumps(codes) if codes else None

    def get_original_results_snapshot(self):
        if self.original_results_snapshot:
            try:
                return json.loads(self.original_results_snapshot)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def set_original_results_snapshot(self, data):
        self.original_results_snapshot = json.dumps(data) if data else None

    def __repr__(self):
        return f"<Complaint {self.complaint_no} - {self.status}>"


class ImprovementRecord(db.Model):
    """
    Improvementын бүртгэл (LAB.02.00.03).

    ISO 17025 - Clause 8.6: Тасралтгүй сайжруулалт.
    """
    __tablename__ = "improvement_record"

    id = db.Column(db.Integer, primary_key=True)
    record_no = db.Column(db.String(50), unique=True, index=True)  # IMP-2026-0001
    record_date = db.Column(db.Date, nullable=False, default=now_mn)

    # ═══ Хэсэг 1: Ажилтны бөглөх хэсэг ═══
    activity_description = db.Column(db.Text)              # Сайжруулах шаардлагатай үйл ажиллагаа
    improvement_plan = db.Column(db.Text)                  # Арга хэмжээний төлөвлөгөө
    deadline = db.Column(db.Date)                          # Хугацаа
    responsible_person = db.Column(db.String(200))         # Хариуцах ажилтан
    documentation = db.Column(db.Text)                     # Баримтжуулалт, нэмэлт тайлбар
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Эх үүсвэр (санал гомдлоос автомат үүссэн бол)
    source_complaint_id = db.Column(db.Integer, db.ForeignKey('customer_complaint.id'), index=True)

    # ═══ Хэсэг 2: Хяналт (Техникийн менежер) ═══
    completed_on_time = db.Column(db.Boolean)              # Тогтсон хугацаанд сайжруулсан эсэх
    fully_implemented = db.Column(db.Boolean)              # Бүрэн хэрэгжсэн эсэх
    control_notes = db.Column(db.Text)                     # Нэмэлт тайлбар
    control_date = db.Column(db.Date)                      # Огноо
    technical_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Төлөв
    status = db.Column(db.String(20), default='pending', index=True)
    # pending → in_progress → reviewed → closed

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='improvement_records')
    technical_manager = db.relationship('User', foreign_keys=[technical_manager_id], backref='reviewed_improvements')
    source_complaint = db.relationship('CustomerComplaint', backref='improvement_records')

    def __repr__(self):
        return f"<Improvement {self.record_no} - {self.status}>"


class NonConformityRecord(db.Model):
    """
    Nonconformity / үл тохирох ажлын бүртгэл (LAB.10.00.01).

    ISO 17025 - Clause 7.10: Үл тохирох ажлын удирдлага.
    """
    __tablename__ = "nonconformity_record"

    id = db.Column(db.Integer, primary_key=True)
    record_no = db.Column(db.String(50), unique=True, index=True)  # NC-2026-0001
    record_date = db.Column(db.Date, nullable=False, default=now_mn)

    # ═══ Хэсэг 1: Илрүүлсэн ажилтан ═══
    detector_name = db.Column(db.String(200))              # Овог, нэр, албан тушаал
    detector_department = db.Column(db.String(200))        # Хэсэг, нэгж
    nc_description = db.Column(db.Text)                    # Мэдээлэл, баримт
    proposed_action = db.Column(db.Text)                   # Авах арга хэмжээний санал
    detector_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # ═══ Хэсэг 2: Хариуцсан нэгж ═══
    responsible_unit = db.Column(db.String(200))           # Хариуцах нэгж/хэсэг
    responsible_person = db.Column(db.String(200))         # Нэр, албан тушаал
    direct_cause = db.Column(db.Text)                      # Шууд шалтгаан
    corrective_action = db.Column(db.Text)                 # Залруулах арга хэмжээ
    corrective_deadline = db.Column(db.Date)               # Хугацаа
    root_cause = db.Column(db.Text)                        # Суурь шалтгаан
    corrective_plan = db.Column(db.Text)                   # Төлөвлөгөө, баримтжуулалт
    responsible_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # ═══ Хэсэг 3: Хяналт ═══
    completed_on_time = db.Column(db.Boolean)              # Тогтсон хугацаанд залруулсан эсэх
    fully_implemented = db.Column(db.Boolean)              # Бүрэн хэрэгжсэн эсэх
    control_notes = db.Column(db.Text)                     # Нэмэлт тайлбар
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Төлөв
    status = db.Column(db.String(20), default='pending', index=True)
    # pending → investigating → reviewed → closed

    # Relationships
    detector_user = db.relationship('User', foreign_keys=[detector_user_id], backref='detected_nonconformities')
    responsible_user = db.relationship('User', foreign_keys=[responsible_user_id], backref='responsible_nonconformities')
    manager = db.relationship('User', foreign_keys=[manager_id], backref='reviewed_nonconformities')

    def __repr__(self):
        return f"<NonConformity {self.record_no} - {self.status}>"
