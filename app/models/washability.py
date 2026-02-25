# -*- coding: utf-8 -*-
"""
Washability models.
"""

from app import db
from app.utils.datetime import now_local as now_mn

class WashabilityTest(db.Model):
    """
    Баяжигдах чанарын шинжилгээ (Washability Test / Float-Sink Analysis).

    Нүүрсний баяжуулах үйлдвэрийн theoretical yield тооцоолоход ашиглана.
    Float-sink аргаар өөр өөр нягттай фракцуудад хуваан шинжилнэ.

    Excel импортоос болон LIMS WTL нэгжээс дата авна.
    """
    __tablename__ = "washability_test"

    id = db.Column(db.Integer, primary_key=True)

    # Дээжийн мэдээлэл
    lab_number = db.Column(db.String(50), index=True)  # #25_45
    sample_name = db.Column(db.String(100), index=True)  # PR12_B23_ST129_4A
    sample_date = db.Column(db.Date, index=True)
    report_date = db.Column(db.Date)
    consignor = db.Column(db.String(100))  # Process engineers team

    # Анхны нүүрсний шинжилгээ (Raw Coal)
    initial_mass_kg = db.Column(db.Float)
    raw_tm = db.Column(db.Float)  # Total Moisture %
    raw_im = db.Column(db.Float)  # Inherent Moisture %
    raw_ash = db.Column(db.Float)  # Ash ad %
    raw_vol = db.Column(db.Float)  # Volatiles ad %
    raw_sulphur = db.Column(db.Float)  # Sulphur ad %
    raw_csn = db.Column(db.Float)  # CSN
    raw_gi = db.Column(db.Float)  # G index
    raw_trd = db.Column(db.Float)  # TRD

    # LIMS холбоос (хэрвээ WTL нэгжээс ирсэн бол)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id', ondelete='SET NULL'), index=True)
    sample = db.relationship('Sample', backref='washability_tests')

    # Импорт мэдээлэл
    source = db.Column(db.String(50), default='excel')  # 'excel', 'lims'
    excel_filename = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=now_mn)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    created_by = db.relationship('User', backref='washability_tests')

    # Relationships
    fractions = db.relationship('WashabilityFraction', back_populates='test',
                                cascade='all, delete-orphan', lazy='dynamic')
    yields = db.relationship('TheoreticalYield', back_populates='test',
                             cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f"<WashabilityTest {self.lab_number} - {self.sample_name}>"


class WashabilityFraction(db.Model):
    """
    Float-sink фракцийн дата.

    Size fraction + Density fraction = Individual data
    Жишээ: -50+16mm, density 1.3-1.325 -> Mass, Ash, Vol, etc.
    """
    __tablename__ = "washability_fraction"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('washability_test.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Size fraction
    size_fraction = db.Column(db.String(20))  # -50+16, -16+8, -8+2, -2+0.5, -0.5+0.25
    size_upper = db.Column(db.Float)  # 50
    size_lower = db.Column(db.Float)  # 16
    size_mass_kg = db.Column(db.Float)  # Энэ size fraction-ийн нийт жин

    # Density fraction
    density_sink = db.Column(db.Float)  # 1.25
    density_float = db.Column(db.Float)  # 1.3

    # Individual data
    mass_gram = db.Column(db.Float)
    mass_percent = db.Column(db.Float)  # Энэ size fraction дотор эзлэх %
    im_percent = db.Column(db.Float)  # Inherent Moisture
    ash_ad = db.Column(db.Float)  # Ash, ad %
    vol_ad = db.Column(db.Float)  # Volatiles, ad %
    sulphur_ad = db.Column(db.Float)  # Sulphur, ad %
    csn = db.Column(db.Float)  # CSN

    # Cumulative values (тооцоологдсон)
    cumulative_yield = db.Column(db.Float)  # Нийт гарц хүртэл
    cumulative_ash = db.Column(db.Float)  # Нийлмэл үнслэг

    test = db.relationship('WashabilityTest', back_populates='fractions')

    def __repr__(self):
        return f"<Fraction {self.size_fraction} F{self.density_float} Y={self.mass_percent}%>"


class TheoreticalYield(db.Model):
    """
    Онолын гарц тооцоолол (Theoretical Yield).

    Тодорхой зорилтот үнслэгт (target ash) хүрэхэд хэдэн % гарц гарахыг тооцоолно.
    Washability муруйгаас interpolation хийж олно.
    """
    __tablename__ = "theoretical_yield"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('washability_test.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    # Тооцооллын параметрүүд
    target_ash = db.Column(db.Float, nullable=False)  # Зорилтот үнслэг (жишээ: 10.5%)
    size_fraction = db.Column(db.String(20))  # Аль size fraction-д? (эсвэл 'all' бүгдэд)

    # Үр дүн
    theoretical_yield = db.Column(db.Float)  # Онолын гарц %
    actual_yield = db.Column(db.Float)  # Үйлдвэрийн бодит гарц (хэрвээ байвал)
    recovery_efficiency = db.Column(db.Float)  # actual / theoretical * 100

    # NGM (Near Gravity Material) - баяжуулахад хэцүү хэсэг
    ngm_plus_01 = db.Column(db.Float)  # ±0.1 density дахь %
    ngm_plus_02 = db.Column(db.Float)  # ±0.2 density дахь %

    # Separation density
    separation_density = db.Column(db.Float)  # Ялгаралтын нягт (target ash-д хүрэх)

    calculated_at = db.Column(db.DateTime, default=now_mn)
    notes = db.Column(db.Text)

    test = db.relationship('WashabilityTest', back_populates='yields')

    def __repr__(self):
        return f"<TheoreticalYield Ash={self.target_ash}% -> Yield={self.theoretical_yield}%>"


class PlantYield(db.Model):
    """
    Үйлдвэрийн бодит гарц (Plant Actual Yield).

    Онолын гарцтай харьцуулахад ашиглана.
    """
    __tablename__ = "plant_yield"

    id = db.Column(db.Integer, primary_key=True)

    # Огноо/хугацаа
    production_date = db.Column(db.Date, nullable=False, index=True)
    shift = db.Column(db.String(20))  # Day, Night, etc.

    # Нүүрсний төрөл/эх үүсвэр
    coal_source = db.Column(db.String(100))  # Pit, Seam
    product_type = db.Column(db.String(50))  # HCC, SSCC, MASHCC

    # Оролт/Гаралт
    feed_tonnes = db.Column(db.Float)  # Оролтын хэмжээ (тонн)
    product_tonnes = db.Column(db.Float)  # Гаралтын хэмжээ (тонн)
    actual_yield = db.Column(db.Float)  # product / feed * 100

    # Чанарын үзүүлэлт
    feed_ash = db.Column(db.Float)  # Оролтын үнслэг
    product_ash = db.Column(db.Float)  # Гаралтын үнслэг

    # Washability тесттэй холбох (хэрвээ байвал)
    washability_test_id = db.Column(db.Integer, db.ForeignKey('washability_test.id', ondelete='SET NULL'), index=True)
    washability_test = db.relationship('WashabilityTest', backref='plant_yields')

    # Харьцуулалт
    theoretical_yield = db.Column(db.Float)  # Онолын гарц (washability-ээс)
    recovery_efficiency = db.Column(db.Float)  # actual / theoretical * 100

    created_at = db.Column(db.DateTime, default=now_mn)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<PlantYield {self.production_date} {self.product_type} = {self.actual_yield}%>"


