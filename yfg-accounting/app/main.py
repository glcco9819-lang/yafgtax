from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import uuid
import zipfile
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.getenv("YFG_DATA_DIR", ROOT / "data")).resolve()
FILES = DATA / "files"
ATTACHMENTS_DIR = DATA / "attachments"
DB_PATH = DATA / "yfg.sqlite3"
MAX_UPLOAD = 20 * 1024 * 1024
CHAT_ATTACHMENT_MAX = 25 * 1024 * 1024
CHAT_ATTACHMENT_ALLOWED = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
    ".pdf", ".txt", ".csv", ".xlsx", ".xls", ".docx", ".doc", ".pptx",
    ".zip", ".7z", ".rar", ".json", ".md"
}
PBKDF2_ROUNDS = 310_000
DATA.mkdir(parents=True, exist_ok=True)
FILES.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="YFG Accounting Desk", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@contextmanager
def db():
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('ADMIN','EMPLOYEE','CEO')),
 active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
 first_name TEXT NOT NULL DEFAULT '', last_name TEXT NOT NULL DEFAULT '',
 phone TEXT NOT NULL DEFAULT '', permissions TEXT
);
CREATE TABLE IF NOT EXISTS sessions(
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 expires_at TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS companies(
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL,
 kind TEXT NOT NULL DEFAULT 'LEGAL', first_name TEXT NOT NULL DEFAULT '', last_name TEXT NOT NULL DEFAULT '',
 national_id TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '',
 postal_code TEXT NOT NULL DEFAULT '', manager_name TEXT NOT NULL DEFAULT '', manager_phone TEXT NOT NULL DEFAULT '',
 description TEXT NOT NULL DEFAULT ''  -- توضیحات شرکت
);
CREATE TABLE IF NOT EXISTS company_contacts(
 id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id),
 contact_type TEXT NOT NULL DEFAULT 'PHONE',  -- PHONE, MOBILE, EMAIL, FAX, WEBSITE, OTHER
 label TEXT NOT NULL DEFAULT '',  -- مثلاً "تلفن دفتر" یا "همراه مدیر"
 value TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
 created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS company_access(
 user_id TEXT NOT NULL REFERENCES users(id), company_id TEXT NOT NULL REFERENCES companies(id),
 PRIMARY KEY(user_id, company_id)
);
CREATE TABLE IF NOT EXISTS tasks(
 id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id), title TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '', fiscal_period TEXT NOT NULL DEFAULT '', scope TEXT NOT NULL DEFAULT '',
 priority TEXT NOT NULL DEFAULT 'NORMAL', weight INTEGER NOT NULL DEFAULT 1,
 due_date TEXT, status TEXT NOT NULL DEFAULT 'ASSIGNED', progress INTEGER NOT NULL DEFAULT 0,
 parent_task_id TEXT REFERENCES tasks(id),
 reference_version_id TEXT REFERENCES reference_versions(id),
 assignee_id TEXT NOT NULL REFERENCES users(id), created_by TEXT NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task_assignments(
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), from_user TEXT,
 to_user TEXT NOT NULL REFERENCES users(id), actor_id TEXT NOT NULL REFERENCES users(id),
 reason TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task_events(
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), actor_id TEXT NOT NULL REFERENCES users(id),
 action TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_versions(
 id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id), fiscal_period TEXT NOT NULL,
 version INTEGER NOT NULL, original_name TEXT NOT NULL, stored_name TEXT NOT NULL, sha256 TEXT NOT NULL,
 row_count INTEGER NOT NULL, coverage_start TEXT, coverage_end TEXT,
 uploaded_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 UNIQUE(company_id, fiscal_period, version)
);
CREATE TABLE IF NOT EXISTS submissions(
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), employee_id TEXT NOT NULL REFERENCES users(id),
 reference_version_id TEXT REFERENCES reference_versions(id),
 version INTEGER NOT NULL, original_name TEXT NOT NULL, stored_name TEXT NOT NULL, sha256 TEXT NOT NULL,
 note TEXT NOT NULL DEFAULT '', claimed_start TEXT, claimed_end TEXT,
 row_count INTEGER NOT NULL, voucher_count INTEGER NOT NULL, duplicate_rows INTEGER NOT NULL,
 out_of_range INTEGER NOT NULL, report_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(task_id, version)
);
CREATE TABLE IF NOT EXISTS normalized_rows(
 id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id), fiscal_period TEXT NOT NULL,
 task_id TEXT NOT NULL REFERENCES tasks(id), submission_id TEXT NOT NULL REFERENCES submissions(id),
 source_row INTEGER NOT NULL, row_key TEXT NOT NULL, row_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions(
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), submission_id TEXT REFERENCES submissions(id),
 decision TEXT NOT NULL, score INTEGER, review_method TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
 exception_reason TEXT NOT NULL DEFAULT '', manager_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS comments(
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), author_id TEXT NOT NULL REFERENCES users(id),
 visibility TEXT NOT NULL CHECK(visibility IN ('EMPLOYEE_VISIBLE','MANAGER_ONLY')),
 body TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS requests(
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), kind TEXT NOT NULL DEFAULT 'GENERAL',
 request_type_id TEXT REFERENCES request_types(id),  -- optional link to a defined request type
 data_json TEXT NOT NULL DEFAULT '{}',  -- dynamic field values: JSON
 user_name_override TEXT NOT NULL DEFAULT '', -- if filled by someone else, otherwise use user.name
 start_date TEXT, end_date TEXT, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING',
 reviewer_id TEXT REFERENCES users(id), review_note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
 reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS request_types(
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 icon TEXT NOT NULL DEFAULT '📝',
 -- fields_json: JSON array of field specs
 -- [{"name":"leave_kind","label":"نوع مرخصی","type":"select","options":["استحقاقی","استعلاجی","بدون حقوق"],"required":true},
 --  {"name":"leave_unit","label":"واحد","type":"select","options":["روزانه","ساعتی"],"required":true},
 --  {"name":"from_date","label":"از تاریخ","type":"date","required":true},
 --  {"name":"to_date","label":"تا تاریخ","type":"date","required":true,"depends":"leave_unit:روزانه"},
 --  {"name":"from_time","label":"از ساعت","type":"time","required":false,"depends":"leave_unit:ساعتی"},
 --  {"name":"to_time","label":"تا ساعت","type":"time","required":false,"depends":"leave_unit:ساعتی"},
 --  {"name":"requester","label":"نام درخواست‌کننده","type":"user_link","required":true},
 --  {"name":"auto_duration","label":"مدت (محاسبه خودکار)","type":"duration","auto":true,"depends_on":["leave_unit","from_date","to_date","from_time","to_time"]},
 --  {"name":"body","label":"شرح","type":"textarea","required":false}]
 fields_json TEXT NOT NULL DEFAULT '[]',
 active INTEGER NOT NULL DEFAULT 1, created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attendance(
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), work_date TEXT NOT NULL,
 check_in TEXT, check_out TEXT, UNIQUE(user_id, work_date)
);
CREATE TABLE IF NOT EXISTS performance_entries(
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), work_date TEXT NOT NULL,
 category TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 1 AND 1440),
 status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','APPROVED','NEEDS_EDIT')),
 review_note TEXT NOT NULL DEFAULT '', reviewer_id TEXT REFERENCES users(id), reviewed_at TEXT,
 created_at TEXT NOT NULL,
 -- Fields to match tasks (added for parity)
 company_id TEXT REFERENCES companies(id),
 fiscal_period TEXT NOT NULL DEFAULT '',
 scope TEXT NOT NULL DEFAULT '',
 priority TEXT NOT NULL DEFAULT 'NORMAL',
 weight INTEGER NOT NULL DEFAULT 1,
 due_date TEXT,
 progress INTEGER NOT NULL DEFAULT 0,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events(
 id TEXT PRIMARY KEY, actor_id TEXT REFERENCES users(id), action TEXT NOT NULL,
 entity_type TEXT NOT NULL, entity_id TEXT, details TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications(
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), title TEXT NOT NULL,
 body TEXT NOT NULL DEFAULT '', read_at TEXT, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tasks_assignee_status ON tasks(assignee_id,status);
CREATE INDEX IF NOT EXISTS ix_submissions_task ON submissions(task_id,version);
CREATE INDEX IF NOT EXISTS ix_normalized_scope_key ON normalized_rows(company_id,fiscal_period,row_key);
CREATE INDEX IF NOT EXISTS ix_audit_created ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS ix_performance_user_date ON performance_entries(user_id,work_date);

-- Phase 2: Time Tracking
CREATE TABLE IF NOT EXISTS time_entries(
 id TEXT PRIMARY KEY, task_id TEXT REFERENCES tasks(id), user_id TEXT NOT NULL REFERENCES users(id),
 start_at TEXT NOT NULL, end_at TEXT, duration_seconds INTEGER NOT NULL DEFAULT 0,
 description TEXT NOT NULL DEFAULT '', billable INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_time_user_date ON time_entries(user_id,start_at);
CREATE INDEX IF NOT EXISTS ix_time_task ON time_entries(task_id);

-- Phase 3: Automations
CREATE TABLE IF NOT EXISTS automations(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, trigger_type TEXT NOT NULL, trigger_config TEXT NOT NULL DEFAULT '{}',
 action_type TEXT NOT NULL, action_config TEXT NOT NULL DEFAULT '{}',
 enabled INTEGER NOT NULL DEFAULT 1, created_by TEXT NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL, last_fired_at TEXT
);

-- Phase 4: Chat (full messenger: DM + GROUP + file attachments)
CREATE TABLE IF NOT EXISTS chat_channels(
 id TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT 'GROUP', -- GROUP | DIRECT
 created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages(
 id TEXT PRIMARY KEY, channel_id TEXT NOT NULL REFERENCES chat_channels(id),
 user_id TEXT NOT NULL REFERENCES users(id), body TEXT NOT NULL DEFAULT '',
 attachment_id TEXT, -- NULL or references chat_attachments.id
 reply_to TEXT REFERENCES chat_messages(id),
 delivered_at TEXT NOT NULL DEFAULT '',  -- filled when other party fetched the message
 read_at TEXT NOT NULL DEFAULT '',       -- filled when other party marked as read
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_channel_members(
 channel_id TEXT NOT NULL REFERENCES chat_channels(id), user_id TEXT NOT NULL REFERENCES users(id),
 last_read_at TEXT NOT NULL DEFAULT '', joined_at TEXT NOT NULL,
 PRIMARY KEY(channel_id, user_id)
);
CREATE TABLE IF NOT EXISTS chat_attachments(
 id TEXT PRIMARY KEY, original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
 mime_type TEXT NOT NULL DEFAULT 'application/octet-stream', size_bytes INTEGER NOT NULL DEFAULT 0,
 sha256 TEXT NOT NULL DEFAULT '', uploaded_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
-- Phase 4b: Customers (persons / portal / contracts / invoices — only persons active now)
CREATE TABLE IF NOT EXISTS persons(
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
 national_id TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
 address TEXT NOT NULL DEFAULT '', postal_code TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
 linked_company_id TEXT REFERENCES companies(id), -- optional link to a company
 active INTEGER NOT NULL DEFAULT 1, created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
-- Phase 4c: Customers — Contracts, Proformas, Invoices (full first version)
CREATE TABLE IF NOT EXISTS contracts(
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
 company_id TEXT NOT NULL REFERENCES companies(id),
 person_id TEXT REFERENCES persons(id),  -- optional contract signer (real person)
 start_date TEXT NOT NULL, end_date TEXT NOT NULL,
 value_amount REAL NOT NULL DEFAULT 0,  -- مبلغ قرارداد
 currency TEXT NOT NULL DEFAULT 'IRR',  -- IRR / USD / EUR
 status TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT / ACTIVE / COMPLETED / TERMINATED
 contract_type TEXT NOT NULL DEFAULT 'general',  -- نوع قرارداد: general, accounting, audit, consulting
 subject TEXT NOT NULL DEFAULT '',  -- موضوع
 notes TEXT NOT NULL DEFAULT '',
 attachment_id TEXT,  -- optional file
 created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS proformas(
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
 company_id TEXT NOT NULL REFERENCES companies(id),
 person_id TEXT REFERENCES persons(id),
 contract_id TEXT REFERENCES contracts(id),  -- optional link to a contract
 issue_date TEXT NOT NULL,
 valid_until TEXT,  -- تاریخ انقضا پیش‌فاکتور
 status TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT / IN_PROGRESS / SENT / ACCEPTED / REJECTED / EXPIRED
 total_amount REAL NOT NULL DEFAULT 0,
 currency TEXT NOT NULL DEFAULT 'IRR',
 items_json TEXT NOT NULL DEFAULT '[]',  -- [{description, qty, unit_price, total, notes}]
 notes TEXT NOT NULL DEFAULT '',
 created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invoices(
 id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
 company_id TEXT NOT NULL REFERENCES companies(id),
 person_id TEXT REFERENCES persons(id),
 proforma_id TEXT REFERENCES proformas(id),  -- optional link to source proforma
 contract_id TEXT REFERENCES contracts(id),  -- optional link to contract
 issue_date TEXT NOT NULL,
 due_date TEXT,  -- تاریخ سررسید
 status TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT / UNPAID / PARTIAL / PAID / OVERDUE / CANCELLED
 total_amount REAL NOT NULL DEFAULT 0,
 paid_amount REAL NOT NULL DEFAULT 0,
 currency TEXT NOT NULL DEFAULT 'IRR',
 items_json TEXT NOT NULL DEFAULT '[]',
 notes TEXT NOT NULL DEFAULT '',
 created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

-- Phase 5: ISO 30414 HR Metrics Snapshots
CREATE TABLE IF NOT EXISTS iso30414_snapshots(
 id TEXT PRIMARY KEY, snapshot_date TEXT NOT NULL, metrics_json TEXT NOT NULL,
 created_by TEXT REFERENCES users(id), created_at TEXT NOT NULL
);

-- Phase 6: Kanban ordering
CREATE TABLE IF NOT EXISTS task_kanban_order(
 task_id TEXT PRIMARY KEY REFERENCES tasks(id), column_status TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0
);

-- Task checklist (5-step workflow)
CREATE TABLE IF NOT EXISTS task_checklist(
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
 step_number INTEGER NOT NULL DEFAULT 1, title TEXT NOT NULL, is_done INTEGER NOT NULL DEFAULT 0,
 done_by TEXT REFERENCES users(id), done_at TEXT, created_at TEXT NOT NULL,
 UNIQUE(task_id, step_number)
);

-- Performance entries enhancements (delegation, score, events)
CREATE TABLE IF NOT EXISTS performance_events(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 actor_id TEXT NOT NULL REFERENCES users(id), action TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL
);

-- Performance delegation (assign part of performance to colleague)
CREATE TABLE IF NOT EXISTS performance_delegations(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 from_user TEXT NOT NULL REFERENCES users(id), to_user TEXT NOT NULL REFERENCES users(id),
 scope TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'DELEGATED',
 created_at TEXT NOT NULL
);

-- Performance scores (0-100 by manager)
CREATE TABLE IF NOT EXISTS performance_scores_v2(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 manager_id TEXT NOT NULL REFERENCES users(id), score INTEGER NOT NULL DEFAULT 0,
 reason TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);

-- Multi-assignee support for tasks
CREATE TABLE IF NOT EXISTS task_collaborators(
 task_id TEXT NOT NULL REFERENCES tasks(id), user_id TEXT NOT NULL REFERENCES users(id),
 role TEXT NOT NULL DEFAULT 'COLLABORATOR', added_by TEXT REFERENCES users(id),
 added_at TEXT NOT NULL, PRIMARY KEY(task_id, user_id)
);

-- Task checklist for performance entries (5-step workflow)
CREATE TABLE IF NOT EXISTS performance_checklist(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 step_number INTEGER NOT NULL DEFAULT 1, title TEXT NOT NULL, is_done INTEGER NOT NULL DEFAULT 0,
 done_by TEXT REFERENCES users(id), done_at TEXT, created_at TEXT NOT NULL,
 UNIQUE(entry_id, step_number)
);

-- Performance comments (separate from task comments)
CREATE TABLE IF NOT EXISTS perf_comments(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 author_id TEXT NOT NULL REFERENCES users(id),
 visibility TEXT NOT NULL CHECK(visibility IN ("EMPLOYEE_VISIBLE","MANAGER_ONLY")),
 body TEXT NOT NULL, created_at TEXT NOT NULL
);

-- Performance submissions (separate from task submissions)
CREATE TABLE IF NOT EXISTS perf_submissions(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 user_id TEXT NOT NULL REFERENCES users(id), version INTEGER NOT NULL,
 original_name TEXT NOT NULL, stored_name TEXT NOT NULL, sha256 TEXT NOT NULL,
 note TEXT NOT NULL DEFAULT "", claimed_start TEXT, claimed_end TEXT,
 row_count INTEGER NOT NULL, voucher_count INTEGER NOT NULL, duplicate_rows INTEGER NOT NULL,
 out_of_range INTEGER NOT NULL, report_json TEXT NOT NULL, created_at TEXT NOT NULL,
 reference_id TEXT, -- مرجع مدیر (در صورت وجود)
 template_valid INTEGER NOT NULL DEFAULT 1, -- اعتبارسنجی قالب (۱=معتبر، ۰=نامعتبر)
 template_errors TEXT NOT NULL DEFAULT "[]", -- خطاهای قالب به JSON
 status TEXT NOT NULL DEFAULT "PENDING", -- PENDING / APPROVED / RETURNED / REJECTED
 manager_id TEXT, decision_at TEXT, decision_note TEXT NOT NULL DEFAULT ""
);

-- Performance reference versions (manager-uploaded reference files for reconciliation)
CREATE TABLE IF NOT EXISTS perf_references(
 id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES performance_entries(id),
 company_id TEXT, fiscal_period TEXT NOT NULL DEFAULT "",
 version INTEGER NOT NULL DEFAULT 1,
 original_name TEXT NOT NULL, stored_name TEXT NOT NULL, sha256 TEXT NOT NULL,
 row_count INTEGER NOT NULL, coverage_start TEXT, coverage_end TEXT,
 uploaded_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);

-- Performance submission reconciliation diffs (row-level)
CREATE TABLE IF NOT EXISTS perf_submission_diffs(
 id TEXT PRIMARY KEY, submission_id TEXT NOT NULL REFERENCES perf_submissions(id),
 source_row INTEGER NOT NULL, voucher TEXT NOT NULL DEFAULT "",
 line TEXT NOT NULL DEFAULT "", date TEXT NOT NULL DEFAULT "",
 account TEXT NOT NULL DEFAULT "", debit TEXT NOT NULL DEFAULT "",
 credit TEXT NOT NULL DEFAULT "", description TEXT NOT NULL DEFAULT "",
 issue_type TEXT NOT NULL, -- MISSING_FROM_REFERENCE / DEBIT_MISMATCH / CREDIT_MISMATCH / DATE_MISMATCH / DESCRIPTION_MISMATCH / VOUCHER_MISMATCH / DUPLICATE / OUT_OF_RANGE
 issue_detail TEXT NOT NULL DEFAULT "",
 ref_debit TEXT, ref_credit TEXT, ref_date TEXT, ref_account TEXT, ref_description TEXT,
 created_at TEXT NOT NULL
);

-- Settings tables (task types, process types, role types, performance types)
CREATE TABLE IF NOT EXISTS task_types(
 id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT NOT NULL DEFAULT '',
 icon TEXT NOT NULL DEFAULT '📋', active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS process_types(
 id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT NOT NULL DEFAULT '',
 default_steps INTEGER NOT NULL DEFAULT 3, active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS role_types(
 id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT NOT NULL DEFAULT '',
 permissions TEXT NOT NULL DEFAULT '[]', active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS performance_types(
 id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL DEFAULT 'general',
 description TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kpis(
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 category TEXT NOT NULL DEFAULT 'quality',
 description TEXT NOT NULL DEFAULT '',
 target_value REAL NOT NULL DEFAULT 100,
 target_operator TEXT NOT NULL DEFAULT '>=',
 unit TEXT NOT NULL DEFAULT '%',
 weight INTEGER NOT NULL DEFAULT 10,
 frequency TEXT NOT NULL DEFAULT 'monthly',
 owner_role TEXT NOT NULL DEFAULT 'EMPLOYEE',
 formula TEXT NOT NULL DEFAULT '',
 active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

-- Seed default KPIs
INSERT OR IGNORE INTO kpis VALUES('kpi1','کیفیت کار','quality','نمره میانگین کیفیت ارائه‌ها (۰ تا ۱۰۰)',90,'>=','%','40','monthly','EMPLOYEE','AVG(performance_scores_v2.score) * 1.0',1,datetime('now'),datetime('now'));
INSERT OR IGNORE INTO kpis VALUES('kpi2','تحویل به‌موقع','ontime','درصد تسک‌های تحویلی در مهلت',85,'>=','%','25','monthly','EMPLOYEE','COUNT(tasks WHERE completed_at<=due_date)/COUNT(tasks)*100',1,datetime('now'),datetime('now'));
INSERT OR IGNORE INTO kpis VALUES('kpi3','حجم کار','volume','مجموع دقیقه‌ی کار ثبت‌شده در ماه',1200,'>=','دقیقه','15','monthly','EMPLOYEE','SUM(performance_entries.duration_minutes)',1,datetime('now'),datetime('now'));
INSERT OR IGNORE INTO kpis VALUES('kpi4','همکاری تیمی','collaboration','تعداد تسک‌های مشارکتی',5,'>=','عدد','15','monthly','EMPLOYEE','COUNT(task_collaborators)',1,datetime('now'),datetime('now'));
INSERT OR IGNORE INTO kpis VALUES('kpi5','رضایت مدیر','satisfaction','میانگین رضایت مدیر از کارکرد',4,'>=','از ۵','5','monthly','EMPLOYEE','AVG(decisions.rating)',1,datetime('now'),datetime('now'));

-- Seed default types
INSERT OR IGNORE INTO task_types VALUES('tt1','ثبت اسناد','ثبت اسناد حسابداری دوره‌ای','📒',1,datetime('now'));
INSERT OR IGNORE INTO task_types VALUES('tt2','بستن دفاتر','بستن دفاتر پایان دوره','📕',1,datetime('now'));
INSERT OR IGNORE INTO task_types VALUES('tt3','اظهارنامه مالیاتی','تهیه و ارسال اظهارنامه','🧾',1,datetime('now'));
INSERT OR IGNORE INTO task_types VALUES('tt4','حسابرسی','حسابرسی و بررسی اسناد','🔍',1,datetime('now'));
INSERT OR IGNORE INTO task_types VALUES('tt5','اصلاح مغایرت','اصلاح اسناد مغایر','🔧',1,datetime('now'));

INSERT OR IGNORE INTO process_types VALUES('pt1','فرآیند ماهانه','دوره ماهانه — ۳ مرحله',3,1,datetime('now'));
INSERT OR IGNORE INTO process_types VALUES('pt2','فرآیند فصلی','دوره فصلی — ۵ مرحله',5,1,datetime('now'));
INSERT OR IGNORE INTO process_types VALUES('pt3','فرآیند سالانه','دوره سالانه — ۵ مرحله',5,1,datetime('now'));

INSERT OR IGNORE INTO role_types VALUES('rt1','ADMIN','مدیر سامانه — دسترسی کامل','["all"]',1,datetime('now'));
INSERT OR IGNORE INTO role_types VALUES('rt2','CEO','مدیرعامل — دید همه شرکت‌ها','["view_all","approve"]',1,datetime('now'));
INSERT OR IGNORE INTO role_types VALUES('rt3','EMPLOYEE','کارمند — دسترسی محدود','["view_assigned","submit_work"]',1,datetime('now'));

INSERT OR IGNORE INTO performance_types VALUES('pft1','حسابداری','accounting','کارهای حسابداری دوره‌ای',1,datetime('now'));
INSERT OR IGNORE INTO performance_types VALUES('pft2','مالیاتی','tax','امور مالیاتی',1,datetime('now'));
INSERT OR IGNORE INTO performance_types VALUES('pft3','حسابرسی','audit','حسابرسی و کنترل',1,datetime('now'));
INSERT OR IGNORE INTO performance_types VALUES('pft4','اداری','admin','کارهای اداری',1,datetime('now'));
INSERT OR IGNORE INTO performance_types VALUES('pft5','مشاوره','consult','مشاوره و پشتیبانی',1,datetime('now'));
INSERT OR IGNORE INTO performance_types VALUES('pft6','سایر','other','سایر کارها',1,datetime('now'));
"""


def init_db() -> None:
    with db() as con:
        con.executescript(SCHEMA)
        # Keep patch-level compatibility if an earlier local 0.1 build already created SQLite.
        for table, column, definition in (
            ("tasks", "parent_task_id", "TEXT REFERENCES tasks(id)"),
            ("tasks", "reference_version_id", "TEXT REFERENCES reference_versions(id)"),
            ("submissions", "reference_version_id", "TEXT REFERENCES reference_versions(id)"),
            # Add new columns to perf_submissions (existing DBs from previous version)
            ("perf_submissions", "reference_id", "TEXT"),
            ("perf_submissions", "template_valid", "INTEGER NOT NULL DEFAULT 1"),
            ("perf_submissions", "template_errors", "TEXT NOT NULL DEFAULT '[]'"),
            ("perf_submissions", "status", "TEXT NOT NULL DEFAULT 'PENDING'"),
            ("perf_submissions", "manager_id", "TEXT"),
            ("perf_submissions", "decision_at", "TEXT"),
            ("perf_submissions", "decision_note", "TEXT NOT NULL DEFAULT ''"),
            # Add task-parity fields to performance_entries (existing DBs)
            ("performance_entries", "company_id", "TEXT REFERENCES companies(id)"),
            ("performance_entries", "fiscal_period", "TEXT NOT NULL DEFAULT ''"),
            ("performance_entries", "scope", "TEXT NOT NULL DEFAULT ''"),
            ("performance_entries", "priority", "TEXT NOT NULL DEFAULT 'NORMAL'"),
            ("performance_entries", "weight", "INTEGER NOT NULL DEFAULT 1"),
            ("performance_entries", "due_date", "TEXT"),
            ("performance_entries", "progress", "INTEGER NOT NULL DEFAULT 0"),
            ("performance_entries", "updated_at", "TEXT"),
            # Settings v2: rich company fields (تعریف شرکت حرفه‌ای)
            ("companies", "kind", "TEXT NOT NULL DEFAULT 'LEGAL'"),
            ("companies", "first_name", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "last_name", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "national_id", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "phone", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "address", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "postal_code", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "manager_name", "TEXT NOT NULL DEFAULT ''"),
            ("companies", "manager_phone", "TEXT NOT NULL DEFAULT ''"),
            # Settings v2: rich user fields + fine-grained permissions
            ("users", "first_name", "TEXT NOT NULL DEFAULT ''"),
            ("users", "last_name", "TEXT NOT NULL DEFAULT ''"),
            ("users", "phone", "TEXT NOT NULL DEFAULT ''"),
            ("users", "permissions", "TEXT"),
        ):
            columns = {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                try:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                except Exception:
                    pass  # column might already exist or table doesn't exist yet

        # Backfill updated_at for old performance entries that don't have it
        try:
            con.execute("UPDATE performance_entries SET updated_at=created_at WHERE updated_at IS NULL OR updated_at=''")
        except Exception:
            pass


init_db()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def tehran_jalali_today() -> str:
    return gregorian_to_jalali(datetime.now(ZoneInfo("Asia/Tehran")).date())


def gregorian_to_jalali(d: date) -> str:
    gy, gm, gd = d.year, d.month, d.day
    month_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + month_days[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def uid() -> str:
    return str(uuid.uuid4())


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${key.hex()}"


def password_ok(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except (ValueError, TypeError):
        return False


def audit(con: sqlite3.Connection, actor: str | None, action: str, entity: str, entity_id: str | None, details: dict[str, Any] | None = None) -> None:
    con.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?,?)", (uid(), actor, action, entity, entity_id, json.dumps(details or {}, ensure_ascii=False), now()))


def notify(con: sqlite3.Connection, user_id: str, title: str, body: str = "") -> None:
    con.execute("INSERT INTO notifications VALUES(?,?,?,?,?,?)", (uid(), user_id, title, body, None, now()))


def current_user(request: Request, con: sqlite3.Connection | None = None) -> sqlite3.Row:
    token = request.cookies.get("yfg_session")
    if not token:
        raise HTTPException(401, "ابتدا وارد سامانه شوید")
    query = "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.active=1"
    args = (hashlib.sha256(token.encode()).hexdigest(), now())
    if con is None:
        with db() as conn:
            row = conn.execute(query, args).fetchone()
    else:
        row = con.execute(query, args).fetchone()
    if row is None:
        raise HTTPException(401, "نشست معتبر نیست؛ دوباره وارد شوید")
    return row


def require_role(user: sqlite3.Row, *roles: str) -> None:
    if user["role"] not in roles:
        raise HTTPException(403, "دسترسی کافی ندارید")


# ===== FINE-GRAINED PERMISSION SYSTEM (نقش‌ها و دسترسی‌ها به ریز فیلد) =====
# هر کاربر می‌تواند علاوه بر نقش پایه، دسترسی‌های ریز داشته باشد.
# users.permissions = NULL یعنی پیش‌فرض نقش؛ در غیر این صورت JSON {perm_key: bool}

PERMISSION_CATALOG = [
    {"group": "داشبورد و گزارش‌ها", "items": [
        {"key": "dashboard.view", "label": "مشاهده نمای کلی", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "reports.kpi", "label": "گزارش عملکرد تیم (KPI)", "roles": ["ADMIN", "CEO"]},
        {"key": "reports.iso", "label": "گزارش ISO 30414", "roles": ["ADMIN", "CEO"]},
        {"key": "audit.view", "label": "گزارش ممیزی", "roles": ["ADMIN"]},
    ]},
    {"group": "تسک‌ها", "items": [
        {"key": "tasks.view", "label": "مشاهده تسک‌ها", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "tasks.create", "label": "ایجاد و واگذاری تسک", "roles": ["ADMIN", "CEO"]},
        {"key": "tasks.decide", "label": "تصمیم مدیر روی تسک (تأیید/برگشت)", "roles": ["ADMIN", "CEO"]},
        {"key": "tasks.reference", "label": "بارگذاری فایل مرجع Excel", "roles": ["ADMIN", "CEO"]},
    ]},
    {"group": "شرکت‌ها", "items": [
        {"key": "companies.view", "label": "مشاهده شرکت‌ها (فقط شرکت‌های واگذارشده)", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "companies.manage", "label": "تعریف/ویرایش/حذف شرکت", "roles": ["ADMIN"]},
    ]},
    {"group": "کاربران", "items": [
        {"key": "users.view", "label": "مشاهده فهرست کاربران", "roles": ["ADMIN", "CEO"]},
        {"key": "users.manage", "label": "ایجاد/ویرایش/غیرفعال‌سازی کاربر", "roles": ["ADMIN"]},
        {"key": "users.permissions", "label": "تعیین نقش‌ها و دسترسی‌های ریز کاربران", "roles": ["ADMIN"]},
    ]},
    {"group": "عملکرد", "items": [
        {"key": "performance.own", "label": "ثبت عملکرد خود", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "performance.review", "label": "بررسی و تصمیم روی عملکرد کارکنان", "roles": ["ADMIN", "CEO"]},
        {"key": "performance.reference", "label": "بارگذاری مرجع عملکرد", "roles": ["ADMIN", "CEO"]},
    ]},
    {"group": "کارکرد و درخواست‌ها", "items": [
        {"key": "attendance.own", "label": "ثبت ورود/خروج خود", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "attendance.all", "label": "مشاهده کارکرد همه کارکنان", "roles": ["ADMIN", "CEO"]},
        {"key": "requests.view", "label": "مشاهده درخواست‌ها", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "requests.decide", "label": "تأیید/رد درخواست‌ها", "roles": ["ADMIN", "CEO"]},
    ]},
    {"group": "ابزارها", "items": [
        {"key": "kanban.view", "label": "برد کانبان", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "time.use", "label": "تایم ترکینگ", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "chat.use", "label": "گفتگو", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "chat.monitor", "label": "نظارت نا‌محسوس بر گفتگوها", "roles": ["ADMIN"]},
        {"key": "automations.manage", "label": "مدیریت اتوماسیون‌ها", "roles": ["ADMIN", "CEO"]},
    ]},
    {"group": "تنظیمات", "items": [
        {"key": "settings.view", "label": "ورود به تنظیمات", "roles": ["ADMIN", "CEO"]},
        {"key": "settings.types", "label": "مدیریت انواع تسک/فرآیند/نقش/عملکرد", "roles": ["ADMIN", "CEO"]},
        {"key": "settings.request_types", "label": "مدیریت انواع درخواست", "roles": ["ADMIN", "CEO"]},
        {"key": "settings.kpi", "label": "مدیریت شاخص‌های کلیدی (KPI)", "roles": ["ADMIN", "CEO"]},
        {"key": "settings.companies", "label": "زیربخش تعریف شرکت", "roles": ["ADMIN", "CEO"]},
        {"key": "settings.users", "label": "زیربخش کاربران", "roles": ["ADMIN", "CEO"]},
        {"key": "settings.permissions", "label": "زیربخش نقش‌ها و دسترسی‌ها", "roles": ["ADMIN", "CEO"]},
    ]},
    {"group": "مشتریان", "items": [
        {"key": "customers.view", "label": "مشاهده اشخاص و شرکت‌های مشتری", "roles": ["ADMIN", "CEO", "EMPLOYEE"]},
        {"key": "customers.manage", "label": "تعریف/ویرایش/حذف اشخاص مشتری", "roles": ["ADMIN", "CEO"]},
        {"key": "customers.contracts", "label": "مدیریت قراردادها", "roles": ["ADMIN", "CEO"]},
        {"key": "customers.proformas", "label": "مدیریت پیش فاکتورها", "roles": ["ADMIN", "CEO"]},
        {"key": "customers.invoices", "label": "مدیریت فاکتورها", "roles": ["ADMIN", "CEO"]},
    ]},
]


def role_default_permissions(role: str) -> dict[str, bool]:
    return {item["key"]: role in item["roles"] for group in PERMISSION_CATALOG for item in group["items"]}


def effective_permissions(user: sqlite3.Row) -> dict[str, bool]:
    perms = role_default_permissions(user["role"])
    raw = user["permissions"] if "permissions" in user.keys() else None
    if raw:
        try:
            override = json.loads(raw)
            if isinstance(override, dict):
                for key, value in override.items():
                    if key in perms:
                        perms[key] = bool(value)
        except (ValueError, TypeError):
            pass
    # محافظت ضد قفل‌شدگی: مدیر فعال همیشه می‌تواند تنظیمات دسترسی را ببیند
    if user["role"] == "ADMIN":
        perms["users.view"] = True
        perms["users.permissions"] = True
        perms["settings.view"] = True
        perms["settings.permissions"] = True
    return perms


def has_perm(user: sqlite3.Row, key: str) -> bool:
    return effective_permissions(user).get(key, False)


def require_perm(user: sqlite3.Row, key: str) -> None:
    if not has_perm(user, key):
        raise HTTPException(403, "دسترسی لازم برای این عملیات را ندارید")


def can_access_company(con: sqlite3.Connection, user: sqlite3.Row, company_id: str) -> bool:
    if user["role"] in ("ADMIN", "CEO"):
        return True
    return con.execute("SELECT 1 FROM company_access WHERE user_id=? AND company_id=?", (user["id"], company_id)).fetchone() is not None


def task_access(con: sqlite3.Connection, user: sqlite3.Row, task_id: str) -> sqlite3.Row:
    task = con.execute("SELECT t.*,c.name AS company_name,c.code AS company_code,u.name AS assignee_name FROM tasks t JOIN companies c ON c.id=t.company_id JOIN users u ON u.id=t.assignee_id WHERE t.id=?", (task_id,)).fetchone()
    if task is None:
        raise HTTPException(404, "تسک پیدا نشد")
    if user["role"] not in ("ADMIN", "CEO") and task["assignee_id"] != user["id"]:
        raise HTTPException(403, "به این تسک دسترسی ندارید")
    return task


def normalize_digits(value: Any) -> str:
    s = str(value if value is not None else "").strip()
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return s.translate(trans)


def normalize_date_input(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return re.sub(r"\s+", "", normalize_digits(value).strip()).replace("-", "/").replace(".", "/")


ALIASES = {
    "row": ["ردیف", "شماره ردیف", "ردیف سند", "row", "row no", "linenumber"],
    "voucher": ["شماره سند", "شماره‌سند", "شماره", "شماره سند حسابداری", "document number", "voucher", "docno"],
    "date": ["تاریخ سند", "تاریخ", "تاریخ‌سند", "document date", "date"],
    "account": ["کد حساب", "حساب", "account", "accountcode", "کل/معین/تفصیل"],
    "major": ["کل", "کد کل", "حساب کل", "major account"],
    "middle": ["معین", "کد معین", "حساب معین", "sub account"],
    "detail": ["تفصیل", "کد تفصیل", "حساب تفصیل", "detail account"],
    "debit": ["بده", "بدهکار", "مبلغ بدهکار", "debit", "debit amount"],
    "credit": ["بس", "بستانکار", "مبلغ بستانکار", "credit", "credit amount"],
    "description": ["شرح سند", "شرح", "توضیحات", "description", "memo"],
}


def norm_header(value: Any) -> str:
    return re.sub(r"[\s_\-]+", "", normalize_digits(value).replace("ي", "ی").replace("ك", "ک").lower())


def parse_amount(value: Any) -> str:
    if value is None:
        return "0"
    s = normalize_digits(value).replace(",", "").replace("٬", "").replace("٫", ".").replace("ریال", "").replace("تومان", "").strip()
    if not s:
        return "0"
    try:
        return str(round(float(s), 2))
    except ValueError:
        return s


def parse_date(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return gregorian_to_jalali(value.date() if isinstance(value, datetime) else value)
    s = normalize_digits(value).strip().replace("-", "/").replace(".", "/")
    s = re.sub(r"\s+", "", s)
    match = re.fullmatch(r"(19\d{2}|20\d{2})/(\d{1,2})/(\d{1,2})", s)
    if match:
        try:
            return gregorian_to_jalali(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            return s
    return s


def read_excel(upload: UploadFile, content: bytes) -> tuple[list[dict[str, str]], str]:
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "حجم فایل بیشتر از ۲۰ مگابایت است")
    if upload.filename and Path(upload.filename).suffix.lower() != ".xlsx":
        raise HTTPException(400, "فقط فایل با پسوند .xlsx پذیرفته می‌شود")
    if not content.startswith(b"PK\x03\x04"):
        raise HTTPException(400, "فایل باید Excel با فرمت .xlsx باشد؛ فایل‌های Macro دار پذیرفته نمی‌شوند")
    try:
        from openpyxl import load_workbook
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(content)) as archive:
            members = archive.infolist()
            if len(members) > 500 or sum(item.file_size for item in members) > 150 * 1024 * 1024:
                raise HTTPException(413, "ساختار داخلی فایل از سقف پردازش مجاز بیشتر است")
            if any("vbaproject" in item.filename.lower() for item in members):
                raise HTTPException(400, "فایل‌های دارای Macro پذیرفته نمی‌شوند")
        wb = load_workbook(BytesIO(content), read_only=True, data_only=True, keep_links=False)
        ws = wb.active
        if ws.max_row and ws.max_row > 200_001:
            raise HTTPException(413, "تعداد ردیف‌ها از سقف مجاز بیشتر است")
        if len(wb.sheetnames) > 10:
            raise HTTPException(413, "تعداد برگه‌های فایل از سقف مجاز بیشتر است")
        header_row = None
        mapping: dict[str, int] = {}
        for idx, row in enumerate(ws.iter_rows(min_row=1, max_row=min(ws.max_row or 1, 15), values_only=True), 1):
            labels = [norm_header(v) for v in row]
            found: dict[str, int] = {}
            for field, variants in ALIASES.items():
                wanted = {norm_header(v) for v in variants}
                for col, label in enumerate(labels):
                    if label in wanted:
                        found[field] = col
                        break
            if "voucher" in found and "date" in found and ("debit" in found or "credit" in found):
                header_row, mapping = idx, found
                break
        if header_row is None:
            raise HTTPException(400, "سربرگ‌های الزامی پیدا نشدند. فایل نمونه را از بخش راهنما دریافت کنید.")
        rows: list[dict[str, str]] = []
        for excel_row, raw in enumerate(ws.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1):
            if not any(v not in (None, "") for v in raw):
                continue
            def val(k: str) -> Any:
                col = mapping.get(k)
                return raw[col] if col is not None and col < len(raw) else ""
            account_parts = [normalize_digits(val(k)) for k in ("major", "middle", "detail") if normalize_digits(val(k))]
            account = "/".join(account_parts) if account_parts else normalize_digits(val("account"))
            row = {
                "source_row": str(excel_row),
                "line": normalize_digits(val("row")) or str(excel_row - header_row),
                "voucher": normalize_digits(val("voucher")),
                "date": parse_date(val("date")),
                "account": account,
                "debit": parse_amount(val("debit")),
                "credit": parse_amount(val("credit")),
                "description": norm_header(val("description")),
            }
            rows.append(row)
            if len(rows) > 200_000:
                raise HTTPException(413, "تعداد ردیف‌های معتبر از سقف مجاز بیشتر است")
        if not rows:
            raise HTTPException(400, "فایل هیچ ردیف اطلاعاتی ندارد")
        return rows, wb.sheetnames[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, "خواندن فایل Excel ناموفق بود؛ قالب یا سلامت فایل را بررسی کنید") from exc


def duplicate_key(row: dict[str, str]) -> tuple[str, ...]:
    return (row["voucher"], row["line"], row["date"], row["account"], row["debit"], row["credit"], row["description"])


def reconcile(sub_rows: list[dict[str, str]], ref_rows: list[dict[str, str]] | None, start: str | None, end: str | None) -> dict[str, Any]:
    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    for row in sub_rows:
        key = duplicate_key(row)
        if key in seen:
            duplicates += 1
        seen.add(key)
    dates = [r["date"] for r in sub_rows if r["date"]]
    out_range = 0
    for d in dates:
        # Lexical range checks apply only to consistently formatted Gregorian or ISO dates;
        # Shamsi dates remain visible for manager review instead of being guessed.
        if start and end and re.match(r"^\d{4}/\d{2}/\d{2}$", d):
            if d < normalize_digits(start).replace("-", "/") or d > normalize_digits(end).replace("-", "/"):
                out_range += 1
    counts: dict[str, int] = {}
    for row in sub_rows:
        counts[row["voucher"]] = counts.get(row["voucher"], 0) + 1
    result: dict[str, Any] = {
        "algorithm_version": "yfg-reconcile-1.0.0",
        "row_count": len(sub_rows),
        "voucher_count": len({r["voucher"] for r in sub_rows if r["voucher"]}),
        "duplicate_rows": duplicates,
        "out_of_range": out_range,
        "min_date": min(dates) if dates else None,
        "max_date": max(dates) if dates else None,
        "debit_total": round(sum(float(r["debit"]) for r in sub_rows if re.fullmatch(r"-?\d+(?:\.\d+)?", r["debit"])), 2),
        "credit_total": round(sum(float(r["credit"]) for r in sub_rows if re.fullmatch(r"-?\d+(?:\.\d+)?", r["credit"])), 2),
        "claimed_start": start,
        "claimed_end": end,
        "reference_attached": ref_rows is not None,
        "reference_row_count": len(ref_rows) if ref_rows is not None else None,
        "matched_exact": None,
        "reference_only": None,
        "submission_only": None,
        "notes": ["شماره سند تکراری به‌تنهایی خطا نیست؛ ردیف‌های یک سند می‌توانند شماره مشترک داشته باشند."],
    }
    result["balanced"] = result["debit_total"] == result["credit_total"]
    if ref_rows is not None:
        remaining = {}
        for r in ref_rows:
            key = duplicate_key(r)
            remaining[key] = remaining.get(key, 0) + 1
        matched = 0
        for r in sub_rows:
            key = duplicate_key(r)
            if remaining.get(key, 0):
                remaining[key] -= 1
                matched += 1
        ref_left = sum(remaining.values())
        result.update(matched_exact=matched, reference_only=ref_left, submission_only=len(sub_rows) - matched)
        result["notes"].append("تطبیق متنی دقیق انجام شده است؛ تفاوت قالب تاریخ یا شرح می‌تواند مورد را برای بررسی مدیر باقی بگذارد.")
    else:
        result["notes"].append("برای این تسک مرجع ثبت نشده؛ نتیجه تطبیق با روش NO_REFERENCE بررسی شود.")
    return result


# ============ Template validation (file structure check) ============

# Expected columns matching the /api/template download
TEMPLATE_EXPECTED_HEADERS = ["voucher", "date", "account", "debit", "credit", "description"]


def validate_template(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Validates the structure of uploaded Excel against the system template.
    Returns: {valid: bool, errors: list[str], missing_columns: list[str], warnings: list[str]}
    """
    errors = []
    warnings = []
    if not rows:
        errors.append("فایل خالی است — هیچ ردیف اطلاعاتی پیدا نشد")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # All required fields must be non-empty for at least one row
    missing_fields = []
    for field in TEMPLATE_EXPECTED_HEADERS:
        has_value = any(r.get(field, "") for r in rows)
        if not has_value:
            missing_fields.append(field)
    if missing_fields:
        errors.append(f"ستون‌های الزامی خالی یا ناقص است: {', '.join(missing_fields)}")

    # Check at least one numeric value in debit/credit
    has_debit = any(re.fullmatch(r"-?\d+(?:\.\d+)?", r.get("debit", "")) for r in rows)
    has_credit = any(re.fullmatch(r"-?\d+(?:\.\d+)?", r.get("credit", "")) for r in rows)
    if not has_debit and not has_credit:
        errors.append("هیچ مقدار عددی در ستون‌های بدهکار/بستانکار پیدا نشد")

    # Check duplicates within the same voucher+line
    seen_keys = set()
    duplicate_count = 0
    for r in rows:
        key = (r.get("voucher", ""), r.get("line", ""), r.get("date", ""))
        if key in seen_keys:
            duplicate_count += 1
        seen_keys.add(key)
    if duplicate_count:
        warnings.append(f"{duplicate_count} ردیف تکراری (شماره سند + خط + تاریخ یکسان) پیدا شد")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(rows),
    }


# ============ Detailed row-level reconciliation ============

def reconcile_detailed(sub_rows: list[dict[str, str]], ref_rows: list[dict[str, str]] | None,
                       start: str | None, end: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Performs full reconciliation AND returns row-level diff list.
    Returns: (summary_report, diffs)
    Each diff: {source_row, voucher, line, date, account, debit, credit, description,
                issue_type, issue_detail, ref_debit, ref_credit, ref_date, ref_account, ref_description}
    """
    summary = reconcile(sub_rows, ref_rows, start, end)
    diffs: list[dict[str, Any]] = []

    # 1. Internal duplicate detection
    seen_keys: dict[tuple, int] = {}
    for r in sub_rows:
        key = duplicate_key(r)
        seen_keys[key] = seen_keys.get(key, 0) + 1

    for r in sub_rows:
        key = duplicate_key(r)
        src_row = int(r.get("source_row", 0))
        # 2. Out-of-range check
        if start and end and r.get("date"):
            d = r["date"]
            if re.match(r"^\d{4}/\d{2}/\d{2}$", d):
                if d < normalize_digits(start).replace("-", "/") or d > normalize_digits(end).replace("-", "/"):
                    diffs.append({
                        "source_row": src_row, "voucher": r["voucher"], "line": r["line"],
                        "date": r["date"], "account": r["account"], "debit": r["debit"],
                        "credit": r["credit"], "description": r["description"],
                        "issue_type": "OUT_OF_RANGE",
                        "issue_detail": f"تاریخ {d} خارج از بازه اعلام‌شده ({start} تا {end}) است",
                        "ref_debit": None, "ref_credit": None, "ref_date": None,
                        "ref_account": None, "ref_description": None,
                    })

    if ref_rows is None:
        # No reference — only internal checks (duplicates, out of range)
        for r in sub_rows:
            key = duplicate_key(r)
            if seen_keys[key] > 1:
                src_row = int(r.get("source_row", 0))
                diffs.append({
                    "source_row": src_row, "voucher": r["voucher"], "line": r["line"],
                    "date": r["date"], "account": r["account"], "debit": r["debit"],
                    "credit": r["credit"], "description": r["description"],
                    "issue_type": "DUPLICATE",
                    "issue_detail": "این ردیف با ردیف دیگری در فایل تکراری است (شماره سند + خط + تاریخ + حساب + مبالغ + شرح)",
                    "ref_debit": None, "ref_credit": None, "ref_date": None,
                    "ref_account": None, "ref_description": None,
                })
                seen_keys[key] -= 1  # only report duplicates once
        return summary, diffs

    # With reference — match by voucher+line (allows description differences)
    ref_index: dict[tuple[str, str], list[dict]] = {}
    for r in ref_rows:
        key = (r["voucher"], r["line"])
        ref_index.setdefault(key, []).append(r)

    consumed: dict[tuple[str, str], int] = {}  # (voucher, line) → consumption count
    matched_sub_rows: set[int] = set()

    for r in sub_rows:
        key = (r["voucher"], r["line"])
        candidates = ref_index.get(key, [])
        src_row = int(r.get("source_row", 0))
        matched = False
        consumed_count = consumed.get(key, 0)
        if consumed_count < len(candidates):
            ref_r = candidates[consumed_count]
            consumed[key] = consumed_count + 1
            matched_sub_rows.add(src_row)
            matched = True
            # Check if exact match
            if (r["date"] == ref_r["date"] and r["account"] == ref_r["account"] and
                r["debit"] == ref_r["debit"] and r["credit"] == ref_r["credit"] and
                r["description"] == ref_r["description"]):
                # Exact match — no diff
                pass
            else:
                # Found by voucher+line but values differ — record mismatch
                diff_details = []
                if r["date"] != ref_r["date"]:
                    diff_details.append(f"تاریخ: {r['date']} ≠ {ref_r['date']}")
                if r["account"] != ref_r["account"]:
                    diff_details.append(f"حساب: {r['account']} ≠ {ref_r['account']}")
                if r["debit"] != ref_r["debit"]:
                    diff_details.append(f"بدهکار: {r['debit']} ≠ {ref_r['debit']}")
                if r["credit"] != ref_r["credit"]:
                    diff_details.append(f"بستانکار: {r['credit']} ≠ {ref_r['credit']}")
                if r["description"] != ref_r["description"]:
                    diff_details.append(f"شرح متفاوت")
                # Determine primary issue type
                if r["debit"] != ref_r["debit"]:
                    issue_type = "DEBIT_MISMATCH"
                elif r["credit"] != ref_r["credit"]:
                    issue_type = "CREDIT_MISMATCH"
                elif r["date"] != ref_r["date"]:
                    issue_type = "DATE_MISMATCH"
                elif r["account"] != ref_r["account"]:
                    issue_type = "ACCOUNT_MISMATCH"
                else:
                    issue_type = "DESCRIPTION_MISMATCH"
                diffs.append({
                    "source_row": src_row, "voucher": r["voucher"], "line": r["line"],
                    "date": r["date"], "account": r["account"], "debit": r["debit"],
                    "credit": r["credit"], "description": r["description"],
                    "issue_type": issue_type,
                    "issue_detail": "، ".join(diff_details),
                    "ref_debit": ref_r["debit"], "ref_credit": ref_r["credit"],
                    "ref_date": ref_r["date"], "ref_account": ref_r["account"],
                    "ref_description": ref_r["description"],
                })
        if not matched:
            # Submission row not found in reference at all
            diffs.append({
                "source_row": src_row, "voucher": r["voucher"], "line": r["line"],
                "date": r["date"], "account": r["account"], "debit": r["debit"],
                "credit": r["credit"], "description": r["description"],
                "issue_type": "MISSING_FROM_REFERENCE",
                "issue_detail": "این ردیف در فایل مرجع پیدا نشد (شماره سند + خط در مرجع وجود ندارد)",
                "ref_debit": None, "ref_credit": None, "ref_date": None,
                "ref_account": None, "ref_description": None,
            })

    # Internal duplicates check (within submission itself)
    for r in sub_rows:
        key = duplicate_key(r)
        if seen_keys[key] > 1:
            src_row = int(r.get("source_row", 0))
            diffs.append({
                "source_row": src_row, "voucher": r["voucher"], "line": r["line"],
                "date": r["date"], "account": r["account"], "debit": r["debit"],
                "credit": r["credit"], "description": r["description"],
                "issue_type": "DUPLICATE",
                "issue_detail": "ردیف تکراری در فایل ارسالی (همه فیلدها یکسان)",
                "ref_debit": None, "ref_credit": None, "ref_date": None,
                "ref_account": None, "ref_description": None,
            })
            seen_keys[key] -= 1

    # Out-of-range rows
    if start and end:
        for r in sub_rows:
            d = r.get("date", "")
            if d and re.match(r"^\d{4}/\d{2}/\d{2}$", d):
                if d < normalize_digits(start).replace("-", "/") or d > normalize_digits(end).replace("-", "/"):
                    src_row = int(r.get("source_row", 0))
                    diffs.append({
                        "source_row": src_row, "voucher": r["voucher"], "line": r["line"],
                        "date": r["date"], "account": r["account"], "debit": r["debit"],
                        "credit": r["credit"], "description": r["description"],
                        "issue_type": "OUT_OF_RANGE",
                        "issue_detail": f"تاریخ {d} خارج از بازه ({start} تا {end})",
                        "ref_debit": None, "ref_credit": None, "ref_date": None,
                        "ref_account": None, "ref_description": None,
                    })

    summary["diff_count"] = len(diffs)
    summary["diffs"] = diffs
    return summary, diffs


class SetupModel(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=200)


class LoginModel(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    first_name: str = Field(default="", max_length=80)
    last_name: str = Field(default="", max_length=80)
    phone: str = Field(default="", max_length=30)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=200)
    password2: str | None = Field(default=None, max_length=200)
    role: str = "EMPLOYEE"
    company_ids: list[str] = []


class UserUpdate(BaseModel):
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str | None = None
    active: bool | None = None
    password: str | None = None
    password2: str | None = None
    company_ids: list[str] | None = None


class CompanyCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    kind: str = Field(default="LEGAL", pattern="^(LEGAL|REAL)$")
    first_name: str = Field(default="", max_length=80)
    last_name: str = Field(default="", max_length=80)
    national_id: str = Field(default="", max_length=20)
    phone: str = Field(default="", max_length=30)
    address: str = Field(default="", max_length=300)
    postal_code: str = Field(default="", max_length=20)
    manager_name: str = Field(default="", max_length=120)
    manager_phone: str = Field(default="", max_length=30)
    description: str = Field(default="", max_length=4000)


class CompanyUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    kind: str | None = Field(default=None, pattern="^(LEGAL|REAL)$")
    first_name: str | None = None
    last_name: str | None = None
    national_id: str | None = None
    phone: str | None = None
    address: str | None = None
    postal_code: str | None = None
    manager_name: str | None = None
    manager_phone: str | None = None
    description: str | None = None
    active: bool | None = None


class TaskCreate(BaseModel):
    company_id: str
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=4000)
    fiscal_period: str = Field(default="", max_length=40)
    scope: str = Field(default="", max_length=500)
    priority: str = "NORMAL"
    weight: int = Field(default=1, ge=1, le=3)
    due_date: str | None = None
    assignee_id: str
    collaborator_ids: list[str] = []  # Multi-assignee support
    checklist_steps: list[str] = []  # 5-step workflow


class TaskUpdate(BaseModel):
    progress: int | None = Field(default=None, ge=0, le=100)
    status: str | None = None
    assignee_id: str | None = None
    reference_version_id: str | None = None
    reason: str = ""


class ChecklistModel(BaseModel):
    steps: list[str] = []  # Up to 5 step titles


class ChecklistToggleModel(BaseModel):
    step_number: int
    is_done: bool


class PerformanceCreateModel(BaseModel):
    work_date: str = Field(min_length=8, max_length=12)
    category: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    duration_minutes: int = Field(ge=1, le=1440)
    checklist_steps: list[str] = []
    delegate_to: str | None = None
    delegate_scope: str = ""


class PerformanceScoreModel(BaseModel):
    score: int = Field(ge=0, le=100)
    reason: str = Field(default="", max_length=500)


class PerformanceDelegateModel(BaseModel):
    to_user: str
    scope: str = Field(default="", max_length=500)


class DelegateModel(BaseModel):
    assignee_id: str
    title: str = Field(min_length=3, max_length=160)
    scope: str = Field(min_length=3, max_length=500)
    description: str = Field(default="", max_length=4000)
    due_date: str | None = None


class DecisionModel(BaseModel):
    decision: str
    score: int | None = Field(default=None, ge=0, le=100)
    review_method: str
    reason: str = ""
    exception_reason: str = ""


class CommentModel(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    visibility: str = "EMPLOYEE_VISIBLE"


class RequestModel(BaseModel):
    kind: str = "GENERAL"
    request_type_id: str | None = None  # if a request_type is selected
    data: dict = {}  # dynamic field values: name -> value
    user_name_override: str = ""  # when filled by someone else on behalf
    # legacy fields still supported
    start_date: str | None = None
    end_date: str | None = None
    body: str = ""

class ReviewRequestModel(BaseModel):
    status: str
    review_note: str = ""

class RequestTypeCreateModel(BaseModel):
    code: str
    name: str
    icon: str = "📝"
    fields: list[dict] = []  # array of field specs
    active: int = 1

class RequestTypeUpdateModel(BaseModel):
    name: str | None = None
    icon: str | None = None
    fields: list[dict] | None = None
    active: int | None = None


class PerformanceEntryModel(BaseModel):
    work_date: str = Field(min_length=8, max_length=12)
    category: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    duration_minutes: int = Field(ge=1, le=1440)
    # Task-parity fields
    company_id: str = Field(default="", max_length=64)
    fiscal_period: str = Field(default="", max_length=40)
    scope: str = Field(default="", max_length=500)
    priority: str = Field(default="NORMAL", max_length=20)
    weight: int = Field(default=1, ge=1, le=3)
    due_date: str = Field(default="", max_length=12)
    progress: int = Field(default=0, ge=0, le=100)


class PerformanceReviewModel(BaseModel):
    status: str
    review_note: str = Field(default="", max_length=1000)


@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(ROOT / "app" / "static" / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(ROOT / "app" / "static" / "sw.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})


@app.get("/api/status")
def status():
    with db() as con:
        return {"setup_needed": con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0, "product": "YFG Accounting Desk", "version": "0.3.0.05"}


@app.post("/api/setup")
def setup(payload: SetupModel, request: Request):
    with db() as con:
        if con.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            raise HTTPException(409, "راه‌اندازی اولیه قبلاً انجام شده است")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", payload.username):
            raise HTTPException(400, "نام کاربری فقط می‌تواند شامل حروف انگلیسی، عدد و . _ - باشد")
        user_id = uid()
        con.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?)", (user_id, payload.name, payload.username.lower(), password_hash(payload.password), "ADMIN", 1, now()))
        audit(con, user_id, "INITIAL_SETUP", "user", user_id)
        issue_session(con, user_id, request)
        return {"ok": True, "user": {"id": user_id, "name": payload.name, "username": payload.username, "role": "ADMIN"}}


def issue_session(con: sqlite3.Connection, user_id: str, request: Request) -> None:
    token = secrets.token_urlsafe(32)
    con.execute("INSERT INTO sessions VALUES(?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user_id, datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1).isoformat(timespec="seconds"), now()))
    request.state.session_token = token


@app.middleware("http")
async def session_cookie_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        if origin:
            host = request.headers.get("host", "")
            # Allow requests from same origin OR from localhost variants (for proxy setups)
            allowed_origins = {
                f"http://{host}", f"https://{host}",
                "http://localhost:3000", "http://127.0.0.1:3000",
                "http://localhost:8000", "http://127.0.0.1:8000",
            }
            if origin not in allowed_origins:
                return HTMLResponse("درخواست مبدأ نامعتبر است", status_code=403)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    token = getattr(request.state, "session_token", None)
    if token:
        response.set_cookie("yfg_session", token, httponly=True, secure=request.url.scheme == "https", samesite="lax", max_age=31_536_000, path="/")
    return response


@app.post("/api/auth/login")
def login(payload: LoginModel, request: Request):
    with db() as con:
        user = con.execute("SELECT * FROM users WHERE username=? AND active=1", (payload.username.lower(),)).fetchone()
        if user is None or not password_ok(payload.password, user["password_hash"]):
            raise HTTPException(401, "نام کاربری یا گذرواژه نادرست است")
        issue_session(con, user["id"], request)
        audit(con, user["id"], "LOGIN", "user", user["id"])
        return {"ok": True}


@app.post("/api/auth/logout")
def logout(request: Request):
    token = request.cookies.get("yfg_session")
    if token:
        with db() as con:
            con.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
    from fastapi.responses import JSONResponse
    response = JSONResponse({"ok": True})
    response.delete_cookie("yfg_session", path="/")
    return response


@app.get("/api/me")
def me(request: Request):
    user = current_user(request)
    return {"id": user["id"], "name": user["name"], "username": user["username"], "role": user["role"],
            "first_name": user["first_name"], "last_name": user["last_name"], "phone": user["phone"],
            "permissions": effective_permissions(user)}


# ===== PERMISSION MANAGEMENT ENDPOINTS (نقش‌ها و دسترسی‌ها) =====

@app.get("/api/permissions/catalog")
def permissions_catalog(request: Request):
    user = current_user(request)
    require_perm(user, "users.view")
    return {
        "catalog": PERMISSION_CATALOG,
        "role_defaults": {role: role_default_permissions(role) for role in ("ADMIN", "CEO", "EMPLOYEE")},
    }


@app.get("/api/users/{user_id}/permissions")
def get_user_permissions(user_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "users.view")
    with db() as con:
        target = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not target:
            raise HTTPException(404, "کاربر یافت نشد")
        override = None
        if target["permissions"]:
            try:
                override = json.loads(target["permissions"])
            except (ValueError, TypeError):
                override = None
        companies = con.execute("""SELECT c.id, c.code, c.name, c.kind FROM company_access a
                                   JOIN companies c ON c.id=a.company_id WHERE a.user_id=? ORDER BY c.name""",
                                (user_id,)).fetchall()
        return {
            "user": {"id": target["id"], "name": target["name"], "username": target["username"],
                     "role": target["role"], "active": target["active"]},
            "effective": effective_permissions(target),
            "override": override,
            "role_defaults": role_default_permissions(target["role"]),
            "companies": [dict(c) for c in companies],
        }


class PermissionsModel(BaseModel):
    permissions: dict[str, bool] | None = None  # None = بازگشت به پیش‌فرض نقش


@app.put("/api/users/{user_id}/permissions")
def set_user_permissions(user_id: str, payload: PermissionsModel, request: Request):
    user = current_user(request)
    require_perm(user, "users.permissions")
    if payload.permissions is not None and user_id == user["id"]:
        # جلوگیری از قفل‌شدن مدیر روی خودش
        raise HTTPException(400, "برای حساب خودتان نمی‌توانید دسترسی‌ها را محدود کنید")
    with db() as con:
        target = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not target:
            raise HTTPException(404, "کاربر یافت نشد")
        if payload.permissions is None:
            con.execute("UPDATE users SET permissions=NULL WHERE id=?", (user_id,))
            audit(con, user["id"], "PERMISSIONS_RESET", "user", user_id, {"role": target["role"]})
        else:
            valid_keys = {item["key"] for group in PERMISSION_CATALOG for item in group["items"]}
            clean = {k: bool(v) for k, v in payload.permissions.items() if k in valid_keys}
            con.execute("UPDATE users SET permissions=? WHERE id=?", (json.dumps(clean, ensure_ascii=False), user_id))
            audit(con, user["id"], "PERMISSIONS_SET", "user", user_id, {"count": len(clean)})
        updated = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))  # اعمال فوری دسترسی‌ها
        return {"ok": True, "effective": effective_permissions(updated)}


@app.get("/api/dashboard")
def dashboard(request: Request):
    user = current_user(request)
    with db() as con:
        where, args = ("", []) if user["role"] in ("ADMIN", "CEO") else ("WHERE assignee_id=?", [user["id"]])
        tasks = con.execute(f"SELECT status,COUNT(*) n FROM tasks {where} GROUP BY status", args).fetchall()
        task_counts = {r["status"]: r["n"] for r in tasks}
        pending_reviews = con.execute("SELECT COUNT(*) FROM tasks WHERE status='SUBMITTED'").fetchone()[0] if user["role"] in ("ADMIN", "CEO") else 0
        open_requests = con.execute("SELECT COUNT(*) FROM requests WHERE status='PENDING'").fetchone()[0] if user["role"] in ("ADMIN", "CEO") else con.execute("SELECT COUNT(*) FROM requests WHERE user_id=? AND status='PENDING'", (user["id"],)).fetchone()[0]
        latest = con.execute(f"SELECT t.id,t.title,t.status,t.progress,t.due_date,c.name company_name,u.name assignee_name FROM tasks t JOIN companies c ON c.id=t.company_id JOIN users u ON u.id=t.assignee_id {where} ORDER BY t.updated_at DESC LIMIT 8", args).fetchall()
        notifs = con.execute("SELECT id,title,body,created_at FROM notifications WHERE user_id=? AND read_at IS NULL ORDER BY created_at DESC LIMIT 8", (user["id"],)).fetchall()
        return {"counts": task_counts, "pending_reviews": pending_reviews, "open_requests": open_requests, "tasks": [dict(r) for r in latest], "notifications": [dict(r) for r in notifs]}


@app.get("/api/companies")
def companies(request: Request):
    user = current_user(request)
    require_perm(user, "companies.view")
    with db() as con:
        if user["role"] in ("ADMIN", "CEO"):
            rows = con.execute("SELECT * FROM companies ORDER BY name").fetchall()
        else:
            rows = con.execute("SELECT c.* FROM companies c JOIN company_access a ON a.company_id=c.id WHERE a.user_id=? AND c.active=1 ORDER BY c.name", (user["id"],)).fetchall()
        return [dict(r) for r in rows]


@app.get("/api/companies/{company_id}/references")
def list_references(company_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        if not can_access_company(con, user, company_id):
            raise HTTPException(403, "به این شرکت دسترسی ندارید")
        return [dict(r) for r in con.execute("SELECT id,fiscal_period,version,original_name,stored_name,sha256,row_count,coverage_start,coverage_end,created_at FROM reference_versions WHERE company_id=? ORDER BY fiscal_period DESC,version DESC", (company_id,))]


@app.post("/api/companies")
def add_company(payload: CompanyCreate, request: Request):
    user = current_user(request)
    require_perm(user, "companies.manage")
    # نام: برای حقیقی از نام + نام خانوادگی ساخته می‌شود اگر خالی باشد
    name = (payload.name or "").strip()
    if payload.kind == "REAL" and not name:
        name = f"{payload.first_name.strip()} {payload.last_name.strip()}".strip()
    if not name or len(name) < 2:
        raise HTTPException(400, "نام شرکت یا نام و نام خانوادگی شخص الزامی است")
    with db() as con:
        company_id = uid()
        try:
            con.execute(
                "INSERT INTO companies(id,code,name,active,created_at,kind,first_name,last_name,national_id,phone,address,postal_code,manager_name,manager_phone,description) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (company_id, payload.code.strip(), name, 1, now(), payload.kind,
                 payload.first_name.strip(), payload.last_name.strip(), payload.national_id.strip(),
                 payload.phone.strip(), payload.address.strip(), payload.postal_code.strip(),
                 payload.manager_name.strip(), payload.manager_phone.strip(), payload.description.strip() if payload.description else "")
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "کد شرکت تکراری است")
        audit(con, user["id"], "COMPANY_CREATE", "company", company_id, {"code": payload.code, "kind": payload.kind})
        return {"id": company_id, "code": payload.code, "name": name, "kind": payload.kind}


@app.get("/api/users")
def users(request: Request):
    user = current_user(request)
    require_perm(user, "users.view")
    with db() as con:
        rows = con.execute("SELECT id,name,username,role,active,created_at,first_name,last_name,phone,permissions FROM users ORDER BY name").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d.pop("permissions", None)  # خروجی خام دسترسی‌ها را لو نده
            n_access = con.execute("SELECT COUNT(*) FROM company_access WHERE user_id=?", (r["id"],)).fetchone()[0]
            d["company_count"] = n_access
            result.append(d)
        return result


@app.post("/api/users")
def add_user(payload: UserCreate, request: Request):
    user = current_user(request)
    require_perm(user, "users.manage")
    if payload.role not in ("EMPLOYEE", "CEO", "ADMIN"):
        raise HTTPException(400, "نقش نامعتبر است")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", payload.username):
        raise HTTPException(400, "نام کاربری فقط می‌تواند شامل حروف انگلیسی، عدد و . _ - باشد")
    if payload.password2 is not None and payload.password != payload.password2:
        raise HTTPException(400, "رمز عبور و تکرار آن یکسان نیستند")
    full_name = (payload.name or "").strip()
    if not full_name:
        full_name = f"{payload.first_name.strip()} {payload.last_name.strip()}".strip()
    if len(full_name) < 2:
        raise HTTPException(400, "نام و نام خانوادگی الزامی است")
    with db() as con:
        new_id = uid()
        try:
            con.execute(
                "INSERT INTO users(id,name,username,password_hash,role,active,created_at,first_name,last_name,phone,permissions) VALUES(?,?,?,?,?,1,?,?,?,?,NULL)",
                (new_id, full_name, payload.username.lower(), password_hash(payload.password), payload.role, now(),
                 payload.first_name.strip(), payload.last_name.strip(), payload.phone.strip())
            )
            for company_id in set(payload.company_ids):
                if not con.execute("SELECT 1 FROM companies WHERE id=?", (company_id,)).fetchone():
                    raise HTTPException(400, "شرکت انتخاب‌شده معتبر نیست")
                con.execute("INSERT INTO company_access VALUES(?,?)", (new_id, company_id))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "نام کاربری تکراری است")
        audit(con, user["id"], "USER_CREATE", "user", new_id, {"role": payload.role, "company_count": len(set(payload.company_ids))})
        return {"id": new_id, "name": full_name, "username": payload.username, "role": payload.role}


# ===== USER MANAGEMENT (edit, deactivate, access control) =====

@app.get("/api/users/{user_id}")
def get_user_detail(user_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "users.view")
    with db() as con:
        u = con.execute("SELECT id,name,username,role,active,created_at,first_name,last_name,phone FROM users WHERE id=?", (user_id,)).fetchone()
        if not u:
            raise HTTPException(404, "کاربر یافت نشد")
        access = con.execute("""SELECT c.id, c.code, c.name FROM company_access a
                                JOIN companies c ON c.id=a.company_id WHERE a.user_id=?""", (user_id,)).fetchall()
        task_count = con.execute("SELECT COUNT(*) FROM tasks WHERE assignee_id=?", (user_id,)).fetchone()[0]
        return {**dict(u), "companies": [dict(r) for r in access], "task_count": task_count}

@app.patch("/api/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate, request: Request):
    user = current_user(request)
    require_perm(user, "users.manage")
    with db() as con:
        existing = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "کاربر یافت نشد")
        updates = {}
        if payload.first_name is not None:
            updates["first_name"] = payload.first_name.strip()
        if payload.last_name is not None:
            updates["last_name"] = payload.last_name.strip()
        if payload.phone is not None:
            updates["phone"] = payload.phone.strip()
        if payload.name is not None and payload.name.strip():
            updates["name"] = payload.name.strip()
        elif payload.first_name is not None or payload.last_name is not None:
            fn = updates.get("first_name", existing["first_name"])
            ln = updates.get("last_name", existing["last_name"])
            composed = f"{fn} {ln}".strip()
            if len(composed) >= 2:
                updates["name"] = composed
        if payload.role is not None:
            if payload.role not in ("EMPLOYEE", "CEO", "ADMIN"):
                raise HTTPException(400, "نقش نامعتبر")
            updates["role"] = payload.role
        if payload.active is not None:
            updates["active"] = 1 if payload.active else 0
        if payload.password is not None:
            if payload.password2 is not None and payload.password != payload.password2:
                raise HTTPException(400, "رمز عبور و تکرار آن یکسان نیستند")
            if len(payload.password) < 4:
                raise HTTPException(400, "رمز عبور باید حداقل ۴ نویسه باشد")
            updates["password_hash"] = password_hash(payload.password)
        if updates:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            con.execute(f"UPDATE users SET {set_clause} WHERE id=?", (*updates.values(), user_id))
            audit(con, user["id"], "USER_UPDATE", "user", user_id, {k: str(v)[:50] for k, v in updates.items()})
        # جایگزینی کامل شرکت‌های واگذارشده در صورت ارسال
        if payload.company_ids is not None:
            for company_id in set(payload.company_ids):
                if not con.execute("SELECT 1 FROM companies WHERE id=?", (company_id,)).fetchone():
                    raise HTTPException(400, "شرکت انتخاب‌شده معتبر نیست")
            con.execute("DELETE FROM company_access WHERE user_id=?", (user_id,))
            for company_id in set(payload.company_ids):
                con.execute("INSERT INTO company_access VALUES(?,?)", (user_id, company_id))
            audit(con, user["id"], "ACCESS_REPLACE", "user", user_id, {"company_count": len(set(payload.company_ids))})
        return {"ok": True, "id": user_id}

@app.delete("/api/users/{user_id}")
def deactivate_user(user_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "users.manage")
    if user_id == user["id"]:
        raise HTTPException(400, "نمی‌توانید حساب خودتان را غیرفعال کنید")
    with db() as con:
        existing = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "کاربر یافت نشد")
        con.execute("UPDATE users SET active=0 WHERE id=?", (user_id,))
        # Also invalidate all sessions
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        audit(con, user["id"], "USER_DEACTIVATE", "user", user_id, {})
        return {"ok": True}

class GrantAccessModel(BaseModel):
    company_ids: list[str] = []

@app.post("/api/users/{user_id}/company-access")
def grant_company_access(user_id: str, payload: GrantAccessModel, request: Request):
    user = current_user(request)
    require_perm(user, "users.manage")
    with db() as con:
        u = con.execute("SELECT 1 FROM users WHERE id=? AND active=1", (user_id,)).fetchone()
        if not u:
            raise HTTPException(404, "کاربر یافت نشد")
        added = 0
        for cid in payload.company_ids:
            if con.execute("SELECT 1 FROM companies WHERE id=? AND active=1", (cid,)).fetchone():
                try:
                    con.execute("INSERT INTO company_access VALUES(?,?)", (user_id, cid))
                    added += 1
                except sqlite3.IntegrityError:
                    pass  # Already exists
        audit(con, user["id"], "ACCESS_GRANT", "user", user_id, {"companies_added": added})
        return {"ok": True, "added": added}

@app.delete("/api/users/{user_id}/company-access/{company_id}")
def revoke_company_access(user_id: str, company_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "users.manage")
    with db() as con:
        con.execute("DELETE FROM company_access WHERE user_id=? AND company_id=?", (user_id, company_id))
        audit(con, user["id"], "ACCESS_REVOKE", "user", user_id, {"company_id": company_id})
        return {"ok": True}


# ===== COMPANY MANAGEMENT (edit, deactivate) =====

@app.patch("/api/companies/{company_id}")
def update_company(company_id: str, payload: CompanyUpdate, request: Request):
    user = current_user(request)
    require_perm(user, "companies.manage")
    with db() as con:
        existing = con.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "شرکت یافت نشد")
        updates = {}
        if payload.name is not None and payload.name.strip():
            updates["name"] = payload.name.strip()
        if payload.code is not None:
            # Check uniqueness
            dup = con.execute("SELECT 1 FROM companies WHERE code=? AND id!=?", (payload.code.strip(), company_id)).fetchone()
            if dup:
                raise HTTPException(409, "کد شرکت تکراری است")
            updates["code"] = payload.code.strip()
        if payload.kind is not None:
            updates["kind"] = payload.kind
        for field in ("first_name", "last_name", "national_id", "phone", "address", "postal_code", "manager_name", "manager_phone"):
            value = getattr(payload, field)
            if value is not None:
                updates[field] = value.strip()
        if payload.description is not None:
            updates["description"] = payload.description.strip()
        if payload.active is not None:
            updates["active"] = 1 if payload.active else 0
        if updates:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            con.execute(f"UPDATE companies SET {set_clause} WHERE id=?", (*updates.values(), company_id))
            audit(con, user["id"], "COMPANY_UPDATE", "company", company_id, {k: str(v)[:50] for k, v in updates.items()})
        return {"ok": True, "id": company_id}

@app.delete("/api/companies/{company_id}")
def deactivate_company(company_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "companies.manage")
    with db() as con:
        existing = con.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "شرکت یافت نشد")
        # Check for active tasks
        active_tasks = con.execute("SELECT COUNT(*) FROM tasks WHERE company_id=? AND status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED')", (company_id,)).fetchone()[0]
        if active_tasks > 0:
            raise HTTPException(400, f"این شرکت {active_tasks} تسک فعال دارد؛ ابتدا تسک‌ها را ببندید")
        con.execute("UPDATE companies SET active=0 WHERE id=?", (company_id,))
        audit(con, user["id"], "COMPANY_DEACTIVATE", "company", company_id, {})
        return {"ok": True}

@app.get("/api/companies/{company_id}/employees")
def company_employees(company_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "users.view")
    with db() as con:
        if not can_access_company(con, user, company_id):
            raise HTTPException(403, "دسترسی ندارید")
        rows = con.execute("""SELECT u.id,u.name,u.username,u.role,u.active FROM users u
                              JOIN company_access a ON a.user_id=u.id WHERE a.company_id=? ORDER BY u.name""", (company_id,)).fetchall()
        return [dict(r) for r in rows]


# ===== PASSWORD CHANGE =====

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@app.post("/api/auth/change-password")
def change_password(payload: PasswordChange, request: Request):
    user = current_user(request)
    if len(payload.new_password) < 4:
        raise HTTPException(400, "رمز جدید باید حداقل ۴ نویسه باشد")
    with db() as con:
        stored = con.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
        if not stored or not password_ok(payload.old_password, stored["password_hash"]):
            raise HTTPException(400, "رمز فعلی نادرست است")
        con.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash(payload.new_password), user["id"]))
        # Invalidate all other sessions
        con.execute("DELETE FROM sessions WHERE user_id!=? OR user_id=?", (user["id"], user["id"]))
        # Actually delete all sessions except we'll create a new one
        con.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
        audit(con, user["id"], "PASSWORD_CHANGE", "user", user["id"], {})
        return {"ok": True, "message": "رمز تغییر یافت؛ لطفاً دوباره وارد شوید"}


# ===== ENHANCED DASHBOARD =====

@app.get("/api/dashboard/v2")
def dashboard_v2(request: Request):
    user = current_user(request)
    require_perm(user, "reports.kpi")
    with db() as con:
        total_companies = con.execute("SELECT COUNT(*) FROM companies WHERE active=1").fetchone()[0]
        total_users = con.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
        total_tasks = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        open_tasks = con.execute("SELECT COUNT(*) FROM tasks WHERE status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED')").fetchone()[0]
        overdue = con.execute("SELECT COUNT(*) FROM tasks WHERE due_date < ? AND status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED')", (now(),)).fetchone()[0]
        submitted = con.execute("SELECT COUNT(*) FROM tasks WHERE status='SUBMITTED'").fetchone()[0]
        returned = con.execute("SELECT COUNT(*) FROM tasks WHERE status='RETURNED'").fetchone()[0]
        approved = con.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('APPROVED','APPROVED_WITH_EXCEPTION')").fetchone()[0]
        pending_reviews = con.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('SUBMITTED','RECONCILING','NEEDS_REVIEW')").fetchone()[0]
        total_submissions = con.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
        pending_leaves = con.execute("SELECT COUNT(*) FROM requests WHERE status='PENDING'").fetchone()[0]
        total_time = con.execute("SELECT COALESCE(SUM(duration_seconds),0) FROM time_entries WHERE end_at IS NOT NULL").fetchone()[0]
        avg_score = con.execute("SELECT COALESCE(AVG(score),0) FROM decisions WHERE score IS NOT NULL").fetchone()[0]

        # Recent activity
        recent_tasks = con.execute("""SELECT t.id,t.title,t.status,t.priority,t.weight,t.due_date,
                                       c.name AS company_name,c.code AS company_code,
                                       u.name AS assignee_name,t.updated_at
                                       FROM tasks t JOIN companies c ON c.id=t.company_id
                                       JOIN users u ON u.id=t.assignee_id
                                       ORDER BY t.updated_at DESC LIMIT 10""").fetchall()
        recent_decisions = con.execute("""SELECT d.id,d.decision,d.score,d.created_at,
                                          t.title AS task_title,u.name AS reviewer_name
                                          FROM decisions d JOIN tasks t ON t.id=d.task_id
                                          JOIN users u ON u.id=d.manager_id
                                          ORDER BY d.created_at DESC LIMIT 10""").fetchall()
        recent_audit = con.execute("""SELECT a.*,u.name AS actor_name FROM audit_events a
                                     LEFT JOIN users u ON u.id=a.actor_id
                                     ORDER BY a.created_at DESC LIMIT 20""").fetchall()

        # Employee workload summary
        workload = con.execute("""SELECT u.id,u.name,u.role,
                                  SUM(CASE WHEN t.status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED') THEN 1 ELSE 0 END) AS open_tasks,
                                  SUM(CASE WHEN t.status IN ('APPROVED','APPROVED_WITH_EXCEPTION') THEN 1 ELSE 0 END) AS done_tasks,
                                  SUM(CASE WHEN t.status='RETURNED' THEN 1 ELSE 0 END) AS returned_tasks,
                                  SUM(CASE WHEN t.due_date < ? AND t.status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED') THEN 1 ELSE 0 END) AS overdue_tasks
                                  FROM users u LEFT JOIN tasks t ON t.assignee_id=u.id
                                  WHERE u.active=1 GROUP BY u.id ORDER BY u.name""", (now(),)).fetchall()

        return {
            "stats": {
                "total_companies": total_companies,
                "total_users": total_users,
                "total_tasks": total_tasks,
                "open_tasks": open_tasks,
                "overdue_tasks": overdue,
                "submitted_tasks": submitted,
                "returned_tasks": returned,
                "approved_tasks": approved,
                "pending_reviews": pending_reviews,
                "total_submissions": total_submissions,
                "pending_leaves": pending_leaves,
                "total_time_hours": round(total_time / 3600, 1),
                "avg_score": round(avg_score, 1),
            },
            "recent_tasks": [dict(r) for r in recent_tasks],
            "recent_decisions": [dict(r) for r in recent_decisions],
            "recent_audit": [{**dict(r), "details": json.loads(r["details"])} for r in recent_audit],
            "employee_workload": [dict(r) for r in workload],
        }


@app.get("/api/tasks")
def list_tasks(request: Request, status_filter: str | None = None):
    user = current_user(request)
    with db() as con:
        sql = "SELECT t.*,c.name company_name,c.code company_code,u.name assignee_name FROM tasks t JOIN companies c ON c.id=t.company_id JOIN users u ON u.id=t.assignee_id"
        args: list[Any] = []
        if user["role"] not in ("ADMIN", "CEO"):
            sql += " WHERE t.assignee_id=?"
            args.append(user["id"])
        if status_filter:
            sql += (" AND " if " WHERE " in sql else " WHERE ") + "t.status=?"
            args.append(status_filter)
        sql += " ORDER BY CASE t.status WHEN 'SUBMITTED' THEN 0 WHEN 'RETURNED' THEN 1 ELSE 2 END,t.due_date IS NULL,t.due_date,t.updated_at DESC"
        return [dict(r) for r in con.execute(sql, args)]


@app.post("/api/tasks")
def create_task(payload: TaskCreate, request: Request):
    user = current_user(request)
    require_perm(user, "tasks.create")
    if payload.priority not in ("NORMAL", "IMPORTANT", "CRITICAL"):
        raise HTTPException(400, "اولویت نامعتبر است")
    payload.fiscal_period=normalize_digits(payload.fiscal_period).strip().replace("-","/")
    payload.due_date=normalize_date_input(payload.due_date)
    with db() as con:
        if not con.execute("SELECT 1 FROM companies WHERE id=? AND active=1", (payload.company_id,)).fetchone():
            raise HTTPException(400, "شرکت انتخاب‌شده معتبر نیست")
        assignee = con.execute("SELECT id,role FROM users WHERE id=? AND active=1", (payload.assignee_id,)).fetchone()
        if not assignee or assignee["role"] not in ("EMPLOYEE", "ADMIN"):
            raise HTTPException(400, "مسئول انتخاب‌شده معتبر نیست")
        if assignee["role"] == "EMPLOYEE" and not can_access_company(con, assignee, payload.company_id):
            raise HTTPException(400, "این کارمند به شرکت انتخاب‌شده دسترسی ندارد")
        # Validate collaborators
        for cid in (payload.collaborator_ids or []):
            coll = con.execute("SELECT id,role FROM users WHERE id=? AND active=1", (cid,)).fetchone()
            if not coll or (coll["role"] == "EMPLOYEE" and not can_access_company(con, coll, payload.company_id)):
                raise HTTPException(400, f"همکار {cid} معتبر نیست یا به این شرکت دسترسی ندارد")
        task_id = uid()
        timestamp = now()
        current_ref = latest_reference(con, payload.company_id, payload.fiscal_period) if payload.fiscal_period else None
        pinned_ref = current_ref["id"] if current_ref else None
        con.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (task_id,payload.company_id,payload.title,payload.description,payload.fiscal_period,payload.scope,payload.priority,payload.weight,payload.due_date,"ASSIGNED",0,None,pinned_ref,payload.assignee_id,user["id"],timestamp,timestamp))
        con.execute("INSERT INTO task_assignments VALUES(?,?,?,?,?,?,?)", (uid(),task_id,None,payload.assignee_id,user["id"],"تخصیص اولیه",timestamp))
        # Add collaborators
        for cid in set(payload.collaborator_ids or []):
            if cid != payload.assignee_id:
                con.execute("INSERT OR IGNORE INTO task_collaborators VALUES(?,?,?,?)", (task_id, cid, "COLLABORATOR", user["id"], timestamp))
                notify(con, cid, "همکار در تسک", f"شما به‌عنوان همکار به تسک «{payload.title}» اضافه شدید")
        # Create checklist steps (up to 5)
        for i, step_title in enumerate((payload.checklist_steps or [])[:5], 1):
            con.execute("INSERT INTO task_checklist VALUES(?,?,?,?,?,?,?,?)", (uid(), task_id, i, step_title.strip(), 0, None, None, timestamp))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)", (uid(),task_id,user["id"],"TASK_CREATED",json.dumps({"status":"ASSIGNED","collaborators":len(payload.collaborator_ids or []),"checklist_steps":len(payload.checklist_steps or [])}),timestamp))
        audit(con, user["id"], "TASK_CREATE", "task", task_id, {"company_id": payload.company_id, "assignee_id": payload.assignee_id})
        notify(con,payload.assignee_id,"تسک جدید",payload.title)
        return {"id": task_id}


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdate, request: Request):
    user = current_user(request)
    with db() as con:
        task = task_access(con,user,task_id)
        changes: list[str] = []
        if payload.assignee_id is not None:
            require_role(user,"ADMIN","CEO")
            target = con.execute("SELECT id,role FROM users WHERE id=? AND active=1",(payload.assignee_id,)).fetchone()
            if not target or (target["role"] == "EMPLOYEE" and not can_access_company(con,target,task["company_id"])):
                raise HTTPException(400,"مسئول جدید به این شرکت دسترسی ندارد")
            old = task["assignee_id"]
            con.execute("UPDATE tasks SET assignee_id=?,updated_at=? WHERE id=?",(payload.assignee_id,now(),task_id))
            con.execute("INSERT INTO task_assignments VALUES(?,?,?,?,?,?,?)",(uid(),task_id,old,payload.assignee_id,user["id"],payload.reason,now()))
            notify(con,payload.assignee_id,"تسک به شما واگذار شد",task["title"])
            changes.append("assignment")
        if payload.progress is not None:
            if user["role"] not in ("ADMIN","CEO") and task["assignee_id"] != user["id"]:
                raise HTTPException(403,"فقط مسئول تسک می‌تواند پیشرفت را ثبت کند")
            con.execute("UPDATE tasks SET progress=?,status=CASE WHEN status IN ('ASSIGNED','IN_PROGRESS','RETURNED') THEN 'IN_PROGRESS' ELSE status END,updated_at=? WHERE id=?",(payload.progress,now(),task_id))
            changes.append("progress")
        if payload.status is not None:
            require_role(user,"ADMIN","CEO")
            if payload.status not in ("CANCELLED", "ASSIGNED"):
                raise HTTPException(400,"از این بخش فقط لغو یا بازتخصیص وضعیت مجاز است")
            con.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?",(payload.status,now(),task_id))
            changes.append("status")
        if payload.reference_version_id is not None:
            require_role(user,"ADMIN","CEO")
            reference=con.execute("SELECT id,company_id,fiscal_period FROM reference_versions WHERE id=?",(payload.reference_version_id,)).fetchone()
            if not reference or reference["company_id"]!=task["company_id"] or reference["fiscal_period"]!=task["fiscal_period"]:
                raise HTTPException(400,"نسخه مرجع باید متعلق به همین شرکت و دوره باشد")
            con.execute("UPDATE tasks SET reference_version_id=?,updated_at=? WHERE id=?",(payload.reference_version_id,now(),task_id))
            changes.append("reference_version")
        if changes:
            con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)",(uid(),task_id,user["id"],"TASK_UPDATE",json.dumps({"changes":changes,"reason":payload.reason},ensure_ascii=False),now()))
            audit(con,user["id"],"TASK_UPDATE","task",task_id,{"changes":changes})
        return {"ok":True}


@app.get("/api/colleagues")
def colleagues(company_id: str, request: Request):
    user=current_user(request)
    with db() as con:
        if not can_access_company(con,user,company_id):
            raise HTTPException(403,"به این شرکت دسترسی ندارید")
        return [dict(r) for r in con.execute("SELECT u.id,u.name FROM users u JOIN company_access a ON a.user_id=u.id WHERE a.company_id=? AND u.active=1 AND u.role='EMPLOYEE' AND u.id<>? ORDER BY u.name",(company_id,user["id"]))]


@app.post("/api/tasks/{task_id}/delegate")
def delegate_task(task_id: str,payload: DelegateModel,request: Request):
    user=current_user(request)
    payload.due_date=normalize_date_input(payload.due_date)
    with db() as con:
        parent=task_access(con,user,task_id)
        if user["role"] in ("ADMIN","CEO") or parent["assignee_id"]!=user["id"]:
            if user["role"] not in ("ADMIN","CEO"):
                raise HTTPException(403,"فقط مسئول تسک می‌تواند بخشی از آن را ارجاع دهد")
        if parent["status"] in ("APPROVED","APPROVED_WITH_EXCEPTION","CANCELLED"):
            raise HTTPException(409,"از تسک پایان‌یافته نمی‌توان بخش ارجاع داد")
        target=con.execute("SELECT id,role FROM users WHERE id=? AND active=1",(payload.assignee_id,)).fetchone()
        if not target or target["role"]!="EMPLOYEE" or not can_access_company(con,target,parent["company_id"]):
            raise HTTPException(400,"همکار انتخاب‌شده به این شرکت دسترسی ندارد")
        child_id=uid(); timestamp=now()
        con.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(child_id,parent["company_id"],payload.title,payload.description,parent["fiscal_period"],payload.scope,parent["priority"],parent["weight"],payload.due_date or parent["due_date"],"ASSIGNED",0,parent["id"],parent["reference_version_id"],payload.assignee_id,user["id"],timestamp,timestamp))
        con.execute("INSERT INTO task_assignments VALUES(?,?,?,?,?,?,?)",(uid(),child_id,None,payload.assignee_id,user["id"],"ارجاع بخش از تسک "+parent["id"],timestamp))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)",(uid(),child_id,user["id"],"TASK_DELEGATED",json.dumps({"parent_task_id":parent["id"],"scope":payload.scope},ensure_ascii=False),timestamp))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)",(uid(),parent["id"],user["id"],"PART_DELEGATED",json.dumps({"child_task_id":child_id,"assignee_id":payload.assignee_id,"scope":payload.scope},ensure_ascii=False),timestamp))
        notify(con,payload.assignee_id,"بخشی از یک تسک به شما ارجاع شد",payload.title)
        audit(con,user["id"],"TASK_DELEGATE","task",child_id,{"parent_task_id":parent["id"],"assignee_id":payload.assignee_id})
        return {"id":child_id,"parent_task_id":parent["id"]}


def latest_reference(con: sqlite3.Connection, company_id: str, period: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM reference_versions WHERE company_id=? AND fiscal_period=? ORDER BY version DESC LIMIT 1",(company_id,period)).fetchone()


@app.post("/api/companies/{company_id}/reference")
async def upload_reference(company_id: str, request: Request, fiscal_period: str = Form(...), coverage_start: str = Form(""), coverage_end: str = Form(""), file: UploadFile = File(...)):
    user = current_user(request)
    require_perm(user, "tasks.reference")
    content = await file.read(MAX_UPLOAD+1)
    rows, _ = read_excel(file,content)
    fiscal_period=normalize_digits(fiscal_period).strip().replace("-","/")
    coverage_start=normalize_date_input(coverage_start) or ""
    coverage_end=normalize_date_input(coverage_end) or ""
    digest = hashlib.sha256(content).hexdigest()
    stored = f"{uuid.uuid4().hex}.xlsx"
    (FILES/stored).write_bytes(content)
    with db() as con:
        company = con.execute("SELECT id FROM companies WHERE id=?",(company_id,)).fetchone()
        if not company: raise HTTPException(404,"شرکت پیدا نشد")
        if con.execute("SELECT 1 FROM reference_versions WHERE company_id=? AND fiscal_period=? AND sha256=?",(company_id,fiscal_period,digest)).fetchone():
            (FILES/stored).unlink(missing_ok=True)
            raise HTTPException(409,"این فایل مرجع قبلاً بارگذاری شده است")
        version = con.execute("SELECT COALESCE(MAX(version),0)+1 FROM reference_versions WHERE company_id=? AND fiscal_period=?",(company_id,fiscal_period)).fetchone()[0]
        ref_id=uid()
        con.execute("INSERT INTO reference_versions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(ref_id,company_id,fiscal_period,version,file.filename or "reference.xlsx",stored,digest,len(rows),coverage_start or None,coverage_end or None,user["id"],now()))
        audit(con,user["id"],"REFERENCE_UPLOAD","reference",ref_id,{"company_id":company_id,"period":fiscal_period,"version":version,"rows":len(rows)})
        return {"id":ref_id,"version":version,"row_count":len(rows)}


@app.post("/api/tasks/{task_id}/submit")
async def submit_task(task_id: str, request: Request, claimed_start: str = Form(""), claimed_end: str = Form(""), note: str = Form(""), file: UploadFile = File(...)):
    user=current_user(request)
    content=await file.read(MAX_UPLOAD+1)
    rows,_=read_excel(file,content)
    claimed_start=normalize_date_input(claimed_start) or ""
    claimed_end=normalize_date_input(claimed_end) or ""
    digest=hashlib.sha256(content).hexdigest()
    with db() as con:
        task=task_access(con,user,task_id)
        if user["role"] not in ("ADMIN","CEO") and task["assignee_id"]!=user["id"]:
            raise HTTPException(403,"فقط مسئول فعلی تسک می‌تواند گزارش بفرستد")
        if task["status"] in ("APPROVED","APPROVED_WITH_EXCEPTION","CANCELLED"):
            raise HTTPException(409,"این تسک دیگر پذیرای گزارش نیست")
        if con.execute("SELECT 1 FROM submissions WHERE task_id=? AND sha256=?",(task_id,digest)).fetchone():
            raise HTTPException(409,"این فایل قبلاً برای همین تسک ارسال شده است")
        ref=con.execute("SELECT * FROM reference_versions WHERE id=?",(task["reference_version_id"],)).fetchone() if task["reference_version_id"] else None
        ref_rows=None
        if ref:
            ref_content=(FILES/ref["stored_name"]).read_bytes()
            ref_rows,_=read_excel(UploadFile(filename=ref["original_name"],file=None),ref_content)
        report=reconcile(rows,ref_rows,claimed_start or None,claimed_end or None)
        row_keys=[hashlib.sha256(json.dumps(duplicate_key(row),ensure_ascii=False,separators=(",",":")).encode()).hexdigest() for row in rows]
        previous_keys:set[str]=set()
        if task["fiscal_period"]:
            unique_keys=list(set(row_keys))
            for offset in range(0,len(unique_keys),400):
                chunk=unique_keys[offset:offset+400]
                placeholders=",".join("?" for _ in chunk)
                previous_keys.update(r["row_key"] for r in con.execute(f"SELECT DISTINCT row_key FROM normalized_rows WHERE company_id=? AND fiscal_period=? AND row_key IN ({placeholders})",[task["company_id"],task["fiscal_period"],*chunk]))
        report["cross_submission_duplicates"] = sum(1 for key in row_keys if key in previous_keys)
        if report["cross_submission_duplicates"]:
            report["notes"].append("برخی ردیف‌ها در گزارش کار قبلی همین شرکت/دوره دیده شده‌اند؛ هم‌پوشانی دامنه را مدیر بررسی کند.")
        report["reference_version_id"] = ref["id"] if ref else None
        report["reference_version"] = ref["version"] if ref else None
        version=con.execute("SELECT COALESCE(MAX(version),0)+1 FROM submissions WHERE task_id=?",(task_id,)).fetchone()[0]
        stored=f"{uuid.uuid4().hex}.xlsx"
        (FILES/stored).write_bytes(content)
        sub_id=uid()
        con.execute("INSERT INTO submissions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(sub_id,task_id,user["id"],ref["id"] if ref else None,version,file.filename or "submission.xlsx",stored,digest,note,claimed_start or None,claimed_end or None,len(rows),report["voucher_count"],report["duplicate_rows"],report["out_of_range"],json.dumps(report,ensure_ascii=False),now()))
        if task["fiscal_period"]:
            timestamp=now()
            con.executemany("INSERT INTO normalized_rows VALUES(?,?,?,?,?,?,?,?,?)",[(uid(),task["company_id"],task["fiscal_period"],task_id,sub_id,int(row["source_row"]),row_keys[i],json.dumps(row,ensure_ascii=False),timestamp) for i,row in enumerate(rows)])
        con.execute("UPDATE tasks SET status='SUBMITTED',progress=100,updated_at=? WHERE id=?",(now(),task_id))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)",(uid(),task_id,user["id"],"SUBMITTED",json.dumps({"submission_id":sub_id,"version":version}),now()))
        managers=con.execute("SELECT id FROM users WHERE role IN ('ADMIN','CEO') AND active=1").fetchall()
        for manager in managers: notify(con,manager["id"],"گزارش کار جدید",task["title"])
        audit(con,user["id"],"SUBMISSION_CREATE","submission",sub_id,{"task_id":task_id,"version":version,"sha256":digest,"row_count":len(rows)})
        return {"id":sub_id,"version":version,"report":report}


@app.get("/api/tasks/{task_id}/detail")
def task_detail(task_id: str, request: Request):
    user=current_user(request)
    with db() as con:
        task=task_access(con,user,task_id)
        submissions=con.execute("SELECT s.*,u.name employee_name FROM submissions s JOIN users u ON u.id=s.employee_id WHERE task_id=? ORDER BY version DESC",(task_id,)).fetchall()
        decisions=con.execute("SELECT d.*,u.name manager_name FROM decisions d JOIN users u ON u.id=d.manager_id WHERE task_id=? ORDER BY created_at DESC",(task_id,)).fetchall()
        if user["role"] in ("ADMIN","CEO"):
            comments=con.execute("SELECT c.*,u.name author_name FROM comments c JOIN users u ON u.id=c.author_id WHERE task_id=? ORDER BY created_at",(task_id,)).fetchall()
        else:
            comments=con.execute("SELECT c.*,u.name author_name FROM comments c JOIN users u ON u.id=c.author_id WHERE task_id=? AND visibility='EMPLOYEE_VISIBLE' ORDER BY created_at",(task_id,)).fetchall()
        history=con.execute("SELECT e.*,u.name actor_name FROM task_events e JOIN users u ON u.id=e.actor_id WHERE task_id=? ORDER BY created_at",(task_id,)).fetchall()
        children=con.execute("SELECT t.id,t.title,t.status,t.progress,u.name assignee_name FROM tasks t JOIN users u ON u.id=t.assignee_id WHERE t.parent_task_id=? ORDER BY t.created_at",(task_id,)).fetchall()
        parent=con.execute("SELECT t.id,t.title FROM tasks t WHERE t.id=?",(task["parent_task_id"],)).fetchone() if task["parent_task_id"] else None
        return {"task":dict(task),"parent":dict(parent) if parent else None,"children":[dict(c) for c in children],"submissions":[{**dict(s),"report":json.loads(s["report_json"])} for s in submissions],"decisions":[dict(d) for d in decisions],"comments":[dict(c) for c in comments],"history":[dict(e) for e in history]}


@app.post("/api/tasks/{task_id}/decision")
def decide(task_id: str,payload: DecisionModel,request: Request):
    user=current_user(request); require_perm(user, "tasks.decide")
    allowed={"APPROVED","APPROVED_WITH_EXCEPTION","RETURNED","CANCELLED"}
    methods={"REFERENCE_RECONCILIATION","MANUAL_REVIEW","NO_REFERENCE"}
    if payload.decision not in allowed or payload.review_method not in methods: raise HTTPException(400,"تصمیم یا روش بررسی نامعتبر است")
    if payload.decision=="RETURNED" and len(payload.reason.strip())<5: raise HTTPException(400,"برای بازگشت، دلیل روشن و قابل مشاهده الزامی است")
    if payload.decision=="APPROVED_WITH_EXCEPTION" and len(payload.exception_reason.strip())<5: raise HTTPException(400,"دلیل ارفاق الزامی است")
    if payload.decision in ("APPROVED","APPROVED_WITH_EXCEPTION") and payload.score is None: raise HTTPException(400,"برای تکمیل تسک نمرهٔ ۰ تا ۱۰۰ الزامی است")
    if payload.decision=="CANCELLED" and len(payload.reason.strip())<5: raise HTTPException(400,"برای لغو تسک دلیل الزامی است")
    if payload.review_method=="NO_REFERENCE" and payload.decision not in ("APPROVED","APPROVED_WITH_EXCEPTION"):
        raise HTTPException(400,"روش NO_REFERENCE فقط برای تأیید قابل انتخاب است")
    with db() as con:
        task=task_access(con,user,task_id)
        sub=con.execute("SELECT id FROM submissions WHERE task_id=? ORDER BY version DESC LIMIT 1",(task_id,)).fetchone()
        if payload.review_method=="REFERENCE_RECONCILIATION":
            checked=con.execute("SELECT report_json FROM submissions WHERE task_id=? ORDER BY version DESC LIMIT 1",(task_id,)).fetchone()
            if not checked or not json.loads(checked["report_json"]).get("reference_attached"):
                raise HTTPException(400,"برای روش تطبیق با مرجع، ارسال دارای مرجع لازم است")
        if payload.review_method=="NO_REFERENCE" and task["reference_version_id"]:
            raise HTTPException(400,"برای این تسک مرجع نسخه‌دار متصل است؛ روش بررسی را انتخاب کنید")
        decision_id=uid(); created=now()
        con.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?,?,?)",(decision_id,task_id,sub["id"] if sub else None,payload.decision,payload.score,payload.review_method,payload.reason,payload.exception_reason,user["id"],created))
        con.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?",(payload.decision,created,task_id))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)",(uid(),task_id,user["id"],"MANAGER_DECISION",json.dumps({"decision":payload.decision,"score":payload.score,"method":payload.review_method,"reason":payload.reason},ensure_ascii=False),created))
        notify(con,task["assignee_id"],"نتیجه بررسی تسک",f"{task['title']} — {payload.decision}")
        audit(con,user["id"],"MANAGER_DECISION","task",task_id,{"decision":payload.decision,"score":payload.score,"review_method":payload.review_method})
        return {"ok":True,"decision_id":decision_id}


@app.post("/api/tasks/{task_id}/comments")
def add_comment(task_id: str,payload: CommentModel,request: Request):
    user=current_user(request)
    if payload.visibility not in ("EMPLOYEE_VISIBLE","MANAGER_ONLY"): raise HTTPException(400,"سطح دید نامعتبر است")
    if payload.visibility=="MANAGER_ONLY": require_role(user,"ADMIN","CEO")
    with db() as con:
        task=task_access(con,user,task_id)
        comment_id=uid(); con.execute("INSERT INTO comments VALUES(?,?,?,?,?,?)",(comment_id,task_id,user["id"],payload.visibility,payload.body,now()))
        if user["role"] in ("ADMIN","CEO") and payload.visibility=="EMPLOYEE_VISIBLE": notify(con,task["assignee_id"],"یادداشت جدید برای تسک",task["title"])
        audit(con,user["id"],"COMMENT_CREATE","task",task_id,{"visibility":payload.visibility})
        return {"id":comment_id}


@app.get("/api/performance")
def performance(request: Request):
    user=current_user(request); require_perm(user, "reports.kpi")
    with db() as con:
        people=con.execute("SELECT id,name FROM users WHERE role='EMPLOYEE' AND active=1 ORDER BY name").fetchall()
        result=[]
        for person in people:
            scores=con.execute("SELECT d.score,t.weight,d.decision FROM decisions d JOIN tasks t ON t.id=d.task_id WHERE t.assignee_id=? AND d.score IS NOT NULL AND d.decision NOT IN ('CANCELLED','RETURNED') AND d.id=(SELECT d2.id FROM decisions d2 WHERE d2.task_id=d.task_id ORDER BY d2.created_at DESC LIMIT 1)",(person["id"],)).fetchall()
            total=con.execute("SELECT COUNT(*) FROM tasks WHERE assignee_id=?",(person["id"],)).fetchone()[0]
            completed=con.execute("SELECT COUNT(*) FROM tasks WHERE assignee_id=? AND status IN ('APPROVED','APPROVED_WITH_EXCEPTION')",(person["id"],)).fetchone()[0]
            vals=[s["score"] for s in scores]
            weight_sum=sum(s["weight"] for s in scores)
            weighted=round(sum(s["score"]*s["weight"] for s in scores)/weight_sum,1) if weight_sum else None
            simple=round(sum(vals)/len(vals),1) if vals else None
            due_rows=con.execute("SELECT due_date FROM tasks WHERE assignee_id=? AND due_date IS NOT NULL AND status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED')",(person["id"],)).fetchall()
            today_jalali=tehran_jalali_today()
            late=sum(1 for r in due_rows if normalize_digits(r["due_date"]).replace("-","/")<today_jalali)
            result.append({"id":person["id"],"name":person["name"],"total":total,"completed":completed,"late":late,"simple_score":simple,"weighted_score":weighted})
        return result


PERFORMANCE_CATEGORIES = {"ACCOUNTING", "RECONCILIATION", "CLIENT_SERVICE", "ADMINISTRATION", "OTHER"}


def clean_work_date(value: str) -> str:
    normalized = normalize_digits(value).strip().replace("-", "/").replace(".", "/")
    match = re.fullmatch(r"(13\d{2}|14\d{2}|15\d{2})/(\d{1,2})/(\d{1,2})", normalized)
    if not match:
        raise HTTPException(400, "تاریخ را به شکل شمسی ۱۴۰۵/۰۷/۲۷ وارد کنید")
    year, month, day = map(int, match.groups())
    if not 1 <= month <= 12 or not 1 <= day <= (31 if month <= 6 else 30):
        raise HTTPException(400, "تاریخ شمسی معتبر نیست")
    return f"{year:04d}/{month:02d}/{day:02d}"


@app.get("/api/performance-entries")
def list_performance_entries(request: Request):
    user = current_user(request)
    with db() as con:
        query = """SELECT p.*,u.name AS user_name,r.name AS reviewer_name,
                   c.name AS company_name
                   FROM performance_entries p JOIN users u ON u.id=p.user_id
                   LEFT JOIN users r ON r.id=p.reviewer_id
                   LEFT JOIN companies c ON c.id=p.company_id"""
        args: tuple[Any, ...] = ()
        if user["role"] not in ("ADMIN", "CEO"):
            query += " WHERE p.user_id=?"
            args = (user["id"],)
        query += " ORDER BY p.work_date DESC,p.created_at DESC LIMIT 500"
        return [dict(row) for row in con.execute(query, args).fetchall()]


@app.post("/api/performance-entries")
def create_performance_entry(payload: PerformanceEntryModel, request: Request):
    user = current_user(request)
    if payload.category not in PERFORMANCE_CATEGORIES:
        raise HTTPException(400, "نوع عملکرد معتبر نیست")
    work_date = clean_work_date(payload.work_date)
    due_date = normalize_date_input(payload.due_date) or None
    entry_id, created = uid(), now()
    with db() as con:
        con.execute("""INSERT INTO performance_entries
            (id,user_id,work_date,category,title,description,duration_minutes,status,created_at,
             company_id,fiscal_period,scope,priority,weight,due_date,progress,updated_at)
            VALUES(?,?,?,?,?,?,?,'PENDING',?,?,?,?,?,?,?,?,?)""",
            (entry_id,user["id"],work_date,payload.category,payload.title.strip(),payload.description.strip(),
             payload.duration_minutes,created,
             payload.company_id or None, payload.fiscal_period, payload.scope,
             payload.priority, payload.weight, due_date, payload.progress, created))
        audit(con,user["id"],"PERFORMANCE_ENTRY_CREATE","performance_entry",entry_id,
              {"category":payload.category,"duration_minutes":payload.duration_minutes,
               "priority":payload.priority,"weight":payload.weight})
    return {"id": entry_id, "status": "PENDING"}


@app.put("/api/performance-entries/{entry_id}")
def update_performance_entry(entry_id: str, payload: PerformanceEntryModel, request: Request):
    user = current_user(request)
    if payload.category not in PERFORMANCE_CATEGORIES:
        raise HTTPException(400, "نوع عملکرد معتبر نیست")
    work_date = clean_work_date(payload.work_date)
    due_date = normalize_date_input(payload.due_date) or None
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if entry is None:
            raise HTTPException(404, "گزارش عملکرد پیدا نشد")
        if entry["user_id"] != user["id"]:
            raise HTTPException(403, "فقط صاحب گزارش می‌تواند آن را ویرایش کند")
        if entry["status"] == "APPROVED":
            raise HTTPException(409, "گزارش تأییدشده قابل ویرایش نیست")
        con.execute("""UPDATE performance_entries SET work_date=?,category=?,title=?,description=?,
            duration_minutes=?,status='PENDING',review_note='',reviewer_id=NULL,reviewed_at=NULL,
            company_id=?,fiscal_period=?,scope=?,priority=?,weight=?,due_date=?,progress=?,updated_at=? WHERE id=?""",
            (work_date,payload.category,payload.title.strip(),payload.description.strip(),payload.duration_minutes,
             payload.company_id or None, payload.fiscal_period, payload.scope,
             payload.priority, payload.weight, due_date, payload.progress, now(), entry_id))
        audit(con,user["id"],"PERFORMANCE_ENTRY_UPDATE","performance_entry",entry_id,
              {"category":payload.category,"duration_minutes":payload.duration_minutes})
    return {"id": entry_id, "status": "PENDING"}


@app.post("/api/performance-entries/{entry_id}/review")
def review_performance_entry(entry_id: str, payload: PerformanceReviewModel, request: Request):
    user = current_user(request)
    require_perm(user, "performance.review")
    if payload.status not in ("APPROVED", "NEEDS_EDIT"):
        raise HTTPException(400, "وضعیت بررسی معتبر نیست")
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if entry is None:
            raise HTTPException(404, "گزارش عملکرد پیدا نشد")
        if entry["user_id"] == user["id"]:
            raise HTTPException(403, "گزارش عملکرد خودتان را نمی‌توانید بررسی کنید")
        if entry["status"] == "APPROVED":
            raise HTTPException(409, "این گزارش قبلاً تأیید شده است")
        reviewed = now()
        con.execute("UPDATE performance_entries SET status=?,review_note=?,reviewer_id=?,reviewed_at=? WHERE id=?",
                    (payload.status,payload.review_note.strip(),user["id"],reviewed,entry_id))
        notify(con,entry["user_id"],"بررسی ثبت عملکرد", "گزارش شما تأیید شد" if payload.status == "APPROVED" else "گزارش شما برای اصلاح بازگشت؛ یادداشت مدیر را ببینید")
        audit(con,user["id"],"PERFORMANCE_ENTRY_REVIEW","performance_entry",entry_id,{"status":payload.status})
    return {"id": entry_id, "status": payload.status}


@app.get("/api/requests")
def list_requests(request: Request):
    user=current_user(request)
    with db() as con:
        if user["role"] in ("ADMIN","CEO"):
            rows=con.execute("""SELECT r.*, u.name user_name, rt.name AS request_type_name, rt.icon AS request_type_icon
                                FROM requests r
                                LEFT JOIN users u ON u.id=r.user_id
                                LEFT JOIN request_types rt ON rt.id=r.request_type_id
                                ORDER BY CASE r.status WHEN 'PENDING' THEN 0 ELSE 1 END, r.created_at DESC""").fetchall()
        else:
            rows=con.execute("""SELECT r.*, u.name user_name, rt.name AS request_type_name, rt.icon AS request_type_icon
                                FROM requests r
                                LEFT JOIN users u ON u.id=r.user_id
                                LEFT JOIN request_types rt ON rt.id=r.request_type_id
                                WHERE r.user_id=? ORDER BY r.created_at DESC""",(user["id"],)).fetchall()
        return [dict(r) for r in rows]


@app.post("/api/requests")
def create_request(payload: RequestModel,request: Request):
    user=current_user(request)
    kind = payload.kind or "GENERAL"
    data_json = json.dumps(payload.data, ensure_ascii=False) if payload.data else "{}"
    start_date = payload.start_date or payload.data.get("from_date") if isinstance(payload.data, dict) else payload.start_date
    end_date = payload.end_date or payload.data.get("to_date") if isinstance(payload.data, dict) else payload.end_date
    body = payload.body or payload.data.get("body","") if isinstance(payload.data, dict) else payload.body

    # Validate request_type if provided
    request_type_name = None
    if payload.request_type_id:
        with db() as con:
            rt = con.execute("SELECT * FROM request_types WHERE id=? AND active=1",(payload.request_type_id,)).fetchone()
            if not rt: raise HTTPException(400,"نوع درخواست نامعتبر یا غیرفعال است")
            request_type_name = rt["name"]

    with db() as con:
        rid=uid()
        con.execute("""INSERT INTO requests
            (id, user_id, kind, request_type_id, data_json, user_name_override,
             start_date, end_date, body, status, reviewer_id, review_note, created_at, reviewed_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, user["id"], kind, payload.request_type_id, data_json, payload.user_name_override,
             start_date, end_date, body or "", "PENDING", None, "", now(), None))
        for manager in con.execute("SELECT id FROM users WHERE role IN ('ADMIN','CEO') AND active=1").fetchall():
            notify(con,manager["id"],"درخواست جدید", request_type_name or kind)
        audit(con,user["id"],"REQUEST_CREATE","request",rid,{"kind":kind, "request_type_id": payload.request_type_id})
    return {"id":rid}


@app.patch("/api/requests/{request_id}")
def review_request(request_id:str,payload:ReviewRequestModel,request:Request):
    user=current_user(request); require_perm(user, "requests.decide")
    if payload.status not in ("APPROVED","REJECTED"): raise HTTPException(400,"وضعیت بررسی نامعتبر است")
    with db() as con:
        item=con.execute("SELECT * FROM requests WHERE id=?",(request_id,)).fetchone()
        if not item: raise HTTPException(404,"درخواست پیدا نشد")
        con.execute("UPDATE requests SET status=?,reviewer_id=?,review_note=?,reviewed_at=? WHERE id=?",(payload.status,user["id"],payload.review_note,now(),request_id))
        notify(con,item["user_id"],"درخواست شما بررسی شد",payload.status)
        audit(con,user["id"],"REQUEST_REVIEW","request",request_id,{"status":payload.status})
        return {"ok":True}


# ========================================================================
# REQUEST TYPES API (تنظیمات → انواع درخواست)
# ========================================================================

@app.get("/api/request-types")
def list_request_types(request: Request):
    user=current_user(request)
    require_perm(user, "requests.view")
    with db() as con:
        rows = con.execute("""SELECT rt.*, u.name AS created_by_name, COUNT(r.id) AS usage_count
                              FROM request_types rt LEFT JOIN users u ON u.id=rt.created_by
                              LEFT JOIN requests r ON r.request_type_id=rt.id
                              GROUP BY rt.id ORDER BY rt.created_at DESC""").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["fields"] = json.loads(r["fields_json"]) if r["fields_json"] else []
            except Exception:
                d["fields"] = []
            del d["fields_json"]
            result.append(d)
        return result

@app.post("/api/request-types")
def create_request_type(payload: RequestTypeCreateModel, request: Request):
    user = current_user(request)
    require_perm(user, "settings.request_types")
    if not payload.code.strip() or not payload.name.strip():
        raise HTTPException(400, "کد و نام نوع درخواست الزامی است")
    rt_id = uid()
    fields_json = json.dumps(payload.fields, ensure_ascii=False) if payload.fields else "[]"
    with db() as con:
        try:
            con.execute("INSERT INTO request_types VALUES(?,?,?,?,?,?,?,?)",
                        (rt_id, payload.code.strip(), payload.name.strip(), payload.icon or "📝",
                         fields_json, payload.active, user["id"], now()))
        except Exception as e:
            if "UNIQUE" in str(e): raise HTTPException(400, "کد نوع درخواست تکراری است")
            raise
        audit(con, user["id"], "REQUEST_TYPE_CREATE", "request_type", rt_id, {"code": payload.code, "name": payload.name})
    return {"id": rt_id, "code": payload.code}

@app.get("/api/request-types/{rt_id}")
def get_request_type(rt_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "requests.view")
    with db() as con:
        r = con.execute("SELECT * FROM request_types WHERE id=?", (rt_id,)).fetchone()
        if not r: raise HTTPException(404, "نوع درخواست پیدا نشد")
        d = dict(r)
        try:
            d["fields"] = json.loads(r["fields_json"]) if r["fields_json"] else []
        except Exception:
            d["fields"] = []
        del d["fields_json"]
        return d

@app.patch("/api/request-types/{rt_id}")
def update_request_type(rt_id: str, payload: RequestTypeUpdateModel, request: Request):
    user = current_user(request)
    require_perm(user, "settings.request_types")
    with db() as con:
        existing = con.execute("SELECT * FROM request_types WHERE id=?", (rt_id,)).fetchone()
        if not existing: raise HTTPException(404, "نوع درخواست پیدا نشد")
        updates = []
        params = []
        if payload.name is not None:
            updates.append("name=?")
            params.append(payload.name.strip())
        if payload.icon is not None:
            updates.append("icon=?")
            params.append(payload.icon)
        if payload.fields is not None:
            updates.append("fields_json=?")
            params.append(json.dumps(payload.fields, ensure_ascii=False))
        if payload.active is not None:
            updates.append("active=?")
            params.append(int(payload.active))
        if not updates:
            return {"ok": True, "updated": 0}
        params.append(rt_id)
        con.execute(f"UPDATE request_types SET {', '.join(updates)} WHERE id=?", params)
        audit(con, user["id"], "REQUEST_TYPE_UPDATE", "request_type", rt_id, {"fields": updates})
    return {"ok": True, "updated": len(updates)}

@app.delete("/api/request-types/{rt_id}")
def delete_request_type(rt_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "settings.request_types")
    with db() as con:
        existing = con.execute("SELECT * FROM request_types WHERE id=?", (rt_id,)).fetchone()
        if not existing: raise HTTPException(404, "نوع درخواست پیدا نشد")
        # Check if there are requests using this type
        count = con.execute("SELECT COUNT(*) FROM requests WHERE request_type_id=?", (rt_id,)).fetchone()[0]
        if count > 0:
            # Soft delete: just deactivate
            con.execute("UPDATE request_types SET active=0 WHERE id=?", (rt_id,))
            audit(con, user["id"], "REQUEST_TYPE_DEACTIVATE", "request_type", rt_id, {"usage": count})
            return {"ok": True, "deactivated": True, "usage": count}
        con.execute("DELETE FROM request_types WHERE id=?", (rt_id,))
        audit(con, user["id"], "REQUEST_TYPE_DELETE", "request_type", rt_id, {"code": existing["code"]})
    return {"ok": True, "deactivated": False}


@app.post("/api/attendance/{action}")
def attendance(action:str,request:Request):
    user=current_user(request)
    if action not in ("in","out"): raise HTTPException(404,"عملیات نامعتبر است")
    with db() as con:
        day=datetime.now(ZoneInfo("Asia/Tehran")).strftime("%Y-%m-%d")
        row=con.execute("SELECT * FROM attendance WHERE user_id=? AND work_date=?",(user["id"],day)).fetchone()
        timestamp=now()
        if action=="in":
            if row and row["check_in"]: raise HTTPException(409,"ورود امروز قبلاً ثبت شده است")
            if row: con.execute("UPDATE attendance SET check_in=? WHERE id=?",(timestamp,row["id"]))
            else: con.execute("INSERT INTO attendance VALUES(?,?,?,?,?)",(uid(),user["id"],day,timestamp,None))
        else:
            if not row or not row["check_in"]: raise HTTPException(409,"ابتدا ورود امروز را ثبت کنید")
            if row["check_out"]: raise HTTPException(409,"خروج امروز قبلاً ثبت شده است")
            con.execute("UPDATE attendance SET check_out=? WHERE id=?",(timestamp,row["id"]))
        audit(con,user["id"],f"ATTENDANCE_{action.upper()}","attendance",user["id"],{"date":day})
        return {"ok":True,"at":timestamp}


@app.get("/api/attendance")
def get_attendance(request:Request):
    user=current_user(request)
    with db() as con:
        if user["role"] in ("ADMIN","CEO"):
            rows=con.execute("SELECT a.*,u.name user_name FROM attendance a JOIN users u ON u.id=a.user_id ORDER BY work_date DESC,check_in DESC LIMIT 100").fetchall()
        else: rows=con.execute("SELECT * FROM attendance WHERE user_id=? ORDER BY work_date DESC LIMIT 30",(user["id"],)).fetchall()
        return [dict(r) for r in rows]


@app.get("/api/notifications")
def get_notifications(request:Request):
    user=current_user(request)
    with db() as con: return [dict(r) for r in con.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",(user["id"],))]


@app.post("/api/notifications/{notification_id}/read")
def mark_read(notification_id:str,request:Request):
    user=current_user(request)
    with db() as con: con.execute("UPDATE notifications SET read_at=? WHERE id=? AND user_id=?",(now(),notification_id,user["id"]))
    return {"ok":True}


@app.get("/api/audit")
def get_audit(request:Request):
    user=current_user(request); require_perm(user, "audit.view")
    with db() as con:
        rows=con.execute("SELECT a.*,u.name actor_name FROM audit_events a LEFT JOIN users u ON u.id=a.actor_id ORDER BY created_at DESC LIMIT 200").fetchall()
        return [{**dict(r),"details":json.loads(r["details"])} for r in rows]


@app.get("/api/files/{stored_name}")
def download_file(stored_name:str,request:Request):
    user=current_user(request)
    if not re.fullmatch(r"[a-f0-9]{32}\.xlsx",stored_name): raise HTTPException(404,"فایل پیدا نشد")
    with db() as con:
        sub=con.execute("SELECT s.task_id,s.original_name,t.company_id,t.assignee_id FROM submissions s JOIN tasks t ON t.id=s.task_id WHERE s.stored_name=?",(stored_name,)).fetchone()
        ref=con.execute("SELECT company_id,original_name FROM reference_versions WHERE stored_name=?",(stored_name,)).fetchone()
        if sub:
            if user["role"] not in ("ADMIN","CEO") and sub["assignee_id"]!=user["id"] and not can_access_company(con,user,sub["company_id"]): raise HTTPException(403,"دسترسی ندارید")
            filename=sub["original_name"]
        elif ref:
            if user["role"] not in ("ADMIN","CEO") and not can_access_company(con,user,ref["company_id"]): raise HTTPException(403,"دسترسی ندارید")
            filename=ref["original_name"]
        else: raise HTTPException(404,"فایل پیدا نشد")
        if not (FILES/stored_name).exists(): raise HTTPException(404,"فایل پیدا نشد")
        return FileResponse(FILES/stored_name,filename=filename,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/api/template")
def template(request:Request):
    current_user(request)
    from io import BytesIO
    from openpyxl import Workbook
    wb=Workbook(); ws=wb.active; ws.title="اسناد"
    ws.append(["ردیف","شماره سند","تاریخ سند","کل","معین","تفصیل","شرح سند","بدهکار","بستانکار"])
    ws.freeze_panes="A2"; ws.auto_filter.ref="A1:I1"
    for col,width in zip("ABCDEFGHI",[10,18,16,18,18,18,36,18,18]): ws.column_dimensions[col].width=width
    out=BytesIO(); wb.save(out); out.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(out,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=yfg-template.xlsx"})


# ========================================================================
# PHASE 2: TIME TRACKING API
# ========================================================================

class TimeStartModel(BaseModel):
    task_id: str
    description: str = ""

@app.post("/api/time/start")
def time_start(payload: TimeStartModel, request: Request):
    user = current_user(request)
    with db() as con:
        # Check no active timer
        active = con.execute("SELECT id FROM time_entries WHERE user_id=? AND end_at IS NULL", (user["id"],)).fetchone()
        if active:
            raise HTTPException(409, "تایمر فعالی دارید؛ ابتدا آن را متوقف کنید")
        entry_id = uid()
        con.execute("INSERT INTO time_entries VALUES(?,?,?,?,?,?,?,?,?)",
                     (entry_id, payload.task_id, user["id"], now(), None, 0, payload.description, 1, now()))
        audit(con, user["id"], "TIME_START", "time_entry", entry_id, {"task_id": payload.task_id})
        return {"id": entry_id, "started_at": now()}

@app.post("/api/time/stop")
def time_stop(request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM time_entries WHERE user_id=? AND end_at IS NULL", (user["id"],)).fetchone()
        if not entry:
            raise HTTPException(404, "تایمر فعالی وجود ندارد")
        end = now()
        start_dt = datetime.fromisoformat(entry["start_at"])
        end_dt = datetime.fromisoformat(end)
        duration = int((end_dt - start_dt).total_seconds())
        con.execute("UPDATE time_entries SET end_at=?, duration_seconds=? WHERE id=?", (end, duration, entry["id"]))
        audit(con, user["id"], "TIME_STOP", "time_entry", entry["id"], {"duration": duration})
        return {"id": entry["id"], "duration_seconds": duration}

@app.get("/api/time/active")
def time_active(request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("""SELECT te.*, t.title AS task_title, c.name AS company_name
                               FROM time_entries te LEFT JOIN tasks t ON t.id=te.task_id
                               LEFT JOIN companies c ON c.id=t.company_id
                               WHERE te.user_id=? AND te.end_at IS NULL""", (user["id"],)).fetchone()
        if entry:
            return dict(entry)
        return None

@app.get("/api/time/entries")
def time_entries_list(request: Request, task_id: str | None = None, user_id: str | None = None):
    user = current_user(request)
    with db() as con:
        query = """SELECT te.*, t.title AS task_title, u.name AS user_name, c.name AS company_name
                   FROM time_entries te LEFT JOIN tasks t ON t.id=te.task_id
                   LEFT JOIN users u ON u.id=te.user_id
                   LEFT JOIN companies c ON c.id=t.company_id WHERE 1=1"""
        args = []
        if user["role"] not in ("ADMIN", "CEO"):
            query += " AND te.user_id=?"
            args.append(user["id"])
        if task_id:
            query += " AND te.task_id=?"
            args.append(task_id)
        if user_id and user["role"] in ("ADMIN", "CEO"):
            query += " AND te.user_id=?"
            args.append(user_id)
        query += " ORDER BY te.start_at DESC LIMIT 200"
        rows = con.execute(query, args).fetchall()
        return [dict(r) for r in rows]

@app.get("/api/time/timesheet")
def timesheet(request: Request, start_date: str | None = None, end_date: str | None = None):
    user = current_user(request)
    with db() as con:
        query = """SELECT te.user_id, u.name AS user_name, te.task_id, t.title AS task_title,
                   c.name AS company_name, SUM(te.duration_seconds) AS total_seconds,
                   COUNT(te.id) AS entry_count
                   FROM time_entries te JOIN users u ON u.id=te.user_id
                   LEFT JOIN tasks t ON t.id=te.task_id
                   LEFT JOIN companies c ON c.id=t.company_id
                   WHERE te.end_at IS NOT NULL"""
        args = []
        if user["role"] not in ("ADMIN", "CEO"):
            query += " AND te.user_id=?"
            args.append(user["id"])
        if start_date:
            query += " AND te.start_at>=?"
            args.append(start_date)
        if end_date:
            query += " AND te.start_at<=?"
            args.append(end_date)
        query += " GROUP BY te.user_id, te.task_id ORDER BY u.name, t.title"
        rows = con.execute(query, args).fetchall()
        return [dict(r) for r in rows]


# ========================================================================
# PHASE 3: AUTOMATIONS API
# ========================================================================

class AutomationModel(BaseModel):
    name: str
    trigger_type: str  # TASK_OVERDUE, TASK_SUBMITTED, TASK_RETURNED, TASK_ASSIGNED
    trigger_config: dict = {}
    action_type: str   # NOTIFY_USER, NOTIFY_MANAGER, SET_PRIORITY, ADD_COMMENT
    action_config: dict = {}
    enabled: bool = True

@app.get("/api/automations")
def list_automations(request: Request):
    user = current_user(request)
    require_perm(user, "automations.manage")
    with db() as con:
        rows = con.execute("SELECT * FROM automations ORDER BY created_at DESC").fetchall()
        return [{**dict(r), "trigger_config": json.loads(r["trigger_config"]), "action_config": json.loads(r["action_config"])} for r in rows]

@app.post("/api/automations")
def create_automation(payload: AutomationModel, request: Request):
    user = current_user(request)
    require_perm(user, "automations.manage")
    with db() as con:
        a_id = uid()
        con.execute("INSERT INTO automations VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (a_id, payload.name, payload.trigger_type, json.dumps(payload.trigger_config, ensure_ascii=False),
                      payload.action_type, json.dumps(payload.action_config, ensure_ascii=False),
                      1 if payload.enabled else 0, user["id"], now(), None))
        audit(con, user["id"], "AUTOMATION_CREATE", "automation", a_id, {"name": payload.name})
        return {"id": a_id}

@app.patch("/api/automations/{automation_id}")
def toggle_automation(automation_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "automations.manage")
    with db() as con:
        a = con.execute("SELECT * FROM automations WHERE id=?", (automation_id,)).fetchone()
        if not a:
            raise HTTPException(404, "اتوماسیون پیدا نشد")
        new_val = 0 if a["enabled"] else 1
        con.execute("UPDATE automations SET enabled=? WHERE id=?", (new_val, automation_id))
        audit(con, user["id"], "AUTOMATION_TOGGLE", "automation", automation_id, {"enabled": new_val})
        return {"enabled": new_val}

@app.delete("/api/automations/{automation_id}")
def delete_automation(automation_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "automations.manage")
    with db() as con:
        con.execute("DELETE FROM automations WHERE id=?", (automation_id,))
        audit(con, user["id"], "AUTOMATION_DELETE", "automation", automation_id, {})
        return {"ok": True}

@app.post("/api/automations/run")
def run_automations(request: Request):
    """Run all enabled automations — check overdue tasks, notify, etc."""
    user = current_user(request)
    require_perm(user, "automations.manage")
    results = []
    with db() as con:
        automations = con.execute("SELECT * FROM automations WHERE enabled=1").fetchall()
        for a in automations:
            fired = False
            if a["trigger_type"] == "TASK_OVERDUE":
                overdue = con.execute("""SELECT t.*, u.id AS assignee_id FROM tasks t JOIN users u ON u.id=t.assignee_id
                                         WHERE t.due_date < ? AND t.status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED')""",
                                       (now(),)).fetchall()
                for t in overdue:
                    notify(con, t["assignee_id"], "مهلت تسک گذشته", f"تسک «{t['title']}» از موعد گذشته است")
                    fired = True
            elif a["trigger_type"] == "TASK_ASSIGNED":
                assigned = con.execute("""SELECT t.*, u.id AS assignee_id FROM tasks t JOIN users u ON u.id=t.assignee_id
                                          WHERE t.status='ASSIGNED' AND t.created_at > ?""", (a["last_fired_at"] or "2000-01-01")).fetchall()
                for t in assigned:
                    notify(con, t["assignee_id"], "تسک جدید", f"تسک «{t['title']}» به شما ارجاع شد")
                    fired = True
            if fired:
                con.execute("UPDATE automations SET last_fired_at=? WHERE id=?", (now(), a["id"]))
                results.append({"automation": a["name"], "fired": True})
        audit(con, user["id"], "AUTOMATION_RUN", "automation", None, {"results": len(results)})
    return {"results": results}


# ========================================================================
# PHASE 4: CHAT API — full in-app messenger
#   • Direct messages (DM) — auto channel between two users
#   • Group channels — admin or any user can create with member_ids
#   • File attachments (chat_attachments table)
#   • Read receipts (last_read_at)
#   • Polling-friendly list (no WebSocket needed for MVP)
# ========================================================================

class ChatMessageModel(BaseModel):
    body: str = ""
    attachment_id: str | None = None
    reply_to: str | None = None

class ChatChannelModel(BaseModel):
    name: str = ""
    member_ids: list[str] = []

class ChatAddMembersModel(BaseModel):
    member_ids: list[str] = []

class ChatRenameModel(BaseModel):
    name: str

def _channel_display_name(channel: sqlite3.Row, viewer_id: str, con) -> str:
    """For DIRECT channels, show the other user's name. For GROUP, show channel name."""
    if channel["kind"] == "DIRECT":
        others = con.execute(
            "SELECT u.name FROM chat_channel_members m JOIN users u ON u.id=m.user_id "
            "WHERE m.channel_id=? AND m.user_id!=?",
            (channel["id"], viewer_id)
        ).fetchall()
        names = [o["name"] for o in others]
        return "، ".join(names) if names else (channel["name"] or "گفتگو مستقیم")
    return channel["name"] or "گروه بدون نام"

@app.get("/api/chat/channels")
def list_channels(request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    with db() as con:
        rows = con.execute("""
            SELECT cc.id, cc.name, cc.kind, cc.created_by, cc.created_at,
                   (SELECT COUNT(*) FROM chat_messages WHERE channel_id=cc.id) AS message_count,
                   (SELECT COUNT(*) FROM chat_messages WHERE channel_id=cc.id
                       AND created_at > COALESCE(
                           (SELECT last_read_at FROM chat_channel_members WHERE channel_id=cc.id AND user_id=?), ''
                       )) AS unread_count
            FROM chat_channels cc
            JOIN chat_channel_members m ON m.channel_id=cc.id AND m.user_id=?
            ORDER BY (SELECT MAX(created_at) FROM chat_messages WHERE channel_id=cc.id) DESC,
                     cc.created_at DESC
        """, (user["id"], user["id"])).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["display_name"] = _channel_display_name(r, user["id"], con)
            result.append(d)
        return result

@app.get("/api/chat/channels/{channel_id}")
def get_channel(channel_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    with db() as con:
        ch = con.execute("SELECT * FROM chat_channels WHERE id=?", (channel_id,)).fetchone()
        if not ch: raise HTTPException(404, "گفتگو پیدا نشد")
        is_member = con.execute(
            "SELECT 1 FROM chat_channel_members WHERE channel_id=? AND user_id=?",
            (channel_id, user["id"])
        ).fetchone()
        if not is_member and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "شما عضو این گفتگو نیستید")
        members = con.execute(
            "SELECT u.id, u.name, u.first_name, u.last_name, u.role, m.joined_at, m.last_read_at "
            "FROM chat_channel_members m JOIN users u ON u.id=m.user_id WHERE m.channel_id=? "
            "ORDER BY m.joined_at",
            (channel_id,)
        ).fetchall()
        d = dict(ch)
        d["display_name"] = _channel_display_name(ch, user["id"], con)
        d["members"] = [dict(m) for m in members]
        return d

@app.post("/api/chat/channels")
def create_channel(payload: ChatChannelModel, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    if not payload.member_ids:
        raise HTTPException(400, "حداقل یک کاربر را انتخاب کنید")
    with db() as con:
        for mid in payload.member_ids:
            exists = con.execute("SELECT 1 FROM users WHERE id=? AND active=1", (mid,)).fetchone()
            if not exists: raise HTTPException(400, f"کاربر انتخاب‌شده وجود ندارد: {mid}")
        if len(payload.member_ids) == 1:
            other = payload.member_ids[0]
            if other == user["id"]:
                raise HTTPException(400, "نمی‌توانید به خودتان گفتگو مستقیم بسازید")
            existing = con.execute("""
                SELECT c.* FROM chat_channels c
                WHERE c.kind='DIRECT'
                AND c.id IN (SELECT channel_id FROM chat_channel_members WHERE user_id=?)
                AND c.id IN (SELECT channel_id FROM chat_channel_members WHERE user_id=?)
                AND (SELECT COUNT(*) FROM chat_channel_members WHERE channel_id=c.id) = 2
            """, (user["id"], other)).fetchone()
            if existing:
                return {"id": existing["id"], "kind": "DIRECT", "name": "", "created": False}
            ch_id = uid()
            con.execute("INSERT INTO chat_channels VALUES(?,?,?,?,?)",
                        (ch_id, "", "DIRECT", user["id"], now()))
            con.execute("INSERT INTO chat_channel_members (channel_id, user_id, joined_at) VALUES(?,?,?)", (ch_id, user["id"], now()))
            con.execute("INSERT INTO chat_channel_members (channel_id, user_id, joined_at) VALUES(?,?,?)", (ch_id, other, now()))
            audit(con, user["id"], "CHAT_DM_CREATE", "chat_channel", ch_id, {"with": other})
            return {"id": ch_id, "kind": "DIRECT", "name": "", "created": True}
        name = (payload.name or "").strip() or "گروه جدید"
        ch_id = uid()
        con.execute("INSERT INTO chat_channels VALUES(?,?,?,?,?)",
                    (ch_id, name, "GROUP", user["id"], now()))
        members = set(payload.member_ids + [user["id"]])
        for mid in members:
            con.execute("INSERT OR IGNORE INTO chat_channel_members (channel_id, user_id, joined_at) VALUES(?,?,?)", (ch_id, mid, now()))
        audit(con, user["id"], "CHAT_GROUP_CREATE", "chat_channel", ch_id, {"name": name, "members": list(members)})
        return {"id": ch_id, "kind": "GROUP", "name": name, "created": True}

@app.patch("/api/chat/channels/{channel_id}")
def rename_channel(channel_id: str, payload: ChatRenameModel, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    name = (payload.name or "").strip()
    if not name: raise HTTPException(400, "نام گروه نمی‌تواند خالی باشد")
    with db() as con:
        ch = con.execute("SELECT * FROM chat_channels WHERE id=?", (channel_id,)).fetchone()
        if not ch: raise HTTPException(404, "گفتگو پیدا نشد")
        if ch["kind"] != "GROUP":
            raise HTTPException(400, "فقط گروه‌ها قابل تغییر نام هستند")
        if user["role"] not in ("ADMIN", "CEO") and ch["created_by"] != user["id"]:
            raise HTTPException(403, "فقط سازنده گروه یا مدیر می‌تواند نام را تغییر دهد")
        con.execute("UPDATE chat_channels SET name=? WHERE id=?", (name, channel_id))
        audit(con, user["id"], "CHAT_RENAME", "chat_channel", channel_id, {"name": name})
        return {"id": channel_id, "name": name}

@app.post("/api/chat/channels/{channel_id}/members")
def add_members(channel_id: str, payload: ChatAddMembersModel, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    with db() as con:
        ch = con.execute("SELECT * FROM chat_channels WHERE id=?", (channel_id,)).fetchone()
        if not ch: raise HTTPException(404, "گفتگو پیدا نشد")
        if ch["kind"] != "GROUP":
            raise HTTPException(400, "فقط در گروه‌ها می‌توان عضو اضافه کرد")
        if user["role"] not in ("ADMIN", "CEO") and ch["created_by"] != user["id"]:
            raise HTTPException(403, "فقط سازنده گروه یا مدیر می‌تواند عضو اضافه کند")
        added = 0
        for mid in payload.member_ids:
            exists = con.execute("SELECT 1 FROM users WHERE id=? AND active=1", (mid,)).fetchone()
            if not exists: continue
            cur = con.execute("INSERT OR IGNORE INTO chat_channel_members (channel_id, user_id, joined_at) VALUES(?,?,?)",
                              (channel_id, mid, now()))
            added += cur.rowcount
            notify(con, mid, "گروه جدید", f"شما به گروه «{ch['name']}» اضافه شدید")
        audit(con, user["id"], "CHAT_ADD_MEMBERS", "chat_channel", channel_id, {"added": added})
        return {"added": added}

@app.get("/api/chat/channels/{channel_id}/messages")
def list_messages(channel_id: str, request: Request, monitor: int = 0):
    """Return messages for a channel. If monitor=1 and user has chat.monitor permission,
    no read/delivered events are recorded (silent admin oversight)."""
    user = current_user(request)
    require_perm(user, "chat.use")
    is_monitor = monitor == 1 and has_perm(user, "chat.monitor")
    with db() as con:
        if not is_monitor:
            is_member = con.execute(
                "SELECT 1 FROM chat_channel_members WHERE channel_id=? AND user_id=?",
                (channel_id, user["id"])
            ).fetchone()
            if not is_member and user["role"] not in ("ADMIN", "CEO"):
                raise HTTPException(403, "شما عضو این گفتگو نیستید")
            # Mark messages NOT sent by me as delivered (single tick → double tick)
            ts = now()
            con.execute("""UPDATE chat_messages SET delivered_at=?
                            WHERE channel_id=? AND user_id!=? AND delivered_at=''""",
                         (ts, channel_id, user["id"]))
            con.commit()
        else:
            # Monitoring silently: do not record delivered_at
            pass
        rows = con.execute("""
            SELECT cm.id, cm.channel_id, cm.user_id, cm.body, cm.attachment_id, cm.reply_to,
                   cm.delivered_at, cm.read_at, cm.created_at,
                   u.name AS user_name, u.first_name, u.last_name, u.role AS user_role,
                   ca.original_name AS attachment_name, ca.size_bytes AS attachment_size, ca.mime_type AS attachment_mime
            FROM chat_messages cm
            JOIN users u ON u.id=cm.user_id
            LEFT JOIN chat_attachments ca ON ca.id=cm.attachment_id
            WHERE cm.channel_id=?
            ORDER BY cm.created_at ASC LIMIT 500
        """, (channel_id,)).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/chat/channels/{channel_id}/messages")
def send_message(channel_id: str, payload: ChatMessageModel, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    if not payload.body.strip() and not payload.attachment_id:
        raise HTTPException(400, "پیام نمی‌تواند خالی باشد")
    with db() as con:
        ch = con.execute("SELECT * FROM chat_channels WHERE id=?", (channel_id,)).fetchone()
        if not ch: raise HTTPException(404, "گفتگو پیدا نشد")
        is_member = con.execute(
            "SELECT 1 FROM chat_channel_members WHERE channel_id=? AND user_id=?",
            (channel_id, user["id"])
        ).fetchone()
        if not is_member and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "شما عضو این گفتگو نیستید")
        if payload.attachment_id:
            att = con.execute("SELECT * FROM chat_attachments WHERE id=?", (payload.attachment_id,)).fetchone()
            if not att or att["uploaded_by"] != user["id"]:
                raise HTTPException(400, "پیوست نامعتبر")
        msg_id = uid()
        con.execute(
            "INSERT INTO chat_messages (id, channel_id, user_id, body, attachment_id, reply_to, delivered_at, read_at, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (msg_id, channel_id, user["id"], payload.body.strip(), payload.attachment_id, payload.reply_to, "", "", now())
        )
        members = con.execute(
            "SELECT user_id FROM chat_channel_members WHERE channel_id=? AND user_id!=?",
            (channel_id, user["id"])
        ).fetchall()
        ch_name = _channel_display_name(ch, user["id"], con) if ch["kind"] == "GROUP" else "گفتگو مستقیم"
        preview = (payload.body[:50] + "…") if len(payload.body) > 50 else payload.body
        if not preview and payload.attachment_id:
            preview = "[فایل پیوست]"
        for m in members:
            notify(con, m["user_id"], f"پیام جدید در {ch_name}", f"{user['name']}: {preview}")
        audit(con, user["id"], "CHAT_MESSAGE", "chat_message", msg_id, {"channel_id": channel_id})
        return {"id": msg_id, "created_at": now()}

@app.post("/api/chat/channels/{channel_id}/read")
def mark_channel_read(channel_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    with db() as con:
        is_member = con.execute(
            "SELECT 1 FROM chat_channel_members WHERE channel_id=? AND user_id=?",
            (channel_id, user["id"])
        ).fetchone()
        if not is_member: raise HTTPException(403, "عضو نیستید")
        ts = now()
        # Update last_read_at (used for unread badges)
        con.execute("UPDATE chat_channel_members SET last_read_at=? WHERE channel_id=? AND user_id=?",
                    (ts, channel_id, user["id"]))
        # Mark all messages NOT sent by me as read (delivered_at → read_at, double tick → blue)
        con.execute("""UPDATE chat_messages SET delivered_at=COALESCE(NULLIF(delivered_at,''), ?), read_at=?
                       WHERE channel_id=? AND user_id!=? AND (read_at='' OR read_at IS NULL)""",
                    (ts, ts, channel_id, user["id"]))
        con.commit()
        return {"ok": True, "read_at": ts}

@app.post("/api/chat/upload")
async def chat_upload(request: Request, file: UploadFile = File(...)):
    """Upload a file for chat attachment. Returns attachment_id to use in send_message."""
    user = current_user(request)
    require_perm(user, "chat.use")
    content = await file.read(CHAT_ATTACHMENT_MAX + 1)
    if len(content) > CHAT_ATTACHMENT_MAX:
        raise HTTPException(413, "حجم فایل بیش از حد مجاز (۲۵ مگابایت)")
    if not file.filename:
        raise HTTPException(400, "نام فایل نامعتبر")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in CHAT_ATTACHMENT_ALLOWED:
        raise HTTPException(400, f"نوع فایل پشتیبانی نمی‌شود: {suffix}. مجاز: تصویر، PDF، اکسل، ورد، فشرده")
    att_id = uid()
    stored_name = f"{att_id}{suffix}"
    (ATTACHMENTS_DIR / stored_name).write_bytes(content)
    import hashlib
    sha = hashlib.sha256(content).hexdigest()
    with db() as con:
        con.execute(
            "INSERT INTO chat_attachments VALUES(?,?,?,?,?,?,?,?)",
            (att_id, file.filename, stored_name, file.content_type or "application/octet-stream",
             len(content), sha, user["id"], now())
        )
        audit(con, user["id"], "CHAT_UPLOAD", "chat_attachment", att_id,
              {"name": file.filename, "size": len(content)})
    return {"attachment_id": att_id, "original_name": file.filename, "size": len(content)}

@app.get("/api/chat/attachments/{att_id}")
def download_attachment(att_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "chat.use")
    with db() as con:
        att = con.execute("SELECT * FROM chat_attachments WHERE id=?", (att_id,)).fetchone()
        if not att: raise HTTPException(404, "پیوست پیدا نشد")
        msg = con.execute(
            "SELECT channel_id FROM chat_messages WHERE attachment_id=?", (att_id,)
        ).fetchone()
        if msg:
            is_member = con.execute(
                "SELECT 1 FROM chat_channel_members WHERE channel_id=? AND user_id=?",
                (msg["channel_id"], user["id"])
            ).fetchone()
            if not is_member and user["role"] not in ("ADMIN", "CEO"):
                raise HTTPException(403, "دسترسی غیرمجاز")
        path = ATTACHMENTS_DIR / att["stored_name"]
        if not path.exists(): raise HTTPException(404, "فایل روی دیسک پیدا نشد")
        from fastapi.responses import FileResponse
        return FileResponse(str(path), filename=att["original_name"], media_type=att["mime_type"])

@app.get("/api/chat/users")
def list_chat_users(request: Request):
    """List active users (other than me) for the new chat picker."""
    user = current_user(request)
    require_perm(user, "chat.use")
    with db() as con:
        rows = con.execute(
            "SELECT id, name, first_name, last_name, role, active FROM users "
            "WHERE active=1 AND id!=? ORDER BY name",
            (user["id"],)
        ).fetchall()
        return [dict(r) for r in rows]

@app.get("/api/chat/admin/all-channels")
def admin_all_channels(request: Request):
    """List ALL channels (for silent admin monitoring).
    Requires chat.monitor permission. Returns display name, member list, last message preview,
    and per-message counts. No read/delivered events are recorded when admin views messages via
    the monitor endpoint."""
    user = current_user(request)
    require_perm(user, "chat.monitor")
    with db() as con:
        rows = con.execute("""
            SELECT c.id, c.name, c.kind, c.created_by, c.created_at,
                   (SELECT COUNT(*) FROM chat_messages WHERE channel_id=c.id) AS message_count,
                   (SELECT created_at FROM chat_messages WHERE channel_id=c.id
                       ORDER BY created_at DESC LIMIT 1) AS last_message_at,
                   (SELECT COUNT(*) FROM chat_channel_members WHERE channel_id=c.id) AS member_count
            FROM chat_channels c
            ORDER BY last_message_at DESC NULLS LAST, c.created_at DESC
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            # Get member names
            members = con.execute(
                "SELECT u.id, u.name, u.role FROM chat_channel_members m JOIN users u ON u.id=m.user_id WHERE m.channel_id=?",
                (r["id"],)
            ).fetchall()
            d["members"] = [dict(m) for m in members]
            if r["kind"] == "DIRECT":
                d["display_name"] = "، ".join(m["name"] for m in d["members"])
            else:
                d["display_name"] = r["name"] or "گروه بدون نام"
            result.append(d)
        return result


# ========================================================================
# PHASE 4b: CUSTOMERS API — persons (active) + placeholder stubs
# ========================================================================

class PersonCreateModel(BaseModel):
    code: str
    first_name: str
    last_name: str
    national_id: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    postal_code: str = ""
    notes: str = ""
    linked_company_id: str | None = None
    active: int = 1

class PersonUpdateModel(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    national_id: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    postal_code: str | None = None
    notes: str | None = None
    linked_company_id: str | None = None
    active: int | None = None

# ===== Contracts / Proformas / Invoices models =====
class ContractCreateModel(BaseModel):
    code: str
    title: str
    company_id: str
    person_id: str | None = None
    start_date: str  # ISO YYYY-MM-DD
    end_date: str
    value_amount: float = 0
    currency: str = "IRR"
    status: str = "DRAFT"
    contract_type: str = "general"
    subject: str = ""
    notes: str = ""

class ContractUpdateModel(BaseModel):
    title: str | None = None
    company_id: str | None = None
    person_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    value_amount: float | None = None
    currency: str | None = None
    status: str | None = None
    contract_type: str | None = None
    subject: str | None = None
    notes: str | None = None

class ProformaItemModel(BaseModel):
    description: str
    qty: float = 1
    unit_price: float = 0
    total: float | None = None
    notes: str = ""

class ProformaCreateModel(BaseModel):
    code: str
    title: str
    company_id: str
    person_id: str | None = None
    contract_id: str | None = None
    issue_date: str
    valid_until: str | None = None
    status: str = "DRAFT"
    total_amount: float = 0
    currency: str = "IRR"
    items: list[dict] = []  # use list[dict] for flexibility (Pydantic v2)
    notes: str = ""

class ProformaUpdateModel(BaseModel):
    title: str | None = None
    company_id: str | None = None
    person_id: str | None = None
    contract_id: str | None = None
    issue_date: str | None = None
    valid_until: str | None = None
    status: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    items: list[dict] | None = None
    notes: str | None = None

class InvoiceCreateModel(BaseModel):
    code: str
    title: str
    company_id: str
    person_id: str | None = None
    proforma_id: str | None = None
    contract_id: str | None = None
    issue_date: str
    due_date: str | None = None
    status: str = "DRAFT"
    total_amount: float = 0
    paid_amount: float = 0
    currency: str = "IRR"
    items: list[dict] = []
    notes: str = ""

class InvoiceUpdateModel(BaseModel):
    title: str | None = None
    company_id: str | None = None
    person_id: str | None = None
    proforma_id: str | None = None
    contract_id: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    status: str | None = None
    total_amount: float | None = None
    paid_amount: float | None = None
    currency: str | None = None
    items: list[dict] | None = None
    notes: str | None = None

class CompanyContactCreateModel(BaseModel):
    contact_type: str = "PHONE"
    label: str = ""
    value: str
    notes: str = ""

@app.get("/api/persons")
def list_persons(request: Request, q: str = ""):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        sql = """SELECT p.*, c.name AS linked_company_name
                 FROM persons p LEFT JOIN companies c ON c.id=p.linked_company_id
                 WHERE 1=1"""
        params: list = []
        if q:
            sql += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR p.code LIKE ? OR p.national_id LIKE ? OR p.phone LIKE ?)"
            kw = f"%{q}%"
            params = [kw, kw, kw, kw, kw]
        sql += " ORDER BY p.created_at DESC LIMIT 500"
        rows = con.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/persons")
def create_person(payload: PersonCreateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.manage")
    if not payload.code.strip() or not payload.first_name.strip() or not payload.last_name.strip():
        raise HTTPException(400, "کد، نام و نام خانوادگی الزامی است")
    if payload.linked_company_id:
        with db() as con:
            if not con.execute("SELECT 1 FROM companies WHERE id=?", (payload.linked_company_id,)).fetchone():
                raise HTTPException(400, "شرکت انتخاب‌شده وجود ندارد")
    pid = uid()
    with db() as con:
        try:
            con.execute("""INSERT INTO persons
                (id, code, first_name, last_name, national_id, phone, email, address, postal_code, notes,
                 linked_company_id, active, created_by, created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, payload.code.strip(), payload.first_name.strip(), payload.last_name.strip(),
                 payload.national_id, payload.phone, payload.email, payload.address, payload.postal_code,
                 payload.notes, payload.linked_company_id, payload.active, user["id"], now()))
        except Exception as e:
            if "UNIQUE" in str(e): raise HTTPException(400, "کد شخص تکراری است")
            raise
        audit(con, user["id"], "PERSON_CREATE", "person", pid, {"code": payload.code, "name": f"{payload.first_name} {payload.last_name}"})
    return {"id": pid, "code": payload.code}

@app.get("/api/persons/{person_id}")
def get_person(person_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        row = con.execute(
            "SELECT p.*, c.name AS linked_company_name FROM persons p "
            "LEFT JOIN companies c ON c.id=p.linked_company_id WHERE p.id=?",
            (person_id,)
        ).fetchone()
        if not row: raise HTTPException(404, "شخص پیدا نشد")
        return dict(row)

@app.patch("/api/persons/{person_id}")
def update_person(person_id: str, payload: PersonUpdateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.manage")
    with db() as con:
        existing = con.execute("SELECT * FROM persons WHERE id=?", (person_id,)).fetchone()
        if not existing: raise HTTPException(404, "شخص پیدا نشد")
        if payload.linked_company_id == "":
            payload.linked_company_id = None
        if payload.linked_company_id:
            if not con.execute("SELECT 1 FROM companies WHERE id=?", (payload.linked_company_id,)).fetchone():
                raise HTTPException(400, "شرکت انتخاب‌شده وجود ندارد")
        updates = []
        params: list = []
        for k, v in payload.model_dump(exclude_unset=True).items():
            if v is None: continue
            updates.append(f"{k}=?")
            params.append(v)
        if not updates:
            return {"ok": True, "updated": 0}
        params.append(person_id)
        con.execute(f"UPDATE persons SET {', '.join(updates)} WHERE id=?", params)
        audit(con, user["id"], "PERSON_UPDATE", "person", person_id, {"fields": updates})
    return {"ok": True, "updated": len(updates)}

@app.delete("/api/persons/{person_id}")
def delete_person(person_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.manage")
    with db() as con:
        existing = con.execute("SELECT * FROM persons WHERE id=?", (person_id,)).fetchone()
        if not existing: raise HTTPException(404, "شخص پیدا نشد")
        con.execute("DELETE FROM persons WHERE id=?", (person_id,))
        audit(con, user["id"], "PERSON_DELETE", "person", person_id, {"code": existing["code"]})
    return {"ok": True}


# ========================================================================
# CONTRACTS API (قراردادها) — full first version
# ========================================================================
def _contract_dict(row, con) -> dict:
    d = dict(row)
    if d.get("company_id"):
        company = con.execute("SELECT name FROM companies WHERE id=?", (d["company_id"],)).fetchone()
        d["company_name"] = company["name"] if company else None
    if d.get("person_id"):
        person = con.execute("SELECT first_name, last_name FROM persons WHERE id=?", (d["person_id"],)).fetchone()
        if person:
            d["person_name"] = f"{person['first_name']} {person['last_name']}".strip()
    # Compute is_active based on current date being within contract range
    today = now()[:10]
    d["is_currently_active"] = (d["status"] == "ACTIVE" and d["start_date"] <= today <= d["end_date"])
    return d

@app.get("/api/contracts")
def list_contracts(request: Request, status: str = "", active: int = 0, company_id: str = ""):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        sql = """SELECT c.* FROM contracts c WHERE 1=1"""
        params: list = []
        if status:
            sql += " AND c.status=?"
            params.append(status)
        if active == 1:
            today = now()[:10]
            sql += " AND c.status='ACTIVE' AND c.start_date<=? AND c.end_date>=?"
            params.extend([today, today])
        if company_id:
            sql += " AND c.company_id=?"
            params.append(company_id)
        sql += " ORDER BY c.start_date DESC, c.created_at DESC"
        rows = con.execute(sql, params).fetchall()
        return [_contract_dict(r, con) for r in rows]

@app.get("/api/contracts/active")
def list_active_contracts(request: Request):
    """Returns only contracts where today's date is within the contract's date range."""
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        today = now()[:10]
        rows = con.execute("""SELECT * FROM contracts
                              WHERE status='ACTIVE' AND start_date<=? AND end_date>=?
                              ORDER BY end_date ASC""", (today, today)).fetchall()
        return [_contract_dict(r, con) for r in rows]

@app.get("/api/contracts/{contract_id}")
def get_contract(contract_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        r = con.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone()
        if not r: raise HTTPException(404, "قرارداد پیدا نشد")
        return _contract_dict(r, con)

@app.post("/api/contracts")
def create_contract(payload: ContractCreateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.contracts")
    if not payload.code.strip() or not payload.title.strip() or not payload.company_id:
        raise HTTPException(400, "کد، عنوان و شرکت الزامی است")
    if payload.end_date < payload.start_date:
        raise HTTPException(400, "تاریخ پایان نباید قبل از شروع باشد")
    if payload.status not in ("DRAFT","ACTIVE","COMPLETED","TERMINATED"):
        raise HTTPException(400, "وضعیت نامعتبر")
    cid = uid()
    ts = now()
    with db() as con:
        try:
            con.execute("""INSERT INTO contracts
                (id, code, title, company_id, person_id, start_date, end_date, value_amount, currency, status, contract_type, subject, notes, attachment_id, created_by, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, payload.code.strip(), payload.title.strip(), payload.company_id, payload.person_id,
                 payload.start_date, payload.end_date, float(payload.value_amount), payload.currency,
                 payload.status, payload.contract_type, payload.subject, payload.notes, None, user["id"], ts, ts))
        except Exception as e:
            if "UNIQUE" in str(e): raise HTTPException(400, "کد قرارداد تکراری است")
            raise
        audit(con, user["id"], "CONTRACT_CREATE", "contract", cid, {"code": payload.code, "title": payload.title})
    return {"id": cid, "code": payload.code}

@app.patch("/api/contracts/{contract_id}")
def update_contract(contract_id: str, payload: ContractUpdateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.contracts")
    with db() as con:
        existing = con.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone()
        if not existing: raise HTTPException(404, "قرارداد پیدا نشد")
        if payload.end_date and payload.start_date and payload.end_date < payload.start_date:
            raise HTTPException(400, "تاریخ پایان نباید قبل از شروع باشد")
        updates = []
        params = []
        for k, v in payload.model_dump(exclude_unset=True).items():
            if v is None: continue
            updates.append(f"{k}=?")
            params.append(v)
        if not updates:
            return {"ok": True, "updated": 0}
        updates.append("updated_at=?")
        params.append(now())
        params.append(contract_id)
        con.execute(f"UPDATE contracts SET {', '.join(updates)} WHERE id=?", params)
        audit(con, user["id"], "CONTRACT_UPDATE", "contract", contract_id, {"fields": updates})
    return {"ok": True, "updated": len(updates) - 1}

@app.delete("/api/contracts/{contract_id}")
def delete_contract(contract_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.contracts")
    with db() as con:
        existing = con.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone()
        if not existing: raise HTTPException(404, "قرارداد پیدا نشد")
        # Check if invoices/proformas reference this contract
        cnt = con.execute("SELECT COUNT(*) FROM invoices WHERE contract_id=?", (contract_id,)).fetchone()[0]
        cnt += con.execute("SELECT COUNT(*) FROM proformas WHERE contract_id=?", (contract_id,)).fetchone()[0]
        if cnt > 0:
            # Soft delete: change status to TERMINATED
            con.execute("UPDATE contracts SET status='TERMINATED', updated_at=? WHERE id=?", (now(), contract_id))
            audit(con, user["id"], "CONTRACT_TERMINATE", "contract", contract_id, {"usage": cnt})
            return {"ok": True, "terminated": True}
        con.execute("DELETE FROM contracts WHERE id=?", (contract_id,))
        audit(con, user["id"], "CONTRACT_DELETE", "contract", contract_id, {"code": existing["code"]})
    return {"ok": True, "terminated": False}


# ========================================================================
# PROFORMAS API (پیش فاکتور)
# ========================================================================
def _proforma_dict(row, con) -> dict:
    d = dict(row)
    try:
        d["items"] = json.loads(row["items_json"]) if row["items_json"] else []
    except Exception:
        d["items"] = []
    del d["items_json"]
    if d.get("company_id"):
        company = con.execute("SELECT name FROM companies WHERE id=?", (d["company_id"],)).fetchone()
        d["company_name"] = company["name"] if company else None
    if d.get("person_id"):
        person = con.execute("SELECT first_name, last_name FROM persons WHERE id=?", (d["person_id"],)).fetchone()
        if person:
            d["person_name"] = f"{person['first_name']} {person['last_name']}".strip()
    if d.get("contract_id"):
        contract = con.execute("SELECT code, title FROM contracts WHERE id=?", (d["contract_id"],)).fetchone()
        if contract:
            d["contract_code"] = contract["code"]
            d["contract_title"] = contract["title"]
    return d

@app.get("/api/proformas")
def list_proformas(request: Request, status: str = "", in_progress: int = 0, company_id: str = ""):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        sql = """SELECT * FROM proformas WHERE 1=1"""
        params: list = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if in_progress == 1:
            sql += " AND status IN ('DRAFT','IN_PROGRESS','SENT')"
        if company_id:
            sql += " AND company_id=?"
            params.append(company_id)
        sql += " ORDER BY issue_date DESC, created_at DESC"
        rows = con.execute(sql, params).fetchall()
        return [_proforma_dict(r, con) for r in rows]

@app.get("/api/proformas/in-progress")
def list_in_progress_proformas(request: Request):
    """Returns proformas that are still in progress (DRAFT, IN_PROGRESS, SENT)."""
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        rows = con.execute("""SELECT * FROM proformas
                              WHERE status IN ('DRAFT','IN_PROGRESS','SENT')
                              ORDER BY issue_date DESC, created_at DESC""").fetchall()
        return [_proforma_dict(r, con) for r in rows]

@app.get("/api/proformas/{proforma_id}")
def get_proforma(proforma_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        r = con.execute("SELECT * FROM proformas WHERE id=?", (proforma_id,)).fetchone()
        if not r: raise HTTPException(404, "پیش فاکتور پیدا نشد")
        return _proforma_dict(r, con)

@app.post("/api/proformas")
def create_proforma(payload: ProformaCreateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.proformas")
    if not payload.code.strip() or not payload.title.strip() or not payload.company_id:
        raise HTTPException(400, "کد، عنوان و شرکت الزامی است")
    if payload.status not in ("DRAFT","IN_PROGRESS","SENT","ACCEPTED","REJECTED","EXPIRED"):
        raise HTTPException(400, "وضعیت نامعتبر")
    pid = uid()
    ts = now()
    items_json = json.dumps(payload.items, ensure_ascii=False) if payload.items else "[]"
    # Auto-calculate total_amount if items are provided and total is 0
    total = float(payload.total_amount)
    if not total and payload.items:
        total = sum((float(i.get("qty",1)) * float(i.get("unit_price",0))) for i in payload.items if isinstance(i, dict))
    with db() as con:
        try:
            con.execute("""INSERT INTO proformas
                (id, code, title, company_id, person_id, contract_id, issue_date, valid_until, status, total_amount, currency, items_json, notes, created_by, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, payload.code.strip(), payload.title.strip(), payload.company_id, payload.person_id,
                 payload.contract_id, payload.issue_date, payload.valid_until, payload.status, total,
                 payload.currency, items_json, payload.notes, user["id"], ts, ts))
        except Exception as e:
            if "UNIQUE" in str(e): raise HTTPException(400, "کد پیش فاکتور تکراری است")
            raise
        audit(con, user["id"], "PROFORMA_CREATE", "proforma", pid, {"code": payload.code, "title": payload.title})
    return {"id": pid, "code": payload.code}

@app.patch("/api/proformas/{proforma_id}")
def update_proforma(proforma_id: str, payload: ProformaUpdateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.proformas")
    with db() as con:
        existing = con.execute("SELECT * FROM proformas WHERE id=?", (proforma_id,)).fetchone()
        if not existing: raise HTTPException(404, "پیش فاکتور پیدا نشد")
        updates = []
        params = []
        for k, v in payload.model_dump(exclude_unset=True).items():
            if v is None: continue
            if k == "items":
                updates.append("items_json=?")
                params.append(json.dumps(v, ensure_ascii=False))
                # Auto-recalculate total if not provided in same payload
                if payload.total_amount is None:
                    new_total = sum((float(i.get("qty",1)) * float(i.get("unit_price",0))) for i in v if isinstance(i, dict))
                    updates.append("total_amount=?")
                    params.append(new_total)
            else:
                updates.append(f"{k}=?")
                params.append(v)
        if not updates:
            return {"ok": True, "updated": 0}
        updates.append("updated_at=?")
        params.append(now())
        params.append(proforma_id)
        con.execute(f"UPDATE proformas SET {', '.join(updates)} WHERE id=?", params)
        audit(con, user["id"], "PROFORMA_UPDATE", "proforma", proforma_id, {"fields": updates})
    return {"ok": True, "updated": len(updates) - 1}

@app.delete("/api/proformas/{proforma_id}")
def delete_proforma(proforma_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.proformas")
    with db() as con:
        existing = con.execute("SELECT * FROM proformas WHERE id=?", (proforma_id,)).fetchone()
        if not existing: raise HTTPException(404, "پیش فاکتور پیدا نشد")
        # Check if invoices reference this proforma
        cnt = con.execute("SELECT COUNT(*) FROM invoices WHERE proforma_id=?", (proforma_id,)).fetchone()[0]
        if cnt > 0:
            con.execute("UPDATE proformas SET status='REJECTED', updated_at=? WHERE id=?", (now(), proforma_id))
            audit(con, user["id"], "PROFORMA_REJECT", "proforma", proforma_id, {"usage": cnt})
            return {"ok": True, "rejected": True}
        con.execute("DELETE FROM proformas WHERE id=?", (proforma_id,))
        audit(con, user["id"], "PROFORMA_DELETE", "proforma", proforma_id, {"code": existing["code"]})
    return {"ok": True, "rejected": False}


# ========================================================================
# INVOICES API (فاکتورها)
# ========================================================================
def _invoice_dict(row, con) -> dict:
    d = dict(row)
    try:
        d["items"] = json.loads(row["items_json"]) if row["items_json"] else []
    except Exception:
        d["items"] = []
    del d["items_json"]
    if d.get("company_id"):
        company = con.execute("SELECT name FROM companies WHERE id=?", (d["company_id"],)).fetchone()
        d["company_name"] = company["name"] if company else None
    if d.get("person_id"):
        person = con.execute("SELECT first_name, last_name FROM persons WHERE id=?", (d["person_id"],)).fetchone()
        if person:
            d["person_name"] = f"{person['first_name']} {person['last_name']}".strip()
    if d.get("proforma_id"):
        proforma = con.execute("SELECT code, title FROM proformas WHERE id=?", (d["proforma_id"],)).fetchone()
        if proforma:
            d["proforma_code"] = proforma["code"]
    if d.get("contract_id"):
        contract = con.execute("SELECT code, title FROM contracts WHERE id=?", (d["contract_id"],)).fetchone()
        if contract:
            d["contract_code"] = contract["code"]
    # Compute balance
    d["balance"] = float(d["total_amount"]) - float(d["paid_amount"])
    return d

@app.get("/api/invoices")
def list_invoices(request: Request, status: str = "", unpaid: int = 0, company_id: str = ""):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        sql = """SELECT * FROM invoices WHERE 1=1"""
        params: list = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if unpaid == 1:
            sql += " AND status IN ('UNPAID','PARTIAL','OVERDUE')"
        if company_id:
            sql += " AND company_id=?"
            params.append(company_id)
        sql += " ORDER BY issue_date DESC, created_at DESC"
        rows = con.execute(sql, params).fetchall()
        return [_invoice_dict(r, con) for r in rows]

@app.get("/api/invoices/unpaid")
def list_unpaid_invoices(request: Request):
    """Returns invoices that are unsettled (UNPAID, PARTIAL, OVERDUE)."""
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        rows = con.execute("""SELECT * FROM invoices
                              WHERE status IN ('UNPAID','PARTIAL','OVERDUE')
                              ORDER BY due_date ASC NULLS LAST, issue_date DESC""").fetchall()
        return [_invoice_dict(r, con) for r in rows]

@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        r = con.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not r: raise HTTPException(404, "فاکتور پیدا نشد")
        return _invoice_dict(r, con)

@app.post("/api/invoices")
def create_invoice(payload: InvoiceCreateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.invoices")
    if not payload.code.strip() or not payload.title.strip() or not payload.company_id:
        raise HTTPException(400, "کد، عنوان و شرکت الزامی است")
    if payload.status not in ("DRAFT","UNPAID","PARTIAL","PAID","OVERDUE","CANCELLED"):
        raise HTTPException(400, "وضعیت نامعتبر")
    iid = uid()
    ts = now()
    items_json = json.dumps(payload.items, ensure_ascii=False) if payload.items else "[]"
    total = float(payload.total_amount)
    if not total and payload.items:
        total = sum((float(i.get("qty",1)) * float(i.get("unit_price",0))) for i in payload.items if isinstance(i, dict))
    with db() as con:
        try:
            con.execute("""INSERT INTO invoices
                (id, code, title, company_id, person_id, proforma_id, contract_id, issue_date, due_date, status, total_amount, paid_amount, currency, items_json, notes, created_by, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (iid, payload.code.strip(), payload.title.strip(), payload.company_id, payload.person_id,
                 payload.proforma_id, payload.contract_id, payload.issue_date, payload.due_date,
                 payload.status, total, float(payload.paid_amount), payload.currency,
                 items_json, payload.notes, user["id"], ts, ts))
        except Exception as e:
            if "UNIQUE" in str(e): raise HTTPException(400, "کد فاکتور تکراری است")
            raise
        audit(con, user["id"], "INVOICE_CREATE", "invoice", iid, {"code": payload.code, "title": payload.title})
    return {"id": iid, "code": payload.code}

@app.patch("/api/invoices/{invoice_id}")
def update_invoice(invoice_id: str, payload: InvoiceUpdateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.invoices")
    with db() as con:
        existing = con.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not existing: raise HTTPException(404, "فاکتور پیدا نشد")
        updates = []
        params = []
        for k, v in payload.model_dump(exclude_unset=True).items():
            if v is None: continue
            if k == "items":
                updates.append("items_json=?")
                params.append(json.dumps(v, ensure_ascii=False))
                if payload.total_amount is None:
                    new_total = sum((float(i.get("qty",1)) * float(i.get("unit_price",0))) for i in v if isinstance(i, dict))
                    updates.append("total_amount=?")
                    params.append(new_total)
            else:
                updates.append(f"{k}=?")
                params.append(v)
        # Auto-update status if paid_amount >= total_amount
        if payload.paid_amount is not None and payload.status is None:
            new_paid = float(payload.paid_amount)
            new_total = float(existing["total_amount"]) if payload.total_amount is None else float(payload.total_amount)
            if new_paid >= new_total and new_total > 0:
                updates.append("status=?")
                params.append("PAID")
            elif new_paid > 0 and new_paid < new_total:
                updates.append("status=?")
                params.append("PARTIAL")
        if not updates:
            return {"ok": True, "updated": 0}
        updates.append("updated_at=?")
        params.append(now())
        params.append(invoice_id)
        con.execute(f"UPDATE invoices SET {', '.join(updates)} WHERE id=?", params)
        audit(con, user["id"], "INVOICE_UPDATE", "invoice", invoice_id, {"fields": updates})
    return {"ok": True, "updated": len(updates) - 1}

@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.invoices")
    with db() as con:
        existing = con.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not existing: raise HTTPException(404, "فاکتور پیدا نشد")
        con.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        audit(con, user["id"], "INVOICE_DELETE", "invoice", invoice_id, {"code": existing["code"]})
    return {"ok": True}


# ========================================================================
# COMPANY CONTACTS API (تماس‌های متعدد شرکت)
# ========================================================================
@app.get("/api/companies/{company_id}/contacts")
def list_company_contacts(company_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        if not con.execute("SELECT 1 FROM companies WHERE id=?", (company_id,)).fetchone():
            raise HTTPException(404, "شرکت پیدا نشد")
        rows = con.execute("SELECT * FROM company_contacts WHERE company_id=? ORDER BY created_at DESC", (company_id,)).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/companies/{company_id}/contacts")
def add_company_contact(company_id: str, payload: CompanyContactCreateModel, request: Request):
    user = current_user(request)
    require_perm(user, "customers.manage")
    with db() as con:
        if not con.execute("SELECT 1 FROM companies WHERE id=?", (company_id,)).fetchone():
            raise HTTPException(404, "شرکت پیدا نشد")
        if payload.contact_type not in ("PHONE","MOBILE","EMAIL","FAX","WEBSITE","OTHER"):
            raise HTTPException(400, "نوع تماس نامعتبر")
        if not payload.value.strip():
            raise HTTPException(400, "مقدار تماس الزامی است")
        cid = uid()
        con.execute("INSERT INTO company_contacts (id, company_id, contact_type, label, value, notes, created_by, created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (cid, company_id, payload.contact_type, payload.label, payload.value.strip(), payload.notes, user["id"], now()))
        audit(con, user["id"], "COMPANY_CONTACT_ADD", "company_contact", cid, {"company_id": company_id, "type": payload.contact_type})
    return {"id": cid}

@app.delete("/api/companies/{company_id}/contacts/{contact_id}")
def delete_company_contact(company_id: str, contact_id: str, request: Request):
    user = current_user(request)
    require_perm(user, "customers.manage")
    with db() as con:
        existing = con.execute("SELECT * FROM company_contacts WHERE id=? AND company_id=?", (contact_id, company_id)).fetchone()
        if not existing: raise HTTPException(404, "تماس پیدا نشد")
        con.execute("DELETE FROM company_contacts WHERE id=?", (contact_id,))
        audit(con, user["id"], "COMPANY_CONTACT_DELETE", "company_contact", contact_id, {"company_id": company_id})
    return {"ok": True}


# ========================================================================
# CUSTOMERS DASHBOARD STATS (۳ کارت آماری)
# ========================================================================
@app.get("/api/customers/stats")
def customers_stats(request: Request):
    """Returns: count of active contracts, in-progress proformas, unpaid invoices, plus totals."""
    user = current_user(request)
    require_perm(user, "customers.view")
    with db() as con:
        today = now()[:10]
        # Active contracts: status=ACTIVE and today is within [start_date, end_date]
        active_contracts = con.execute("""SELECT COUNT(*) FROM contracts
            WHERE status='ACTIVE' AND start_date<=? AND end_date>=?""", (today, today)).fetchone()[0]
        # In-progress proformas: status IN (DRAFT, IN_PROGRESS, SENT)
        in_progress_proformas = con.execute("""SELECT COUNT(*) FROM proformas
            WHERE status IN ('DRAFT','IN_PROGRESS','SENT')""").fetchone()[0]
        # Unpaid invoices: status IN (UNPAID, PARTIAL, OVERDUE)
        unpaid_invoices = con.execute("""SELECT COUNT(*) FROM invoices
            WHERE status IN ('UNPAID','PARTIAL','OVERDUE')""").fetchone()[0]
        # Sum of unpaid invoice balances
        unpaid_balance_row = con.execute("""SELECT COALESCE(SUM(total_amount - paid_amount), 0) FROM invoices
            WHERE status IN ('UNPAID','PARTIAL','OVERDUE')""").fetchone()
        unpaid_balance = float(unpaid_balance_row[0]) if unpaid_balance_row else 0.0
        # Total counts
        total_companies = con.execute("SELECT COUNT(*) FROM companies WHERE active=1").fetchone()[0]
        total_persons = con.execute("SELECT COUNT(*) FROM persons WHERE active=1").fetchone()[0]
        total_contracts = con.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        total_proformas = con.execute("SELECT COUNT(*) FROM proformas").fetchone()[0]
        total_invoices = con.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        return {
            "active_contracts": active_contracts,
            "in_progress_proformas": in_progress_proformas,
            "unpaid_invoices": unpaid_invoices,
            "unpaid_balance": unpaid_balance,
            "total_companies": total_companies,
            "total_persons": total_persons,
            "total_contracts": total_contracts,
            "total_proformas": total_proformas,
            "total_invoices": total_invoices,
        }




@app.get("/api/iso30414/report")
def iso30414_report(request: Request):
    user = current_user(request)
    require_perm(user, "reports.iso")
    with db() as con:
        # 11 areas of ISO 30414 with computed metrics
        total_users = con.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
        total_tasks = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        approved = con.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('APPROVED','APPROVED_WITH_EXCEPTION')").fetchone()[0]
        returned = con.execute("SELECT COUNT(*) FROM tasks WHERE status='RETURNED'").fetchone()[0]
        overdue = con.execute("SELECT COUNT(*) FROM tasks WHERE due_date < ? AND status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED')", (now(),)).fetchone()[0]
        total_time = con.execute("SELECT COALESCE(SUM(duration_seconds),0) FROM time_entries WHERE end_at IS NOT NULL").fetchone()[0]
        avg_score = con.execute("SELECT COALESCE(AVG(score),0) FROM decisions WHERE score IS NOT NULL").fetchone()[0]
        total_companies = con.execute("SELECT COUNT(*) FROM companies WHERE active=1").fetchone()[0]
        pending_reviews = con.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('SUBMITTED','RECONCILING','NEEDS_REVIEW')").fetchone()[0]
        leave_pending = con.execute("SELECT COUNT(*) FROM requests WHERE status='PENDING'").fetchone()[0]
        total_submissions = con.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
        
        metrics = {
            "snapshot_date": tehran_jalali_today(),
            "area_1_composition": {
                "total_employees": total_users,
                "total_companies": total_companies,
                "employees_by_role": {r[0]: r[1] for r in con.execute("SELECT role, COUNT(*) FROM users WHERE active=1 GROUP BY role").fetchall()},
            },
            "area_2_costs": {
                "total_tracked_hours": round(total_time / 3600, 1),
                "hours_per_employee": round(total_time / 3600 / max(total_users, 1), 1),
            },
            "area_3_diversity": {
                "note": "تنوع نیروی کار — نیاز به داده‌های دموگرافیک",
            },
            "area_4_leadership": {
                "managers_count": con.execute("SELECT COUNT(*) FROM users WHERE role IN ('ADMIN','CEO') AND active=1").fetchone()[0],
                "span_of_control": round(total_users / max(con.execute("SELECT COUNT(*) FROM users WHERE role IN ('ADMIN','CEO') AND active=1").fetchone()[0], 1), 1),
            },
            "area_5_culture": {
                "avg_performance_score": round(avg_score, 1),
                "approval_rate": round(approved / max(total_tasks, 1) * 100, 1),
                "return_rate": round(returned / max(total_tasks, 1) * 100, 1),
            },
            "area_6_health_safety": {
                "pending_leave_requests": leave_pending,
                "note": "سلامت و ایمنی — نیاز به داده‌های غیبت",
            },
            "area_7_productivity": {
                "tasks_completed": approved,
                "tasks_overdue": overdue,
                "total_submissions": total_submissions,
                "pending_reviews": pending_reviews,
                "productivity_ratio": round(approved / max(total_tasks, 1) * 100, 1),
            },
            "area_8_training": {
                "note": "آموزش و توسعه — نیاز به ثبت داده‌های آموزش",
            },
            "area_9_recruitment": {
                "note": "جذب و استخدام — خارج از دامنه فعلی",
            },
            "area_10_turnover": {
                "active_users": total_users,
                "inactive_users": con.execute("SELECT COUNT(*) FROM users WHERE active=0").fetchone()[0],
            },
            "area_11_other": {
                "total_tasks": total_tasks,
                "total_decisions": con.execute("SELECT COUNT(*) FROM decisions").fetchone()[0],
            },
        }
        return metrics

@app.post("/api/iso30414/snapshot")
def save_iso_snapshot(request: Request):
    user = current_user(request)
    require_perm(user, "reports.iso")
    # Get current metrics and save
    with db() as con:
        snap_id = uid()
        # Compute metrics inline (simplified)
        total_users = con.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
        total_tasks = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        approved = con.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('APPROVED','APPROVED_WITH_EXCEPTION')").fetchone()[0]
        metrics = json.dumps({"date": tehran_jalali_today(), "employees": total_users, "tasks": total_tasks, "approved": approved}, ensure_ascii=False)
        con.execute("INSERT INTO iso30414_snapshots VALUES(?,?,?,?)", (snap_id, tehran_jalali_today(), metrics, user["id"], now()))
        audit(con, user["id"], "ISO30414_SNAPSHOT", "iso30414_snapshot", snap_id, {})
        return {"id": snap_id, "saved_at": now()}


# ========================================================================
# PHASE 6: DASHBOARD CHART DATA API
# ========================================================================

@app.get("/api/dashboard/charts")
def dashboard_charts(request: Request):
    user = current_user(request)
    with db() as con:
        # Task status distribution (for pie chart)
        status_dist = {r[0]: r[1] for r in con.execute(
            "SELECT status, COUNT(*) FROM tasks GROUP BY status").fetchall()}
        
        # Tasks per company (for bar chart)
        company_tasks = [{"name": r[0], "count": r[1]} for r in con.execute(
            "SELECT c.name, COUNT(t.id) FROM companies c LEFT JOIN tasks t ON t.company_id=c.id GROUP BY c.id ORDER BY COUNT(t.id) DESC LIMIT 10").fetchall()]
        
        # Workload per employee (for bar chart)
        workload = [{"name": r[0], "open": r[1], "done": r[2]} for r in con.execute(
            """SELECT u.name, SUM(CASE WHEN t.status NOT IN ('APPROVED','APPROVED_WITH_EXCEPTION','CANCELLED') THEN 1 ELSE 0 END),
               SUM(CASE WHEN t.status IN ('APPROVED','APPROVED_WITH_EXCEPTION') THEN 1 ELSE 0 END)
               FROM users u LEFT JOIN tasks t ON t.assignee_id=u.id WHERE u.role='EMPLOYEE' AND u.active=1 GROUP BY u.id""").fetchall()]
        
        # Time tracked per day (for line chart)
        time_per_day = [{"date": r[0], "hours": round(r[1]/3600, 1)} for r in con.execute(
            """SELECT DATE(te.start_at) AS d, SUM(te.duration_seconds) FROM time_entries te
               WHERE te.end_at IS NOT NULL AND te.start_at >= date('now','-30 days')
               GROUP BY d ORDER BY d""").fetchall()]
        
        # Performance scores trend (for line chart)
        score_trend = [{"date": r[0], "avg_score": r[1]} for r in con.execute(
            """SELECT DATE(d.created_at) AS d, AVG(d.score) FROM decisions d
               WHERE d.score IS NOT NULL GROUP BY d ORDER BY d DESC LIMIT 30""").fetchall()]
        
        # Priority distribution (for doughnut chart)
        priority_dist = {r[0]: r[1] for r in con.execute(
            "SELECT priority, COUNT(*) FROM tasks GROUP BY priority").fetchall()}
        
        return {
            "status_distribution": status_dist,
            "company_tasks": company_tasks,
            "employee_workload": workload,
            "time_per_day": time_per_day,
            "score_trend": score_trend,
            "priority_distribution": priority_dist,
        }


# ========================================================================
# PHASE 7: KANBAN ORDERING API
# ========================================================================

class KanbanOrderModel(BaseModel):
    task_id: str
    column_status: str
    sort_order: int = 0

@app.post("/api/kanban/order")
def update_kanban_order(payload: KanbanOrderModel, request: Request):
    user = current_user(request)
    with db() as con:
        con.execute("INSERT OR REPLACE INTO task_kanban_order VALUES(?,?,?)",
                     (payload.task_id, payload.column_status, payload.sort_order))
        # Also update task status to match column
        valid_statuses = ["ASSIGNED", "IN_PROGRESS", "SUBMITTED", "NEEDS_REVIEW", "APPROVED", "RETURNED"]
        if payload.column_status in valid_statuses:
            con.execute("UPDATE tasks SET status=? WHERE id=?", (payload.column_status, payload.task_id))
            audit(con, user["id"], "KANBAN_MOVE", "task", payload.task_id,
                  {"column": payload.column_status, "order": payload.sort_order})
        return {"ok": True, "kanban": True}


# ========================================================================
# TASK CHECKLIST API (5-step workflow)
# ========================================================================

@app.get("/api/tasks/{task_id}/checklist")
def get_checklist(task_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        task_access(con, user, task_id)
        rows = con.execute("SELECT * FROM task_checklist WHERE task_id=? ORDER BY step_number", (task_id,)).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/tasks/{task_id}/checklist")
def create_checklist(task_id: str, payload: ChecklistModel, request: Request):
    user = current_user(request)
    with db() as con:
        task_access(con, user, task_id)
        con.execute("DELETE FROM task_checklist WHERE task_id=?", (task_id,))
        for i, title in enumerate((payload.steps or [])[:5], 1):
            con.execute("INSERT INTO task_checklist VALUES(?,?,?,?,?,?,?,?)", (uid(), task_id, i, title.strip(), 0, None, None, now()))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)", (uid(), task_id, user["id"], "CHECKLIST_CREATED", json.dumps({"steps": len(payload.steps or [])}), now()))
        return {"ok": True, "steps_created": len((payload.steps or [])[:5])}

@app.post("/api/tasks/{task_id}/checklist/toggle")
def toggle_checklist_item(task_id: str, payload: ChecklistToggleModel, request: Request):
    user = current_user(request)
    with db() as con:
        task_access(con, user, task_id)
        item = con.execute("SELECT * FROM task_checklist WHERE task_id=? AND step_number=?", (task_id, payload.step_number)).fetchone()
        if not item:
            raise HTTPException(404, "مرحله پیدا نشد")
        if payload.is_done:
            con.execute("UPDATE task_checklist SET is_done=1, done_by=?, done_at=? WHERE id=?", (user["id"], now(), item["id"]))
        else:
            con.execute("UPDATE task_checklist SET is_done=0, done_by=NULL, done_at=NULL WHERE id=?", (item["id"],))
        con.execute("INSERT INTO task_events VALUES(?,?,?,?,?,?)", (uid(), task_id, user["id"], "CHECKLIST_TOGGLE", json.dumps({"step": payload.step_number, "done": payload.is_done}), now()))
        total = con.execute("SELECT COUNT(*) FROM task_checklist WHERE task_id=?", (task_id,)).fetchone()[0]
        done = con.execute("SELECT COUNT(*) FROM task_checklist WHERE task_id=? AND is_done=1", (task_id,)).fetchone()[0]
        if total > 0:
            progress = int((done / total) * 100)
            con.execute("UPDATE tasks SET progress=?, updated_at=? WHERE id=?", (progress, now(), task_id))
        return {"ok": True, "done": done, "total": total}


# ========================================================================
# TASK HISTORY / ACTIVITY LOG API
# ========================================================================

@app.get("/api/tasks/{task_id}/history")
def get_task_history(task_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        task_access(con, user, task_id)
        rows = con.execute("""SELECT e.*, u.name AS actor_name FROM task_events e
                              JOIN users u ON u.id=e.actor_id WHERE task_id=? ORDER BY created_at ASC""", (task_id,)).fetchall()
        return [{**dict(r), "details": json.loads(r["details"])} for r in rows]

@app.get("/api/tasks/{task_id}/collaborators")
def get_collaborators(task_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        task_access(con, user, task_id)
        rows = con.execute("""SELECT tc.*, u.name AS user_name, u.role FROM task_collaborators tc
                              JOIN users u ON u.id=tc.user_id WHERE tc.task_id=?""", (task_id,)).fetchall()
        return [dict(r) for r in rows]


# ========================================================================
# PERFORMANCE ENHANCEMENT: Create with checklist + delegate + score
# ========================================================================

PERFORMANCE_CATEGORIES_SET = {"حسابداری","مالیاتی","حسابرسی","اداری","مشاوره","سایر"}

@app.post("/api/performance-entries/v2")
def create_performance_v2(payload: PerformanceCreateModel, request: Request):
    user = current_user(request)
    if payload.category not in PERFORMANCE_CATEGORIES_SET:
        raise HTTPException(400, "نوع عملکرد معتبر نیست")
    work_date = clean_work_date(payload.work_date)
    with db() as con:
        entry_id = uid()
        con.execute("""INSERT INTO performance_entries(id,user_id,work_date,category,title,description,duration_minutes,status,review_note,reviewer_id,reviewed_at,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (entry_id, user["id"], work_date, payload.category, payload.title.strip(),
                      payload.description.strip(), payload.duration_minutes, "PENDING", "", None, None, now()))
        for i, step in enumerate((payload.checklist_steps or [])[:5], 1):
            con.execute("INSERT INTO performance_checklist VALUES(?,?,?,?,?,?,?,?)", (uid(), entry_id, i, step.strip(), 0, None, None, now()))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "CREATED", json.dumps({"checklist_steps": len(payload.checklist_steps or [])}), now()))
        if payload.delegate_to:
            target = con.execute("SELECT id FROM users WHERE id=? AND active=1", (payload.delegate_to,)).fetchone()
            if target:
                con.execute("INSERT INTO performance_delegations VALUES(?,?,?,?,?,?)",
                            (uid(), entry_id, user["id"], payload.delegate_to, payload.delegate_scope, "DELEGATED", now()))
                notify(con, payload.delegate_to, "ارجاع عملکرد", f"بخشی از عملکرد «{payload.title}» به شما ارجاع شد")
                con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "DELEGATED", json.dumps({"to": payload.delegate_to, "scope": payload.delegate_scope}), now()))
        audit(con, user["id"], "PERFORMANCE_CREATE_V2", "performance_entry", entry_id, {"category": payload.category})
        return {"id": entry_id}

@app.post("/api/performance-entries/{entry_id}/score")
def score_performance(entry_id: str, payload: PerformanceScoreModel, request: Request):
    user = current_user(request)
    require_perm(user, "performance.review")
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "گزارش عملکرد پیدا نشد")
        con.execute("INSERT INTO performance_scores_v2 VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], payload.score, payload.reason, now()))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "SCORED", json.dumps({"score": payload.score, "reason": payload.reason}), now()))
        notify(con, entry["user_id"], "امتیاز عملکرد", f"به عملکرد شما نمره {payload.score}/۱۰۰ داده شد")
        audit(con, user["id"], "PERFORMANCE_SCORE", "performance_entry", entry_id, {"score": payload.score})
        return {"ok": True, "score": payload.score}

@app.post("/api/performance-entries/{entry_id}/delegate")
def delegate_performance(entry_id: str, payload: PerformanceDelegateModel, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "گزارش عملکرد پیدا نشد")
        if entry["user_id"] != user["id"] and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "فقط صاحب گزارش می‌تواند ارجاع دهد")
        target = con.execute("SELECT id FROM users WHERE id=? AND active=1", (payload.to_user,)).fetchone()
        if not target:
            raise HTTPException(404, "کاربر هدف پیدا نشد")
        con.execute("INSERT INTO performance_delegations VALUES(?,?,?,?,?,?)",
                    (uid(), entry_id, user["id"], payload.to_user, payload.scope, "DELEGATED", now()))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "DELEGATED", json.dumps({"to": payload.to_user, "scope": payload.scope}), now()))
        notify(con, payload.to_user, "ارجاع عملکرد", f"بخشی از عملکرد به شما ارجاع شد")
        return {"ok": True}

@app.get("/api/performance-entries/{entry_id}/history")
def performance_history(entry_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "گزارش پیدا نشد")
        if entry["user_id"] != user["id"] and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "دسترسی ندارید")
        events = con.execute("""SELECT e.*, u.name AS actor_name FROM performance_events e
                                JOIN users u ON u.id=e.actor_id WHERE e.entry_id=? ORDER BY e.created_at""", (entry_id,)).fetchall()
        scores = con.execute("""SELECT s.*, u.name AS manager_name FROM performance_scores_v2 s
                               JOIN users u ON u.id=s.manager_id WHERE s.entry_id=? ORDER BY s.created_at DESC""", (entry_id,)).fetchall()
        delegations = con.execute("""SELECT d.*, u.name AS to_name FROM performance_delegations d
                                    JOIN users u ON u.id=d.to_user WHERE d.entry_id=? ORDER BY d.created_at""", (entry_id,)).fetchall()
        checklist = con.execute("SELECT * FROM performance_checklist WHERE entry_id=? ORDER BY step_number", (entry_id,)).fetchall()
        return {
            "events": [{**dict(r), "details": json.loads(r["details"])} for r in events],
            "scores": [dict(r) for r in scores],
            "delegations": [dict(r) for r in delegations],
            "checklist": [dict(r) for r in checklist],
        }

@app.get("/api/performance-entries/v2")
def list_performance_v2(request: Request):
    user = current_user(request)
    with db() as con:
        if user["role"] in ("ADMIN", "CEO"):
            rows = con.execute("""SELECT p.*, u.name AS user_name FROM performance_entries p
                                 JOIN users u ON u.id=p.user_id ORDER BY p.created_at DESC LIMIT 200""").fetchall()
        else:
            rows = con.execute("""SELECT p.*, u.name AS user_name FROM performance_entries p
                                 JOIN users u ON u.id=p.user_id WHERE p.user_id=? ORDER BY p.created_at DESC""", (user["id"],)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            scores = con.execute("SELECT score FROM performance_scores_v2 WHERE entry_id=? ORDER BY created_at DESC LIMIT 1", (r["id"],)).fetchall()
            d["latest_score"] = scores[0]["score"] if scores else None
            result.append(d)
        return result



# ========================================================================
# SETTINGS API — manage task types, process types, role types, performance types
# ========================================================================

class TypeModel(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    icon: str = "📋"
    active: bool = True

class ProcessTypeModel(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    default_steps: int = Field(default=3, ge=1, le=5)
    active: bool = True

class RoleTypeModel(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    description: str = Field(default="", max_length=500)
    permissions: str = "[]"
    active: bool = True

class PerfTypeModel(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    category: str = "general"
    description: str = Field(default="", max_length=500)
    active: bool = True

class KPIModel(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(default="quality", max_length=40)
    description: str = Field(default="", max_length=1000)
    target_value: float = Field(ge=0, le=100000)
    target_operator: str = Field(default=">=", max_length=4)
    unit: str = Field(default="%", max_length=20)
    weight: int = Field(default=10, ge=1, le=100)
    frequency: str = Field(default="monthly", max_length=20)
    owner_role: str = Field(default="EMPLOYEE", max_length=20)
    formula: str = Field(default="", max_length=500)
    active: bool = True

@app.get("/api/settings")
def get_all_settings(request: Request):
    user = current_user(request)
    require_perm(user, "settings.view")
    with db() as con:
        return {
            "task_types": [dict(r) for r in con.execute("SELECT * FROM task_types ORDER BY name").fetchall()],
            "process_types": [dict(r) for r in con.execute("SELECT * FROM process_types ORDER BY name").fetchall()],
            "role_types": [dict(r) for r in con.execute("SELECT * FROM role_types ORDER BY name").fetchall()],
            "performance_types": [dict(r) for r in con.execute("SELECT * FROM performance_types ORDER BY name").fetchall()],
            "kpis": [dict(r) for r in con.execute("SELECT * FROM kpis ORDER BY weight DESC, name").fetchall()],
        }

@app.get("/api/settings/task-types")
def list_tt(request: Request):
    current_user(request)
    with db() as con: return [dict(r) for r in con.execute("SELECT * FROM task_types ORDER BY name").fetchall()]

@app.post("/api/settings/task-types")
def create_tt(payload: TypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        tid = uid()
        try: con.execute("INSERT INTO task_types VALUES(?,?,?,?,?,?)", (tid, payload.name, payload.description, payload.icon, 1 if payload.active else 0, now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "نام تکراری است")
        audit(con, user["id"], "TT_CREATE", "setting", tid, {"name": payload.name})
        return {"id": tid, "ok": True}

@app.patch("/api/settings/task-types/{tid}")
def update_tt(tid: str, payload: TypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        if not con.execute("SELECT 1 FROM task_types WHERE id=?", (tid,)).fetchone(): raise HTTPException(404, "نوع پیدا نشد")
        con.execute("UPDATE task_types SET name=?, description=?, icon=?, active=? WHERE id=?", (payload.name, payload.description, payload.icon, 1 if payload.active else 0, tid))
        return {"ok": True}

@app.delete("/api/settings/task-types/{tid}")
def delete_tt(tid: str, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con: con.execute("DELETE FROM task_types WHERE id=?", (tid,)); return {"ok": True}

@app.get("/api/settings/process-types")
def list_pt(request: Request):
    current_user(request)
    with db() as con: return [dict(r) for r in con.execute("SELECT * FROM process_types ORDER BY name").fetchall()]

@app.post("/api/settings/process-types")
def create_pt(payload: ProcessTypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        tid = uid()
        try: con.execute("INSERT INTO process_types VALUES(?,?,?,?,?,?)", (tid, payload.name, payload.description, payload.default_steps, 1 if payload.active else 0, now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "نام تکراری است")
        return {"id": tid, "ok": True}

@app.patch("/api/settings/process-types/{tid}")
def update_pt(tid: str, payload: ProcessTypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        if not con.execute("SELECT 1 FROM process_types WHERE id=?", (tid,)).fetchone(): raise HTTPException(404, "نوع پیدا نشد")
        con.execute("UPDATE process_types SET name=?, description=?, default_steps=?, active=? WHERE id=?", (payload.name, payload.description, payload.default_steps, 1 if payload.active else 0, tid))
        return {"ok": True}

@app.delete("/api/settings/process-types/{tid}")
def delete_pt(tid: str, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con: con.execute("DELETE FROM process_types WHERE id=?", (tid,)); return {"ok": True}

@app.get("/api/settings/role-types")
def list_rt(request: Request):
    current_user(request)
    with db() as con: return [dict(r) for r in con.execute("SELECT * FROM role_types ORDER BY name").fetchall()]

@app.post("/api/settings/role-types")
def create_rt(payload: RoleTypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        tid = uid()
        try: con.execute("INSERT INTO role_types VALUES(?,?,?,?,?,?)", (tid, payload.name, payload.description, payload.permissions, 1 if payload.active else 0, now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "نام تکراری است")
        return {"id": tid, "ok": True}

@app.patch("/api/settings/role-types/{tid}")
def update_rt(tid: str, payload: RoleTypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        if not con.execute("SELECT 1 FROM role_types WHERE id=?", (tid,)).fetchone(): raise HTTPException(404, "نوع پیدا نشد")
        con.execute("UPDATE role_types SET name=?, description=?, permissions=?, active=? WHERE id=?", (payload.name, payload.description, payload.permissions, 1 if payload.active else 0, tid))
        return {"ok": True}

@app.delete("/api/settings/role-types/{tid}")
def delete_rt(tid: str, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con: con.execute("DELETE FROM role_types WHERE id=?", (tid,)); return {"ok": True}

@app.get("/api/settings/performance-types")
def list_pft(request: Request):
    current_user(request)
    with db() as con: return [dict(r) for r in con.execute("SELECT * FROM performance_types ORDER BY name").fetchall()]

@app.post("/api/settings/performance-types")
def create_pft(payload: PerfTypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        tid = uid()
        try: con.execute("INSERT INTO performance_types VALUES(?,?,?,?,?,?)", (tid, payload.name, payload.category, payload.description, 1 if payload.active else 0, now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "نام تکراری است")
        return {"id": tid, "ok": True}

@app.patch("/api/settings/performance-types/{tid}")
def update_pft(tid: str, payload: PerfTypeModel, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con:
        if not con.execute("SELECT 1 FROM performance_types WHERE id=?", (tid,)).fetchone(): raise HTTPException(404, "نوع پیدا نشد")
        con.execute("UPDATE performance_types SET name=?, category=?, description=?, active=? WHERE id=?", (payload.name, payload.category, payload.description, 1 if payload.active else 0, tid))
        return {"ok": True}

@app.delete("/api/settings/performance-types/{tid}")
def delete_pft(tid: str, request: Request):
    user = current_user(request); require_perm(user, "settings.types")
    with db() as con: con.execute("DELETE FROM performance_types WHERE id=?", (tid,)); return {"ok": True}

# ---- KPI CRUD ----
@app.get("/api/settings/kpis")
def list_kpis(request: Request):
    current_user(request)
    with db() as con: return [dict(r) for r in con.execute("SELECT * FROM kpis ORDER BY weight DESC, name").fetchall()]

@app.post("/api/settings/kpis")
def create_kpi(payload: KPIModel, request: Request):
    user = current_user(request); require_perm(user, "settings.kpi")
    with db() as con:
        tid = uid()
        ts = now()
        con.execute(
            "INSERT INTO kpis(id,name,category,description,target_value,target_operator,unit,weight,frequency,owner_role,formula,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tid, payload.name.strip(), payload.category, payload.description.strip(),
             payload.target_value, payload.target_operator, payload.unit,
             payload.weight, payload.frequency, payload.owner_role,
             payload.formula.strip(), 1 if payload.active else 0, ts, ts)
        )
        audit(con, user["id"], "KPI_CREATE", "kpi", tid, {"name": payload.name, "category": payload.category})
        return {"id": tid, "ok": True}

@app.patch("/api/settings/kpis/{tid}")
def update_kpi(tid: str, payload: KPIModel, request: Request):
    user = current_user(request); require_perm(user, "settings.kpi")
    with db() as con:
        if not con.execute("SELECT 1 FROM kpis WHERE id=?", (tid,)).fetchone():
            raise HTTPException(404, "شاخص کلیدی پیدا نشد")
        con.execute(
            "UPDATE kpis SET name=?, category=?, description=?, target_value=?, target_operator=?, unit=?, weight=?, frequency=?, owner_role=?, formula=?, active=?, updated_at=? WHERE id=?",
            (payload.name.strip(), payload.category, payload.description.strip(),
             payload.target_value, payload.target_operator, payload.unit,
             payload.weight, payload.frequency, payload.owner_role,
             payload.formula.strip(), 1 if payload.active else 0, now(), tid)
        )
        audit(con, user["id"], "KPI_UPDATE", "kpi", tid, {"name": payload.name})
        return {"ok": True}

@app.delete("/api/settings/kpis/{tid}")
def delete_kpi(tid: str, request: Request):
    user = current_user(request); require_perm(user, "settings.kpi")
    with db() as con:
        if not con.execute("SELECT 1 FROM kpis WHERE id=?", (tid,)).fetchone():
            raise HTTPException(404, "شاخص کلیدی پیدا نشد")
        con.execute("DELETE FROM kpis WHERE id=?", (tid,))
        audit(con, user["id"], "KPI_DELETE", "kpi", tid, {})
        return {"ok": True}

@app.get("/api/settings/kpis/{tid}/evaluate")
def evaluate_kpi(tid: str, request: Request):
    """Evaluate a single KPI for a given user/month — returns current value and status."""
    user = current_user(request); require_role(user, "ADMIN", "CEO")
    target_user = request.query_params.get("user_id", "")
    period = request.query_params.get("period", "")
    with db() as con:
        kpi = con.execute("SELECT * FROM kpis WHERE id=?", (tid,)).fetchone()
        if not kpi: raise HTTPException(404, "شاخص پیدا نشد")
        # Simple live evaluation based on category (placeholder formula parser)
        current_value = 0.0
        status = "PENDING"
        if kpi["category"] == "quality" and target_user:
            row = con.execute(
                "SELECT AVG(score) as v FROM performance_scores_v2 WHERE user_id=?", (target_user,)
            ).fetchone()
            current_value = float(row["v"]) if row and row["v"] is not None else 0.0
        elif kpi["category"] == "volume" and target_user:
            row = con.execute(
                "SELECT COALESCE(SUM(duration_minutes),0) as v FROM performance_entries WHERE user_id=?", (target_user,)
            ).fetchone()
            current_value = float(row["v"]) if row else 0.0
        elif kpi["category"] == "ontime" and target_user:
            # Use task_events for completion tracking, then compare completion time to due_date
            row = con.execute(
                """SELECT CAST(SUM(CASE WHEN te.created_at <= t.due_date THEN 1 ELSE 0 END) AS REAL) /
                   NULLIF(COUNT(*),0) * 100 as v
                   FROM task_events te
                   JOIN tasks t ON t.id = te.task_id
                   JOIN task_assignments ta ON ta.task_id = t.id
                   WHERE ta.to_user=? AND te.action='COMPLETED' AND t.due_date IS NOT NULL""",
                (target_user,)
            ).fetchone()
            current_value = float(row["v"]) if row and row["v"] is not None else 0.0
        elif kpi["category"] == "collaboration" and target_user:
            row = con.execute(
                "SELECT COUNT(*) as v FROM task_collaborators WHERE user_id=?", (target_user,)
            ).fetchone()
            current_value = float(row["v"]) if row else 0.0
        op = kpi["target_operator"]
        target = float(kpi["target_value"])
        if op == ">=": status = "PASS" if current_value >= target else "FAIL"
        elif op == "<=": status = "PASS" if current_value <= target else "FAIL"
        elif op == ">": status = "PASS" if current_value > target else "FAIL"
        elif op == "<": status = "PASS" if current_value < target else "FAIL"
        elif op == "==": status = "PASS" if abs(current_value - target) < 0.01 else "FAIL"
        return {
            "kpi_id": tid, "name": kpi["name"], "category": kpi["category"],
            "target_value": target, "operator": op, "unit": kpi["unit"],
            "current_value": current_value, "status": status, "period": period
        }


# ========================================================================
# KPI-BASED PERFORMANCE REPORT  (replaces fixed simple/weighted from /api/performance)
# ========================================================================
def _kpi_current_value(con, kpi: dict, user_id: str, period: str | None) -> float:
    """Compute current raw value of a single KPI for a user. Period is YYYY/MM (jalali) or empty."""
    cat = kpi["category"]
    if cat == "quality":
        row = con.execute(
            "SELECT AVG(s.score) as v FROM performance_scores_v2 s JOIN performance_entries e ON e.id=s.entry_id WHERE e.user_id=?",
            (user_id,)
        ).fetchone()
        return float(row["v"]) if row and row["v"] is not None else 0.0
    if cat == "volume":
        row = con.execute(
            "SELECT COALESCE(SUM(duration_minutes),0) as v FROM performance_entries WHERE user_id=?",
            (user_id,)
        ).fetchone()
        return float(row["v"]) if row else 0.0
    if cat == "ontime":
        row = con.execute(
            """SELECT CAST(SUM(CASE WHEN te.created_at <= t.due_date THEN 1 ELSE 0 END) AS REAL) /
                   NULLIF(COUNT(*),0) * 100 as v
               FROM task_events te
               JOIN tasks t ON t.id = te.task_id
               JOIN task_assignments ta ON ta.task_id = t.id
               WHERE ta.to_user=? AND te.action='COMPLETED' AND t.due_date IS NOT NULL""",
            (user_id,)
        ).fetchone()
        return float(row["v"]) if row and row["v"] is not None else 0.0
    if cat == "collaboration":
        row = con.execute(
            "SELECT COUNT(*) as v FROM task_collaborators WHERE user_id=?", (user_id,)
        ).fetchone()
        return float(row["v"]) if row else 0.0
    if cat == "satisfaction":
        # Use manager decision approval rate as proxy
        row = con.execute(
            """SELECT CAST(SUM(CASE WHEN d.decision='APPROVED' THEN 1 ELSE 0 END) AS REAL) /
                   NULLIF(COUNT(*),0) * 5 as v
               FROM decisions d JOIN tasks t ON t.id=d.task_id WHERE t.assignee_id=?""",
            (user_id,)
        ).fetchone()
        return float(row["v"]) if row and row["v"] is not None else 0.0
    # custom: try to read formula-based aggregate — fallback to 0
    return 0.0


def _kpi_ratio(current: float, target: float, op: str) -> float:
    """Return 0-1 ratio of achievement vs target."""
    if target <= 0:
        return 1.0 if current > 0 else 0.0
    if op in (">=", ">"):
        return min(current / target, 1.0)
    if op in ("<=", "<"):
        return min(target / max(current, 0.001), 1.0)
    if op == "==":
        return 1.0 if abs(current - target) < 0.01 else max(0.0, 1.0 - abs(current - target) / target)
    return min(current / target, 1.0)


@app.get("/api/performance/kpi-report")
def kpi_performance_report(request: Request):
    """For every employee: compute each KPI current_value + achievement ratio + weighted_score.
    Returns total_score (0-100) per employee using active KPI weights."""
    user = current_user(request); require_role(user, "ADMIN", "CEO")
    period = request.query_params.get("period", "")
    target_role = request.query_params.get("role", "EMPLOYEE")
    with db() as con:
        kpis = [dict(r) for r in con.execute("SELECT * FROM kpis WHERE active=1 ORDER BY weight DESC, name").fetchall()]
        people = [dict(r) for r in con.execute(
            "SELECT id, name, username FROM users WHERE role=? AND active=1 ORDER BY name", (target_role,)
        ).fetchall()]
        report = []
        for p in people:
            kpi_rows = []
            weighted_sum = 0.0
            weight_total = 0
            for k in kpis:
                current = _kpi_current_value(con, k, p["id"], period)
                target = float(k["target_value"])
                op = k["target_operator"]
                ratio = _kpi_ratio(current, target, op)
                weighted_score = round(ratio * 100, 2)
                contribution = (ratio * 100 * k["weight"]) / 100.0
                weighted_sum += contribution
                weight_total += k["weight"]
                # status
                if op == ">=": status = "PASS" if current >= target else "FAIL"
                elif op == "<=": status = "PASS" if current <= target else "FAIL"
                elif op == ">": status = "PASS" if current > target else "FAIL"
                elif op == "<": status = "PASS" if current < target else "FAIL"
                elif op == "==": status = "PASS" if abs(current - target) < 0.01 else "FAIL"
                else: status = "PENDING"
                kpi_rows.append({
                    "kpi_id": k["id"], "name": k["name"], "category": k["category"],
                    "target_value": target, "operator": op, "unit": k["unit"],
                    "current_value": round(current, 2), "ratio": round(ratio, 4),
                    "weighted_score": weighted_score, "weight": k["weight"],
                    "contribution": round(contribution, 2),
                    "status": status,
                })
            total = round(weighted_sum, 2) if weight_total else 0.0
            # Normalize to 100 if total weight != 100
            if weight_total and weight_total != 100:
                total = round(total * 100 / weight_total, 2)
            passed = sum(1 for k in kpi_rows if k["status"] == "PASS")
            report.append({
                "user_id": p["id"], "name": p["name"], "username": p["username"],
                "kpis": kpi_rows,
                "total_score": total,
                "passed": passed,
                "total_kpis": len(kpi_rows),
                "weight_total": weight_total,
                "grade": "عالی" if total >= 90 else "خوب" if total >= 75 else "متوسط" if total >= 60 else "ضعیف",
            })
        # Sort by total_score desc
        report.sort(key=lambda x: -x["total_score"])
        # Aggregate KPI summary across all employees
        summary = []
        for k in kpis:
            vals = [r["kpis"][i]["current_value"] for r in report for i, kk in enumerate(r["kpis"]) if kk["kpi_id"] == k["id"]]
            summary.append({
                "kpi_id": k["id"], "name": k["name"], "category": k["category"],
                "target_value": float(k["target_value"]), "unit": k["unit"], "weight": k["weight"],
                "avg_value": round(sum(vals) / len(vals), 2) if vals else 0.0,
                "min_value": round(min(vals), 2) if vals else 0.0,
                "max_value": round(max(vals), 2) if vals else 0.0,
            })
        return {
            "period": period,
            "generated_at": now(),
            "kpis": kpis,
            "employees": report,
            "summary": summary,
            "total_weight": sum(k["weight"] for k in kpis),
        }


@app.get("/api/performance/kpi-report/{user_id}")
def kpi_performance_for_user(user_id: str, request: Request):
    """KPI breakdown for a single user — used in user detail panel."""
    user = current_user(request)
    if user["id"] != user_id:
        require_role(user, "ADMIN", "CEO")
    period = request.query_params.get("period", "")
    with db() as con:
        kpis = [dict(r) for r in con.execute("SELECT * FROM kpis WHERE active=1 ORDER BY weight DESC, name").fetchall()]
        person = con.execute("SELECT id, name, username FROM users WHERE id=?", (user_id,)).fetchone()
        if not person: raise HTTPException(404, "کاربر پیدا نشد")
        kpi_rows = []
        weighted_sum = 0.0
        weight_total = 0
        for k in kpis:
            current = _kpi_current_value(con, k, user_id, period)
            target = float(k["target_value"])
            op = k["target_operator"]
            ratio = _kpi_ratio(current, target, op)
            contribution = (ratio * 100 * k["weight"]) / 100.0
            weighted_sum += contribution
            weight_total += k["weight"]
            if op == ">=": status = "PASS" if current >= target else "FAIL"
            elif op == "<=": status = "PASS" if current <= target else "FAIL"
            elif op == ">": status = "PASS" if current > target else "FAIL"
            elif op == "<": status = "PASS" if current < target else "FAIL"
            elif op == "==": status = "PASS" if abs(current - target) < 0.01 else "FAIL"
            else: status = "PENDING"
            kpi_rows.append({
                "kpi_id": k["id"], "name": k["name"], "category": k["category"],
                "target_value": target, "operator": op, "unit": k["unit"],
                "current_value": round(current, 2), "ratio": round(ratio, 4),
                "weighted_score": round(ratio * 100, 2), "weight": k["weight"],
                "contribution": round(contribution, 2),
                "status": status, "description": k.get("description", ""),
            })
        total = round(weighted_sum, 2) if weight_total else 0.0
        if weight_total and weight_total != 100:
            total = round(total * 100 / weight_total, 2)
        passed = sum(1 for k in kpi_rows if k["status"] == "PASS")
        return {
            "user_id": user_id,
            "name": person["name"],
            "username": person["username"],
            "kpis": kpi_rows,
            "total_score": total,
            "passed": passed,
            "total_kpis": len(kpi_rows),
            "weight_total": weight_total,
            "grade": "عالی" if total >= 90 else "خوب" if total >= 75 else "متوسط" if total >= 60 else "ضعیف",
            "period": period,
        }


# ========================================================================
# PERFORMANCE ENHANCEMENT: Add missing task-like features
# ========================================================================

class PerfV3Model(BaseModel):
    work_date: str = Field(min_length=8, max_length=12)
    category: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    duration_minutes: int = Field(ge=1, le=1440)
    company_id: str = ""
    priority: str = "NORMAL"
    weight: int = Field(default=1, ge=1, le=3)
    due_date: str = ""
    collaborator_ids: list[str] = []
    checklist_steps: list[str] = []
    delegate_to: str = ""
    delegate_scope: str = ""

class PerfChecklistToggleModel(BaseModel):
    step_number: int
    is_done: bool

class PerfCommentModel(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    visibility: str = "EMPLOYEE_VISIBLE"

@app.post("/api/performance-entries/v3")
def create_perf_v3(payload: PerfV3Model, request: Request):
    user = current_user(request)
    work_date = clean_work_date(payload.work_date)
    with db() as con:
        entry_id = uid()
        con.execute("""INSERT INTO performance_entries(id,user_id,work_date,category,title,description,duration_minutes,status,review_note,reviewer_id,reviewed_at,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (entry_id, user["id"], work_date, payload.category, payload.title.strip(),
                      payload.description.strip(), payload.duration_minutes, "PENDING", "", None, None, now()))
        # Checklist
        for i, step in enumerate((payload.checklist_steps or [])[:5], 1):
            con.execute("INSERT INTO performance_checklist VALUES(?,?,?,?,?,?,?,?)", (uid(), entry_id, i, step.strip(), 0, None, None, now()))
        # Collaborators (reuse task_collaborators structure with a perf_ prefix table)
        for cid in set(payload.collaborator_ids or []):
            if cid != user["id"]:
                try:
                    con.execute("INSERT INTO performance_delegations VALUES(?,?,?,?,?,?)",
                                (uid(), entry_id, user["id"], cid, "COLLABORATOR", "DELEGATED", now()))
                    notify(con, cid, "همکار در عملکرد", f"شما به عملکرد «{payload.title}» اضافه شدید")
                except: pass
        # Delegate
        if payload.delegate_to:
            target = con.execute("SELECT id FROM users WHERE id=? AND active=1", (payload.delegate_to,)).fetchone()
            if target:
                con.execute("INSERT INTO performance_delegations VALUES(?,?,?,?,?,?)",
                            (uid(), entry_id, user["id"], payload.delegate_to, payload.delegate_scope or "", "DELEGATED", now()))
                notify(con, payload.delegate_to, "ارجاع عملکرد", f"بخشی از عملکرد «{payload.title}» به شما ارجاع شد")
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "CREATED", json.dumps({"checklist": len(payload.checklist_steps or []), "collaborators": len(payload.collaborator_ids or [])}), now()))
        audit(con, user["id"], "PERF_CREATE_V3", "performance_entry", entry_id, {"title": payload.title})
        return {"id": entry_id}

@app.post("/api/performance-entries/{entry_id}/checklist/toggle")
def toggle_perf_checklist(entry_id: str, payload: PerfChecklistToggleModel, request: Request):
    user = current_user(request)
    with db() as con:
        item = con.execute("SELECT * FROM performance_checklist WHERE entry_id=? AND step_number=?", (entry_id, payload.step_number)).fetchone()
        if not item:
            raise HTTPException(404, "مرحله پیدا نشد")
        if payload.is_done:
            con.execute("UPDATE performance_checklist SET is_done=1, done_by=?, done_at=? WHERE id=?", (user["id"], now(), item["id"]))
        else:
            con.execute("UPDATE performance_checklist SET is_done=0, done_by=NULL, done_at=NULL WHERE id=?", (item["id"],))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "CHECKLIST_TOGGLE", json.dumps({"step": payload.step_number, "done": payload.is_done}), now()))
        total = con.execute("SELECT COUNT(*) FROM performance_checklist WHERE entry_id=?", (entry_id,)).fetchone()[0]
        done = con.execute("SELECT COUNT(*) FROM performance_checklist WHERE entry_id=? AND is_done=1", (entry_id,)).fetchone()[0]
        return {"ok": True, "done": done, "total": total, "progress": int((done/max(total,1))*100)}

@app.post("/api/performance-entries/{entry_id}/comments")
def perf_comment(entry_id: str, payload: PerfCommentModel, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        cid = uid()
        con.execute("INSERT INTO perf_comments VALUES(?,?,?,?,?,?)", (cid, entry_id, user["id"], payload.visibility, payload.body, now()))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "COMMENT", json.dumps({"visibility": payload.visibility}), now()))
        return {"id": cid}

@app.get("/api/performance-entries/{entry_id}/comments")
def list_perf_comments(entry_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        if user["role"] not in ("ADMIN", "CEO"):
            rows = con.execute("""SELECT c.*, u.name AS author_name FROM perf_comments c
                                  JOIN users u ON u.id=c.author_id WHERE c.entry_id=? AND c.visibility='EMPLOYEE_VISIBLE'""", (entry_id,)).fetchall()
        else:
            rows = con.execute("""SELECT c.*, u.name AS author_name FROM perf_comments c
                                  JOIN users u ON u.id=c.author_id WHERE c.entry_id=?""", (entry_id,)).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/performance-entries/{entry_id}/submit-file")
async def perf_submit_file(entry_id: str, request: Request):
    """Employee uploads Excel file. System validates against template (sample format).
    If template doesn't match, returns error message. Otherwise saves submission.
    Manager will later upload reference file and system reconciles."""
    user = current_user(request)
    form = await request.form()
    file = form.get("file")
    note = form.get("note", "")
    claimed_start = form.get("claimed_start", "")
    claimed_end = form.get("claimed_end", "")
    if not file:
        raise HTTPException(400, "فایل ارسال نشده")
    content = await file.read(MAX_UPLOAD + 1)
    rows, sheet_name = read_excel(file, content)
    file_hash = hashlib.sha256(content).hexdigest()

    # Step 1: Validate against template (system sample format)
    template_check = validate_template(rows)
    if not template_check["valid"]:
        # File doesn't match template — return error with details so employee can fix
        return {
            "accepted": False,
            "template_valid": False,
            "errors": template_check["errors"],
            "warnings": template_check["warnings"],
            "row_count": len(rows),
            "message": "فایل با قالب سیستم مطابقت ندارد. لطفاً خطاهای زیر را اصلاح کنید.",
        }

    stored_name = f"{file_hash}.xlsx"
    (FILES / stored_name).write_bytes(content)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        # Check existing reference for this entry — if one exists, reconcile now
        ref = con.execute("SELECT * FROM perf_references WHERE entry_id=? ORDER BY version DESC LIMIT 1", (entry_id,)).fetchone()
        ref_rows = None
        ref_id = None
        if ref:
            ref_id = ref["id"]
            ref_content = (FILES / ref["stored_name"]).read_bytes()
            ref_rows, _ = read_excel(UploadFile(filename=ref["original_name"], file=None), ref_content)

        # Step 2: Reconcile (with reference if available)
        report, diffs = reconcile_detailed(rows, ref_rows, claimed_start or None, claimed_end or None)
        report["template_valid"] = True
        report["template_errors"] = []
        report["template_warnings"] = template_check.get("warnings", [])
        report["reference_id"] = ref_id
        report["reference_attached"] = ref_rows is not None

        # Step 3: Save submission
        sub_id = uid()
        version = con.execute("SELECT COUNT(*) FROM perf_submissions WHERE entry_id=?", (entry_id,)).fetchone()[0] + 1
        ts = now()
        # INSERT with all new columns
        con.execute("""INSERT INTO perf_submissions
            (id, entry_id, user_id, version, original_name, stored_name, sha256,
             note, claimed_start, claimed_end,
             row_count, voucher_count, duplicate_rows, out_of_range, report_json, created_at,
             reference_id, template_valid, template_errors, status, manager_id, decision_at, decision_note)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sub_id, entry_id, user["id"], version, file.filename, stored_name, file_hash,
             note, claimed_start, claimed_end,
             report["row_count"], report["voucher_count"], report["duplicate_rows"],
             report["out_of_range"], json.dumps(report, ensure_ascii=False), ts,
             ref_id, 1, "[]", "PENDING", None, None, ""))

        # Step 4: Save row-level diffs
        for d in diffs:
            con.execute("""INSERT INTO perf_submission_diffs
                (id, submission_id, source_row, voucher, line, date, account, debit, credit, description,
                 issue_type, issue_detail, ref_debit, ref_credit, ref_date, ref_account, ref_description, created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (uid(), sub_id, d["source_row"], d["voucher"], d["line"], d["date"],
                 d["account"], d["debit"], d["credit"], d["description"],
                 d["issue_type"], d["issue_detail"], d.get("ref_debit"), d.get("ref_credit"),
                 d.get("ref_date"), d.get("ref_account"), d.get("ref_description"), ts))

        # Notify managers about new submission
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)",
            (uid(), entry_id, user["id"], "FILE_SUBMITTED",
             json.dumps({"version": version, "rows": report["row_count"], "diffs": len(diffs)}), ts))
        managers = con.execute("SELECT id FROM users WHERE role IN ('ADMIN','CEO') AND active=1").fetchall()
        for m in managers:
            notify(con, m["id"], "ثبت عملکرد جدید برای بررسی",
                   f"عملکرد «{entry['title']}» — نسخه {version} ({len(diffs)} اختلاف)")
        audit(con, user["id"], "PERF_FILE_SUBMIT", "performance_entry", entry_id,
              {"rows": report["row_count"], "diffs": len(diffs)})
        return {
            "id": sub_id, "version": version, "accepted": True,
            "template_valid": True, "report": report, "diff_count": len(diffs),
            "diffs_sample": diffs[:20],  # first 20 diffs for preview
        }


# ============ Manager uploads reference Excel for performance entry ============

@app.post("/api/performance-entries/{entry_id}/reference")
async def perf_upload_reference(entry_id: str, request: Request):
    """Manager uploads the reference Excel file for a performance entry.
    System then re-reconciles all existing submissions against this reference."""
    user = current_user(request)
    require_role(user, "ADMIN", "CEO")
    form = await request.form()
    file = form.get("file")
    fiscal_period = form.get("fiscal_period", "")
    coverage_start = form.get("coverage_start", "")
    coverage_end = form.get("coverage_end", "")
    if not file:
        raise HTTPException(400, "فایل مرجع ارسال نشده")
    content = await file.read(MAX_UPLOAD + 1)
    rows, _ = read_excel(file, content)
    digest = hashlib.sha256(content).hexdigest()
    stored = f"{uuid.uuid4().hex}.xlsx"
    (FILES / stored).write_bytes(content)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        # Determine version
        version = con.execute("SELECT COALESCE(MAX(version), 0) + 1 FROM perf_references WHERE entry_id=?", (entry_id,)).fetchone()[0]
        ref_id = uid()
        ts = now()
        # Try to find company_id from entry's submissions (since entry itself may not have company)
        company_id = entry["user_id"]  # fallback
        con.execute("""INSERT INTO perf_references
            (id, entry_id, company_id, fiscal_period, version, original_name, stored_name, sha256,
             row_count, coverage_start, coverage_end, uploaded_by, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ref_id, entry_id, company_id, fiscal_period, version, file.filename, stored, digest,
             len(rows), coverage_start or None, coverage_end or None, user["id"], ts))

        # Re-reconcile all existing submissions against this new reference
        existing_subs = con.execute("SELECT * FROM perf_submissions WHERE entry_id=? ORDER BY version", (entry_id,)).fetchall()
        re_reconciled_count = 0
        for sub in existing_subs:
            sub_content = (FILES / sub["stored_name"]).read_bytes()
            sub_rows, _ = read_excel(UploadFile(filename=sub["original_name"], file=None), sub_content)
            report, diffs = reconcile_detailed(sub_rows, rows, sub["claimed_start"], sub["claimed_end"])
            report["template_valid"] = bool(sub["template_valid"])
            report["template_errors"] = json.loads(sub["template_errors"] or "[]")
            report["reference_id"] = ref_id
            report["reference_attached"] = True
            # Update submission
            con.execute("""UPDATE perf_submissions SET
                report_json=?, reference_id=?, row_count=?, voucher_count=?,
                duplicate_rows=?, out_of_range=? WHERE id=?""",
                (json.dumps(report, ensure_ascii=False), ref_id, report["row_count"],
                 report["voucher_count"], report["duplicate_rows"], report["out_of_range"], sub["id"]))
            # Delete old diffs for this submission
            con.execute("DELETE FROM perf_submission_diffs WHERE submission_id=?", (sub["id"],))
            for d in diffs:
                con.execute("""INSERT INTO perf_submission_diffs
                    (id, submission_id, source_row, voucher, line, date, account, debit, credit, description,
                     issue_type, issue_detail, ref_debit, ref_credit, ref_date, ref_account, ref_description, created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (uid(), sub["id"], d["source_row"], d["voucher"], d["line"], d["date"],
                     d["account"], d["debit"], d["credit"], d["description"],
                     d["issue_type"], d["issue_detail"], d.get("ref_debit"), d.get("ref_credit"),
                     d.get("ref_date"), d.get("ref_account"), d.get("ref_description"), ts))
            re_reconciled_count += 1

        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)",
            (uid(), entry_id, user["id"], "REFERENCE_UPLOADED",
             json.dumps({"version": version, "rows": len(rows), "re_reconciled": re_reconciled_count}), ts))
        audit(con, user["id"], "PERF_REF_UPLOAD", "perf_reference", ref_id,
              {"entry_id": entry_id, "rows": len(rows), "re_reconciled": re_reconciled_count})
        return {
            "id": ref_id, "version": version, "row_count": len(rows),
            "re_reconciled_submissions": re_reconciled_count,
            "message": f"مرجع بارگذاری شد و {re_reconciled_count} ثبت عملکرد مجدداً بررسی شد",
        }


# ============ List reference versions for performance entry ============

@app.get("/api/performance-entries/{entry_id}/references")
def list_perf_references(entry_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        rows = con.execute("""
            SELECT r.*, u.name AS uploaded_by_name
            FROM perf_references r JOIN users u ON u.id=r.uploaded_by
            WHERE r.entry_id=? ORDER BY r.version DESC""", (entry_id,)).fetchall()
        return [dict(r) for r in rows]


# ============ Get diffs for a specific submission ============

@app.get("/api/performance-entries/{entry_id}/submissions/{sub_id}/diffs")
def get_perf_submission_diffs(entry_id: str, sub_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        sub = con.execute("SELECT * FROM perf_submissions WHERE id=? AND entry_id=?", (sub_id, entry_id)).fetchone()
        if not sub:
            raise HTTPException(404, "ارسال پیدا نشد")
        # Permission: owner or admin
        if sub["user_id"] != user["id"] and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "دسترسی ندارید")
        diffs = con.execute("SELECT * FROM perf_submission_diffs WHERE submission_id=? ORDER BY source_row", (sub_id,)).fetchall()
        return {
            "submission": dict(sub),
            "report": json.loads(sub["report_json"]),
            "diffs": [dict(d) for d in diffs],
            "diff_count": len(diffs),
        }


# ============ Download diffs as Excel ============

@app.get("/api/performance-entries/{entry_id}/submissions/{sub_id}/diffs/excel")
def download_perf_submission_diffs_excel(entry_id: str, sub_id: str, request: Request):
    """Download all diffs as an Excel file (for offline review)."""
    user = current_user(request)
    with db() as con:
        sub = con.execute("SELECT * FROM perf_submissions WHERE id=? AND entry_id=?", (sub_id, entry_id)).fetchone()
        if not sub:
            raise HTTPException(404, "ارسال پیدا نشد")
        if sub["user_id"] != user["id"] and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "دسترسی ندارید")
        diffs = con.execute("SELECT * FROM perf_submission_diffs WHERE submission_id=? ORDER BY source_row", (sub_id,)).fetchall()
        # Build Excel
        from io import BytesIO
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = Workbook()
        ws = wb.active
        ws.title = "اختلافات"
        # Header row
        headers = ["ردیف فایل", "شماره سند", "خط", "تاریخ", "حساب", "بدهکار", "بستانکار", "شرح",
                   "نوع اختلاف", "جزئیات اختلاف",
                   "بدهکار مرجع", "بستانکار مرجع", "تاریخ مرجع", "حساب مرجع", "شرح مرجع"]
        ws.append(headers)
        # Style header
        header_fill = PatternFill(start_color="0b8f89", end_color="0b8f89", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        # Color-code issue types
        issue_colors = {
            "MISSING_FROM_REFERENCE": "FECACA",    # red
            "DEBIT_MISMATCH": "FED7AA",            # orange
            "CREDIT_MISMATCH": "FED7AA",           # orange
            "DATE_MISMATCH": "FEF3C7",              # yellow
            "ACCOUNT_MISMATCH": "FEF3C7",           # yellow
            "DESCRIPTION_MISMATCH": "E0F2FE",      # blue
            "DUPLICATE": "F3E8FF",                 # purple
            "OUT_OF_RANGE": "FEE2E2",              # red
        }
        issue_labels = {
            "MISSING_FROM_REFERENCE": "در مرجع نیست",
            "DEBIT_MISMATCH": "اختلاف بدهکار",
            "CREDIT_MISMATCH": "اختلاف بستانکار",
            "DATE_MISMATCH": "اختلاف تاریخ",
            "ACCOUNT_MISMATCH": "اختلاف حساب",
            "DESCRIPTION_MISMATCH": "اختلاف شرح",
            "DUPLICATE": "ردیف تکراری",
            "OUT_OF_RANGE": "خارج از بازه",
        }
        for d in diffs:
            row_data = [
                d["source_row"], d["voucher"], d["line"], d["date"], d["account"],
                d["debit"], d["credit"], d["description"],
                issue_labels.get(d["issue_type"], d["issue_type"]),
                d["issue_detail"],
                d["ref_debit"] or "", d["ref_credit"] or "", d["ref_date"] or "",
                d["ref_account"] or "", d["ref_description"] or "",
            ]
            ws.append(row_data)
            row_idx = ws.max_row
            color = issue_colors.get(d["issue_type"], "FFFFFF")
            fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            for col_idx in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = fill
        # Column widths
        for col_letter, width in zip("ABCDEFGHIJKLMNO", [10, 18, 8, 14, 22, 14, 14, 30, 18, 50, 14, 14, 14, 22, 30]):
            ws.column_dimensions[col_letter].width = width
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{chr(64 + len(headers))}1"
        out = BytesIO()
        wb.save(out)
        out.seek(0)
        from fastapi.responses import StreamingResponse
        filename = f"diffs-entry-{entry_id}-v{sub['version']}.xlsx"
        return StreamingResponse(out,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ============ Manager decision on a submission ============

class PerfDecisionModel(BaseModel):
    decision: str = Field(min_length=2, max_length=20)  # APPROVED / RETURNED / REJECTED
    note: str = Field(default="", max_length=2000)


@app.post("/api/performance-entries/{entry_id}/submissions/{sub_id}/decision")
def perf_submission_decision(entry_id: str, sub_id: str, payload: PerfDecisionModel, request: Request):
    """Manager approves / returns / rejects a submission."""
    user = current_user(request)
    require_perm(user, "performance.review")
    if payload.decision not in ("APPROVED", "RETURNED", "REJECTED"):
        raise HTTPException(400, "تصمیم باید APPROVED، RETURNED یا REJECTED باشد")
    with db() as con:
        sub = con.execute("SELECT * FROM perf_submissions WHERE id=? AND entry_id=?", (sub_id, entry_id)).fetchone()
        if not sub:
            raise HTTPException(404, "ارسال پیدا نشد")
        ts = now()
        con.execute("""UPDATE perf_submissions SET status=?, manager_id=?, decision_at=?, decision_note=?
                       WHERE id=?""",
                     (payload.decision, user["id"], ts, payload.note, sub_id))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)",
                    (uid(), entry_id, user["id"], f"SUBMISSION_{payload.decision}",
                     json.dumps({"submission_id": sub_id, "version": sub["version"], "note": payload.note}), ts))
        # Notify employee
        notify(con, sub["user_id"], f"تصمیم مدیر: {payload.decision}",
               f"نسخه {sub['version']} از عملکرد — {payload.decision}")
        audit(con, user["id"], f"PERF_SUB_{payload.decision}", "perf_submission", sub_id,
              {"entry_id": entry_id, "note": payload.note})
        return {"ok": True, "status": payload.decision}



@app.get("/api/performance-entries/{entry_id}/submissions")
def list_perf_submissions(entry_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        if entry["user_id"] != user["id"] and user["role"] not in ("ADMIN", "CEO"):
            raise HTTPException(403, "دسترسی ندارید")
        rows = con.execute("""
            SELECT s.*, u.name AS user_name, m.name AS manager_name,
                   (SELECT COUNT(*) FROM perf_submission_diffs WHERE submission_id=s.id) AS diff_count,
                   (SELECT COUNT(*) FROM perf_references WHERE entry_id=s.entry_id) AS reference_count
            FROM perf_submissions s
            JOIN users u ON u.id=s.user_id
            LEFT JOIN users m ON m.id=s.manager_id
            WHERE s.entry_id=? ORDER BY s.version DESC""", (entry_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["report"] = json.loads(r["report_json"])
            del d["report_json"]
            result.append(d)
        return result

@app.post("/api/performance-entries/{entry_id}/timer/start")
def perf_timer_start(entry_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        active = con.execute("SELECT id FROM time_entries WHERE user_id=? AND end_at IS NULL", (user["id"],)).fetchone()
        if active:
            raise HTTPException(409, "تایمر فعالی دارید")
        entry = con.execute("SELECT * FROM performance_entries WHERE id=?", (entry_id,)).fetchone()
        if not entry:
            raise HTTPException(404, "عملکرد پیدا نشد")
        tid = uid()
        con.execute("INSERT INTO time_entries VALUES(?,?,?,?,?,?,?,?,?)", (tid, None, user["id"], now(), None, 0, f"performance:{entry_id}", 1, now()))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "TIMER_START", json.dumps({}), now()))
        return {"id": tid, "started_at": now()}

@app.post("/api/performance-entries/{entry_id}/timer/stop")
def perf_timer_stop(entry_id: str, request: Request):
    user = current_user(request)
    with db() as con:
        entry = con.execute("SELECT * FROM time_entries WHERE user_id=? AND end_at IS NULL AND description=?", (user["id"], f"performance:{entry_id}")).fetchone()
        if not entry:
            raise HTTPException(404, "تایمر فعال پیدا نشد")
        end = now()
        start_dt = datetime.fromisoformat(entry["start_at"])
        end_dt = datetime.fromisoformat(end)
        duration = int((end_dt - start_dt).total_seconds())
        con.execute("UPDATE time_entries SET end_at=?, duration_seconds=? WHERE id=?", (end, duration, entry["id"]))
        con.execute("INSERT INTO performance_events VALUES(?,?,?,?,?,?)", (uid(), entry_id, user["id"], "TIMER_STOP", json.dumps({"duration": duration}), now()))
        return {"duration_seconds": duration, "minutes": round(duration/60)}
