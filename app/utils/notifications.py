# app/utils/notifications.py
# -*- coding: utf-8 -*-
"""
Имэйл мэдэгдлийн систем

Төвлөрсөн мэдэгдлийн систем - QC, Sample status, Equipment гэх мэт.
"""

import logging
from typing import List, Optional, Dict, Any
from jinja2 import Environment
from flask_mail import Message
from app import mail, db
from app.models import User, SystemSetting
from app.utils.datetime import now_local

logger = logging.getLogger(__name__)

# Autoescape-тэй Jinja2 environment (XSS хамгаалалт)
_email_env = Environment(autoescape=True)


def _render_email(template_str: str, **kwargs) -> str:
    """render_template_string-ийн оронд autoescape=True-тэй render хийнэ."""
    tmpl = _email_env.from_string(template_str)
    return tmpl.render(**kwargs)


# ============================================================
# ИМЭЙЛ ЗАГВАРУУД
# ============================================================

QC_FAILURE_TEMPLATE = """
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #dc3545;">⚠️ QC Westgard Alert</h2>
    <p>QC шалгалтад Westgard дүрэм зөрчигдсөн байна:</p>

    <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
        <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Шинжилгээ:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ analysis_code }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>QC Дээж:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ qc_sample }}</td>
        </tr>
        <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Статус:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; color: #dc3545;"><strong>{{ status }}</strong></td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Зөрчигдсөн дүрмүүд:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ rules_violated }}</td>
        </tr>
    </table>

    <p style="color: #6c757d; font-size: 12px;">
        Энэ мэдэгдэл Coal LIMS системээс автоматаар илгээгдсэн.
    </p>
</div>
"""

SAMPLE_STATUS_TEMPLATE = """
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: {{ color }};">{{ icon }} Дээжийн статус өөрчлөгдлөө</h2>

    <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
        <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Дээжийн код:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ sample_code }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Шинэ статус:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; color: {{ color }};">
                <strong>{{ new_status }}</strong>
            </td>
        </tr>
        {% if reason %}
        <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Шалтгаан:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ reason }}</td>
        </tr>
        {% endif %}
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Хэн:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ changed_by }}</td>
        </tr>
        <tr style="background: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Огноо:</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ timestamp }}</td>
        </tr>
    </table>

    <p style="color: #6c757d; font-size: 12px;">
        Энэ мэдэгдэл Coal LIMS системээс автоматаар илгээгдсэн.
    </p>
</div>
"""

# Email Signature Template - Energy Resources LLC форматаар
EMAIL_SIGNATURE_TEMPLATE = """
<div style="margin-top: 30px; font-family: Arial, sans-serif; font-size: 12px; color: #333;">
    <p style="margin: 0 0 10px 0;">Regards,</p>

    <p style="margin: 0 0 3px 0; font-weight: bold; color: #1a4480;">
        {{ sender_name }}
    </p>
    <p style="margin: 0 0 15px 0; color: #666;">{{ sender_position }}</p>

    <table style="font-family: Arial, sans-serif; font-size: 11px; color: #333; border-collapse: collapse;">
        <tr>
            <td style="padding: 0; vertical-align: top;">
                <p style="margin: 0 0 3px 0; font-weight: bold; color: #1a4480;">ENERGY RESOURCES LLC</p>
                <p style="margin: 0 0 3px 0; color: #666;">
                    | Ukhaa Khudag Branch, Tsogttsetsii soum, Umnugobi province 46040, MONGOLIA |
                </p>
                <p style="margin: 0 0 3px 0; color: #666;">
                    | Tel.: (976)7012 2279, 7013 2279 | Fax: (976) 11 322279
                    {% if sender_phone %}| Mobile: {{ sender_phone }}{% endif %} |
                </p>
                <p style="margin: 0 0 3px 0;">
                    {% if sender_email %}
                    | <a href="mailto:{{ sender_email }}"
                       style="color: #0066cc; text-decoration: none;">{{ sender_email }}</a> |
                    {% endif %}
                    <a href="http://www.mmc.mn/" style="color: #0066cc; text-decoration: none;">http://www.mmc.mn/</a> |
                </p>
            </td>
        </tr>
    </table>

    <hr style="border: none; border-top: 1px solid #ccc; margin: 15px 0;">

    <p style="margin: 0 0 8px 0; font-size: 10px; color: #666;">
        <em>This email was automatically sent from Coal LIMS (Laboratory Information Management System)</em>
    </p>

    <p style="margin: 0; font-size: 10px; color: #999; font-style: italic;">
        This email is CONFIDENTIAL and is intended only for the use of the person to whom it is addressed.
        Any distribution, copying or other use by anyone else is strictly prohibited.
        If you have received this email in error, please telephone or email us immediately and destroy this email.
    </p>
</div>
"""


