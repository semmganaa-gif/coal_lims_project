# Mine2NEMO ProcessControl Integration — 2026-05-17

> **Зорилго:** Хуучин Zobo.exe-ийн frm_tolow логикийг шинэ web LIMS-руу port хийх.
> CHPP 2-hourly дээжүүдийн approved үр дүнг Mine2NEMO SQL Server-ийн
> ProcessControl schema-руу шууд бичих.

**Commit:** `7c19215`
**Status:** Production data-руу 5 row амжилттай бичигдсэн (тест), code бэлэн

---

## 1. КОНТЕКСТ

### Хуучин workflow (Zobo.exe — frm_tolow)
- MS SQL Server 172.16.228.56 (Database "Lab")
- Chemist `frm_tolow` хуудаснаас grid-аас sample сонгоод "Send" товч даран
- 3-part SQL `INSERT INTO Mine2NEMO.ProcessControl.QualityPlantFeed` cross-DB-аар Mine2NEMO-руу бичдэг
- Sample кодын prefix-аар route:
  - `PF2*` → QualityPlantFeed
  - `cc_*` → QualityPrimaryProduct
  - `tc_*` → QualitySecondaryProduct

### Шинэ систем (coal_lims_project)
- Python Flask + PostgreSQL
- Дээжийн нэр шинэчлэгдсэн:
  - `PF211_<date>_<shift>` — PF хэвээр
  - `UHG MV_HCC_<date>_<shift>` — CC категори (5 өөр бүтээгдэхүүн)
  - `UHG MASHCC_2_<date>_<shift>` — TC категори (4 өөр бүтээгдэхүүн)
- Sample Summary хуудсанд "Mine2NEMO" товч нэмэх — Zobo-той ижил workflow

### Бизнесийн challenge
- Mine2NEMO бол хуучин аж`CC`/`TC` нэрээр л хүлээж авна
- Шинэ системд **бүтээгдэхүүн ялгагдсан** (UHG MV_HCC ≠ BN SSCC) боловч overlap гэж байхгүй
- Урт хугацаандаа Mine2NEMO dev team шинэ нэрсэд бэлэн болно — одоохондоо `CC_<date>_<shift>` болгож rewrite

---

## 2. IMPLEMENTATION

### Файлуудын бүтэц

| Файл | Үүрэг |
|------|-------|
| `app/constants/mine2nemo_mapping.py` | Sample routing + SampleCode rewrite logic |
| `app/services/mine2nemo_service.py` | SQL Server connection + INSERT/UPDATE service |
| `app/routes/api/mine2nemo_api.py` | `/api/v1/mine2nemo/{send,status}` endpoints |
| `app/templates/sample_summary.html` | "Mine2NEMO" button (Simulator-ийн хажууд) |
| `app/static/js/sample_summary.js` | Click handler, confirm dialog, result alert |
| `config/integrations.py` | `MINE2NEMO_DATABASE_URL` config |
| `.env` | `mssql+pymssql://sa:***@172.16.228.56:1433/Mine2NEMO?tds_version=7.0` |
| `requirements.txt` | `pymssql>=2.3.0` |
| `scripts/diagnose_mine2nemo.py` | Network/TDS/auth диагностик tool |

### Routing logic

```python
# basename detection
PF211_20260517_D3 → basename "PF211"        → QualityPlantFeed
UHG MV_HCC_20260517_N3 → basename "UHG MV_HCC" → QualityPrimaryProduct
UHG Midd_20260517_D5 → basename "UHG Midd"  → QualitySecondaryProduct

# SampleCode rewrite (Mine2NEMO 6-digit YYMMDD convention)
PF211_20260517_D3 → PF211_260517_D3 (group: Plant feed SA-211)
UHG MV_HCC_20260517_N3 → CC_260517_N3
UHG MASHCC_2_20260517_D5 → TC_260517_D5

# SampleTime mapping (2-hourly shifts)
D1=08:00 D2=10:00 D3=12:00 D4=14:00 D5=16:00 D6=18:00
N1=20:00 N2=22:00 N3=00:00 N4=02:00 N5=04:00 N6=06:00
```

