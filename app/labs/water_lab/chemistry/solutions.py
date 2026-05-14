# app/labs/water_lab/chemistry/solutions.py
# -*- coding: utf-8 -*-
"""Уусмал бэлдэх дэвтэр (Solution Journal) + Уусмалын жор (Solution Recipes)."""

import logging
from datetime import datetime, date

from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.repositories import ChemicalRepository
from app.utils.decorators import lab_required
from app.utils.converters import to_float
from app.labs.water_lab.chemistry.routes import water_bp

logger = logging.getLogger(__name__)


# ============================================================
# УУСМАЛ БЭЛДЭХ ДЭВТЭР (Solution Journal)
# ============================================================

@water_bp.route('/solution_journal')
@login_required
@lab_required('water_chemistry')
def solution_journal():
    """Уусмал бэлдэх дэвтэр - жагсаалт."""
    from app.models import SolutionPreparation
    from datetime import timedelta

    # Шүүлтүүр
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'all')

    query = SolutionPreparation.query

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(SolutionPreparation.prepared_date >= start_dt)
        except (ValueError, TypeError):
            start_date = None

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(SolutionPreparation.prepared_date <= end_dt)
        except (ValueError, TypeError):
            end_date = None

    if status and status != 'all':
        query = query.filter(SolutionPreparation.status == status)

    solutions = query.order_by(SolutionPreparation.prepared_date.desc()).all()

    # Статистик
    today = date.today()
    stats = {
        'total': SolutionPreparation.query.count(),
        'active': SolutionPreparation.query.filter_by(status='active').count(),
        'expired': SolutionPreparation.query.filter(
            SolutionPreparation.expiry_date < today
        ).count(),
    }

    return render_template(
        'labs/water/chemistry/solution_journal.html',
        title='Уусмал бэлдэх дэвтэр',
        solutions=solutions,
        stats=stats,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )


