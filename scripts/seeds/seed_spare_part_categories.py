# seed_spare_part_categories.py
"""
Тоног төхөөрөмжөөс SparePartCategory үүсгэх.

Ажиллуулах:
    python seed_spare_part_categories.py
"""

from app import create_app, db
from app.models import Equipment, SparePartCategory

app = create_app()


def seed_categories():
    """Equipment-ээс SparePartCategory үүсгэх."""

    print("=" * 60)
    print("СЭЛБЭГИЙН КАТЕГОРИ SEED")
    print("=" * 60)

    # Идэвхтэй equipment-үүдийг авах
    equipments = Equipment.query.filter(
        Equipment.status != 'retired'
    ).order_by(Equipment.name).all()

    print(f"Идэвхтэй тоног төхөөрөмж: {len(equipments)}")

    created = 0
    skipped = 0

    for eq in equipments:
        # Code үүсгэх (name + model)
        code = eq.name.lower().replace(' ', '_').replace('/', '_').replace(',', '')
        if eq.model:
            model_clean = eq.model.replace(' ', '_').replace('/', '_').replace('*', 'x')
            code = f"{code}_{model_clean}".lower()

        # Хэт урт код богиносгох
        if len(code) > 45:
            code = code[:45]

        # Давхардал шалгах
        existing = SparePartCategory.query.filter_by(code=code).first()
        if existing:
            skipped += 1
            continue

        # Категори үүсгэх
        cat = SparePartCategory(
            code=code,
            name=eq.name,
            name_en=eq.model,
            description=f"{eq.manufacturer or ''} {eq.model or ''} ({eq.location or ''})".strip(),
            equipment_id=eq.id,
            sort_order=created,
            is_active=True,
        )
        db.session.add(cat)
        created += 1
        print(f"  + {code[:40]:<40} | {eq.name}")

    db.session.commit()

    print("-" * 60)
    print(f"Шинээр үүсгэсэн: {created}")
    print(f"Давхардсан: {skipped}")
    print(f"Нийт SparePartCategory: {SparePartCategory.query.count()}")
    print("=" * 60)


if __name__ == '__main__':
    with app.app_context():
        seed_categories()
