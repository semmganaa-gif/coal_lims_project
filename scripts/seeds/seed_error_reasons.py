# seed_error_reasons.py
# -*- coding: utf-8 -*-
"""
ERROR_REASON_LABELS-ийг constants-аас DB руу шилжүүлэх script
"""

from app import create_app, db
from app.models import SystemSetting
from app.constants import ERROR_REASON_LABELS

app = create_app()

with app.app_context():
    print("🔄 ERROR_REASON_LABELS → SystemSetting хүснэгт рүү...")

    # Өмнөх өгөгдлийг устгах (цэвэрлэх)
    existing = SystemSetting.query.filter_by(category='error_reason').all()
    for item in existing:
        db.session.delete(item)

    # Шинэ өгөгдөл оруулах
    sort_order = 0
    for key, label in ERROR_REASON_LABELS.items():
        setting = SystemSetting(
            category='error_reason',
            key=key,
            value=label,
            description=f'Алдааны шалтгаан: {key}',
            is_active=True,
            sort_order=sort_order
        )
        db.session.add(setting)
        sort_order += 1
        print(f"  ✅ {key}: {label}")

    db.session.commit()
    print(f"\n✅ {len(ERROR_REASON_LABELS)} ширхэг ERROR_REASON амжилттай хадгалагдлаа!")