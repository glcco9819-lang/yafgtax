import io
import os
import tempfile

os.environ["YFG_DATA_DIR"] = tempfile.mkdtemp(prefix="yfg-test-")

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app, password_hash, password_ok, reconcile


def xlsx_bytes(rows):
    wb = Workbook()
    ws = wb.active
    ws.append(["ردیف", "شماره سند", "تاریخ سند", "کل", "معین", "تفصیل", "شرح سند", "بدهکار", "بستانکار"])
    for row in rows:
        ws.append(row)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def normalized_row(line="1", voucher="10", debit="100", credit="100", memo="شرح"):
    return {"voucher": voucher, "line": line, "date": "1405/07/20", "account": "100/20/1", "debit": debit, "credit": credit, "description": memo}


def test_password_hash_and_comparison_are_stable():
    encoded = password_hash("a very strong password")
    assert password_ok("a very strong password", encoded)
    assert not password_ok("wrong password", encoded)


def test_reconciliation_flags_duplicates_and_explains_no_reference():
    row = normalized_row()
    report = reconcile([row, row.copy()], None, "1405/07/01", "1405/07/30")
    assert report["row_count"] == 2
    assert report["voucher_count"] == 1
    assert report["duplicate_rows"] == 1
    assert report["reference_attached"] is False
    assert report["balanced"] is True


