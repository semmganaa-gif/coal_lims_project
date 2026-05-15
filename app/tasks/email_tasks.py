# app/tasks/email_tasks.py
# -*- coding: utf-8 -*-
"""
Email илгээх background tasks.

Blocking SMTP call-ыг Celery worker-д шилжүүлнэ.
"""

import logging
from celery import shared_task
from flask_mail import Message

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_async(self, subject, recipients, html_body, reply_to=None, attachments=None):
    """
    Email илгээх (background).

    Args:
        subject: Имэйлийн гарчиг
        recipients: Хүлээн авагчдын жагсаалт
        html_body: HTML агуулга
        reply_to: Хариу имэйл хаяг
        attachments: [{filename, content_type, data(base64)}]
    """
    try:
        from app import mail

        msg = Message(
            subject=f"[Coal LIMS] {subject}",
            recipients=recipients,
            html=html_body,
        )

        if reply_to:
            msg.reply_to = reply_to

        if attachments:
            import base64
            for att in attachments:
                data = base64.b64decode(att["data"]) if isinstance(att["data"], str) else att["data"]
                msg.attach(
                    att["filename"],
                    att.get("content_type", "application/octet-stream"),
                    data,
                )

        mail.send(msg)
        logger.info("Email sent: %s to %d recipients", subject, len(recipients))
        return {"success": True, "recipients": len(recipients)}

    except (OSError, RuntimeError) as exc:
        logger.error("Email send failed (attempt %d): %s", self.request.retries + 1, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_sla_overdue_alert(self, lab_type="coal"):
    """
    SLA хугацаа хэтэрсэн дээжний мэдэгдэл илгээх.

    Manager/admin хэрэглэгчдэд overdue жагсаалт илгээнэ.
    """
    try:
        from sqlalchemy import select
        from app import db
        from app.models import User
        from app.services.sla_service import get_overdue_samples, get_sla_summary
        from app.utils.notifications import send_notification

        summary = get_sla_summary(lab_type)
        if summary.overdue == 0:
            return {"success": True, "message": "No overdue samples"}

        overdue = get_overdue_samples(lab_type, limit=20)

        # Manager/admin имэйл хаягууд
        managers = list(db.session.execute(
            select(User).where(
                User.role.in_(["manager", "admin"]),
                User.email.isnot(None),
            )
        ).scalars().all())
        recipients = [u.email for u in managers if u.email]

        if not recipients:
            return {"success": False, "message": "No manager emails configured"}

        # HTML бэлдэх
        rows_html = ""
        for s in overdue:
            rows_html += (
                f"<tr><td>{s.sample_code}</td><td>{s.client_name}</td>"
                f"<td>{s.due_date}</td><td style='color:red'>{s.overdue_hours:.0f} цаг</td>"
                f"<td>{s.pending_analyses}</td></tr>"
            )

        html_body = f"""
        <h2>SLA Хугацаа хэтэрсэн дээжүүд ({summary.overdue})</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
            <tr style="background:#f8f9fa">
                <th>Дээж</th><th>Клиент</th><th>Due</th>
                <th>Хэтэрсэн</th><th>Pending</th>
            </tr>
            {rows_html}
        </table>
        <p>Нийт: {summary.overdue} overdue, {summary.due_soon} due soon</p>
        """

        send_notification(
            subject=f"SLA Alert: {summary.overdue} дээж хугацаа хэтэрсэн",
            recipients=recipients,
            html_body=html_body,
            include_signature=False,
        )

        return {"success": True, "overdue": summary.overdue, "notified": len(recipients)}

    except Exception as exc:
        logger.error("SLA alert failed: %s", exc)
        raise self.retry(exc=exc)