EQUIPMENT_CALIBRATION_TEMPLATE = """
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #ffc107;">🔧 Тоног төхөөрөмжийн калибровкийн сануулга</h2>

    <p>Дараах тоног төхөөрөмжийн калибровкийн хугацаа дөхөж байна:</p>

    <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
        <tr style="background: #343a40; color: white;">
            <th style="padding: 10px; border: 1px solid #dee2e6;">Нэр</th>
            <th style="padding: 10px; border: 1px solid #dee2e6;">Дараагийн калибровк</th>
            <th style="padding: 10px; border: 1px solid #dee2e6;">Үлдсэн хоног</th>
        </tr>
        {% for eq in equipment_list %}
        <tr style="{{ 'background: #fff3cd;' if eq.days_left <= 7 else '' }}">
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ eq.name }}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{{ eq.next_calibration }}</td>
            <td style="padding: 10px; border: 1px solid #dee2e6;
                color: {{ '#dc3545' if eq.days_left <= 7 else '#28a745' }};">
                <strong>{{ eq.days_left }} хоног</strong></td>
        </tr>
        {% endfor %}
    </table>

    <p style="color: #6c757d; font-size: 12px;">
        Энэ мэдэгдэл Coal LIMS системээс автоматаар илгээгдсэн.
    </p>
</div>
"""


# ============================================================
# МЭДЭГДЛИЙН ФУНКЦҮҮД
# ============================================================

def get_email_signature(user: Optional['User'] = None) -> str:
    """
    Имэйлийн signature үүсгэх - Energy Resources LLC форматаар

    Args:
        user: Илгээж буй хэрэглэгч (ихэвчлэн approve хийсэн ахлах химич)

    Returns:
        HTML signature string
    """
    if not user:
        # Default signature - системийн автомат мэдэгдэл
        return _render_email(
            EMAIL_SIGNATURE_TEMPLATE,
            sender_name="Laboratory Team",
            sender_position="Coal Analysis Laboratory",
            sender_email="",
            sender_phone=""
        )

    return _render_email(
        EMAIL_SIGNATURE_TEMPLATE,
        sender_name=user.full_name or user.username,
        sender_position=user.position or "Senior Chemist, Laboratory",
        sender_email=user.email or "",
        sender_phone=user.phone or ""
    )


def get_notification_recipients(notification_type: str) -> List[str]:
    """
    Мэдэгдлийн хүлээн авагчдыг авах

    Args:
        notification_type: 'qc_alert', 'sample_status', 'equipment', 'all'

    Returns:
        Email хаягуудын жагсаалт
    """
    from sqlalchemy import select
    # SystemSetting-ээс авах эсвэл default
    setting = db.session.execute(
        select(SystemSetting).filter_by(
            category='notifications',
            key=f'{notification_type}_recipients'
        )
    ).scalars().first()

    if setting and setting.value:
        return [e.strip() for e in setting.value.split(',') if e.strip()]

    # Default: Admin болон Senior Chemist-ууд
    admins = db.session.execute(
        select(User).filter(User.role.in_(['admin', 'senior']))
    ).scalars().all()
    return [u.email for u in admins if u.email]


def send_notification(
    subject: str,
    recipients: List[str],
    html_body: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    sender_user: Optional['User'] = None,
    include_signature: bool = True
) -> bool:
    """
    Email мэдэгдэл илгээх

    Args:
        subject: Имэйлийн гарчиг
        recipients: Хүлээн авагчид
        html_body: HTML агуулга
        attachments: Хавсралтууд [{"filename": "", "content_type": "", "data": bytes}]
        sender_user: Илгээж буй хэрэглэгч (signature-д ашиглана)
        include_signature: Signature нэмэх эсэх

    Returns:
        Амжилттай эсэх
    """
    if not recipients:
        logger.warning("No recipients for notification")
        return False

    try:
        # Signature нэмэх
        if include_signature:
            signature = get_email_signature(sender_user)
            html_body = f"{html_body}{signature}"

        msg = Message(
            subject=f"[Coal LIMS] {subject}",
            recipients=recipients,
            html=html_body
        )

        # Reply-To: Хариу имэйлийг илгээсэн хүн рүү явуулах
        if sender_user and sender_user.email:
            msg.reply_to = sender_user.email

        if attachments:
            for att in attachments:
                msg.attach(
                    att['filename'],
                    att.get('content_type', 'application/octet-stream'),
                    att['data']
                )

        mail.send(msg)
        logger.info(f"Notification sent: {subject} to {len(recipients)} recipients")
        return True

    except (OSError, RuntimeError) as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def notify_qc_failure(
    analysis_code: str,
    qc_sample: str,
    status: str,
    rules_violated: List[str]
) -> bool:
    """QC Westgard зөрчлийн мэдэгдэл"""

    recipients = get_notification_recipients('qc_alert')
    if not recipients:
        return False

    html = _render_email(
        QC_FAILURE_TEMPLATE,
        analysis_code=analysis_code,
        qc_sample=qc_sample,
        status=status.upper(),
        rules_violated=', '.join(rules_violated)
    )

    return send_notification(
        subject=f"QC Alert: {analysis_code} - {status.upper()}",
        recipients=recipients,
        html_body=html
    )


