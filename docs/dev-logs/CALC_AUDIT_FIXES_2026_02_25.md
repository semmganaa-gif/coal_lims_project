# Тооцооллын Аудит & Засвар — 2026-02-25

## Хамрах хүрээ
- `server_calculations.py` — 18 тооцооллын функц
- `analysis_rules.py` — статус тодорхойлох дүрмүүд
- `validators.py` — оролтын баталгаажуулалт
- `analysis_api.py` — API endpoint хамгаалалт
- `converters.py` — to_float утга хөрвүүлэлт

---

## Засагдсан асуудлууд

### 1. CV Alpha Interpolation → Дискрет утга (ISO 1928)
- **Файл:** `server_calculations.py:471-479`
- **Асуудал:** Linear interpolation хийж байсан (0.0010-0.0012 хооронд)
- **Стандарт:** MNS ISO 1928 дискрет утга:
  - ≤ 16.70 MJ/kg → α = 0.0010
  - 16.70 < x ≤ 25.10 → α = 0.0012
  - > 25.10 → α = 0.0016
- **Нөлөө:** CV тооцоолол 16.70-25.10 MJ/kg мужид буруу alpha ашиглаж байсан

### 2. TRD Temperature — Linear Interpolation нэмсэн
- **Файл:** `server_calculations.py:803-815`
- **Асуудал:** `round()` (banker's rounding) ашиглаж бүхэл тоо руу дугуйлж байсан
- **Засвар:** Хүснэгтийн утгуудын хооронд шугаман интерполяци хийдэг болсон
- **Жишээ:** 20.5°C → kt_20 + (kt_21 - kt_20) * 0.5

### 3. Division by Zero — Floating-point safe
- **Файл:** `server_calculations.py` (4 газар: 487, 658, 721, 850)
- **Асуудал:** `== 0` шалгалт floating-point-д найдвартай биш
- **Засвар:** `abs(x) < 1e-10` болгосон

### 4. save_results Role Check
- **Файл:** `analysis_api.py:282-284`
- **Асуудал:** `@login_required` л байсан, ямар ч role шалгаагүй
- **Засвар:** chemist, senior, admin role шалгалт нэмсэн
- **Нөлөө:** prep хэрэглэгч шинжилгээний үр дүн хадгалж чадахгүй болсон

### 5. Race Condition — Pessimistic Lock
- **Файл:** `analysis_api.py:550-553`
- **Асуудал:** Нэгэн зэрэг хадгалалт мөргөлдөх боломжтой байсан
- **Засвар:** `.with_for_update()` нэмсэн — row-level lock

### 6. raw_data Dict Validation
- **Файл:** `analysis_api.py:352`
- **Асуудал:** raw_data string/list ирвэл normalize_raw_data алдаа гаргана
- **Засвар:** `isinstance(raw_data, dict)` шалгалт нэмсэн

### 7. analysis_rules.py CSN Dead Code
- **Файл:** `analysis_rules.py:164-170`
- **Асуудал:** `> 1.0` шалгаад дараа нь `== 1.0` шалгасан (dead code)
- **Засвар:** `>= 1.0` нэг шалгалт болгосон

### 8. analysis_rules.py raw_data Type Check
- **Файл:** `analysis_rules.py:99`
- **Асуудал:** `is None` л шалгаж, string/list ирвэл .get() алдаа
- **Засвар:** `isinstance(raw_data, dict)` болгосон

---

## Шалгагдсан, зөв байсан зүйлс

| Функц | Томьёо | Тайлбар |
|-------|--------|---------|
| calc_moisture_mad | ✅ Зөв | m1=тигель, m2=дээж, m3=тигель+хатаасан convention |
| calc_ash_aad | ✅ Зөв | (m3-m1)/m2 * 100 |
| calc_volatile_vad | ✅ Зөв | (m2-m3)/m1 * 100 |
| calc_sulfur_ts | ✅ Зөв | K=0.34296 (BaSO4 → S conversion) |
| calc_phosphorus_p | ✅ Зөв | Titration томьёо |
| calc_gray_king_gi | ✅ Зөв | 5:1 болон 3:3 mode |
| calc_free_moisture_fm | ✅ Зөв | (Wb-Wa)/(Wa-Wt) * 100 |
| calc_solid | ✅ Зөв | C*100/(A-B) |
| calc_trd | ✅ Зөв | md/(md+m2-m1)*kt |
| _safe_float | ✅ Зөв | NaN/Infinity → None |
| _get_from_dict | ✅ Зөв | Nested dict → _safe_float |

---

## Хойшлуулсан / Цаашид анхаарах

| # | Асуудал | Шалтгаан |
|---|---------|----------|
| 1 | Vdaf, FCd, CSN, CSR, CRI тооцоолол байхгүй | Client-д тооцоолдог, серверт verify байхгүй |
| 2 | Parallel tolerance check (p1 ≈ p2) | analysis_rules.py-д хийдэг |
| 3 | Result range validation (0-100%) | validators.py-д хийдэг |
| 4 | F, Cl — pass-through (тооцоолол биш) | Багажийн үр дүн шууд оруулдаг |
| 5 | converters.py `f != f` NaN check | Ажилладаг ч `math.isnan()` илүү тодорхой |
