# app/cli.py
"""
Flask CLI командууд.

flask create-user, flask import-equipment зэрэг командуудыг тодорхойлно.
"""

from app import db
from app.models import User, Equipment, SystemSetting
from app.utils.repeatability_loader import clear_cache
from sqlalchemy import select
import click
import pandas as pd
from pathlib import Path
import json
from math import inf


# --------- Жижиг helper функцууд --------- #
def _safe_str(value):
    """Утгыг string руу аюулгүй хөрвүүлэх."""
    try:
        import pandas as _pd
    except ImportError:
        _pd = None
    if value is None:
        return ""
    if _pd is not None and isinstance(value, float) and _pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value, default=None):
    """Утгыг integer руу аюулгүй хөрвүүлэх."""
    try:
        import pandas as _pd
    except ImportError:
        _pd = None
    try:
        if value is None:
            return default
        if _pd is not None and isinstance(value, float) and _pd.isna(value):
            return default
        s = str(value).strip()
        if s == "":
            return default
        return int(float(s))
    except (ValueError, TypeError):
        return default


def _safe_float(value, default=None):
    """Утгыг float руу аюулгүй хөрвүүлэх."""
    try:
        import pandas as _pd
    except ImportError:
        _pd = None
    try:
        if value is None:
            return default
        if _pd is not None and isinstance(value, float) and _pd.isna(value):
            return default
        s = str(value).strip()
        if s == "":
            return default
        s = s.replace(" ", "").replace(",", "")
        return float(s)
    except (ValueError, TypeError):
        return default


