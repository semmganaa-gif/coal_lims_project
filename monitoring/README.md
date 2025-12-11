# Coal LIMS Monitoring

Prometheus + Grafana monitoring stack.

## Эхлүүлэх

```bash
cd monitoring
docker-compose up -d
```

## Хандах

| Service | URL | Нэвтрэх |
|---------|-----|---------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |

## Flask App тохиргоо

Flask app-аа дараах port дээр ажиллуулна:

```bash
flask run --host=0.0.0.0 --port=5000
```

## Metrics endpoint

App-аас `/metrics` endpoint-ээр Prometheus metrics авна:

```
http://localhost:5000/metrics
```

## Custom Metrics

| Metric | Тайлбар |
|--------|---------|
| `lims_samples_total` | Нийт бүртгэгдсэн дээжний тоо |
| `lims_analysis_total` | Нийт шинжилгээний тоо |
| `lims_qc_checks_total` | QC шалгалтын тоо |
| `lims_active_users` | Идэвхтэй хэрэглэгчийн тоо |
| `lims_db_query_duration_seconds` | DB query хугацаа |

## Dashboard

Grafana-д `Coal LIMS Dashboard` автоматаар үүснэ:

- Нийт дээж, шинжилгээ
- QC алдаа
- HTTP request rate
- Response time (p50, p95)
- Шинжилгээний төрлийн харьцаа
- Захиалагчийн харьцаа

## Зогсоох

```bash
docker-compose down
```

Data устгах:
```bash
docker-compose down -v
```
