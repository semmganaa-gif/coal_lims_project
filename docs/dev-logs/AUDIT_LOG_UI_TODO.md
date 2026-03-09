# Audit Log UI — TODO

## Зорилго
`AnalysisResultLog` моделийг UI дээр харуулах, бүрэн audit trail бий болгох.

## Одоогийн байдал
- Model бэлэн: `app/models/analysis_audit.py`
- DB хүснэгт: `analysis_result_log` (бүтэц үүссэн)
- **Approve/Reject лог**: `app/routes/analysis/senior.py:190-206` дээр аль хэдийн бичигдэж байна
  - `update_result_status()` — approve/reject бүрд AnalysisResultLog үүсгэнэ
  - `bulk_update_status()` — bulk approve/reject бүрд бас бичнэ
  - `data_hash`, `sample_code_snapshot` бөглөгдөж байна

## Хийх ажлууд

### 1. Лог бичих (Backend) — нэмэлт
- [x] Senior dashboard approve/reject — **аль хэдийн хийгдсэн** (`senior.py:190-206`)
- [x] Bulk approve/reject — **аль хэдийн хийгдсэн** (`senior.py:236+`)
- [ ] Шинжилгээний үр дүн анх хадгалахад (`CREATED`) лог бичих
- [ ] Үр дүн засварлахад (`UPDATED`) лог бичих
- [ ] Дахин шинжилгээ (`REANALYSIS`) лог бичих
- [ ] `original_user_id`, `original_timestamp` бөглөх

### 2. UI харуулах
- [ ] Дээжний дэлгэрэнгүй хуудсанд түүх tab нэмэх
- [ ] Тусдаа audit хуудас (admin) — бүх логийг шүүж, хайж харах
- [ ] AG-Grid table + filter (огноо, хэрэглэгч, action, analysis_code)

### 3. Нэмэлт
- [ ] (шаардлагатай бол энд нэмнэ)
