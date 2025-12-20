# -*- coding: utf-8 -*-
"""
License Routes - Лицензийн хуудсууд
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from datetime import datetime

from app.utils.license_protection import license_manager
from app.utils.hardware_fingerprint import get_hardware_info, generate_short_hardware_id

license_bp = Blueprint('license', __name__, url_prefix='/license')


@license_bp.route('/activate', methods=['GET', 'POST'])
def activate():
    """Лиценз идэвхжүүлэх хуудас"""
    hardware_info = get_hardware_info()

    if request.method == 'POST':
        license_key = request.form.get('license_key', '').strip()

        if not license_key:
            flash('Лиценз түлхүүр оруулна уу.', 'error')
            return render_template('license/activate.html', hardware_info=hardware_info)

        # Лиценз идэвхжүүлэх
        result = license_manager.activate_license(license_key)

        if result['success']:
            flash('Лиценз амжилттай идэвхжлээ!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash(f'Лиценз идэвхжүүлэхэд алдаа: {result["error"]}', 'error')

    return render_template('license/activate.html', hardware_info=hardware_info)


@license_bp.route('/expired')
def expired():
    """Лиценз дууссан хуудас"""
    license_obj = license_manager.get_current_license()
    hardware_id = generate_short_hardware_id()
    return render_template('license/expired.html', license=license_obj, hardware_id=hardware_id)


@license_bp.route('/error')
def error():
    """Лицензийн алдааны хуудас"""
    license_obj = license_manager.get_current_license()
    hardware_id = generate_short_hardware_id()
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
def check():
    """Лиценз шалгах API"""
    result = license_manager.validate_license()

    return jsonify({
        'valid': result['valid'],
        'error': result.get('error'),
        'warning': result.get('warning'),
        'days_remaining': result['license'].days_remaining if result.get('license') else 0,
        'company': result['license'].company_name if result.get('license') else None
    })


@license_bp.route('/hardware-id')
def hardware_id():
    """Hardware ID авах (идэвхжүүлэхэд хэрэгтэй)"""
    info = get_hardware_info()
    return jsonify({
        'hardware_id': info['hardware_id'],
        'short_id': info['short_id'],
        'hostname': info['hostname']
    })
