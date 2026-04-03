# -*- coding: utf-8 -*-
"""
Solution preparation and recipe models.

Separated from models.py for maintainability.
"""

from app import db
from app.utils.datetime import now_local as now_mn


# -------------------------
# УУСМАЛ БЭЛДЭХ ДЭВТЭР (Усны хими)
# -------------------------
class SolutionPreparation(db.Model):
    """
    Уусмал бэлдэх дэвтэр (Усны химийн лаб).

    Стандарт уусмал бэлдэх, титр тогтоох бүртгэл.

    Attributes:
        id (int): Primary key
        solution_name (str): Уусмалын нэр
        concentration (float): Концентраци (мг/л)
        volume_ml (float): Эзэлхүүн (мл)
        chemical_used_mg (float): Зарцуулсан бодис (мг)
        prepared_date (date): Огноо
        v1 (float): Титрийн V1 хэмжилт
        v2 (float): Титрийн V2 хэмжилт
        v_avg (float): Vд - дундаж
        titer_coefficient (float): Титрийн коэффициент
        preparation_notes (str): Уусмал бэлдэх явц / заалт
        prepared_by_id (int): Foreign key → User
        chemical_id (int): Foreign key → Chemical (optional)

    Example:
        >>> solution = SolutionPreparation(
        ...     solution_name='HCl 0.1N',
        ...     concentration=0.1,
        ...     volume_ml=1000,
        ...     chemical_used_mg=3650,
        ...     titer_coefficient=0.9985
        ... )
    """
    __tablename__ = 'solution_preparation'

    id = db.Column(db.Integer, primary_key=True)

    # Үндсэн мэдээлэл
    solution_name = db.Column(db.String(200), nullable=False, index=True)
    concentration = db.Column(db.Float)                     # Концентраци (мг/л, mol/L, N)
    concentration_unit = db.Column(db.String(20), default='mg/L')  # mg/L, mol/L, N, %
    volume_ml = db.Column(db.Float)                         # Эзэлхүүн (мл)

    # Зарцуулсан бодис
    chemical_used_mg = db.Column(db.Float)                  # Зарцуулсан бодис (мг)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id', ondelete='SET NULL'), index=True)

    # Жортой холбоос (шинэ)
    recipe_id = db.Column(db.Integer, db.ForeignKey('solution_recipe.id', ondelete='SET NULL'), index=True)

    # Огноо
    prepared_date = db.Column(db.Date, nullable=False, index=True)
    expiry_date = db.Column(db.Date)                        # Хүчинтэй хугацаа

    # Титр тогтоолт
    v1 = db.Column(db.Float)                                # V1 хэмжилт
    v2 = db.Column(db.Float)                                # V2 хэмжилт
    v3 = db.Column(db.Float)                                # V3 хэмжилт (optional)
    v_avg = db.Column(db.Float)                             # Vд - дундаж
    titer_coefficient = db.Column(db.Float)                 # Титрийн коэффициент (K)

    # Уусмал бэлдэх явц
    preparation_notes = db.Column(db.Text)                  # Бэлдэх заавар / тэмдэглэл

    # Төлөв
    status = db.Column(db.String(20), default='active', index=True)  # active, expired, empty

    # Хэрэглэгч
    prepared_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    created_at = db.Column(db.DateTime, default=now_mn)

    # Relationships
    prepared_by = db.relationship('User', foreign_keys=[prepared_by_id])
    chemical = db.relationship('Chemical', foreign_keys=[chemical_id])

    def calculate_v_avg(self):
        """Дундаж V тооцоолох."""
        values = [v for v in [self.v1, self.v2, self.v3] if v is not None]
        if values:
            self.v_avg = sum(values) / len(values)
        return self.v_avg

    def __repr__(self):
        return f"<SolutionPreparation {self.solution_name} ({self.prepared_date})>"


class SolutionRecipe(db.Model):
    """
    Уусмалын жор (Recipe) - урьдчилан тодорхойлсон уусмал бэлдэх заавар.

    Жишээ нь: Трилон Б 0.05N, HCl 0.1N, NaOH 0.1M гэх мэт.
    Тус бүрдээ ямар химийн бодис, хэр хэмжээгээр орох вэ гэдгийг тодорхойлно.

    Attributes:
        id (int): Primary key
        name (str): Уусмалын нэр (жнь: "Трилон Б 0.05N")
        concentration (float): Зорилтот концентраци
        concentration_unit (str): Нэгж (N, M, %, mg/L)
        standard_volume_ml (float): Жорын стандарт эзэлхүүн (жнь: 1000мл)
        preparation_notes (str): Уусмал бэлдэх дэлгэрэнгүй заавар
        lab_type (str): Лабын төрөл (water, coal, micro, petro)
        is_active (bool): Идэвхтэй эсэх
    """
    __tablename__ = 'solution_recipe'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    concentration = db.Column(db.Float)
    concentration_unit = db.Column(db.String(20), default='N')  # N, M, %, mg/L
    standard_volume_ml = db.Column(db.Float, default=1000)  # Стандарт эзэлхүүн

    # Бэлдэх заавар
    preparation_notes = db.Column(db.Text)  # Дэлгэрэнгүй заавар

    # Категори
    lab_type = db.Column(db.String(20), default='water_chemistry', index=True)  # water_chemistry, coal, microbiology, petrography
    category = db.Column(db.String(50))  # titrant, buffer, indicator, standard, reagent

    # Төлөв
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    ingredients = db.relationship('SolutionRecipeIngredient', backref='recipe', lazy='dynamic',
                                  cascade='all, delete-orphan')
    preparations = db.relationship('SolutionPreparation', backref='recipe', lazy='dynamic')

    def calculate_ingredients(self, target_volume_ml):
        """
        Зорилтот эзэлхүүнд шаардагдах бодисын хэмжээг тооцоолох.

        Args:
            target_volume_ml: Бэлдэх эзэлхүүн (мл)

        Returns:
            list: [{'chemical': Chemical, 'amount': float, 'unit': str}, ...]
        """
        ratio = target_volume_ml / self.standard_volume_ml if self.standard_volume_ml else 1
        result = []
        for ing in self.ingredients:
            result.append({
                'chemical': ing.chemical,
                'chemical_id': ing.chemical_id,
                'amount': ing.amount * ratio,
                'unit': ing.unit,
                'ingredient_id': ing.id
            })
        return result

    def __repr__(self):
        return f"<SolutionRecipe {self.name}>"


class SolutionRecipeIngredient(db.Model):
    """
    Уусмалын жорын найрлага (орц) - нэг жорт хэд хэдэн химийн бодис орж болно.

    Attributes:
        id (int): Primary key
        recipe_id (int): Foreign key → SolutionRecipe
        chemical_id (int): Foreign key → Chemical
        amount (float): Хэмжээ (стандарт эзэлхүүнд)
        unit (str): Нэгж (g, mg, mL)
    """
    __tablename__ = 'solution_recipe_ingredient'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('solution_recipe.id', ondelete='CASCADE'), nullable=False, index=True)
    chemical_id = db.Column(db.Integer, db.ForeignKey('chemical.id', ondelete='SET NULL'), index=True)
    amount = db.Column(db.Float, nullable=False)  # Стандарт эзэлхүүнд орох хэмжээ
    unit = db.Column(db.String(20), default='g')  # g, mg, mL

    # Relationship
    chemical = db.relationship('Chemical')

    def __repr__(self):
        return f"<SolutionRecipeIngredient {self.chemical.name if self.chemical else 'Unknown'}: {self.amount} {self.unit}>"
