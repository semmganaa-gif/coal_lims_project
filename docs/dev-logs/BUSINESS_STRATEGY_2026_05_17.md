# BUSINESS STRATEGY & GO-TO-MARKET — Coal LIMS

**Огноо:** 2026-05-17
**Зорилго:** Энэ нь **бизнес талын** баримт — техник install биш, харин: үнэлгээ
   тогтоох, гэрээ хийх, customer-той ярилцах, IT компани болж өсөх зам.

> **Техникийн install заавар:** `DEPLOY_GUIDE.md` (717 мөр, бүрэн дэлгэрэнгүй)
> **Production readiness төлөв:** `docs_all/PRODUCTION_REPORT_2026_02_28.md` (8.4/10)
> **Code audit түүх:** `docs/dev-logs/PRODUCTION_AUDIT_2026_02_16.md`

---

## 1. ТАНЫ НӨХЦӨЛ БАЙДАЛ

| Зүйл | Тодорхойлолт |
|------|--------------|
| Хөгжүүлэгч | **Гантулга, нэгээрээ** |
| Хийсэн ажлын хэмжээ | 100+ commit, 657+ тест pass, ISO 17025-д нийцсэн систем |
| Анхны customer | **Аль хэдийн ярилцаж буй** уул уурхайн компанийн дотоод лаб |
| Customer scale | 50 хэрэглэгч, сард ~80,000 шинжилгээ, өөрсдийн сервер + IT team |
| Customer тэдгээрийн төсвийн боломж | Уул уурхайн компанийн IT-ийн төсөв ₮100+ сая жилд (магадгүй) |
| Бизнес зорилго | **IT компани болж өргөжих** — recurring orлогын модель |
| Гол сэтгэл зовинол | Эх код алдрах — copy aваад хэн нэгэн дахин зарж/тараах эрсдэл |

---

## 2. ҮНЭЛГЭЭ — ХЭДЭН ТӨГРӨГ ГЭХ ВЭ

### 2.1 Реалистик 1-р customer-ийн үнэлгээ

| Зүйл | Эхний жил | Дараагийн жил тутамд |
|------|-----------|----------------------|
| **Лиценз** (1 жилийн ашиглалт, hardware-bound) | ₮15-20 сая | ₮10-12 сая (renewal) |
| **Install + сургалт** (1-р удаа) | ₮5-10 сая | — |
| **Maintenance contract** (bug fix, шинэ feature) | багтсан | ₮5-8 сая |
| **Support contract** (24-цагт хариу, on-site хэрэгцээтэй үед) | багтсан | ₮3-5 сая |
| **НИЙТ** | **₮25-40 сая** | **₮18-25 сая жилд** |

### 2.2 Үнэлгээний логик

50 хэрэглэгч × 80k шинжилгээ/сар — энэ нь:
- ₮20 сая ÷ 50 хэрэглэгч = **₮400,000/хэрэглэгч/жил** = $115 USD
- Орчин үеийн enterprise LIMS-ийн стандарт үнэ: $200-1000/хэрэглэгч/жил
- **Чи зах зээлээс хямд** байгаа учир customer-руу borloyлахад хүндрэлгүй

### 2.3 Хэлэлцээнд бэлэн байх

⚠️ Customer бараг ВСЕГДА хямдруулахыг хүснэ. **Үндсэн заавар:**

- Эхний санал илүү өндөр (₮35-40 сая) тавь
- Customer хямдруулъя гэхэд ₮25-руу "discount" хэлбэрээр буулга
- "Reference customer benefit" — анхны customer тул special үнэ
- **Хэзээ ч ₮20 саяас доош огт зөвшөөрөхгүй** (тэгвэл support cost cover хийхгүй)

### 2.4 5 жилийн орлогын loyalty төсөөлөл

1 customer-аас:
- Жил 1: ₮25 сая
- Жил 2: ₮18 сая
- Жил 3: ₮18 сая
- Жил 4: ₮18 сая
- Жил 5: ₮18 сая
- **Нийт 5 жилд: ₮97 сая**

5 customer-той бол 5 жилд **₮485 сая** — 2-3 хүний IT компани боломжтой.

---

## 3. КОД ХАМГААЛАЛТ — БИЗНЕС ЭРСДЛИЙГ БУУРУУЛАХ