def register_commands(app):
    """CLI командуудыг бүртгэх."""
    # =======================
    # 1) Хэрэглэгчийн команд
    # =======================
    @app.cli.group()
    def users():
        """Хэрэглэгчийн удирдлагын командууд."""
        pass

    @users.command("create")
    @click.argument("username")
    @click.argument("password")
    @click.argument("role")
    def create_user(username, password, role):
        """Шинэ хэрэглэгч үүсгэх."""
        if db.session.execute(select(User).filter_by(username=username)).scalars().first():
            click.echo(f"'{username}' user already exists.")
            return

        if role not in ["prep", "chemist", "senior", "manager", "admin"]:
            click.echo(
                "Алдаа: Эрх буруу байна. 'prep', 'chemist', 'senior', 'manager', "
                "'admin' гэсэн утгуудын аль нэгийг сонгоно уу."
            )
            return

        user = User(username=username, role=role)
        try:
            user.set_password(password)
        except ValueError as e:
            click.echo(f"Error: {e}")
            return
        db.session.add(user)
        db.session.commit()
        click.echo(f"'{username}' нэртэй, '{role}' эрхтэй хэрэглэгчийг амжилттай үүсгэлээ.")

    # =======================
    # 2) Тоног төхөөрөмжийн командууд
    # =======================
    @app.cli.group()
    def equipment():
        """Тоног төхөөрөмжийн Excel импорт/экспорт командууд."""
        pass
    # ---------- IMPORT ----------

    @equipment.command("import-excel")
    @click.argument("excel_path")
    @click.option(
        "--sheet",
        default="1",
        show_default=True,
        help="Унших sheet-ийн нэр эсвэл дугаар. Ж: 1, 2, 3 ...",
    )
    def import_equipment_from_excel(excel_path, sheet):
        """
        Excel-ээс тоног төхөөрөмжийн бүртгэл импортлох.

        Жишээ:
            flask equipment import-excel "Багаж тоног төхөөрөмжийн нэгдсэн бүртгэл-2024.09 (002).xlsx" --sheet 1
            flask equipment import-excel "Багаж тоног төхөөрөмжийн нэгдсэн бүртгэл-2024.09 (002).xlsx" --sheet 2
        """
        excel_path = Path(excel_path)
        if not excel_path.exists():
            click.echo(f"Файл олдсонгүй: {excel_path}")
            return

        click.echo(f"➡ Excel уншиж байна: {excel_path} (sheet={sheet})")

        # Энэ файл дээр sheet 1,2,3,... бүгд дээр 3-р мөрөнд (index=2) үндсэн header-үүд байна
        df = pd.read_excel(excel_path, sheet_name=sheet, header=2)

        # -------------------------------------------------
        # ЗАГВАР A: Sheet 1 зэрэг энгийн хүснэгт
        # -------------------------------------------------
        if "Тоног төхөөрөмжийн нэр" in df.columns:
            click.echo("→ Загвар A (ердийн хүснэгт) гэж танилаа.")

            if "Тоног төхөөрөмжийн нэр" not in df.columns:
                click.echo("Алдаа: 'Тоног төхөөрөмжийн нэр' багана олдсонгүй.")
                return

            df = df[df["Тоног төхөөрөмжийн нэр"].notna()].copy()

            created = 0
            skipped = 0

            for _, row in df.iterrows():
                name = _safe_str(row.get("Тоног төхөөрөмжийн нэр"))
                if not name:
                    continue

                manufacturer = _safe_str(row.get("Үйлдвэрлэгч"))
                model = _safe_str(row.get("Марк дугаар"))
                location = _safe_str(row.get("Зориулалт"))

                calibration_note = _safe_str(row.get("Шалгалт тохируулга"))
                quantity = _safe_int(row.get("Тоо хэмжээ"), default=1) or 1

                manufactured_info = _safe_str(row.get("Үйлдвэрлэсэн огноо"))
                commissioned_info = _safe_str(row.get("Ашиглалтанд орсон огноо"))

                initial_price = _safe_float(row.get("Анхны үнэ /төг/"))
                residual_price = _safe_float(row.get("Үлдэгдэл үнэ /төг/"))
                remark = _safe_str(row.get("Тайлбар"))

                # Давхардал шалгах (нэр + марк + байршил)
                existing = db.session.execute(select(Equipment).filter_by(
                    name=name or None,
                    model=model or None,
                    location=location or None,
                )).scalars().first()

                if existing:
                    skipped += 1
                    continue

                eq = Equipment(
                    name=name,
                    manufacturer=manufacturer or None,
                    model=model or None,
                    location=location or None,
                    calibration_note=calibration_note or None,
                    quantity=quantity,
                    manufactured_info=manufactured_info or None,
                    commissioned_info=commissioned_info or None,
                    initial_price=initial_price,
                    residual_price=residual_price,
                    remark=remark or None,
                    status="normal",
                )

                db.session.add(eq)
                created += 1

            db.session.commit()
            click.echo(
                f"✅ Импорт (Загвар A) дууслаа. Шинэ бичлэг: {created}, алгассан (давхардсан): {skipped}"
            )
            return

        # -------------------------------------------------
        # ЗАГВАР B: Sheet 2, 3, ... олон мөр header-тэй хүснэгт
        # -------------------------------------------------
        click.echo("→ Загвар B (олон мөр header-тэй хүснэгт) гэж танилаа.")

        # Энэ загварт header=2-оор уншихад бүх column нь Unnamed:0.. гээд явна.
        # Жинхэнэ утгууд нь:
        #   col2: Багаж, тоног төхөөрөмжийн нэр
        #   col3: Үйлдвэрлэгчийн нэр
        #   col4: Марк, дугаар
        #   col5: Лабораторийн дугаар
        #   col6: Тоо хэмжээ
        #   col7: Ашиглалтад орсон огноо (жил/жил.сар)
        #   col8: Байршил
        if len(df.columns) < 9:
            click.echo("Алдаа: Энэ sheet-ийн баганын тоо хэт бага байна, таньж чадсангүй.")
            return

        col_name = df.columns[2]
        col_manufacturer = df.columns[3]
        col_model = df.columns[4]
        col_labcode = df.columns[5]
        col_qty = df.columns[6]
        col_commissioned = df.columns[7]
        col_location = df.columns[8]

        # Нэр хоосон мөрүүдийг алгасана
        df = df[df[col_name].notna()].copy()

        created = 0
        skipped = 0

        for _, row in df.iterrows():
            name = _safe_str(row.get(col_name))
            if not name:
                continue

            # Хэсгийн гарчиг мөрүүдийг алгасах (жишээ: "Төв лаб- ... тоног төхөөрөмж")
            lowered = name.lower()
            if "тоног төхөөрөмж" in lowered and ("лаб" in lowered or "лаборатор" in lowered):
                continue

            manufacturer = _safe_str(row.get(col_manufacturer))
            model = _safe_str(row.get(col_model))
            lab_code = _safe_str(row.get(col_labcode))
            quantity = _safe_int(row.get(col_qty), default=1) or 1
            commissioned_info = _safe_str(row.get(col_commissioned))
            location = _safe_str(row.get(col_location))

            existing = db.session.execute(select(Equipment).filter_by(
                name=name or None,
                model=model or None,
                location=location or None,
            )).scalars().first()
            if existing:
                skipped += 1
                continue

            # Лабораторийн дотоод кодыг remark-д хийгээд хадгалчихъя (жишээ: MHG_3)
            remark = lab_code or None

            eq = Equipment(
                name=name,
                manufacturer=manufacturer or None,
                model=model or None,
                location=location or None,
                quantity=quantity,
                commissioned_info=commissioned_info or None,
                remark=remark,
                status="normal",
            )

            db.session.add(eq)
            created += 1

        db.session.commit()
        click.echo(
            f"✅ Импорт (Загвар B) дууслаа. Шинэ бичлэг: {created}, алгассан (давхардсан): {skipped}"
        )

    # =======================
    # LICENSE COMMANDS
    # =======================
    @app.cli.group()
    def license():
        """Лицензийн удирдлагын командууд."""
        pass

    @license.command("generate")
    @click.option("--company", required=True, help="Компанийн нэр")
    @click.option("--expiry", required=True, help="Дуусах огноо (YYYY-MM-DD)")
    @click.option("--hardware-id", default=None, help="Hardware ID (заавал биш)")
    @click.option("--max-users", default=10, help="Хэрэглэгчийн дээд хязгаар")
    @click.option("--max-samples", default=10000, help="Сарын дээжний дээд хязгаар")
    @click.option("--trial", is_flag=True, help="Туршилтын лиценз")
    def generate_license(company, expiry, hardware_id, max_users, max_samples, trial):
        """
        Лиценз түлхүүр үүсгэх.

        Жишээ:
            flask license generate --company "Erdenes TT" --expiry "2027-12-31"
            flask license generate --company "Test" --expiry "2026-06-30" --trial
            flask license generate --company "Erdenes TT" --expiry "2027-12-31" --hardware-id ABC123
        """
        from app.utils.license_protection import license_manager

        key = license_manager.generate_license_key(
            company=company,
            expiry_date=f"{expiry}T23:59:59",
            hardware_id=hardware_id,
            max_users=max_users,
            max_samples=max_samples,
            is_trial=trial,
        )

        click.echo("")
        click.echo("=" * 60)
        click.echo("  ЛИЦЕНЗ ТҮЛХҮҮР ҮҮСЛЭЭ")
        click.echo("=" * 60)
        click.echo(f"  Компани:     {company}")
        click.echo(f"  Дуусах:      {expiry}")
        click.echo(f"  Хэрэглэгч:  {max_users}")
        click.echo(f"  Дээж/сар:    {max_samples}")
        click.echo(f"  Hardware:    {hardware_id or 'ямар ч сервер'}")
        click.echo(f"  Туршилт:    {'Тийм' if trial else 'Үгүй'}")
        click.echo("=" * 60)
        click.echo("")
        click.echo(key)
        click.echo("")
        click.echo("Дээрх түлхүүрийг захиалагчид илгээнэ үү.")
        click.echo("Захиалагч /license/activate хуудсанд оруулна.")

    @license.command("info")
    def license_info():
        """Одоогийн лицензийн мэдээлэл харах."""
        from app.models import SystemLicense

        lic = db.session.execute(select(SystemLicense).filter_by(is_active=True)).scalars().first()
        if not lic:
            click.echo("Идэвхтэй лиценз олдсонгүй.")
            return

        click.echo("")
        click.echo(f"  Компани:      {lic.company_name}")
        click.echo(f"  Олгосон:      {lic.issued_date}")
        click.echo(f"  Дуусах:       {lic.expiry_date}")
        click.echo(f"  Үлдсэн хоног: {lic.days_remaining}")
        click.echo(f"  Хэрэглэгч:   {lic.max_users}")
        click.echo(f"  Дээж/сар:     {lic.max_samples_per_month}")
        click.echo(f"  Hardware:     {lic.hardware_id or '-'}")
        click.echo(f"  Хүчинтэй:    {'Тийм' if lic.is_valid else 'ҮГҮЙ'}")
        click.echo(f"  Tampering:    {'ИЛЭРСЭН!' if lic.tampering_detected else 'Үгүй'}")

    @license.command("extend")
    @click.option("--days", type=int, default=None, help="Хэдэн хоногоор сунгах")
    @click.option("--expiry", default=None, help="Шинэ дуусах огноо (YYYY-MM-DD)")
    def extend_license(days, expiry):
        """
        Идэвхтэй лицензийн хугацааг сунгах (серверт шууд ажиллуулна).

        Жишээ:
            flask license extend --days 365
            flask license extend --expiry "2028-06-30"
        """
        from datetime import datetime, timedelta
        from app.models import SystemLicense

        if not days and not expiry:
            click.echo("Алдаа: --days эсвэл --expiry-н аль нэгийг заана уу.")
            return

        lic = db.session.execute(select(SystemLicense).filter_by(is_active=True)).scalars().first()
        if not lic:
            click.echo("Идэвхтэй лиценз олдсонгүй.")
            return

        old_expiry = lic.expiry_date
        if expiry:
            lic.expiry_date = datetime.fromisoformat(f"{expiry}T23:59:59")
        else:
            lic.expiry_date = lic.expiry_date + timedelta(days=days)

        db.session.commit()

        click.echo(f"Лиценз сунгагдлаа:")
        click.echo(f"  Хуучин: {old_expiry}")
        click.echo(f"  Шинэ:   {lic.expiry_date}")
        click.echo(f"  Үлдсэн: {lic.days_remaining} хоног")

    @license.command("hwid")
    def show_hardware_id():
        """Энэ компьютерийн Hardware ID харуулах."""
        from app.utils.hardware_fingerprint import get_hardware_info

        info = get_hardware_info()
        click.echo("")
        click.echo(f"  Hostname:   {info['hostname']}")
        click.echo(f"  Short ID:   {info['short_id']}")
        click.echo(f"  Full ID:    {info['hardware_id']}")
        click.echo("")
        click.echo("Захиалагч энэ Short ID-г чамд илгээнэ.")

    # ---------- EXPORT ----------
    @equipment.command("export-excel")
    @click.argument("excel_path")
    def export_equipment_to_excel(excel_path):
        """
        Тоног төхөөрөмжийн бүртгэлийг Excel файл руу экспортлох.

        Жишээ:
            flask equipment export-excel equipment_export.xlsx
        """
        excel_path = Path(excel_path)
        click.echo(f"⬅ Excel рүү экспортолж байна: {excel_path}")

        equipments = db.session.execute(select(Equipment).order_by(Equipment.id)).scalars().all()

        rows = []
        for idx, eq in enumerate(equipments, start=1):
            rows.append(
                {
                    "№": idx,
                    "Тоног төхөөрөмжийн нэр": eq.name,
                    "Үйлдвэрлэгч": eq.manufacturer,
                    "Марк дугаар": eq.model,
                    "Зориулалт": eq.location,
                    "Шалгалт тохируулга": eq.calibration_note,
                    "Тоо хэмжээ": eq.quantity,
                    "Үйлдвэрлэсэн огноо": eq.manufactured_info,
                    "Ашиглалтад орсон огноо": eq.commissioned_info,
                    "Анхны үнэ /төг/": eq.initial_price,
                    "Үлдэгдэл үнэ /төг/": eq.residual_price,
                    "Тайлбар": eq.remark,
                }
            )

        df = pd.DataFrame(
            rows,
            columns=[
                "№",
                "Тоног төхөөрөмжийн нэр",
                "Үйлдвэрлэгч",
                "Марк дугаар",
                "Зориулалт",
                "Шалгалт тохируулга",
                "Тоо хэмжээ",
                "Үйлдвэрлэсэн огноо",
                "Ашиглалтад орсон огноо",
                "Анхны үнэ /төг/",
                "Үлдэгдэл үнэ /төг/",
                "Тайлбар",
            ],
        )

        df.to_excel(excel_path, index=False)
        click.echo("✅ Экспорт амжилттай.")

    # =======================
    # 3) Repeatability limits ?????? (CSV -> SystemSetting)
    # =======================
    @app.cli.command("import-limits")
    @click.argument("csv_path")
    def import_limits_from_csv(csv_path):
        """
        Давтамж/нарийвч (repeatability) хязгааруудыг CSV-ээс уншиж SystemSetting-д хадгална.
        CSV header: Арга хэмжилт, Стандартын нэр хэмжигдэх, Хэмжигдэх мужийн, %, Давтамжийн хязгаа, Тайрцын тэмдэг
        """
        def code_from_method(name, explicit):
            if explicit:
                return explicit.strip() or None
            name = (name or "").lower()
            mapping = {
                "lab.07.02": "MT",
                "нийт чийг": "MT",
                "lab.07.03": "Mad",
                "анализ чийг": "Mad",
                "lab.07.04": "Vad",
                "дэгдэмхий": "Vad",
                "lab.07.05": "Aad",
                "үнс": "Aad",
                "lab.07.06": "Gi",
                "индекс": "Gi",
                "lab.07.07": "CRI",
                "идэвхжилт": "CRI",
                "реакц": "CRI",
                "lab.07.08": "TS",
                "хүхэр": "TS",
                "lab.07.09": "P",
                "фосфор": "P",
                "lab.07.10": "Cl",
                "хлор": "Cl",
                "lab.07.10f": "F",  # Фтор — lab.07.10-тай collision тул "f" suffix
                "фтор": "F",
                "lab.07.11": "TRD",
                "нягт": "TRD",
                "lab.07.12": "CV",
                "илчлэг": "CV",
                "lab.07.13": "X",
                "хатуулаг": "X",
                "csn": "CSN",
            }
            for k,v in mapping.items():
                if k in name:
                    return v
            return None

        def parse_limit(val):
            if val is None:
                return (None, None)
            s = str(val).strip()
            if not s or s == "-":
                return (None, None)
            if "үр дүнгийн 1/2" in s:
                return (0.5, "percent")
            mode = "abs"
            if "%" in s:
                mode = "percent"
                s = s.replace("%"," ").strip()
            try:
                num = float(s)
            except (ValueError, TypeError):
                return (None, None)
            return (num, mode)

        def parse_upper(val):
            if val is None:
                return None
            s = str(val).strip()
            if not s or s == "-":
                return None
            if s.startswith("<"):
                try:
                    return float(s[1:].strip())
                except (ValueError, TypeError):
                    return None
            if s.startswith(">"):
                return inf
            if "-" in s:
                try:
                    parts = s.split("-")
                    return float(parts[-1])
                except (ValueError, TypeError):
                    return None
            try:
                return float(s)
            except (ValueError, TypeError):
                return None

        csv_path = Path(csv_path)
        if not csv_path.exists():
            click.echo(f"Файл олдсонгүй: {csv_path}")
            return

        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
        except Exception as e:
            click.echo(f"CSV уншихад алдаа: {e}")
            return

        cols = list(df.columns)
        if len(cols) < 5:
            click.echo(f"Баганы тоо хүрэлцэхгүй: {cols}")
            return
        col_method, col_std, col_band, col_limit, col_taarts = cols[:5]

        rules = {}
        last_code = None
        for _, row in df.iterrows():
            method = row.get(col_method)
            std = row.get(col_std)
            band_val = row.get(col_band)
            limit_val = row.get(col_limit)
            taarts = row.get(col_taarts)

            code = code_from_method(method if pd.notna(method) else None, None)
            if code:
                last_code = code
            code = code or last_code
            if not code:
                continue

            limit, mode = parse_limit(limit_val)
            upper = parse_upper(band_val)
            if limit is None:
                continue

            rule = rules.setdefault(code, {"bands": []})
            if pd.notna(std) and str(std).strip():
                rule["standard"] = str(std)
            if pd.notna(taarts) and str(taarts).strip():
                rule["taarts_note"] = str(taarts)

            if upper is None:
                rule["single"] = {"limit": limit, "mode": mode or "abs"}
            else:
                rule["bands"].append({"upper": upper, "limit": limit, "mode": mode or "abs"})

        for code, rule in rules.items():
            bands = rule.get("bands") or []
            if bands:
                rule["bands"] = sorted(bands, key=lambda b: b["upper"])
            if rule.get("single") and rule.get("bands"):
                rule.pop("bands", None)

        payload = json.dumps(rules, ensure_ascii=False)
        setting = db.session.execute(select(SystemSetting).filter_by(category="repeatability", key="limits")).scalars().first()
        if not setting:
            setting = SystemSetting(category="repeatability", key="limits")
            db.session.add(setting)
        setting.value = payload
        db.session.commit()
        clear_cache()
        click.echo(f"Амжилттай хадгаллаа: {len(rules)} дүрмийг шинэ DB-д хадгалсан.")
