# -*- coding: utf-8 -*-
"""
Theoretical Yield Routes

Washability test импорт, тооцоолол, харьцуулалт
"""

import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import WashabilityTest, WashabilityFraction, TheoreticalYield, PlantYield
from app.utils.excel_import import (
    import_washability_excel, calculate_and_store_yields
)
from app.utils.washability import (
    FractionData, calculate_theoretical_yield, analyze_washability_quality
)

yield_bp = Blueprint('yield', __name__, url_prefix='/yield')


# ==============================================================================
# VIEWS
# ==============================================================================

@yield_bp.route('/')
@login_required
def index():
    """Yield тооцооллын үндсэн хуудас"""
    tests = WashabilityTest.query.order_by(WashabilityTest.sample_date.desc()).limit(50).all()
    return render_template('yield/index.html', tests=tests)


@yield_bp.route('/test/<int:test_id>')
@login_required
def test_detail(test_id):
    """Washability test дэлгэрэнгүй харах"""
    test = WashabilityTest.query.get_or_404(test_id)

    # Get yields grouped by size fraction
    yields_by_size = {}
    for y in test.yields.order_by(TheoreticalYield.target_ash).all():
        if y.size_fraction not in yields_by_size:
            yields_by_size[y.size_fraction] = []
        yields_by_size[y.size_fraction].append(y)

    # Get fractions grouped by size
    fractions_by_size = {}
    for f in test.fractions.order_by(WashabilityFraction.density_float).all():
        if f.size_fraction not in fractions_by_size:
            fractions_by_size[f.size_fraction] = []
        fractions_by_size[f.size_fraction].append(f)

    return render_template('yield/test_detail.html',
                           test=test,
                           yields_by_size=yields_by_size,
                           fractions_by_size=fractions_by_size)


@yield_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_excel():
    """Excel файл импортлох"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith(('.xlsx', '.xls')):
            filename = secure_filename(file.filename)

            # Save temporarily
            upload_folder = os.path.join(current_app.root_path, 'uploads', 'washability')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            try:
                # Import
                test = import_washability_excel(file_path, current_user.id)

                # Calculate yields
                target_ashes = request.form.getlist('target_ash')
                if target_ashes:
                    target_ashes = [float(a) for a in target_ashes]
                else:
                    target_ashes = [8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]

                calculate_and_store_yields(test, target_ashes)

                flash(f'Successfully imported: {test.lab_number} - {test.sample_name}', 'success')
                return redirect(url_for('yield.test_detail', test_id=test.id))

            except Exception as e:
                flash(f'Import error: {str(e)}', 'error')
                return redirect(request.url)

            finally:
                # Clean up temp file
                if os.path.exists(file_path):
                    os.remove(file_path)

    return render_template('yield/import.html')


@yield_bp.route('/compare')
@login_required
def compare():
    """Theoretical vs Actual yield харьцуулалт"""
    tests = WashabilityTest.query.order_by(WashabilityTest.sample_date.desc()).all()
    plant_yields = PlantYield.query.order_by(PlantYield.production_date.desc()).limit(100).all()

    return render_template('yield/compare.html',
                           tests=tests,
                           plant_yields=plant_yields)


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@yield_bp.route('/api/tests')
@login_required
def api_list_tests():
    """Washability test жагсаалт API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = WashabilityTest.query.order_by(WashabilityTest.sample_date.desc())

    # Filters
    if request.args.get('sample_name'):
        query = query.filter(WashabilityTest.sample_name.ilike(f"%{request.args.get('sample_name')}%"))

    if request.args.get('date_from'):
        query = query.filter(WashabilityTest.sample_date >= request.args.get('date_from'))

    if request.args.get('date_to'):
        query = query.filter(WashabilityTest.sample_date <= request.args.get('date_to'))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tests': [{
            'id': t.id,
            'lab_number': t.lab_number,
            'sample_name': t.sample_name,
            'sample_date': t.sample_date.isoformat() if t.sample_date else None,
            'raw_ash': t.raw_ash,
            'source': t.source
        } for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@yield_bp.route('/api/test/<int:test_id>')