### 3.1 Одоо аль хэдийн хийгдсэн (DEPLOY_GUIDE.md-д тэмдэглэгдсэн)

| Давхарга | Юу хийдэг | Хүчин чадал |
|----------|-----------|-------------|
| **1. GitHub Private repo** | Интернетээс код татаж авах боломжгүй | ⭐⭐⭐ |
| **2. SSH түлхүүр + Firewall** | Зөвшөөрөлгүй серверт нэвтрэхгүй | ⭐⭐⭐ |
| **3. .pyc байтекод** | .py биш, хөрвүүлсэн файл л Docker image-д орно | ⭐⭐ |
| **4. Лиценз + Hardware fingerprint** | Код хуулсан ч өөр сервер дээр ажиллахгүй | ⭐⭐⭐⭐⭐ |
| **5. chmod 600/750 + non-root** | Container дотор root биш, файлын эрх хязгаар | ⭐⭐ |

### 3.2 Нэмж сэргэх ёстой давхарга (бизнесийн хувьд чухал)

**PyArmor — Python код encryption** ⭐⭐⭐⭐⭐

Одоогийн .pyc нь decompile хийгдэх боломжтой (`uncompyle6` гэх мэт tool-аар). PyArmor нь зөв encrypt хийдэг:

- **Үнэ:** $129-249/жил (хувийн licence)
- **Setup time:** 1-2 хоног
- **Үр дүн:** Customer-ийн серверт `analysis_workflow.py` биш зөвхөн encrypted binary үлдэнэ — decompile хийх боломжгүй

**Бизнесийн хувьд яагаад чухал:**
- Customer-ийн IT нь "энэ програм юу хийдгийг ойлгох" зорилгоор код-руу хандсан ч мэдээлэл авч чадахгүй
- Гэрээ цуцалсан хэдий ч customer тэр кодыг ашиглах боломжгүй
- Bytecode decompiling-ээс хамаагүй илүү найдвартай

### 3.3 Гэрээний хууль зүйн заалт

Кодыг хичнээн нягт хамгаалсан ч **гэрээний заалт** хэрэгтэй. Loyer-аас тусламж авах хэрэгтэй заавал орох мэдээлэл:

- "Customer нь программын код-руу хандах эрхгүй"
- "Гэрээний хугацаа дуусахад Customer нь программыг бүрэн устгана"
- "Program-ыг 3-р этгээдэд тарааж борлуулах хориглоно"
- "Зөрчсөн тохиолдолд хуулийн хариуцлага хүлээнэ + €/₮ хохирол барагдуулна"
- "Data ownership: Customer-ийн дата нь Customer-д харьяалагдана"
- "Audit rights: Лиценз эзэмшигч нь 30 хоногийн advance notice-той audit хийх эрхтэй"

---

## 4. ГЭРЭЭ — ЗААВАЛ ОРОХ ЗААЛТ

### 4.1 Үнэлгээ ба төлбөрийн нөхцөл
- Эхний жилийн лиценз
- Дараагийн жилийн renewal үнэлгээ (inflation clause байж болно: жил тутамд +5%)
- Төлбөрийн нөхцөл: 50% deposit + 50% delivery, эсвэл 12 хуваан тооцоо

### 4.2 Лицензийн хязгаар
- 1 компани, 1 сервер, 1 жил
- Олон сервер хэрэгцээтэй бол нэмэлт лиценз ₮3-5 сая
- Лиценз hardware-bound (CPU + MAC)

### 4.3 Service Level Agreement (SLA)
- **Hot fix** (production-down алдаа): 4 цагт хариу, 24 цагт solution
- **Critical bug** (workflow stops): 1 ажлын өдөр
- **Normal bug** (UI cosmetic): 1 долоо хоног
- **Feature request:** Quarterly release-д хамруулна

### 4.4 Maintenance scope
- ✅ Bug fix (одоогийн feature)
- ✅ Security patch
- ✅ Минор UI improvement
- ❌ Шинэ модуль (extra cost)
- ❌ Custom integration (extra cost)

### 4.5 Support hours
- Эхний 30 хоног: 24/7
- Дараа: 9:00-18:00 (Mongolian time), email + phone
- After-hours emergency: extra fee per call

