# -*- coding: utf-8 -*-
"""
License Routes - Лицензийн хуудсууд
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l

from app.utils.license_protection import license_manager
from app.utils.hardware_fingerprint import get_hardware_info, generate_short_hardware_id

license_bp = Blueprint('license', __name__, url_prefix='/license')


@license_bp.route('/activate', methods=['GET', 'POST'])
@login_required
def activate():
    """Лиценз идэвхжүүлэх хуудас"""
    if current_user.role != 'admin':
        flash(_l('Зөвхөн админ лиценз идэвхжүүлэх боломжтой.'), 'danger')
        return redirect(url_for('main.index'))
    hardware_info = get_hardware_info()

    if request.method == 'POST':
        license_key = request.form.get('license_key', '').strip()

        if not license_key:
            flash(_l('Лицензийн түлхүүр оруулна уу.'), 'error')
            return render_template('license/activate.html', hardware_info=hardware_info)

        # Лиценз идэвхжүүлэх
        result = license_manager.activate_license(license_key)

        if result['success']:
            flash(_l('Лиценз амжилттай идэвхжүүлэгдлээ!'), 'success')
            return redirect(url_for('main.index'))
        else:
            flash(f'Лиценз идэвхжүүлэхэд алдаа: {result["error"]}', 'error')

    return render_template('license/activate.html', hardware_info=hardware_info)


@license_bp.route('/expired')
@login_required
def expired():
    """Лиценз дууссан хуудас"""
    license_obj = license_manager.get_current_license()
    hardware_id = generate_short_hardware_id() if current_user.role == 'admin' else None
    return render_template('license/expired.html', license=license_obj, hardware_id=hardware_id)


@license_bp.route('/error')
@login_required
def error():
    """Лицензийн алдааны хуудас"""
    license_obj = license_manager.get_current_license()
    hardware_id = generate_short_hardware_id() if current_user.role == 'admin' else None
    return render_template('license/error.html', license=license_obj, hardware_id=hardware_id)


@license_bp.route('/info')
@login_required
def info():
    """Лицензийн мэдээлэл харах"""
    license_obj = license_manager.get_current_license()
    hardware_info = get_hardware_info()

    return render_template('license/info.html',
                           license=license_obj,
                           hardware_info=hardware_info)


@license_bp.route('/check')
@login_required
def check():
    """Лиценз шалгах API"""
    result = license_manager.validate_license()

    return jsonify({
        'valid': result['valid'],
        'error': result.get('error'),
        'warning': result.get('warning'),
        'days_remaining': result['license'].days_remaining if result.get('license') else 0,
    })


@license_bp.route('/hardware-id')
@login_required
def hardware_id():
    """Hardware ID авах (идэвхжүүлэхэд хэрэгтэй) — зөвхөн админ"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Хандах эрхгүй'}), 403
    info = get_hardware_info()
    return jsonify({
        'hardware_id': info['hardware_id'],
        'short_id': info['short_id'],
        'hostname': info['hostname']
    })