@login_required
def api_test_detail(test_id):
    """Washability test дэлгэрэнгүй API"""
    test = WashabilityTest.query.get_or_404(test_id)

    fractions_data = {}
    for f in test.fractions.all():
        if f.size_fraction not in fractions_data:
            fractions_data[f.size_fraction] = []
        fractions_data[f.size_fraction].append({
            'density_sink': f.density_sink,
            'density_float': f.density_float,
            'mass_gram': f.mass_gram,
            'mass_percent': f.mass_percent,
            'ash_ad': f.ash_ad,
            'cumulative_yield': f.cumulative_yield,
            'cumulative_ash': f.cumulative_ash
        })

    yields_data = {}
    for y in test.yields.all():
        if y.size_fraction not in yields_data:
            yields_data[y.size_fraction] = []
        yields_data[y.size_fraction].append({
            'target_ash': y.target_ash,
            'theoretical_yield': y.theoretical_yield,
            'separation_density': y.separation_density,
            'ngm_01': y.ngm_plus_01,
            'quality': analyze_washability_quality(y.ngm_plus_01) if y.ngm_plus_01 else None
        })

    return jsonify({
        'test': {
            'id': test.id,
            'lab_number': test.lab_number,
            'sample_name': test.sample_name,
            'sample_date': test.sample_date.isoformat() if test.sample_date else None,
            'report_date': test.report_date.isoformat() if test.report_date else None,
            'consignor': test.consignor,
            'initial_mass_kg': test.initial_mass_kg,
            'raw_coal': {
                'tm': test.raw_tm,
                'im': test.raw_im,
                'ash': test.raw_ash,
                'vol': test.raw_vol,
                'sulphur': test.raw_sulphur,
                'csn': test.raw_csn,
                'gi': test.raw_gi,
                'trd': test.raw_trd
            }
        },
        'fractions': fractions_data,
        'yields': yields_data
    })


@yield_bp.route('/api/calculate', methods=['POST'])
@login_required
def api_calculate_yield():
    """Custom theoretical yield тооцоолох API"""
    data = request.get_json()

    test_id = data.get('test_id')
    target_ash = data.get('target_ash')
    size_fraction = data.get('size_fraction', 'ALL')

    if not test_id or target_ash is None:
        return jsonify({'error': 'test_id and target_ash are required'}), 400

    test = WashabilityTest.query.get_or_404(test_id)

    # Get fractions
    query = test.fractions
    if size_fraction and size_fraction != 'ALL':
        query = query.filter_by(size_fraction=size_fraction)

    fractions = [FractionData(
        density_sink=f.density_sink or 0,
        density_float=f.density_float or 0,
        mass_gram=f.mass_gram or 0,
        mass_percent=f.mass_percent or 0,
        ash_ad=f.ash_ad or 0
    ) for f in query.all()]

    result = calculate_theoretical_yield(fractions, float(target_ash))

    return jsonify({
        'target_ash': result.target_ash,
        'theoretical_yield': result.theoretical_yield,
        'separation_density': result.separation_density,
        'ngm_01': result.ngm_01,
        'ngm_02': result.ngm_02,
        'quality': analyze_washability_quality(result.ngm_01)
    })


@yield_bp.route('/api/curve/<int:test_id>')
@login_required
def api_washability_curve(test_id):
    """Washability curve дата API (график-д)"""
    test = WashabilityTest.query.get_or_404(test_id)
    size_fraction = request.args.get('size_fraction')

    curves = {}

    # Group fractions by size
    size_groups = {}
    for f in test.fractions.all():
        if f.size_fraction not in size_groups:
            size_groups[f.size_fraction] = []
        size_groups[f.size_fraction].append(f)

    for size_name, fractions in size_groups.items():
        if size_fraction and size_name != size_fraction:
            continue

        # Sort by density
        fractions.sort(key=lambda x: x.density_float or 0)

        curves[size_name] = {
            'yield': [f.cumulative_yield for f in fractions if f.cumulative_yield],
            'ash': [f.cumulative_ash for f in fractions if f.cumulative_ash],
            'density': [f.density_float for f in fractions if f.density_float]
        }

    return jsonify(curves)