def test_web_workflow_and_manager_only_comment_is_private():
    client = TestClient(app)
    r = client.post("/api/setup", json={"name": "مدیر", "username": "admin", "password": "StrongPassword123"})
    assert r.status_code == 200, r.text
    company = client.post("/api/companies", json={"code": "A", "name": "شرکت الف"}).json()
    reference = xlsx_bytes([[1, 10, "1405/07/20", 100, 20, 1, "شرح سند", 100, 100]])
    ref_result = client.post(f"/api/companies/{company['id']}/reference", data={"fiscal_period": "1405/07", "coverage_start": "1405/07/01", "coverage_end": "1405/07/30"}, files={"file": ("reference.xlsx", reference, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert ref_result.status_code == 200, ref_result.text
    employee = client.post("/api/users", json={
        "name": "کارمند الف", "username": "employee1", "password": "EmployeeStrong123",
        "role": "EMPLOYEE", "company_ids": [company["id"]]
    })
    assert employee.status_code == 200, employee.text
    teammate = client.post("/api/users", json={
        "name": "کارمند ب", "username": "employee2", "password": "TeammateStrong123",
        "role": "EMPLOYEE", "company_ids": [company["id"]]
    })
    assert teammate.status_code == 200, teammate.text
    task = client.post("/api/tasks", json={
        "company_id": company["id"], "title": "ثبت اسناد ماهانه", "fiscal_period": "1405/07",
        "assignee_id": employee.json()["id"], "weight": 2
    })
    assert task.status_code == 200, task.text
    task_id = task.json()["id"]
    second_task = client.post("/api/tasks", json={
        "company_id": company["id"], "title": "تطبیق اسناد خرید", "fiscal_period": "1405/07",
        "assignee_id": employee.json()["id"]
    })
    assert second_task.status_code == 200, second_task.text
    # Upload a new reference after task creation; the open task must remain pinned to v1.
    newer_reference = xlsx_bytes([[2, 11, "1405/07/21", 100, 20, 2, "سند جدید", 50, 50]])
    ref2 = client.post(f"/api/companies/{company['id']}/reference", data={"fiscal_period": "1405/07"}, files={"file": ("reference-v2.xlsx", newer_reference, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert ref2.status_code == 200, ref2.text

    # Add a manager-only comment; the employee must never receive its text.
    assert client.post(f"/api/tasks/{task_id}/comments", json={"body": "یادداشت محرمانه", "visibility": "MANAGER_ONLY"}).status_code == 200

    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "employee1", "password": "EmployeeStrong123"}).status_code == 200
    detail = client.get(f"/api/tasks/{task_id}/detail")
    assert detail.status_code == 200, detail.text
    assert all(c["body"] != "یادداشت محرمانه" for c in detail.json()["comments"])

    upload = xlsx_bytes([[1, 10, "1405/07/20", 100, 20, 1, "شرح سند", 100, 100]])
    response = client.post(f"/api/tasks/{task_id}/submit", data={"claimed_start": "1405/07/01", "claimed_end": "1405/07/30", "note": "ثبت شد"}, files={"file": ("report.xlsx", upload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert response.status_code == 200, response.text
    report = response.json()["report"]
    assert report["row_count"] == 1
    assert report["voucher_count"] == 1
    assert report["balanced"] is True
    assert report["reference_attached"] is True
    assert report["reference_version"] == 1
    assert report["matched_exact"] == 1
    assert report["reference_only"] == 0
    performance_entry = client.post("/api/performance-entries", json={
        "work_date": "۱۴۰۵/۰۷/۲۰", "category": "RECONCILIATION", "title": "کنترل اسناد خرید",
        "description": "بررسی و تطبیق اسناد", "duration_minutes": 90
    })
    assert performance_entry.status_code == 200, performance_entry.text
    entry_id = performance_entry.json()["id"]
    assert performance_entry.json()["status"] == "PENDING"
    assert [row["id"] for row in client.get("/api/performance-entries").json()] == [entry_id]
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "employee2", "password": "TeammateStrong123"}).status_code == 200
    assert client.get("/api/performance-entries").json() == []
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "employee1", "password": "EmployeeStrong123"}).status_code == 200
    second_submission = client.post(f"/api/tasks/{second_task.json()['id']}/submit", data={"claimed_start": "1405/07/01", "claimed_end": "1405/07/30"}, files={"file": ("report-copy.xlsx", upload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert second_submission.status_code == 200, second_submission.text
    assert second_submission.json()["report"]["cross_submission_duplicates"] == 1
    delegated = client.post(f"/api/tasks/{task_id}/delegate", json={"assignee_id":teammate.json()["id"],"title":"بخش خرید اسناد","scope":"اسناد خرید از ۱۴۰۵/۰۷/۰۱ تا ۱۴۰۵/۰۷/۱۵"})
    assert delegated.status_code == 200, delegated.text
    assert client.get(f"/api/tasks/{delegated.json()['id']}/detail").status_code == 403

    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "admin", "password": "StrongPassword123"}).status_code == 200
    manager_entries = client.get("/api/performance-entries")
    assert manager_entries.status_code == 200
    assert any(row["id"] == entry_id and row["user_name"] == "کارمند الف" for row in manager_entries.json())
    returned = client.post(f"/api/performance-entries/{entry_id}/review", json={"status": "NEEDS_EDIT", "review_note": "شرح دقیق‌تر شود"})
    assert returned.status_code == 200, returned.text
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "employee1", "password": "EmployeeStrong123"}).status_code == 200
    updated = client.put(f"/api/performance-entries/{entry_id}", json={
        "work_date": "1405/07/20", "category": "RECONCILIATION", "title": "کنترل اسناد خرید - اصلاح‌شده",
        "description": "بررسی و تطبیق اسناد با شرح کامل", "duration_minutes": 95
    })
    assert updated.status_code == 200, updated.text
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "admin", "password": "StrongPassword123"}).status_code == 200
    approved_entry = client.post(f"/api/performance-entries/{entry_id}/review", json={"status": "APPROVED", "review_note": "تأیید شد"})
    assert approved_entry.status_code == 200, approved_entry.text
    rejected = client.post(f"/api/tasks/{task_id}/decision", json={"decision":"RETURNED","score":50,"review_method":"MANUAL_REVIEW","reason":""})
    assert rejected.status_code == 400
    exception = client.post(f"/api/tasks/{task_id}/decision", json={"decision":"APPROVED_WITH_EXCEPTION","score":50,"review_method":"NO_REFERENCE","reason":"","exception_reason":""})
    assert exception.status_code == 400
    approved = client.post(f"/api/tasks/{task_id}/decision", json={"decision":"APPROVED","score":92,"review_method":"REFERENCE_RECONCILIATION","reason":"بررسی شد"})
    assert approved.status_code == 200, approved.text
    parent_detail = client.get(f"/api/tasks/{task_id}/detail").json()
    assert parent_detail["children"][0]["title"] == "بخش خرید اسناد"
    performance = client.get("/api/performance")
    assert performance.status_code == 200
    assert performance.json()[0]["simple_score"] == 92