### 4.6 Termination clause
- Customer-ийн хүсэлтээр гэрээг 90 хоногийн notice-р цуцална
- Цуцалсны дараа Customer-ийн дата 30 хоног хадгалагдана (хүсэлтээр export)
- Дараа нь дата устгагдана + Customer-ийн серверээс программ устгана

### 4.7 Data ownership & privacy
- Customer-ийн дата нь Customer-ийнх
- Чи зөвхөн support зорилгоор log-руу хандана
- GDPR-style: customer-ийн зөвшөөрлийг audit log-д хадгална

---

## 5. CUSTOMER-ТОЙ ЯРИЛЦАХДАА БАСАЛЦАХ АСУУЛТ

### Эхний уулзалтад:

#### Технологийн нөхцөл (1 цаг)
1. Серверийн OS — Ubuntu, RHEL, Windows Server, аль вэ?
2. PostgreSQL аль хэдийн ашигладаг уу, шинээр суулгах уу?
3. Internet-руу outbound зөвшөөрөгдөх үү? (license check, шинэчлэлт татах)
4. Backup-ийн infrastructure — Veeam, Acronis, эсвэл pg_dump simple?
5. Backup-ыг хэдэн өдөр хадгалдаг бэ?
6. Disaster recovery (DR) — secondary server байдаг уу?
7. Domain нэр байгаа юу — `lims.companyname.mn` гэх мэт?
8. Internal CA cert-төй юу, эсвэл Let's Encrypt ашиглах уу?

#### Process нөхцөл (1 цаг)
1. **Хэзээ go-live төлөвлөгөөтэй вэ?** (важна — performance test + бэлтгэлд цаг хэрэгтэй)
2. 50 хэрэглэгчээс хэдэн хүн **зэрэг сургах** хэрэгтэй вэ?
3. Аль одоо ямар системтэй вэ — Excel, paper, өөр LIMS?
4. **Data migration** хэрэгтэй юу? Хэдэн жилийн дата шилжүүлэх вэ?
5. Compliance шаардлага — ISO 17025 internal audit, external accreditation бий юу?
6. Лабын ажлын цаг — 24/7 ажилладаг уу, ердийн ажлын цаг 8-18?

#### Бизнесийн нөхцөл (30 минут)
1. **Төсөв** — ₮20 сая, ₮40 сая, ₮100 сая нь real number уу?
2. Гэрээний хугацаа — 1 жил, 3 жил, 5 жил?
3. Decision-maker — IT director, lab manager, COO, CEO аль вэ?
4. Procurement process — RFP бичих хэрэгтэй юу, эсвэл direct contract?
5. Reference хэлэх боломжтой юу — case study/testimonial?

---

## 6. 6-САРЫН GO-TO-MARKET ROADMAP

### Сар 1 — Бэлтгэл (өөртөө)

| Долоо хоног | Ажил | Үр дүн |
|-------------|------|--------|
| 1 | **PyArmor суулгаж test env-д кодыг encrypt хийх** | Encrypted dist + license file ажиллана |
| 2 | **Performance test script бичих** (100k sample seed) | Load test result — UI 3 секундын дотор |
| 3 | **HTTPS-той staging environment ажиллуулах** | Let's Encrypt + nginx working |
| 4 | **Гэрээ template бэлдэх** (хуулийн зөвлөгөө авах) | Signed-ready гэрээ |

### Сар 2 — Customer-төй ярилцаа

| Долоо хоног | Ажил |
|-------------|------|
| 1 | Эхний уулзалт — асуултын жагсаалт (хэсэг 5) ашиглах |
| 2 | Customer-ийн IT-төй техникийн review |
| 3 | Proposal + үнэлгээ хүргүүлэх |
| 4 | Хэлэлцээ — final гэрээ зурах |

### Сар 3 — Install бэлтгэл

| Долоо хоног | Ажил |
|-------------|------|
| 1 | Customer-ийн орчинд **dry run** (test database, test license) |
| 2 | 50 user үүсгэх + role хуваарилах |
| 3 | **Train-the-trainer** — 5 key user-ийг сургах |
| 4 | Documentation Mongolian-аар хүргүүлэх |

### Сар 4 — Go-live

