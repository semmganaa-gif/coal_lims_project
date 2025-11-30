# seed_sample_types.py
from app import create_app, db
from app.models import SystemSetting
from app.constants import SAMPLE_TYPE_CHOICES_MAP, UNIT_ABBREVIATIONS
import json

app = create_app()

with app.app_context():
    # 1. SAMPLE_TYPE_CHOICES_MAP
    SystemSetting.query.filter_by(category='sample_type').delete()
    for client, types in SAMPLE_TYPE_CHOICES_MAP.items():
        setting = SystemSetting(
            category='sample_type',
            key=client,
            value=json.dumps(types),
        )
        db.session.add(setting)

    # 2. UNIT_ABBREVIATIONS
    SystemSetting.query.filter_by(category='unit_abbr').delete()
    for unit, abbr in UNIT_ABBREVIATIONS.items():
        setting = SystemSetting(
            category='unit_abbr',
            key=unit,
            value=abbr,
        )
        db.session.add(setting)

    db.session.commit()
    print(f"✅ {len(SAMPLE_TYPE_CHOICES_MAP)} sample types")
    print(f"✅ {len(UNIT_ABBREVIATIONS)} unit abbreviations")