def notify_sample_status_change(
    sample_code: str,
    new_status: str,
    changed_by: str,
    reason: Optional[str] = None,
    timestamp: Optional[str] = None
) -> bool:
    """Дээжийн статус өөрчлөгдсөн мэдэгдэл"""

    recipients = get_notification_recipients('sample_status')
    if not recipients:
        return False

    # Статусын өнгө, icon
    status_config = {
        'approved': {'color': '#28a745', 'icon': '✅'},
        'rejected': {'color': '#dc3545', 'icon': '❌'},
        'pending': {'color': '#ffc107', 'icon': '⏳'},
    }
    config = status_config.get(new_status.lower(), {'color': '#6c757d', 'icon': '📋'})

    html = _render_email(
        SAMPLE_STATUS_TEMPLATE,
        sample_code=sample_code,
        new_status=new_status,
        changed_by=changed_by,
        reason=reason,
        timestamp=timestamp or now_local().strftime('%Y-%m-%d %H:%M'),
        color=config['color'],
        icon=config['icon']
    )

    return send_notification(
        subject=f"Sample {new_status}: {sample_code}",
        recipients=recipients,
        html_body=html
    )


def notify_equipment_calibration_due(equipment_list: List[Dict]) -> bool:
    """
    Калибровкийн хугацаа дөхсөн тоног төхөөрөмжийн мэдэгдэл

    Args:
        equipment_list: [{"name": "", "next_calibration": "", "days_left": int}]
    """
    if not equipment_list:
        return False

    recipients = get_notification_recipients('equipment')
    if not recipients:
        return False

    html = _render_email(
        EQUIPMENT_CALIBRATION_TEMPLATE,
        equipment_list=equipment_list
    )

    urgent_count = sum(1 for eq in equipment_list if eq.get('days_left', 999) <= 7)

    return send_notification(
        subject=f"Equipment Calibration Due ({urgent_count} urgent)",
        recipients=recipients,
        html_body=html
    )


# ============================================================
# БАГЦ МЭДЭГДЭЛ ШАЛГАХ (Scheduler дуудна)
# ============================================================

def check_and_send_equipment_notifications():
    """
    Калибровкийн хугацаа дөхсөн тоног төхөөрөмжийг шалгаж мэдэгдэл илгээх

    Scheduler-ээс өдөр бүр дуудагдана.
    """
    from app.models import Equipment
    from datetime import timedelta

    today = now_local().date()
    threshold = today + timedelta(days=30)  # 30 хоногийн дотор

    from sqlalchemy import select
    equipment_due = db.session.execute(
        select(Equipment).filter(
            Equipment.next_calibration_date <= threshold,
            Equipment.next_calibration_date >= today,
            Equipment.status == 'active'
        )
    ).scalars().all()

    if not equipment_due:
        logger.info("No equipment calibration due within 30 days")
        return

    equipment_list = []
    for eq in equipment_due:
        days_left = (eq.next_calibration_date - today).days
        equipment_list.append({
            'name': eq.name,
            'next_calibration': eq.next_calibration_date.strftime('%Y-%m-%d'),
            'days_left': days_left
        })

    # Хугацаагаар эрэмбэлэх
    equipment_list.sort(key=lambda x: x['days_left'])

    notify_equipment_calibration_due(equipment_list)


def check_and_notify_westgard():
    """
    Бүх QC дээжийн Westgard статусыг шалгаж, зөрчил байвал мэдэгдэл илгээх

    Scheduler-ээс өдөр бүр дуудагдана.
    """
    from app.repositories import QCControlChartRepository
    from app.utils.westgard import check_westgard_rules, get_qc_status

    # Өвөрмөц analysis_code + qc_sample_name хосуудыг авах
    unique_pairs = QCControlChartRepository.get_unique_analysis_qc_pairs()

    alerts_sent = 0

    for analysis_code, qc_sample in unique_pairs:
        if not analysis_code or not qc_sample:
            continue

        charts = QCControlChartRepository.get_recent_for_qc(
            analysis_code, qc_sample, limit=20,
        )

        if len(charts) < 2:
            continue

        values = [c.measured_value for c in charts if c.measured_value is not None]
        first_chart = charts[0]
        target = first_chart.target_value or 0

        if first_chart.ucl and first_chart.target_value:
            sd = (first_chart.ucl - first_chart.target_value) / 2
        else:
            import statistics
            sd = statistics.stdev(values) if len(values) >= 2 else 1

        if sd <= 0:
            sd = 0.001

        violations = check_westgard_rules(values, target, sd)
        qc_status = get_qc_status(violations)

        # Зөвхөн reject үед мэдэгдэл илгээх
        if qc_status['status'] == 'reject':
            notify_qc_failure(
                analysis_code=analysis_code,
                qc_sample=qc_sample,
                status=qc_status['status'],
                rules_violated=qc_status.get('rules_violated', [])
            )
            alerts_sent += 1

    logger.info(f"Westgard check completed. {alerts_sent} alerts sent.")