| Долоо хоног | Ажил |
|-------------|------|
| 1 | **Customer-ийн оффис очиж production install** |
| 2 | "Training mode" — алдаа гарвал шууд засах, daily check |
| 3 | Бүх 50 user руу access өгөх, төв ширэн |
| 4 | Эхний 30 хоног on-call — call-руу шууд хариулна |

### Сар 5 — Stabilization

| Долоо хоног | Ажил |
|-------------|------|
| 1-2 | Bug fix цикл — 1 долоо хоног тутамд patch release |
| 3 | User feedback цуглуулах (анкет/уулзалт) |
| 4 | Хоёр дахь customer-руу зориулсан **case study** үүсгэх |

### Сар 6 — Хоёр дахь customer

| Долоо хоног | Ажил |
|-------------|------|
| 1 | Reference call зохион байгуулах (1-р customer → 2-р customer) |
| 2 | Шинэ proposal илүү confident үнэлгээгээр |
| 3-4 | Хоёр дахь customer-төй хэлэлцээ + гэрээ |

---

## 7. SOLO → IT КОМПАНИЙН 5 ЖИЛИЙН ЗАМ

### Жил 1: Solo + 1 customer
- Орлого: ₮25-30 сая
- Бүх ажил өөрөө
- Goal: **Хэвлэлд хувь нэмэр оруулах reference case**

### Жил 2: Solo + 3 customer
- Орлого: ₮75-90 сая
- **Хоёр дахь хүн хөлслөх** (support engineer эсвэл junior dev) ₮3 сая/сар × 12 = ₮36 сая
- Үлдсэн ₮40-50 сая → бизнес reinvest
- Goal: **Тогтсон process** (онбординг, support, billing)

### Жил 3: 2-3 хүний баг + 5 customer
- Орлого: ₮125-150 сая
- Маркетинг (website, brochure, mining expo)
- Customer support: 24/7 boilerplate
- Goal: **Self-service onboarding** — customer өөрсдөө install хийх боломжтой

### Жил 4: 3-5 хүний баг + 10 customer
- Орлого: ₮250+ сая
- **CTO эсвэл engineering manager хөлслөх**
- Чи бизнес/sales/strategy-руу шилжих
- Goal: **Product feature roadmap** — competitor-ээс ялгаатай функц

### Жил 5: 5-10 хүний баг + 20+ customer
- Орлого: ₮500+ сая
- Mongolia outside marketing (Kazakhstan, Russia mining? Asia mining?)
- Goal: **Эх компанийн valuation** ₮2-5 тэрбум

---

## 8. ТҮГЭЭМЭЛ БИЗНЕС АЛДАА

### Customer-төй ярилцахдаа:

1. ❌ **Үнэлгээг хямд тавих** — "₮5 сая хангалттай" гэхэд customer-ийн нүдэнд "хямд, чанаргүй" харагдана. Дараа жилийн contract-аас давж босох боломжгүй.

2. ❌ **Эх кодыг өгчих** — "ямар ч асуудалгүй, удамшил үнэн" гэж бодоход. Дараа тэр customer-ийн IT нь өөрсдөө хуулж бусад customer-руу зарж эхлэх боломжтой.

3. ❌ **Гэрээгүй ажиллаж эхлэх** — "найзаа л шдээ" гэж нөхөрсөг яриа. Энэ нь бизнесс биш, ажил.

4. ❌ **Хэт өндөр амлалт өгөх** — "10 секундын дотор хариу" гэдгийг бичигдсэн гэрээнд оруулахгүй. Realistic SLA — 2-3 секунд.

5. ❌ **Анхны customer-руу discount-аар оруулах хэт их** — "100% discount, бид өсөж эхлэх customer"-гэдэг хэрэглэсэн ч 0 орлогоос бизнес босохгүй.

6. ❌ **Support-аа free хийх** — Customer бэлэн program-ыг үнэгүй support-той авч байх олонлог. Дараа support-аа charge хийхэд "өмнө үнэгүй өгсөн чи яаж" гэж эсэргүүцэх.

7. ❌ **Customer-ийн request бүхнийг тийм гэх** — Customer feature-руу listed-гүй зүйл хүсэхэд "нэмэлт ажил, нэмэлт төлбөр" гэж заавал зөвлөмж. Бид inflate scope.

### Технологийн өнцгөөс:

1. ❌ **Performance test хийгээгүй** ⇒ 100k record-ийн дотор UI 30 секунд хүлээж байх → customer satisfaction zero
2. ❌ **Backup restore test хийгээгүй** ⇒ ажил саатсан үед "backup байгаа боловч restore хийж чадахгүй"
3. ❌ **User training хангалттай бус** ⇒ "энэ систем хэцүү, ашигладаггүй" гэж тайлагнагдана
4. ❌ **HTTPS-гүй deploy** ⇒ security audit-ийн үед гэрээ цуцлагдана

---

## 9. ЭНЭ ДОЛОО ХОНОГТ ХИЙХ ЁСТОЙ — IMMEDIATE NEXT STEPS

### Эхний шат (1-2 өдөр)

1. **Customer-ийн жинхэнэ нэр + contact list бичих** — кэйс юу гэж нэрлэх вэ?
2. **Decision-maker-төй уулзах өдөр товлох** — IT director эсвэл lab manager аль нь decision хийдэг вэ?
3. **PyArmor-ыг туршиж үзэх** ($129 USD, test environment-д suulgaad code encrypt хийгээд ажиллуулна)

### Хоёр дахь шат (3-7 өдөр)

4. **Performance load test script бичих** — 100k sample, 1M result үүсгэх script
5. **Proposal-ийн эхний draft** — 5-7 хуудас PDF (price, scope, timeline, references)
6. **Хуулийн loyer хайх** — гэрээ template-д тусламж авах (₮500к-1сая зөвлөгөөний цаг)

### Гурав дахь шат (1-2 долоо хоног)

7. **Бэлтгэлд:**
   - HTTPS staging environment-д идэвхжүүлэх
   - Backup restore test (toy data-аар)
   - 5 key user-руу training material бэлдэх (slide + video)

8. **Customer-руу formal proposal илгээх**

---

## 10. ОЙЛГОХГҮЙ БАЙГАА ЗҮЙЛ — АСУУЛТЫН ЖАГСААЛТ

Энэ файлыг уншиж явахдаа дараах хэлбэрээр тэмдэглэж асуу:

```
[ ] Section 2.3 — "anchor pricing" гэж юу гэсэн үг вэ?
[ ] Section 3.2 — PyArmor байгаа бол яагаад .pyc хангалттай биш вэ?
[ ] Section 4.3 — SLA "hot fix 4 цаг" гэдэг ийм хурдан хариулж чадах уу?
[ ] Section 7 — Жил 2-руу "хоёр дахь хүн хөлслөх" гэхэд ямар хүн хэрэгтэй вэ?
```

Эдгээрийг гүйцэтгэхдээ нэг нэгээр асууж тайлбарлуулж явна.

---

## ХОЛБООТОЙ ФАЙЛУУД

| Файл | Хамаарлал |
|------|-----------|
| `DEPLOY_GUIDE.md` | Техник install заавар (IT-руу зориулсан, Docker-based) |
| `docs_all/PRODUCTION_REPORT_2026_02_28.md` | 2026-02 production бэлдэлтийн progress report |
| `docs/dev-logs/PRODUCTION_AUDIT_2026_02_16.md` | Code audit, severity-аар category-аар |
| `docs/dev-logs/PRODUCTION_READINESS_AUDIT_2026_02_27.md` | Readiness scorecard 8.4/10 |
| `docs_all/LIMS_-_ROLE_PERMISSIONS_LOG.md` | Role policy + permission matrix |
| `docs/dev-logs/ROLE_PERMISSIONS_MATRIX_2026_05_16.md` | Кодоос шууд scan хийсэн 120+ үйлдлийн матриц |

---

## ТҮҮХ

| Огноо | Бичсэн |
|-------|--------|
| 2026-05-17 | Эхний draft — бизнес strategy, үнэлгээ, 6-сарын go-to-market roadmap, IT компани өсөх 5 жилийн зам |

---

**Файл үүсгэсэн:** Claude Opus 4.7 (зөвлөгөө)
**Зорилго:** Эхний customer-руу амжилттай deploy хийгээд IT компани болж өргөжих
   business strategy + roadmap.
**Дараа уншихдаа:** Тодорхойгүй хэсэг олдвол § дугаар + асуултаа бэлдэж асуу.
