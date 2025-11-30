# app/cli.py

from app import db
from app.models import User, Equipment, SystemSetting
from app.utils.repeatability_loader import clear_cache
import click
import pandas as pd
from pathlib import Path
import json
import csv
from math import inf
from math import inf


# --------- Жижиг helper функцууд --------- #
def _safe_str(value):
    try:
        import pandas as _pd
    except Exception:
        _pd = None
    if value is None:
        return ""
    if _pd is not None and isinstance(value, float) and _pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value, default=None):
    try:
        import pandas as _pd
    except Exception:
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
    except Exception:
        return default


def _safe_float(value, default=None):
    try:
        import pandas as _pd
    except Exception:
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
    except Exception:
        return default


def register_commands(app):
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
        if User.query.filter_by(username=username).first():
            click.echo(f"'{username}' нэртэй хэрэглэгч аль хэдийн байна.")
            return

        if role not in ["beltgegch", "himich", "ahlah", "admin"]:
            click.echo(
                "Алдаа: Эрх буруу байна. 'beltgegch', 'himich', 'ahlah', 'admin' гэсэн утгуудын аль нэгийг сонгоно уу."
            )
            return

        user = User(username=username, role=role)
        try:
            user.set_password(password)
        except ValueError as e:
            click.echo(f"Алдаа: {e}")
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
                existing = Equipment.query.filter_by(
                    name=name or None,
                    model=model or None,
                    location=location or None,
                ).first()

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
                    status="active",
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

            existing = Equipment.query.filter_by(
                name=name or None,
                model=model or None,
                location=location or None,
            ).first()
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
                status="active",
            )

            db.session.add(eq)
            created += 1

        db.session.commit()
        click.echo(
            f"✅ Импорт (Загвар B) дууслаа. Шинэ бичлэг: {created}, алгассан (давхардсан): {skipped}"
        )

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

        equipments = Equipment.query.order_by(Equipment.id).all()

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
        ??????/????? (repeatability) ??????????? CSV-??? ????? SystemSetting-? ????????.
        CSV header: ???? ????????, ?????????? ??? ????????, ????????? ??????, %, ???????? ????? , ??????? ?????
        """
        def code_from_method(name, explicit):
            if explicit:
                return explicit.strip() or None
            name = (name or "").lower()
            mapping = {
                "lab.07.02": "MT",
                "???? ????": "MT",
                "lab.07.03": "Mad",
                "?????? ????": "Mad",
                "lab.07.04": "Vad",
                "?????????": "Vad",
                "lab.07.05": "Aad",
                "???": "Aad",
                "lab.07.06": "Gi",
                "?????": "Gi",
                "lab.07.07": "CRI",
                "??????????": "CRI",
                "?????": "CRI",
                "lab.07.08": "TS",
                "?????": "TS",
                "lab.07.09": "P",
                "??????": "P",
                "lab.07.10": "Cl",
                "????": "Cl",
                "lab.07.10 ": "F",  # ???? ???? LAB.07.10 = ????
                "????": "F",
                "lab.07.11": "TRD",
                "????": "TRD",
                "lab.07.12": "CV",
                "??????": "CV",
                "lab.07.13": "X",
                "??????????": "X",
                "csn": "CSN",
            }
            for k,v in mapping.items():
                if k in name:
                    return v
            return None

        def parse_limit(val):
            if val is None: return (None, None)
            s = str(val).strip()
            if not s or s == "-": return (None, None)
            if "?? ??????? 1/2" in s:
                return (0.5, "percent")
            mode = "abs"
            if "%" in s:
                mode = "percent"
                s = s.replace("%"," ").strip()
            try:
                num = float(s)
            except Exception:
                return (None, None)
            return (num, mode)

        def parse_upper(val):
            if val is None: return None
            s = str(val).strip()
            if not s or s == "-": return None
            if s.startswith("<"):
                try: return float(s[1:].strip())
                except Exception: return None
            if s.startswith(">"):
                return inf
            if "-" in s:
                try:
                    parts = s.split("-")
                    return float(parts[-1])
                except Exception:
                    return None
            try:
                return float(s)
            except Exception:
                return None

        csv_path = Path(csv_path)
        if not csv_path.exists():
            click.echo(f"???? ?????????: {csv_path}")
            return

        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
        except Exception as e:
            click.echo(f"CSV ??????? ?????: {e}")
            return

        cols = list(df.columns)
        if len(cols) < 5:
            click.echo(f"?????? ?????? ?????: {cols}")
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
        setting = SystemSetting.query.filter_by(category="repeatability", key="limits").first()
        if not setting:
            setting = SystemSetting(category="repeatability", key="limits")
            db.session.add(setting)
        setting.value = payload
        db.session.commit()
        clear_cache()
        click.echo(f"?????? ?????????: {len(rules)} ??????? ????? DB-? ?????????.")