@water_bp.route('/solution_journal/add', methods=['GET', 'POST'])
@login_required
@lab_required('water_chemistry')
def add_solution():
    """Шинэ уусмал бүртгэх."""
    from app.models import SolutionPreparation, Chemical, ChemicalUsage, ChemicalLog

    if request.method == 'POST':
        try:
            # Огноо parse
            prepared_date = datetime.strptime(
                request.form.get('prepared_date'), '%Y-%m-%d'
            ).date()

            expiry_date = None
            if request.form.get('expiry_date'):
                expiry_date = datetime.strptime(
                    request.form.get('expiry_date'), '%Y-%m-%d'
                ).date()

            # Float талбарууд
            chemical_used_mg = to_float(request.form.get('chemical_used_mg'))
            chemical_id = request.form.get('chemical_id')

            solution = SolutionPreparation(
                solution_name=request.form.get('solution_name'),
                concentration=to_float(request.form.get('concentration')),
                concentration_unit=request.form.get('concentration_unit', 'mg/L'),
                volume_ml=to_float(request.form.get('volume_ml')),
                chemical_used_mg=chemical_used_mg,
                prepared_date=prepared_date,
                expiry_date=expiry_date,
                v1=to_float(request.form.get('v1')),
                v2=to_float(request.form.get('v2')),
                v3=to_float(request.form.get('v3')),
                titer_coefficient=to_float(request.form.get('titer_coefficient')),
                preparation_notes=request.form.get('preparation_notes'),
                prepared_by_id=current_user.id,
            )

            # Дундаж тооцоолох
            solution.calculate_v_avg()

            # Chemical холбох + автомат зарцуулалт
            if chemical_id and chemical_used_mg and chemical_used_mg > 0:
                chemical = db.session.get(Chemical, int(chemical_id))
                if chemical:
                    solution.chemical_id = chemical.id

                    # mg → g хөрвүүлэх (хэрэв chemical нь g нэгжтэй бол)
                    quantity_to_deduct = chemical_used_mg
                    if chemical.unit == 'g':
                        quantity_to_deduct = chemical_used_mg / 1000  # mg to g
                    elif chemical.unit == 'kg':
                        quantity_to_deduct = chemical_used_mg / 1000000  # mg to kg
                    elif chemical.unit == 'mL' or chemical.unit == 'L':
                        if chemical.unit == 'L':
                            quantity_to_deduct = chemical_used_mg / 1000000
                        else:
                            quantity_to_deduct = chemical_used_mg / 1000

                    old_quantity = chemical.quantity

                    # Хүрэлцэхгүй бол анхааруулга
                    if quantity_to_deduct > chemical.quantity:
                        flash(f"Warning: {chemical.name} stock ({chemical.quantity} {chemical.unit}) is insufficient!", 'warning')

                    # Хасах
                    chemical.quantity = max(0, chemical.quantity - quantity_to_deduct)
                    new_quantity = chemical.quantity

                    # ChemicalUsage бүртгэл үүсгэх
                    usage = ChemicalUsage(
                        chemical_id=chemical.id,
                        quantity_used=quantity_to_deduct,
                        unit=chemical.unit,
                        purpose=f"Уусмал бэлдэх: {solution.solution_name}",
                        analysis_code='SOLUTION_PREP',
                        used_by_id=current_user.id,
                        quantity_before=old_quantity,
                        quantity_after=new_quantity,
                    )
                    db.session.add(usage)

                    # ChemicalLog аудит бүртгэл (with hash - ISO 17025)
                    log = ChemicalLog(
                        chemical_id=chemical.id,
                        user_id=current_user.id,
                        action='consumed',
                        quantity_change=-quantity_to_deduct,
                        quantity_before=old_quantity,
                        quantity_after=new_quantity,
                        details=f"Уусмал бэлдэхэд зарцуулав: {solution.solution_name} ({chemical_used_mg} мг)"
                    )
                    log.data_hash = log.compute_hash()
                    db.session.add(log)

                    # Химийн бодисын төлөв шинэчлэх
                    chemical.update_status()

            db.session.add(solution)
            db.session.commit()

            flash(f"'{solution.solution_name}' registered successfully.", 'success')
            return redirect(url_for('water.solution_journal'))

        except (ValueError, TypeError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.exception('add_solution error')
            flash(_l('Уусмал нэмэхэд алдаа гарлаа.'), 'danger')

    # GET - Химийн бодисын жагсаалт
    chemicals = ChemicalRepository.get_for_water_lab()

    return render_template(
        'labs/water/chemistry/solution_form.html',
        title='Шинэ уусмал бүртгэх',
        solution=None,
        chemicals=chemicals,
        mode='add',
    )


@water_bp.route('/solution_journal/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@lab_required('water_chemistry')
def edit_solution(id):
    """Уусмал засварлах."""
    from app.models import SolutionPreparation, Chemical

    solution = SolutionPreparation.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Огноо parse
            solution.prepared_date = datetime.strptime(
                request.form.get('prepared_date'), '%Y-%m-%d'
            ).date()

            if request.form.get('expiry_date'):
                solution.expiry_date = datetime.strptime(
                    request.form.get('expiry_date'), '%Y-%m-%d'
                ).date()
            else:
                solution.expiry_date = None

            # Float талбарууд
            solution.solution_name = request.form.get('solution_name')
            solution.concentration = to_float(request.form.get('concentration'))
            solution.concentration_unit = request.form.get('concentration_unit', 'mg/L')
            solution.volume_ml = to_float(request.form.get('volume_ml'))
            solution.chemical_used_mg = to_float(request.form.get('chemical_used_mg'))
            solution.v1 = to_float(request.form.get('v1'))
            solution.v2 = to_float(request.form.get('v2'))
            solution.v3 = to_float(request.form.get('v3'))
            solution.titer_coefficient = to_float(request.form.get('titer_coefficient'))
            solution.preparation_notes = request.form.get('preparation_notes')
            solution.status = request.form.get('status', 'active')

            # Дундаж тооцоолох
            solution.calculate_v_avg()

            # Chemical холбох
            chemical_id = request.form.get('chemical_id')
            if chemical_id:
                solution.chemical_id = int(chemical_id)
            else:
                solution.chemical_id = None

            db.session.commit()
            flash('Updated successfully.', 'success')
            return redirect(url_for('water.solution_journal'))

        except (ValueError, TypeError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.exception('edit_solution error: id=%s', id)
            flash(_l('Уусмал засахад алдаа гарлаа.'), 'danger')

    # GET
    chemicals = ChemicalRepository.get_for_water_lab()

    return render_template(
        'labs/water/chemistry/solution_form.html',
        title='Уусмал засварлах',
        solution=solution,
        chemicals=chemicals,
        mode='edit',
    )


@water_bp.route('/solution_journal/delete/<int:id>', methods=['POST'])
@login_required
@lab_required('water_chemistry')
def delete_solution(id):
    """Уусмал устгах."""
    from app.models import SolutionPreparation, Chemical, ChemicalLog
    from app.utils.database import safe_commit

    if current_user.role not in ('senior', 'admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('water.solution_journal'))

    solution = SolutionPreparation.query.get_or_404(id)
    name = solution.solution_name

    if solution.chemical_id and solution.chemical_used_mg:
        chemical = db.session.get(Chemical, solution.chemical_id)
        if chemical:
            quantity_to_return = solution.chemical_used_mg
            if chemical.unit == 'g':
                quantity_to_return = solution.chemical_used_mg / 1000
            elif chemical.unit == 'kg':
                quantity_to_return = solution.chemical_used_mg / 1000000

            old_quantity = chemical.quantity
            chemical.quantity += quantity_to_return
            new_quantity = chemical.quantity

            # Аудит бичлэг
            log = ChemicalLog(
                chemical_id=chemical.id,
                user_id=current_user.id,
                action='returned',
                quantity_change=quantity_to_return,
                quantity_before=old_quantity,
                quantity_after=new_quantity,
                details=f"Уусмал устгагдсан тул буцаав: {name}"
            )
            log.data_hash = log.compute_hash()
            db.session.add(log)
            chemical.update_status()

    db.session.delete(solution)
    if not safe_commit():
        flash('DB error.', 'danger')
        return redirect(url_for('water.solution_journal'))

    flash(f"'{name}' deleted.", 'warning')
    return redirect(url_for('water.solution_journal'))


@water_bp.route('/api/solutions')
@login_required
@lab_required('water_chemistry')
def api_solutions():
    """Уусмалын жагсаалт API."""
    from app.models import SolutionPreparation

    solutions = SolutionPreparation.query.order_by(
        SolutionPreparation.prepared_date.desc()
    ).all()

    data = [{
        'id': s.id,
        'solution_name': s.solution_name,
        'concentration': s.concentration,
        'concentration_unit': s.concentration_unit,
        'volume_ml': s.volume_ml,
        'chemical_used_mg': s.chemical_used_mg,
        'prepared_date': s.prepared_date.strftime('%Y-%m-%d') if s.prepared_date else '',
        'expiry_date': s.expiry_date.strftime('%Y-%m-%d') if s.expiry_date else '',
        'v1': s.v1,
        'v2': s.v2,
        'v3': s.v3,
        'v_avg': s.v_avg,
        'titer_coefficient': s.titer_coefficient,
        'status': s.status,
        'prepared_by': s.prepared_by.username if s.prepared_by else '',
    } for s in solutions]

    return jsonify(data)


# ============================================================
# УУСМАЛЫН ЖОР (Solution Recipes) - Карт систем
# ============================================================

def convert_recipe_unit_to_chemical(amount, recipe_unit, chemical_unit):
    """
    Жорын нэгжийг химийн бодисын нэгж рүү хөрвүүлэх.
    """
    # Эхлээд грамм руу хөрвүүлэх
    if recipe_unit == 'mg':
        amount_g = amount / 1000
    elif recipe_unit == 'g':
        amount_g = amount
    elif recipe_unit == 'kg':
        amount_g = amount * 1000
    elif recipe_unit == 'mL':
        amount_g = amount  # Нягт ~1 гэж үзнэ
    elif recipe_unit == 'L':
        amount_g = amount * 1000
    else:
        amount_g = amount

    # Химийн бодисын нэгж рүү хөрвүүлэх
    if chemical_unit == 'mg':
        return amount_g * 1000
    elif chemical_unit == 'g':
        return amount_g
    elif chemical_unit == 'kg':
        return amount_g / 1000
    elif chemical_unit == 'mL':
        return amount_g  # Нягт ~1 гэж үзнэ
    elif chemical_unit == 'L':
        return amount_g / 1000
    else:
        return amount_g


@water_bp.route('/solution_recipes')
@login_required
@lab_required('water_chemistry')
def solution_recipes():
    """Уусмалын жорын жагсаалт - карт хэлбэрээр."""
    from app.models import SolutionRecipe, SolutionPreparation

    recipes = SolutionRecipe.query.filter_by(
        lab_type='water_chemistry', is_active=True
    ).order_by(SolutionRecipe.name).all()

    # Recipe бүрийн статистик — нэг query-р авах
    recipe_ids = [r.id for r in recipes]
    recipe_stats = {rid: {'last_prep': None, 'prep_count': 0} for rid in recipe_ids}

    if recipe_ids:
        count_rows = db.session.query(
            SolutionPreparation.recipe_id,
            func.count(SolutionPreparation.id),
            func.max(SolutionPreparation.prepared_date),
        ).filter(
            SolutionPreparation.recipe_id.in_(recipe_ids)
        ).group_by(SolutionPreparation.recipe_id).all()

        max_dates = {}
        for rid, cnt, max_date in count_rows:
            recipe_stats[rid]['prep_count'] = cnt
            max_dates[rid] = max_date

        # Сүүлийн бэлдэлтүүдийг нэг query-р авах
        if max_dates:
            last_preps = SolutionPreparation.query.filter(
                SolutionPreparation.recipe_id.in_(list(max_dates.keys()))
            ).order_by(SolutionPreparation.prepared_date.desc()).all()
            seen = set()
            for p in last_preps:
                if p.recipe_id not in seen:
                    recipe_stats[p.recipe_id]['last_prep'] = p
                    seen.add(p.recipe_id)

    return render_template(
        'labs/water/chemistry/solution_recipes.html',
        title='Уусмалын жор',
        recipes=recipes,
        recipe_stats=recipe_stats,
    )


@water_bp.route('/solution_recipes/<int:id>')
@login_required
@lab_required('water_chemistry')
def recipe_detail(id):
    """Уусмалын жорын дэлгэрэнгүй + найруулах форм."""
    from app.models import SolutionRecipe, SolutionPreparation

    recipe = SolutionRecipe.query.get_or_404(id)

    # Сүүлийн 10 бэлдэлт
    recent_preps = SolutionPreparation.query.filter_by(
        recipe_id=recipe.id
    ).order_by(SolutionPreparation.prepared_date.desc()).limit(10).all()

    # Орц бодисуудын одоогийн нөөц
    ingredients_info = []
    for ing in recipe.ingredients:
        chemical = ing.chemical
        if chemical:
            ingredients_info.append({
                'ingredient': ing,
                'chemical': chemical,
                'stock': chemical.quantity,
                'stock_unit': chemical.unit,
            })

    return render_template(
        'labs/water/chemistry/solution_recipe_detail.html',
        title=recipe.name,
        recipe=recipe,
        recent_preps=recent_preps,
        ingredients_info=ingredients_info,
    )


@water_bp.route('/solution_recipes/<int:id>/prepare', methods=['POST'])
@login_required
@lab_required('water_chemistry')
def prepare_from_recipe(id):
    """Жороор уусмал найруулах - химийн бодис автоматаар хасагдана."""
    from app.models import SolutionRecipe, SolutionPreparation, Chemical, ChemicalUsage, ChemicalLog

    recipe = SolutionRecipe.query.get_or_404(id)

    try:
        # Найруулах эзэлхүүн
        target_volume = float(request.form.get('volume_ml', recipe.standard_volume_ml or 1000))
        if not (0 < target_volume <= 100_000):
            raise ValueError(f"Эзэлхүүн хүчингүй: {target_volume}")

        # Шаардлагатай бодисуудыг тооцоолох
        required_ingredients = recipe.calculate_ingredients(target_volume)

        # Нөөц шалгах
        insufficient = []
        for item in required_ingredients:
            chemical = item['chemical']
            if chemical:
                required_amount = item['amount']
                converted_amount = convert_recipe_unit_to_chemical(
                    required_amount, item['unit'], chemical.unit
                )
                if converted_amount > chemical.quantity:
                    insufficient.append({
                        'chemical': chemical.name,
                        'required': f"{converted_amount:.4f} {chemical.unit}",
                        'available': f"{chemical.quantity:.4f} {chemical.unit}",
                    })

        if insufficient:
            msg = "Нөөц хүрэлцэхгүй: " + ", ".join(
                [f"{i['chemical']} (хэрэгтэй: {i['required']}, байгаа: {i['available']})" for i in insufficient]
            )
            flash(msg, 'danger')
            return redirect(url_for('water.recipe_detail', id=id))

        # Титрийн утгууд (optional)
        v1 = to_float(request.form.get('v1'))
        v2 = to_float(request.form.get('v2'))
        v3 = to_float(request.form.get('v3'))
        titer_coefficient = to_float(request.form.get('titer_coefficient'))

        # Хугацаа
        expiry_date = None
        if request.form.get('expiry_date'):
            expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()

        # Бэлдэлт үүсгэх
        preparation = SolutionPreparation(
            solution_name=recipe.name,
            concentration=recipe.concentration,
            concentration_unit=recipe.concentration_unit,
            volume_ml=target_volume,
            recipe_id=recipe.id,
            prepared_date=date.today(),
            expiry_date=expiry_date,
            v1=v1,
            v2=v2,
            v3=v3,
            titer_coefficient=titer_coefficient,
            preparation_notes=request.form.get('notes'),
            prepared_by_id=current_user.id,
        )

        # Дундаж тооцоолох
        preparation.calculate_v_avg()

        # Бодис хасах + бүртгэл
        total_consumed = []
        for item in required_ingredients:
            chemical = item['chemical']
            if chemical:
                required_amount = item['amount']
                converted_amount = convert_recipe_unit_to_chemical(
                    required_amount, item['unit'], chemical.unit
                )

                old_quantity = chemical.quantity
                chemical.quantity = max(0, chemical.quantity - converted_amount)
                new_quantity = chemical.quantity

                # ChemicalUsage бүртгэл
                usage = ChemicalUsage(
                    chemical_id=chemical.id,
                    quantity_used=converted_amount,
                    unit=chemical.unit,
                    purpose=f"Уусмал найруулах: {recipe.name} ({target_volume}мл)",
                    analysis_code='SOLUTION_PREP',
                    used_by_id=current_user.id,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                )
                db.session.add(usage)

                # ChemicalLog аудит (with hash - ISO 17025)
                log = ChemicalLog(
                    chemical_id=chemical.id,
                    user_id=current_user.id,
                    action='consumed',
                    quantity_change=-converted_amount,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                    details=f"Уусмал найруулахад зарцуулав: {recipe.name} ({target_volume}мл)"
                )
                log.data_hash = log.compute_hash()
                db.session.add(log)

                # Төлөв шинэчлэх
                chemical.update_status()

                total_consumed.append(f"{chemical.name}: {converted_amount:.4f} {chemical.unit}")

        # Нийт зарцуулсан бодисыг mg-ээр хадгалах (эхний бодис)
        if required_ingredients:
            first_ing = required_ingredients[0]
            if first_ing['chemical']:
                preparation.chemical_id = first_ing['chemical'].id
                preparation.chemical_used_mg = first_ing['amount'] * (
                    1000 if first_ing['unit'] == 'g' else 1
                )

        db.session.add(preparation)
        db.session.commit()

        consumed_str = ", ".join(total_consumed) if total_consumed else "бодис байхгүй"
        flash(f"'{recipe.name}' ({target_volume}мл) амжилттай найруулагдлаа. Зарцуулсан: {consumed_str}", 'success')
        return redirect(url_for('water.recipe_detail', id=id))

    except (ValueError, TypeError, SQLAlchemyError) as e:
        db.session.rollback()
        logger.exception('prepare_from_recipe error: id=%s', id)
        flash(_l('Уусмал найруулахад алдаа гарлаа.'), 'danger')
        return redirect(url_for('water.recipe_detail', id=id))


@water_bp.route('/solution_recipes/add', methods=['GET', 'POST'])
@login_required
@lab_required('water_chemistry')
def add_recipe():
    """Шинэ уусмалын жор нэмэх."""
    from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

    if request.method == 'POST':
        try:
            recipe = SolutionRecipe(
                name=request.form.get('name'),
                concentration=to_float(request.form.get('concentration')),
                concentration_unit=request.form.get('concentration_unit', 'N'),
                standard_volume_ml=to_float(request.form.get('standard_volume_ml')) or 1000,
                preparation_notes=request.form.get('preparation_notes'),
                lab_type='water_chemistry',
                category=request.form.get('category'),
                created_by_id=current_user.id,
            )
            db.session.add(recipe)
            db.session.flush()  # ID авахын тулд

            # Орц нэмэх
            chemical_ids = request.form.getlist('chemical_id[]')
            amounts = request.form.getlist('amount[]')
            units = request.form.getlist('ingredient_unit[]')

            for i, chem_id in enumerate(chemical_ids):
                if chem_id and amounts[i]:
                    ingredient = SolutionRecipeIngredient(
                        recipe_id=recipe.id,
                        chemical_id=int(chem_id),
                        amount=float(amounts[i]),
                        unit=units[i] if i < len(units) else 'g',
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"'{recipe.name}' recipe created successfully.", 'success')
            return redirect(url_for('water.solution_recipes'))

        except (ValueError, TypeError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.exception('add_recipe error')
            flash(_l('Жор нэмэхэд алдаа гарлаа.'), 'danger')

    # GET
    chemicals = ChemicalRepository.get_for_water_lab()

    return render_template(
        'labs/water/chemistry/solution_recipe_form.html',
        title='Шинэ жор нэмэх',
        recipe=None,
        chemicals=chemicals,
        mode='add',
    )


@water_bp.route('/solution_recipes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@lab_required('water_chemistry')
def edit_recipe(id):
    """Уусмалын жор засварлах."""
    from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

    recipe = SolutionRecipe.query.get_or_404(id)

    if request.method == 'POST':
        try:
            recipe.name = request.form.get('name')
            recipe.concentration = to_float(request.form.get('concentration'))
            recipe.concentration_unit = request.form.get('concentration_unit', 'N')
            recipe.standard_volume_ml = to_float(request.form.get('standard_volume_ml')) or 1000
            recipe.preparation_notes = request.form.get('preparation_notes')
            recipe.category = request.form.get('category')

            # Хуучин орц устгаад шинээр нэмэх
            SolutionRecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

            chemical_ids = request.form.getlist('chemical_id[]')
            amounts = request.form.getlist('amount[]')
            units = request.form.getlist('ingredient_unit[]')

            for i, chem_id in enumerate(chemical_ids):
                if chem_id and amounts[i]:
                    ingredient = SolutionRecipeIngredient(
                        recipe_id=recipe.id,
                        chemical_id=int(chem_id),
                        amount=float(amounts[i]),
                        unit=units[i] if i < len(units) else 'g',
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash('Recipe updated successfully.', 'success')
            return redirect(url_for('water.solution_recipes'))

        except (ValueError, TypeError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.exception('edit_recipe error: id=%s', id)
            flash(_l('Жор засахад алдаа гарлаа.'), 'danger')

    # GET
    chemicals = ChemicalRepository.get_for_water_lab()

    return render_template(
        'labs/water/chemistry/solution_recipe_form.html',
        title='Жор засварлах',
        recipe=recipe,
        chemicals=chemicals,
        mode='edit',
    )


@water_bp.route('/solution_recipes/delete/<int:id>', methods=['POST'])
@login_required
@lab_required('water_chemistry')
def delete_recipe(id):
    """Уусмалын жор устгах."""
    from app.models import SolutionRecipe

    if current_user.role not in ('senior', 'admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('water.solution_recipes'))

    recipe = SolutionRecipe.query.get_or_404(id)
    name = recipe.name

    db.session.delete(recipe)
    db.session.commit()

    flash(f"'{name}' recipe deleted.", 'warning')
    return redirect(url_for('water.solution_recipes'))