### QualityCategoryID UUID-ууд (Mine2NEMO.ProcessControl.QualityCategory-аас)

| Category | UUID |
|----------|------|
| Plant feed SA-211 | `71d262a2-df27-4c71-82ac-e152e3587d7b` |
| Plant feed SA-221 | `c9c41600-f00e-489b-a4f4-0b65bf93963b` |
| Plant feed SA-231 | `601b7680-18b5-401a-978c-eb431f8b56c7` |
| Primary Product /CC/ | `bfcdaacb-feea-438c-a5a2-15adb5893f24` |
| Secondary Product /TC/ | `3e50f369-f755-4a52-86bf-866d9f8261f9` |

### Verification mechanism (3-давхар trail)

1. **SELECT-back** — INSERT/UPDATE-ийн дараа тэр row-аа Mine2NEMO-аас уншиж Mt_ar/Mad/Aad/CreatedDate/CreatedBy харьцуулна
2. **AuditLog entry** — `mine2nemo_inserted`/`updated`/`failed` action бичигдэнэ (ISO 17025)
3. **UI verification display** — success alert-д "Mine2NEMO баталгаажсан Aad=12.5, Mt_ar=8.2, By=gantulga.u"

---

## 3. CHALLENGES ОЛДСОН ЗАСВАР

### Issue 1: SQL Server port буруу — 6964 vs 1433
- Zobo.exe.config-д `port=6964` гэсэн ч connection string-д port specified биш (default 1433)
- `6964` нь HTTP listening port (different service)
- **Fix:** `.env`-д `:1433` ашиглах

### Issue 2: TDS protocol handshake fail
- SQL Server 2012 (хуучин) + pymssql 2.3.13 default TDS 7.4 → handshake fail
- 5 TDS version туршсан: 7.0 only one работает
- **Fix:** `.env`-ийн URL-руу `?tds_version=7.0` query param

### Issue 3: Sample code basename detection
- `UHG MASHCC_2_20260312_D6` дотор underscore бий → naive split fail
- **Fix:** Сүүлийн 2 underscore-ыг гаргаж, дунд хэсэг 6+ digit бол date гэж тогтоох

### Issue 4: QualityCategoryID NOT NULL
- INSERT түрсэн: `Cannot insert NULL into column 'QualityCategoryID'`
- Mine2NEMO-аас одоо байгаа category-уудыг лавлаж UUID-аар mapping үүсгэх
- **Fix:** `PF_GROUP_INFO`-руу UUID шууд hard-code (DBA UUID-аа өөрчилбөл өөр)

### Issue 5: Verification SQL — column нэрийн typo
- `QualityPlantFeed` нь `ModifedDate` (typo) — бусдад `ModifiedDate` (зөв)
- **Fix:** Table-specific verify SQL builder

### Issue 6: CC/TC бүтээгдэхүүн convention mismatch
- Шинэ системд 5 өөр CC бүтээгдэхүүн (UHG MV_HCC, BN SSCC, etc.) — overlap байхгүй
- Mine2NEMO зөвхөн нэг `CC_*` slot — хуучин design
- **Decision:** Бүгдийг `CC_<yymmdd>_<shift>` болгож rewrite (last-write-wins). Урт хугацаанд Mine2NEMO dev team шинэ category нэмэх ёстой.

---

## 4. PRODUCTION VERIFICATION

### Бичигдсэн row-ууд (тест) — гэхдээ зарим нь real prod data-руу UPDATE хийсэн

