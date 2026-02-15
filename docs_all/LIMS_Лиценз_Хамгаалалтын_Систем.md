> **⚠️ OUTDATED** — This document is no longer maintained. See newer audit/documentation files.

# LIMS Лиценз Хамгаалалтын Систем

## Тойм

Энэ систем нь таны LIMS программыг хамгаалж:
- Лицензийн хугацаа шалгана
- Өөр компьютерт хуулахаас хамгаална
- Хууран мэхлэхийг илрүүлнэ

---

## Идэвхжүүлэх алхамуу|

### Алхам 1: Нууц түлхүүрүүдийг өөрчлөх

**МАША ЧУХАЛ!** Доорх 2 файлд нууц түлхүүрүүдийг ижил байдлаар өөрчилнө үү:

**Файл 1:** `app/utils/license_protection.py` (мөр ~20-22)
```python
LICENSE_SECRET_KEY = "ТАНЫ_САНАМСАРГҮЙ_32_ТЭМДЭГТ_ЭНД"
LICENSE_SALT = "ТАНЫ_SALT_ЭНД_2024"
SIGNATURE_KEY = "ТАНЫ_SIGNATURE_KEY_ЭНД"
```

**Файл 2:** `scripts/generate_license.py` (мөр ~20-22)
```python
LICENSE_SECRET_KEY = "ТАНЫ_САНАМСАРГҮЙ_32_ТЭМДЭГТ_ЭНД"  # Дээрхтэй ЯГЛАЖ ижил!
LICENSE_SALT = "ТАНЫ_SALT_ЭНД_2024"
SIGNATURE_KEY = "ТАНЫ_SIGNATURE_KEY_ЭНД"
```

**Нууц түлхүүр үүсгэх жишээ:**
```python
import secrets
print(secrets.token_hex(16))  # 32 тэмдэгт үүснэ
```

---

### Алхам 2: App-д бүртгэх

`app/__init__.py` файлд дараах өөрчлөлтүүдийг хийнэ:

**1. Import нэмэх (файлын эхэнд):**
```python
from app.routes.license_routes import license_bp
from app.utils.license_protection import license_manager, check_license_middleware
```

**2. Blueprint бүртгэх (бусад blueprint-уудын дараа):**
```python
safe_register_blueprint(license_bp)
```

**3. Before request нэмэх (create_app функц дотор, return app-ийн өмнө):**
```python
# Лиценз шалгалт идэвхжүүлэх (Production-д)
# АНХААРУУЛГА: Хөгжүүлэлтийн үед comment хийж болно
if not app.debug:
    app.before_request(check_license_middleware)
```

---

### Алхам 3: Migration хийх

```bash
flask db migrate -m "Add license tables"
flask db upgrade
```

---

### Алхам 4: Анхны лиценз үүсгэх

```bash
python scripts/generate_license.py
```

Интерактив горимд:
1. Компанийн нэр оруулах
2. Хугацаа сонгох
3. Hardware ID (хоосон үлдээж болно)

---

## Ашиглах

### Үйлчлүүлэгчид лиценз үүсгэх

1. Үйлчлүүлэгчээс Hardware ID авах:
   - Тэд `http://[server]/license/hardware-id` хаягаар орно
   - Эсвэл `http://[server]/license/activate` хуудаснаас харна

2. Лиценз үүсгэх:
```bash
python scripts/generate_license.py
```

3. Лиценз түлхүүрийг үйлчлүүлэгчид илгээх

### Үйлчлүүлэгч лиценз идэвхжүүлэх

1. `http://[server]/license/activate` хаягаар орно
2. Лиценз түлхүүрийг буулгана
3. "Идэвхжүүлэх" товч дарна

---

## Хуудсууд

| URL | Тайлбар |
|-----|---------|
| `/license/activate` | Лиценз идэвхжүүлэх |
| `/license/expired` | Лиценз дууссан |
| `/license/error` | Лицензийн алдаа |
| `/license/info` | Лицензийн мэдээлэл (нэвтэрсэн хэрэглэгчид) |
| `/license/check` | API - лиценз шалгах |
| `/license/hardware-id` | API - hardware ID авах |

---

## Хамгаалалтын түвшингүүд

### Түвшин 1: Хугацааны хязгаар
- Лицензийн хугацаа дуусвал систем ажиллахаа болино

### Түвшин 2: Hardware binding
- Тодорхой компьютерт л ажиллана
- Хуулсан ч өөр компьютерт ажиллахгүй

### Түвшин 3: Tampering detection
- Hardware ID өөрчлөгдвөл илрүүлнэ
- Лиценз файлыг засах оролдлогыг илрүүлнэ

---

## Анхааруулга

1. **Нууц түлхүүрүүд** - Хэзээ ч бусдад өгөх, GitHub-д push хийхгүй!
2. **generate_license.py** - Зөвхөн та ашиглана, үйлчлүүлэгчид өгөхгүй!
3. **Backup** - Нууц түлхүүрүүдийг аюулгүй газар хадгална

---

## Асуултууд

**Q: Hardware ID өөрчлөгдвөл яах вэ?**
A: Шинэ лиценз үүсгэж өгнө. Эсвэл `allowed_hardware_ids` талбарт олон ID нэмж болно.

**Q: Интернэтгүй ажиллах уу?**
A: Тийм, энэ систем бүрэн offline ажиллана.

**Q: Хэр найдвартай вэ?**
A: 100% хамгаалалт байхгүй ч, хуулахаас илүү худалдаж авах нь хялбар байхаар хийгдсэн.
