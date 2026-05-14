# app/labs/water_lab/__init__.py
"""
Усны лабораторийн namespace package.

Дэд лабораториуд (тус тусдаа BaseLab subclass):
- Chemistry (Хими)        — app.labs.water_lab.chemistry.ChemistryLab
- Microbiology (Микробио) — app.labs.water_lab.microbiology.MicrobiologyLab

NOTE: Өмнө нь хоёрыг нэгтгэсэн `WaterLaboratory` parent class байсныг
refactor commit e206e63 дээр тус тусад салгасан. Үлдсэн dead code (parent
class, water_lab_bp, water_lab_hub.html) 2026-05-14 audit Phase 3-аар
цэвэрлэгдсэн.
"""
