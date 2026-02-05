# seed_chemicals_water.py
# -*- coding: utf-8 -*-
"""
Усны лабын химийн бодисын seed script.
Уусмалын жороос задалсан бодисууд.
"""

from app import create_app, db
from app.models import Chemical, SolutionRecipe, SolutionRecipeIngredient

# Усны лабын үндсэн химийн бодисууд
CHEMICALS = [
    # Давс, бодисууд
    {"name": "ЭДТА динатрийн давс (Na2EDTA·2H2O)", "formula": "C10H14N2O8Na2·2H2O", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Аммонийн хлорид (NH4Cl)", "formula": "NH4Cl", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Аммиак 25%", "formula": "NH3", "category": "base", "unit": "mL", "quantity": 1000},
    {"name": "ЭДТА-ийн динатри магнийн давс", "formula": "C10H12N2O8Na2Mg", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Эрихром хар T (индикатор)", "formula": "C20H12N3O7SNa", "category": "indicator", "unit": "g", "quantity": 25},
    {"name": "Натрийн хлорид (NaCl)", "formula": "NaCl", "category": "salt", "unit": "g", "quantity": 1000},
    {"name": "Триэтаноламин", "formula": "C6H15NO3", "category": "solvent", "unit": "mL", "quantity": 500},
    {"name": "Этанол 96%", "formula": "C2H5OH", "category": "solvent", "unit": "mL", "quantity": 1000},
    {"name": "Кальцийн карбонат (CaCO3)", "formula": "CaCO3", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Давсны хүчил конц (HCl)", "formula": "HCl", "category": "acid", "unit": "mL", "quantity": 2500},
    {"name": "Метил улаан (индикатор)", "formula": "C15H15N3O2", "category": "indicator", "unit": "g", "quantity": 25},

    # Хромат, нитрат
    {"name": "Калийн хромат (K2CrO4)", "formula": "K2CrO4", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Мөнгөний нитрат (AgNO3)", "formula": "AgNO3", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Аммонийн роданид (NH4CNS)", "formula": "NH4CNS", "category": "salt", "unit": "g", "quantity": 250},

    # Сегнет, Несслер, Грисс
    {"name": "Сегнетийн давс (KNaC4H4O6·4H2O)", "formula": "KNaC4H4O6·4H2O", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Натрийн гидроксид (NaOH)", "formula": "NaOH", "category": "base", "unit": "g", "quantity": 1000},
    {"name": "Несслерийн урвалж", "formula": "K2HgI4", "category": "reagent", "unit": "mL", "quantity": 500},
    {"name": "Гриссийн урвалж", "formula": "", "category": "reagent", "unit": "mL", "quantity": 500},

    # Сульфат, хлорид
    {"name": "Цайрын сульфат (ZnSO4)", "formula": "ZnSO4", "category": "salt", "unit": "g", "quantity": 250},
    {"name": "Аскорбины хүчил (C6H8O6)", "formula": "C6H8O6", "category": "acid", "unit": "g", "quantity": 100},
    {"name": "Аммонийн гепамолибдат ((NH4)6Mo7O24·4H2O)", "formula": "(NH4)6Mo7O24·4H2O", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Сурьма-калийн тартрат", "formula": "K(SbO)C4H4O6·1/2H2O", "category": "salt", "unit": "g", "quantity": 50},

    # Салицилат, цитрат
    {"name": "Салицилийн хүчлийн натри (C7H5O3Na)", "formula": "C7H5O3Na", "category": "salt", "unit": "g", "quantity": 250},
    {"name": "Натрийн цитрат (C6H5O7Na3·2H2O)", "formula": "C6H5O7Na3·2H2O", "category": "salt", "unit": "g", "quantity": 250},
    {"name": "Натрийн нитропруссид", "formula": "[Fe(CN)5NO]Na2·2H2O", "category": "salt", "unit": "g", "quantity": 25},
    {"name": "Натрийн дихлороизоцианурат (C3N3O3Cl2Na·2H2O)", "formula": "C3N3O3Cl2Na·2H2O", "category": "salt", "unit": "g", "quantity": 50},

    # Фосфат, хүчил
    {"name": "Ортофосфорын хүчил (H3PO4)", "formula": "H3PO4", "category": "acid", "unit": "mL", "quantity": 500},
    {"name": "4-аминобензолсульфонамид", "formula": "NH2C6H4SO2NH2", "category": "reagent", "unit": "g", "quantity": 50},
    {"name": "N-(1-нафтил)-этилендиамин дигидрохлорид", "formula": "C10H7NH-CH2-CH2-NH2·2HCl", "category": "reagent", "unit": "g", "quantity": 25},

    # Буфер бодисууд
    {"name": "Калийн дигидрофосфат (KH2PO4)", "formula": "KH2PO4", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Калийн гидрофосфат (K2HPO4·3H2O)", "formula": "K2HPO4·3H2O", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Натрийн гидрофосфат (Na2HPO4)", "formula": "Na2HPO4", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Магнийн сульфат (MgSO4·7H2O)", "formula": "MgSO4·7H2O", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Кальцийн хлорид усгүй (CaCl2)", "formula": "CaCl2", "category": "salt", "unit": "g", "quantity": 500},
    {"name": "Төмрийн хлорид (FeCl3·6H2O)", "formula": "FeCl3·6H2O", "category": "salt", "unit": "g", "quantity": 250},

    # Иод, тиосульфат
    {"name": "Калийн иодид (KI)", "formula": "KI", "category": "salt", "unit": "g", "quantity": 250},
    {"name": "Натрийн азид (NaN3)", "formula": "NaN3", "category": "salt", "unit": "g", "quantity": 50},
    {"name": "Манганийн хлорид (MnCl2·H2O)", "formula": "MnCl2·H2O", "category": "salt", "unit": "g", "quantity": 250},
    {"name": "Хүхрийн хүчил конц (H2SO4)", "formula": "H2SO4", "category": "acid", "unit": "mL", "quantity": 2500},
    {"name": "Калийн иодат (KIO3)", "formula": "KIO3", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Натрийн тиосульфат (Na2S2O3·5H2O)", "formula": "Na2S2O3·5H2O", "category": "salt", "unit": "g", "quantity": 500},

    # Глюкоз, бусад
    {"name": "Глюкоз усгүй", "formula": "C6H12O6", "category": "other", "unit": "g", "quantity": 250},
    {"name": "Глутамины хүчил", "formula": "C5H9NO4", "category": "other", "unit": "g", "quantity": 100},
    {"name": "Аллилтиоурэа (ATU)", "formula": "C4H8N2S", "category": "reagent", "unit": "g", "quantity": 25},
    {"name": "Цардуул (крахмал)", "formula": "(C6H10O5)n", "category": "indicator", "unit": "g", "quantity": 250},
    {"name": "Микроталст эслэг", "formula": "", "category": "other", "unit": "g", "quantity": 100},

    # Стандарт
    {"name": "Төмөр аммони цөр (NH4Fe(SO4)2·12H2O)", "formula": "NH4Fe(SO4)2·12H2O", "category": "standard", "unit": "g", "quantity": 250},
    {"name": "Натрийн нитрит (NaNO2)", "formula": "NaNO2", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Натрийн нитрат (NaNO3)", "formula": "NaNO3", "category": "salt", "unit": "g", "quantity": 250},
    {"name": "Хоёр хромат хүчлийн кали (K2Cr2O7)", "formula": "K2Cr2O7", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Хүхрийн хүчлийн кобальт (CoSO4)", "formula": "CoSO4", "category": "salt", "unit": "g", "quantity": 100},
    {"name": "Устөрөгчийн хэт исэл (H2O2)", "formula": "H2O2", "category": "reagent", "unit": "mL", "quantity": 500},
]

# Жор <-> Бодис холбоос (recipe_name -> [(chemical_name, amount, unit), ...])
RECIPE_INGREDIENTS = {
    "ТРИЛОН Б": [
        ("ЭДТА динатрийн давс (Na2EDTA·2H2O)", 3.725, "g"),
    ],
    "БУФЕР УУСМАЛ": [
        ("Аммонийн хлорид (NH4Cl)", 6.75, "g"),
        ("Аммиак 25%", 57, "mL"),
        ("ЭДТА-ийн динатри магнийн давс", 0.5, "g"),
    ],
    "ЭРИХРОМ ХАР ИНДИКАТОР": [
        ("Эрихром хар T (индикатор)", 0.5, "g"),
        ("Натрийн хлорид (NaCl)", 50, "g"),
        ("Этанол 96%", 25, "mL"),
    ],
    "КАЛЬЦИЙН КАРБОНАТ СТАНДАРТ УУСМАЛ": [
        ("Кальцийн карбонат (CaCO3)", 1.001, "g"),
        ("Давсны хүчил конц (HCl)", 10, "mL"),
    ],
    "КАЛИЙН ХРОМАТ": [
        ("Калийн хромат (K2CrO4)", 10, "g"),
    ],
    "МӨНГӨНИЙ НИТРАТ": [
        ("Мөнгөний нитрат (AgNO3)", 16.9874, "g"),
    ],
    "НАТРИЙН ХЛОРИД": [
        ("Натрийн хлорид (NaCl)", 5.8443, "g"),
    ],
    "ДАВСНЫ ХҮЧИЛ": [
        ("Давсны хүчил конц (HCl)", 100, "mL"),
    ],
    "АММОНИЙН РОДАНИД": [
        ("Аммонийн роданид (NH4CNS)", 50, "g"),
    ],
    "СЕГНЕТИЙН ДАВС": [
        ("Сегнетийн давс (KNaC4H4O6·4H2O)", 50, "g"),
        ("Натрийн гидроксид (NaOH)", 5, "g"),
    ],
    "ЦАЙРЫН СУЛЬФАТ": [
        ("Цайрын сульфат (ZnSO4)", 10, "g"),
    ],
    "НАТРИЙН ГИДРОКСИД": [
        ("Натрийн гидроксид (NaOH)", 7, "g"),
    ],
    "АСКОРБИНЫ ХҮЧИЛ": [
        ("Аскорбины хүчил (C6H8O6)", 10, "g"),
    ],
    "ХҮЧИЛЛЭГ МОЛИБДАТ, уусмал I": [
        ("Аммонийн гепамолибдат ((NH4)6Mo7O24·4H2O)", 13, "g"),
        ("Сурьма-калийн тартрат", 0.35, "g"),
    ],
    "ӨНГӨНИЙ УРВАЛЖ": [
        ("Салицилийн хүчлийн натри (C7H5O3Na)", 13, "g"),
        ("Натрийн цитрат (C6H5O7Na3·2H2O)", 13, "g"),
        ("Натрийн нитропруссид", 0.097, "g"),
    ],
    "НАТРИЙН ДИХЛОРОИЗОЦИАНУРАТ": [
        ("Натрийн гидроксид (NaOH)", 3.2, "g"),
        ("Натрийн дихлороизоцианурат (C3N3O3Cl2Na·2H2O)", 0.2, "g"),
    ],
    "ӨНГӨ ҮҮСГЭХ УРВАЛЖ": [
        ("Ортофосфорын хүчил (H3PO4)", 10, "mL"),
        ("4-аминобензолсульфонамид", 4, "g"),
        ("N-(1-нафтил)-этилендиамин дигидрохлорид", 0.2, "g"),
    ],
    "ФОСФАТЫН БУФЕР": [
        ("Калийн дигидрофосфат (KH2PO4)", 0.85, "g"),
        ("Калийн гидрофосфат (K2HPO4·3H2O)", 2.175, "g"),
        ("Натрийн гидрофосфат (Na2HPO4)", 3.34, "g"),
        ("Аммонийн хлорид (NH4Cl)", 0.17, "g"),
    ],
    "МАГНИЙН СУЛЬФАТ": [
        ("Магнийн сульфат (MgSO4·7H2O)", 2.25, "g"),
    ],
    "КАЛЬЦИЙН ХЛОРИД": [
        ("Кальцийн хлорид усгүй (CaCl2)", 2.75, "g"),
    ],
    "ТӨМРИЙН ХЛОРИД": [
        ("Төмрийн хлорид (FeCl3·6H2O)", 0.25, "g"),
    ],
    "ШҮЛТИЙН УУСМАЛ": [
        ("Натрийн гидроксид (NaOH)", 35, "g"),
        ("Калийн иодид (KI)", 30, "g"),
        ("Натрийн азид (NaN3)", 1, "g"),
    ],
    "МАНГАНИЙН СУЛЬФАТ": [
        ("Манганийн хлорид (MnCl2·H2O)", 38, "g"),
    ],
    "ХҮХРИЙН ХҮЧИЛ": [
        ("Хүхрийн хүчил конц (H2SO4)", 500, "mL"),
    ],
    "КАЛИЙН ИОДАТ": [
        ("Калийн иодат (KIO3)", 3.567, "g"),
    ],
    "НАТРИЙН ТИОСУЛЬФАТ": [
        ("Натрийн тиосульфат (Na2S2O3·5H2O)", 2.5, "g"),
        ("Натрийн гидроксид (NaOH)", 0.4, "g"),
    ],
    "ГЛУКОЗ-ГЛУТАМИНЫ ХҮЧЛИЙН УУСМАЛ": [
        ("Глюкоз усгүй", 0.15, "g"),
        ("Глутамины хүчил", 0.15, "g"),
    ],
    "АЛЛИТИР(ATU)": [
        ("Аллилтиоурэа (ATU)", 0.2, "g"),
    ],
    "ЦАРДУУЛ": [
        ("Цардуул (крахмал)", 10, "g"),
    ],
    "МИКРОТАЛСТ ЭСЛЭГ": [
        ("Микроталст эслэг", 0.5, "g"),
    ],
    "ТӨМӨР АММОНИЙН ЦӨРИЙН СТАНДАРТ УУСМАЛ": [
        ("Төмөр аммони цөр (NH4Fe(SO4)2·12H2O)", 0.8836, "g"),
        ("Давсны хүчил конц (HCl)", 2, "mL"),
    ],
    "ОРТОФОСФАТЫН СТАНДАРТ УУСМАЛ": [
        ("Калийн дигидрофосфат (KH2PO4)", 0.2197, "g"),
        ("Хүхрийн хүчил конц (H2SO4)", 10, "mL"),
    ],
    "АММОНИЙН ХЛОРИДЫН СТАНДАРТ УУСМАЛ": [
        ("Аммонийн хлорид (NH4Cl)", 0.2965, "g"),
    ],
    "НАТРИЙН НИТРИТИЙН СТАНДАРТ УУСМАЛ": [
        ("Натрийн нитрит (NaNO2)", 0.6157, "g"),
    ],
    "НАТРИЙН НИТРАТИЙН СТАНДАРТ УУСМАЛ": [
        ("Аммонийн хлорид (NH4Cl)", 3.819, "g"),
    ],
    "ӨНГӨ ТОДОРХОЙЛОХ СТАНДАРТ УУСМАЛ": [
        ("Хоёр хромат хүчлийн кали (K2Cr2O7)", 0.0875, "g"),
        ("Хүхрийн хүчлийн кобальт (CoSO4)", 2, "g"),
        ("Хүхрийн хүчил конц (H2SO4)", 1, "mL"),
    ],
    "АММОНИ АЗОТ СТАНДАРТ УУСМАЛ": [
        ("Аммонийн хлорид (NH4Cl)", 3.819, "g"),
    ],
}


def seed_chemicals():
    """Химийн бодис seed хийх."""
    app = create_app()
    with app.app_context():
        added = 0
        for chem_data in CHEMICALS:
            existing = Chemical.query.filter_by(
                name=chem_data["name"],
                lab_type='water'
            ).first()
            if existing:
                continue

            chemical = Chemical(
                name=chem_data["name"],
                formula=chem_data.get("formula", ""),
                category=chem_data.get("category", "other"),
                unit=chem_data["unit"],
                quantity=chem_data["quantity"],
                lab_type='water',
                status='active',
            )
            db.session.add(chemical)
            added += 1
            print(f"  + {chem_data['name']}")

        db.session.commit()
        print(f"\n{added} химийн бодис нэмэгдлээ.")


def link_recipe_ingredients():
    """Жор <-> Бодис холбох."""
    app = create_app()
    with app.app_context():
        linked = 0
        for recipe_name, ingredients in RECIPE_INGREDIENTS.items():
            recipe = SolutionRecipe.query.filter_by(name=recipe_name, lab_type='water').first()
            if not recipe:
                print(f"  ! Жор олдсонгүй: {recipe_name}")
                continue

            # Хуучин орц устгах
            SolutionRecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

            for chem_name, amount, unit in ingredients:
                chemical = Chemical.query.filter_by(name=chem_name, lab_type='water').first()
                if not chemical:
                    print(f"  ! Бодис олдсонгүй: {chem_name}")
                    continue

                ingredient = SolutionRecipeIngredient(
                    recipe_id=recipe.id,
                    chemical_id=chemical.id,
                    amount=amount,
                    unit=unit,
                )
                db.session.add(ingredient)
                linked += 1

            print(f"  + {recipe_name}: {len(ingredients)} бодис")

        db.session.commit()
        print(f"\n{linked} холбоос үүсгэгдлээ.")


if __name__ == '__main__':
    print("=== Химийн бодис seed ===")
    seed_chemicals()
    print("\n=== Жор <-> Бодис холбох ===")
    link_recipe_ingredients()
