# app/routes/main/hourly_report.py
# -*- coding: utf-8 -*-
"""
Цагийн тайлан илгээх (Hourly Report) — Excel template бөглөж имэйл илгээх
"""

import os
from io import BytesIO
from datetime import timedelta

from flask import flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

from app import db, mail
from app.models import Sample, SystemSetting
from app.repositories import SystemSettingRepository
from app.utils.datetime import now_local
from app.utils.database import safe_commit

from . import main_bp


def get_report_email_recipients():
    """
    Тайлан илгээх имэйл хаягуудыг SystemSetting-ээс авах

    Returns:
        dict: {'to': [...], 'cc': [...]}
    """
    result = {'to': [], 'cc': []}

    to_setting = SystemSettingRepository.get('email', 'report_recipients_to')
    if to_setting and getattr(to_setting, 'is_active', True) and to_setting.value:
        result['to'] = [e.strip() for e in to_setting.value.split(',') if e.strip()]

    cc_setting = SystemSettingRepository.get('email', 'report_recipients_cc')
    if cc_setting and getattr(cc_setting, 'is_active', True) and cc_setting.value:
        result['cc'] = [e.strip() for e in cc_setting.value.split(',') if e.strip()]

    return result


@main_bp.route("/send-hourly-report")
@login_required
def send_hourly_report():
    """Цагийн тайлан илгээх - зөвхөн senior, admin"""
    if current_user.role not in ['senior', 'admin']:
        flash('Энэ үйлдлийг гүйцэтгэх эрхгүй байна.', 'error')
        return redirect(url_for('main.index'))

    try:
        current_app.logger.debug("HOURLY REPORT STARTED (FIXED POSITIONING)")

        # =========================================================================
        # 1. ТОХИРГОО
        # =========================================================================

        # --- 2 HOURLY MAPPING (Суурь мөрүүд) ---
        PF_MAPPING = { 'PF211': 20, 'PF221': 33, 'PF231': 46 }
        HCC_KEYWORDS = ['UHG MV', 'UHG HV', 'BN HV', 'BN SSCC']
        MIDD_KEYWORDS = ['BN MASHCC', 'BN MIDD', 'UHG MASHCC', 'UHG MIDD', 'MASHCC_2']

        SUFFIX_OFFSET_MAP = {
            'D1': 0, 'D2': 1, 'D3': 2, 'D4': 3, 'D5': 4, 'D6': 5,
            'N1': 6, 'N2': 7, 'N3': 8, 'N4': 9, 'N5': 10, 'N6': 11
        }

        # 2H Баганын дугаарууд
        COL_2H_NAME = 1   # A: Sample ID
        COL_2H_MT   = 3   # C
        COL_2H_MAD  = 4   # D
        COL_2H_AAD  = 5   # E
        COL_2H_AD   = 6   # F
        COL_2H_VAD  = 7   # G
        COL_2H_VDAF = 8   # H
        COL_2H_GI   = 15  # O

        # --- 4 HOURLY CONFIG ---
        ROW_BUCKETS_4H = {
            (8, 12):  87,  # 10:00
            (12, 16): 91,  # 14:00
            (16, 20): 95,  # 18:00
            (20, 24): 99,  # 22:00
            (0, 4):   103, # 02:00
            (4, 8):   107  # 06:00
        }

        CF_OFFSET_MAP = {
            # MOD I
            "CF501":       { "cols": {"Aad": 3, "FM": 5}, "offset": 0 },
            "CF502":       { "cols": {"Aad": 3, "FM": 5}, "offset": 1 },
            "CF601":       { "cols": {"Aad": 3, "FM": 5}, "offset": 2 },
            "CF602":       { "cols": {"Aad": 3, "FM": 5}, "offset": 2 },
            # MOD II
            "CF521":       { "cols": {"Aad": 11, "FM": 13}, "offset": 0 },
            "CF522":       { "cols": {"Aad": 11, "FM": 13}, "offset": 1 },
            "CF621":       { "cols": {"Aad": 11, "FM": 13}, "offset": 2 },
            "CF622":       { "cols": {"Aad": 11, "FM": 13}, "offset": 2 },
            # MOD III
            "CF541":       { "cols": {"Aad": 19, "FM": 21}, "offset": 0 },
            "CF542":       { "cols": {"Aad": 19, "FM": 21}, "offset": 1 },
            "CF641":       { "cols": {"Aad": 19, "FM": 21}, "offset": 2 },
            "CF642":       { "cols": {"Aad": 19, "FM": 21}, "offset": 2 },
        }

        # =========================================================================
        # 2. ЦАГ ХУГАЦАА
        # =========================================================================
        current_time = now_local()
        calc_time = current_time - timedelta(hours=2)
        report_hour = (calc_time.hour // 2) * 2
        report_dt = calc_time.replace(hour=report_hour, minute=0, second=0, microsecond=0)

        report_time_str = report_dt.strftime('%H:%M')
        report_date_str = report_dt.strftime('%Y.%m.%d')

        if report_dt.hour < 8:
            start_time = (report_dt - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        else:
            start_time = report_dt.replace(hour=8, minute=0, second=0, microsecond=0)

        end_time = current_time

        # =========================================================================
        # 3. EXCEL НЭЭХ
        # =========================================================================
        template_path = os.path.join(current_app.root_path, 'static', 'hourly_template.xlsx')
        if not os.path.exists(template_path):
            if os.path.exists(template_path + ".xlsx"):
                template_path += ".xlsx"
            else:
                flash("Загвар файл олдсонгүй!", "danger")
                return redirect(url_for('main.index'))

        with open(template_path, "rb") as f:
            output = BytesIO(f.read())

        wb = load_workbook(output)
        ws = wb.active

        center_align = Alignment(horizontal='center', vertical='center')
        font_reg = Font(name='Times New Roman', size=12)
        font_bold = Font(name='Times New Roman', size=12, bold=False)

        # -------------------------------------------------------------
        # HEADER & COUNTER
        # -------------------------------------------------------------
        setting_key = f"report_counter_{start_time.year}"
        last_update_key = f"last_update_{start_time.year}"

        setting_count = SystemSettingRepository.get('report_config', setting_key)
        setting_last = SystemSettingRepository.get('report_config', last_update_key)

        current_count = int(setting_count.value) if setting_count else 0
        last_updated_date = setting_last.value if setting_last else ""
        today_str = start_time.strftime('%Y-%m-%d')

        if report_time_str == "07:00" and last_updated_date != today_str:
            current_count += 1
            if not setting_count:
                db.session.add(SystemSetting(category='report_config', key=setting_key, value=str(current_count)))
            else:
                setting_count.value = str(current_count)
            if not setting_last:
                db.session.add(SystemSetting(category='report_config', key=last_update_key, value=today_str))
            else:
                setting_last.value = today_str
            safe_commit(error_msg="Тайлангийн тоолуур хадгалахад алдаа гарлаа")

        display_count = current_count if current_count > 0 else 1

        ws['E10'] = f"{start_time.year}_{display_count:03d}"
        ws['E10'].font = font_reg
        ws['E10'].alignment = Alignment(horizontal='left', vertical='center')

        ws['E11'] = start_time.strftime('%d-%b-%Y')
        ws['E11'].font = font_reg
        ws['E11'].alignment = Alignment(horizontal='left', vertical='center')

        ws['O3'] = f"№ {start_time.strftime('%y-%m-%d')}"
        ws['O3'].font = Font(name='Times New Roman', size=14, bold=True)
        ws['O3'].alignment = Alignment(horizontal='right', vertical='center')

        ws['C4'] = start_time.strftime('%Y.%m.%d')
        ws['C4'].font = font_reg

        # =========================================================================
        # 4. ХЭСЭГ 1: 2 HOURLY ДЭЭЖҮҮД (FIXED POSITIONING)
        # =========================================================================
        samples_2h = Sample.query.filter(
            Sample.received_date >= start_time,
            Sample.received_date <= end_time,
            Sample.client_name == 'CHPP',
            Sample.sample_type.in_(['2 hourly', '2 Hourly'])
        ).all()

        row_is_partial = {20: True, 33: True, 46: True, 59: False, 72: False}

        for s in samples_2h:
            code_upper = (s.sample_code or "").strip().upper()
            calc = s.get_calculations()

            # 1. СУУРЬ МӨРӨӨ ОЛОХ
            start_row = None
            for pf_key, r_num in PF_MAPPING.items():
                if pf_key in code_upper:
                    start_row = r_num
                    break

            if not start_row:
                for k in HCC_KEYWORDS:
                    if k in code_upper:
                        start_row = 59
                        break
                if not start_row and "UHG MASHCC" in code_upper and "MASHCC_2" not in code_upper:
                    start_row = 59

            if not start_row:
                for k in MIDD_KEYWORDS:
                    if k in code_upper:
                        start_row = 72
                        break

            if not start_row:
                start_row = 59

            # 2. ШИЛЖИЛТЭЭ ОЛОХ
            row_offset = 0
            for suffix, offset in SUFFIX_OFFSET_MAP.items():
                if f"_{suffix}" in code_upper or code_upper.endswith(suffix):
                    row_offset = offset
                    break

            final_row = start_row + row_offset

            # 3. БИЧИХ
            def w_cell(c, v, f=font_reg):
                cell = ws.cell(row=final_row, column=c, value=v)
                cell.alignment = center_align
                cell.font = f

            w_cell(COL_2H_NAME, s.sample_code, font_bold)

            w_cell(COL_2H_MT, calc.mt if calc.mt is not None else "-")
            w_cell(COL_2H_AAD, calc.aad if calc.aad is not None else "-")
            w_cell(COL_2H_GI, int(calc.gi) if calc.gi is not None else "-")

            if not row_is_partial[start_row]:
                w_cell(COL_2H_MAD, calc.mad if calc.mad is not None else "-")
                w_cell(COL_2H_AD, round(calc.ash_dry, 2) if calc.ash_dry is not None else "-")
                w_cell(COL_2H_VAD, round(calc.vad, 2) if calc.vad is not None else "-")
                v_daf = getattr(calc, 'volatiles_daf', None)
                w_cell(COL_2H_VDAF, round(v_daf, 2) if v_daf is not None else "-")

        # =========================================================================
        # 5. ХЭСЭГ 2: 4 HOURLY
        # =========================================================================
        samples_4h = Sample.query.filter(
            Sample.received_date >= start_time,
            Sample.received_date <= end_time,
            Sample.client_name == 'CHPP',
            Sample.sample_type.in_(['4 hourly', '4 Hourly'])
        ).all()

        for s in samples_4h:
            hour = s.received_date.hour
            code_upper = (s.sample_code or "").strip().upper()
            calc = s.get_calculations()

            base_row = None
            for (h_start, h_end), r_num in ROW_BUCKETS_4H.items():
                if h_start < h_end:
                    if h_start <= hour < h_end:
                        base_row = r_num
                        break
                else:
                    if hour >= h_start or hour < h_end:
                        base_row = r_num
                        break

            target_cols = None
            row_offset = 0

            for cf_key, conf in CF_OFFSET_MAP.items():
                if cf_key in code_upper:
                    target_cols = conf["cols"]
                    row_offset = conf["offset"]
                    break

            if base_row and target_cols:
                final_row = base_row + row_offset

                val_aad = calc.aad if calc.aad is not None else "-"
                cell_aad = ws.cell(row=final_row, column=target_cols['Aad'], value=val_aad)
                cell_aad.alignment = center_align
                cell_aad.font = font_reg

                val_fm = getattr(calc, 'fm', None)
                if val_fm is None:
                    val_fm = calc.mt
                final_fm = val_fm if val_fm is not None else "-"

                cell_fm = ws.cell(row=final_row, column=target_cols['FM'], value=final_fm)
                cell_fm.alignment = center_align
                cell_fm.font = font_reg

        # =========================================================================
        # 6. ХАДГАЛАХ
        # =========================================================================
        final_output = BytesIO()
        wb.save(final_output)
        final_output.seek(0)

        filename = f"Hourly_Report_{report_date_str}_{report_time_str.replace(':', '')}.xlsx"
        email_subject = f"Hourly Report {report_time_str}"

        sender_name = current_user.full_name or current_user.username
        sender_position = current_user.position or "Senior Chemist, Laboratory"
        sender_email = current_user.email or "lab@energyresources.mn"
        sender_phone = current_user.phone or ""

        phone_display = f"|Mobile: (976) {sender_phone}" if sender_phone else ""

        email_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #000000;">
            <p>Dear all,</p>
            <p>Please see the <strong>{report_time_str}</strong> hour sample results from the attachment.</p>
            <br>
            <p>Regards,</p>
            <p>
                <b>{sender_name}</b><br>
                {sender_position}
            </p>
            <p>
                <b>ENERGY RESOURCES LLC</b><br>
                | Ukhaa Khudag Branch, Tsogttsetsii soum, Umnugobi province 46040 , MONGOLIA|<br>
                |Tel.: (976)7012 2279, 7013 2279 |Fax: (976) 11 322279 {phone_display}<br>
                |{sender_email} | <a href="http://www.mmc.mn/">http://www.mmc.mn/</a> |
            </p>
            <div style="border-top: 1px solid #000; margin-top: 10px; padding-top: 5px;">
                <span style="font-size: 11px; color: #555;">
                    This email is CONFIDENTIAL and is intended only for
                    the use of the person to whom it is addressed.<br>
                    Any distribution, copying or other use by anyone else
                    is strictly prohibited.<br>
                    If you have received this email in error, please telephone
                    or email us immediately and destroy this email.
                </span>
            </div>
        </div>
        """

        email_recipients = get_report_email_recipients()
        to_list = email_recipients['to']
        cc_list = email_recipients['cc']

        if not to_list:
            flash("Имэйл хүлээн авагч тохируулагдаагүй байна. Тохиргооноос тохируулна уу.", "warning")
            return redirect(url_for('main.index'))

        msg = Message(
            subject=email_subject,
            recipients=to_list,
            cc=cc_list if cc_list else None,
            html=email_html
        )
        msg.attach(filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", final_output.read())
        mail.send(msg)

        sent_to = ", ".join(to_list)
        if cc_list:
            sent_to += f" (CC: {', '.join(cc_list)})"
        flash(f"Амжилттай илгээгдлээ! → {sent_to}", "success")

    except (OSError, RuntimeError, ValueError) as e:
        current_app.logger.exception("Error in send_hourly_report")
        flash("Имэйл илгээхэд алдаа гарлаа.", "danger")

    return redirect(url_for('main.index'))