| SampleCode (Mine2NEMO) | Table | Action | Verified |
|-----------------------|-------|--------|----------|
| `PF211_20260312_D6` | QualityPlantFeed | INSERT (нэвтрэх) | ✅ |
| `PF221_20260312_D6` | QualityPlantFeed | INSERT | ✅ |
| `PF231_20260312_D6` | QualityPlantFeed | INSERT | ✅ |
| `CC_260312_D6` | QualityPrimaryProduct | UPDATE ⚠️ | ✅ |
| `CC_251120_N1` | QualityPrimaryProduct | UPDATE ⚠️ | ✅ |

⚠️ **2 CC row нь real production-ын хуучин дата дээр давхар бичигдсэн** (хуучин creator: Tugsjargal Ariya, Chinzorig Burenzaya). PF row-ууд DELETE хийгдсэн (test cleanup). CC row-ууд хэвээр.

### Verified Mine2NEMO connection params

- Server: `172.16.228.56:1433`
- Database: `Mine2NEMO`
- User: `sa` / Password: `P@ssw0rd`
- TDS Version: `7.0` (заавал — SQL Server 2012 хуучин стек)
- Тables: `QualityPlantFeed` (63140 row), `QualityPrimaryProduct` (28229 row), `QualitySecondaryProduct` (23666 row)

---

## 5. ҮЛДСЭН АЖИЛ

### A. Production-руу гарахаас өмнө

1. **End-to-end browser smoke test** — өнөөдрийн real data-аар illgeej Mine2NEMO-аас process engineer-уудаар баталгаажуулах
2. **"Already sent" indicator** Sample Summary grid-д — Mine2NEMO-руу аль хэдийн илгээсэн row тэмдэглэх
3. **Pre-send confirmation enhancement** — LIMS→NEMO mapping preview confirm dialog-руу
4. **Test mode flag** — production-аас гадуур UPDATE хориглох (overwrite сэргийлэх)

### B. Дараагийн iteration (Mine2NEMO dev team-той ярилцсаны дараа)

5. **4 hourly, 12 hourly, com** sample type-ыг Mine2NEMO-руу нэмэх
6. **Бүтээгдэхүүн ялгасан** QualityCategory entries Mine2NEMO-руу нэмэх (UHG MV_HCC, BN SSCC г.м.)
7. **Schema evolution** — Mine2NEMO-руу `ProductCode` багана нэмж шинэ нэршил дэмжүүлэх

### C. Long-term safety

8. **Backup/restore процедур** — production data corruption-аас сэргийлэх
9. **Audit trail UI** — Mine2NEMO-руу илгээсэн дээжүүдийн жагсаалт LIMS dashboard-д

---

## 6. KEY INSIGHTS

1. **Legacy systems-тэй integration хийхэд **3 том issue:**
   - Connection (port, TDS version)
   - Schema differences (typo column names, NOT NULL constraints)
   - Domain naming convention mismatch (1 row vs N rows per shift)

2. **Test data → real prod**: `UPDATE existing row` is dangerous in shared systems. Always test against snapshot/test DB first. (Бид 2 row overwrite хийсэн — урт хугацаанд "safe test mode" нэмэх ёстой)

3. **Diagnostic script-ийн үнэ цэнэ**: `scripts/diagnose_mine2nemo.py` нь network/protocol/auth/schema-ийг алхам алхмаар шалгаж root cause-ыг хурдан олно. **Шинэ system integration-д заавал бичих ёстой pattern.**

---

## 7. ХОЛБООТОЙ ФАЙЛУУД

- `DEPLOY_GUIDE.md` — Production install
- `docs/dev-logs/BUSINESS_STRATEGY_2026_05_17.md` — Customer strategy
- `docs_all/LIMS_-_ROLE_PERMISSIONS_LOG.md` — Role policy (Mine2NEMO send: senior+admin)
- `/e/Lab/session_log_2026-05-09.md` — Zobo decompile session log (исх source)

---

**Файл үүсгэсэн:** Claude Opus 4.7
**Зорилго:** Mine2NEMO integration-ыг future maintenance + onboarding-руу хадгалах
