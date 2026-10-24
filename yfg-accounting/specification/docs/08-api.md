# ۸. طرح اولیه API

این‌ها قرارداد پیشنهادی‌اند، نه endpointهای پیاده‌سازی‌شده. همه مسیرها باید احراز هویت و مجوز سمت سرور داشته باشند.

## مسیرها
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`
- `GET/POST /api/companies`
- `GET/POST /api/companies/{id}/periods`
- `GET/POST /api/tasks`
- `GET/PATCH /api/tasks/{id}`
- `POST /api/tasks/{id}/assignments`
- `POST /api/tasks/{id}/submit`
- `POST /api/tasks/{id}/decision`
- `POST /api/reference-sets/{id}/versions`
- `POST /api/tasks/{id}/submissions`
- `POST /api/tasks/{id}/reconciliation-runs`
- `GET /api/reconciliation-runs/{id}/diffs`
- `POST /api/reconciliation-diffs/{id}/review`
- `POST/GET /api/tasks/{id}/comments`
- `GET /api/reports/performance`
- `GET /api/audit-events`

## نمونه قرارداد تصمیم
```json
{
  "decision": "APPROVED_WITH_EXCEPTION",
  "score": 72,
  "review_method": "REFERENCE_RECONCILIATION",
  "reconciliation_run_id": "uuid",
  "decision_reason": "توضیح تصمیم",
  "exception_reason": "دلیل ارفاق",
  "correction_due_at": null
}
```
برای `RETURNED` دلیل قابل مشاهده اجباری است؛ برای ارفاق `exception_reason` اجباری است. در `NO_REFERENCE` اجرای تطبیق نباید ثبت شود.
