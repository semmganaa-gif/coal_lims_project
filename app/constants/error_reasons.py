# app/constants/error_reasons.py
"""KPI / Алдааны шалтгааны тогтмолууд."""

ERROR_REASON_KEYS = [
    "sample_prep",
    "measurement",
    "qc_fail",
    "equipment",
    "data_entry",
    "method",
    "sample_mixup",
    "customer_complaint",
]

ERROR_REASON_LABELS = {
    "sample_prep":          "1. Дээж бэлтгэлийн алдаа (Бутлалт/Хуваалт)",
    "measurement":          "2. Шинжилгээний гүйцэтгэлийн алдаа",
    "qc_fail":              "3. QC / Стандарт дээжийн зөрүү",
    "equipment":            "4. Тоног төхөөрөмж / Орчны нөхцөл",
    "data_entry":           "5. Өгөгдөл шивэлт / Тооцооллын алдаа",
    "method":               "6. Арга аргачлал зөрчсөн (SOP)",
    "sample_mixup":         "7. Дээж солигдсон / Буруу дээж",
    "customer_complaint":   "8. Санал гомдол / Хяналтын шинжилгээ",
}