@yield_bp.route('/api/plant_yield', methods=['POST'])
@login_required
def api_add_plant_yield():
    """Үйлдвэрийн бодит гарц нэмэх API"""
    data = request.get_json()

    plant_yield = PlantYield(
        production_date=data.get('production_date'),
        shift=data.get('shift'),
        coal_source=data.get('coal_source'),
        product_type=data.get('product_type'),
        feed_tonnes=data.get('feed_tonnes'),
        product_tonnes=data.get('product_tonnes'),
        feed_ash=data.get('feed_ash'),
        product_ash=data.get('product_ash'),
        washability_test_id=data.get('washability_test_id'),
        notes=data.get('notes')
    )

    # Calculate actual yield
    if plant_yield.feed_tonnes and plant_yield.product_tonnes:
        plant_yield.actual_yield = (plant_yield.product_tonnes / plant_yield.feed_tonnes) * 100

    # If linked to washability test, get theoretical yield
    if plant_yield.washability_test_id and plant_yield.product_ash:
        theoretical = TheoreticalYield.query.filter_by(
            test_id=plant_yield.washability_test_id,
            size_fraction='ALL',
            target_ash=round(plant_yield.product_ash, 1)
        ).first()

        if theoretical:
            plant_yield.theoretical_yield = theoretical.theoretical_yield
            if plant_yield.actual_yield and theoretical.theoretical_yield:
                plant_yield.recovery_efficiency = (plant_yield.actual_yield / theoretical.theoretical_yield) * 100

    db.session.add(plant_yield)
    db.session.commit()

    return jsonify({
        'id': plant_yield.id,
        'actual_yield': plant_yield.actual_yield,
        'theoretical_yield': plant_yield.theoretical_yield,
        'recovery_efficiency': plant_yield.recovery_efficiency
    })


@yield_bp.route('/api/comparison')
@login_required
def api_comparison_data():
    """Theoretical vs Actual харьцуулалтын дата API"""
    # Get plant yields with linked washability tests
    plant_yields = PlantYield.query.filter(
        PlantYield.washability_test_id.isnot(None)
    ).order_by(PlantYield.production_date.desc()).limit(100).all()

    data = []
    for py in plant_yields:
        data.append({
            'date': py.production_date.isoformat() if py.production_date else None,
            'product_type': py.product_type,
            'actual_yield': py.actual_yield,
            'theoretical_yield': py.theoretical_yield,
            'recovery_efficiency': py.recovery_efficiency,
            'product_ash': py.product_ash,
            'sample_name': py.washability_test.sample_name if py.washability_test else None
        })

    return jsonify(data)


@yield_bp.route('/api/trend')
@login_required
def api_yield_trend():
    """Yield trend дата (цаг хугацааны хандлага)"""
    from sqlalchemy import func

    # Monthly average yields
    monthly_data = db.session.query(
        func.date_trunc('month', PlantYield.production_date).label('month'),
        func.avg(PlantYield.actual_yield).label('avg_actual'),
        func.avg(PlantYield.theoretical_yield).label('avg_theoretical'),
        func.avg(PlantYield.recovery_efficiency).label('avg_recovery')
    ).group_by(
        func.date_trunc('month', PlantYield.production_date)
    ).order_by('month').all()

    return jsonify([{
        'month': row.month.isoformat() if row.month else None,
        'avg_actual': round(row.avg_actual, 2) if row.avg_actual else None,
        'avg_theoretical': round(row.avg_theoretical, 2) if row.avg_theoretical else None,
        'avg_recovery': round(row.avg_recovery, 2) if row.avg_recovery else None
    } for row in monthly_data])
