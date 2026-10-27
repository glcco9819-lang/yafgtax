---
Task ID: root
Agent: main
Task: Production of a deep 20+ page strategic report (Persian, RTL) covering accounting office management system research, tool comparison, KPI framework, Excel template spec, multi-database architecture, and implementation roadmap. Deliver both PDF and Word formats.

Work Log:
- Searched web for accounting practice management tools (Karbon, Canopy, TaxDome, Financial Cents, Pixie, Jetpack Workflow, Trello, Asana, Monday).
- Searched for Iranian HR software (Radical by Faravision, Megapardaz).
- Searched for KPI frameworks for accounting firms (CPA firm KPIs, employee performance metrics).
- Searched for multi-tenant multi-database SaaS patterns and Adapter Pattern architecture.
- Asked user clarifying questions (output format, length, focus, mandatory sections, audience, build/buy stance).
- User chose: PDF + Word both, 20+ pages deep, focus on architecture & building, all 6 mandatory sections included, combined management + technical audience, hybrid (build) recommendation.
- User confirmed: 50 companies use mixed accounting software (Hamkaran, Sepidar, Holoo, etc.); databases include all types, especially Excel and SQL Server.
- Loaded pdf and docx skills.
- Created outline with 14 sections (cover + 13 chapters).
- Installed Vazirmatn Persian font (3 weights) from GitHub to /home/z/my-project/fonts/.
- Installed arabic-reshaper and python-bidi in venv for proper Persian RTL text rendering in ReportLab.
- Wrote /home/z/my-project/scripts/generate_accounting_report_pdf.py (~970 lines) with full RTL support, custom cover page with dark background, body template with header/footer, 13 chapters with tables, callouts, code blocks.
- Generated PDF: 31 pages, 164 KB, saved to /home/z/my-project/download/سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.pdf
- Wrote /home/z/my-project/scripts/generate_accounting_report_docx.py (~660 lines) using python-docx with RTL paragraph settings, complex script font binding, styled tables with RTL bidiVisual, callout boxes, cover page with dark background.
- Generated DOCX: 239 paragraphs, 34 tables, 73 KB, saved to /home/z/my-project/download/سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.docx

Stage Summary:
- Final deliverables (both saved to /home/z/my-project/download/):
  1. PDF (31 pages, 164 KB): سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.pdf
  2. DOCX (239 paras, 34 tables, 73 KB): سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.docx
- Both files contain identical content (13 chapters):
  - Chapter 1: Problem understanding and needs assessment
  - Chapter 2: Survey of off-the-shelf software (with comparison matrix of 7 tools + Iranian HR tools across 14 criteria)
  - Chapter 3: Build vs Buy analysis (with cost comparison matrix)
  - Chapter 4: 5-layer architecture (Web panel, Workflow engine, Excel control engine, Data standardization, Adapter layer)
  - Chapter 5: Multi-database Adapter Pattern (Python interface, 4 adapter types, connection settings)
  - Chapter 6: Excel template spec (9 columns with validation rules, sample file)
  - Chapter 7: 9-step intelligent document control engine (with 5-state modification vs duplicate rules, sample control report)
  - Chapter 8: 5-KPI staff evaluation framework (35/25/20/10/10 weighting, monthly scorecard, daily dashboard)
  - Chapter 9: Task data model, state machine, sub-task delegation rules
  - Chapter 10: Attendance, leave, requests, immutable audit log
  - Chapter 11: 5-phase implementation roadmap (13 weeks to MVP)
  - Chapter 12: Cost analysis (177-242M IRR year 1), tech stack, deployment options
  - Chapter 13: Final recommendations and immediate next steps
- Final recommendation: Build custom system with hybrid architecture, on Iranian private cloud (Liara/ParsPack), 80-150M IRR MVP cost, 8-12 week timeline.
- Scripts saved to /home/z/my-project/scripts/ for future iteration/regeneration.

---
Task ID: v2-update
Agent: main
Task: Update the accounting office report (v2.0) based on deep analysis of Financial Cents, Karbon, Pixie websites + all final design decisions from user's attached file.

Work Log:
- Fetched and analyzed Financial Cents website: extracted features (400+ templates, AI File Validator, capacity view, QuickBooks integration, financial-cents.com pricing details $19-$69/user)
- Fetched and analyzed Karbon website: extracted features (FIFO queues, role-based templates, email integration, Progress Report Dashboard, Work Scheduler, developer API)
- Fetched and analyzed Pixie website: extracted features (workflow breakdown to steps, auto-start based on key dates, flat pricing by client count, Zapier integration)
- Conducted secondary web search to confirm pricing details (Financial Cents: Solo $19, Team $49, Scale $69, Enterprise custom; Karbon: Team $59, Business $89, Enterprise custom; Pixie: $129/$199/$329 by client count)
- Read user's attached file (تسک حسابداری.txt) containing 14-step strategic conversation with final design decisions
- Extracted 4 key decisions from attached file:
  1. Excel template must include SourceLineID (line ID from source database) - changes after delete-recreate
  2. Reference file is OPTIONAL - manager can approve without uploading reference file
  3. Score 0-100 is INDEPENDENT of approval status
  4. Two-level notes (visible to employee / manager-confidential)
  5. Mandatory reason for rejection/return
  6. Reference file versioning - multiple tasks can use same version
  7. Multi-employee, multi-task, multi-version per company-period
  8. Architecture: hybrid (central server + local agent), data stays in office
  9. Software: Tandis, Holoo, Hamkaran, Sepidar - need Adapter for each
  10. SourceLineID changes after delete-recreate → algorithm must handle replacement detection
- Wrote /home/z/my-project/scripts/generate_accounting_report_v2_pdf.py (~750 lines) with 11 chapters:
  Ch1: Executive summary - 4 key changes from v1
  Ch2: Deep analysis of 3 softwares (workflow, features, structure - not price/API)
  Ch3: Patterns to borrow from each software + features NOT to borrow
  Ch4: Final architecture (central + local agent) + data boundary table
  Ch5: Updated data model with all 18 central tables + 14 local tables
  Ch6: NEW chapter - Optional reference file + 4 manager decisions + score 0-100 + two-level notes + mandatory reason
  Ch7: Reconciliation algorithm with SourceLineID + replacement detection logic
  Ch8: Updated KPI framework (quality 40% based on score 0-100, on-time 25%, volume 20%, collaboration 15%)
  Ch9: Excel template with SourceLineID as first column (11 columns)
  Ch10: Updated 5-phase roadmap (13 weeks to MVP)
  Ch11: Final recommendations and checklist
- Generated PDF v2: 27 pages, 148 KB
- Wrote /home/z/my-project/scripts/generate_accounting_report_v2_docx.py (~500 lines) with same 11 chapters
- Generated DOCX v2: 220 paragraphs, 25 tables, 66 KB

Stage Summary:
- Final deliverables (v2) saved to /home/z/my-project/download/:
  1. PDF v2 (27 pages, 148 KB): سامانه_مدیریت_دفتر_حسابداری_نسخه_۲.pdf
  2. DOCX v2 (220 paras, 25 tables, 66 KB): سامانه_مدیریت_دفتر_حسابداری_نسخه_۲.docx
- Original v1 files preserved: سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.pdf (31 pages), .docx
- v2 key updates from v1:
  - Added: Deep analysis of Financial Cents (400+ templates, AI features), Karbon (FIFO, email integration), Pixie (step breakdown, key dates)
  - Added: Patterns to borrow + patterns NOT to borrow (QuickBooks, IRS, Adobe Sign etc.)
  - Updated: Excel template now has SourceLineID as first column
  - Added: New Chapter 6 - Optional reference file, score 0-100, two-level notes, mandatory reason
  - Updated: KPI weights (40/25/20/15 instead of 35/25/20/10/10)
  - Updated: Architecture with explicit data boundary (raw data stays in office)
  - Added: Replacement detection logic for SourceLineID changes after delete-recreate
  - Updated: Final recommendation emphasizes all 4 v1 + 4 v2 decisions
- Scripts saved to /home/z/my-project/scripts/ for future iteration

---
Task ID: build-program
Agent: main
Task: Build technical spec document + task list + implement Next.js MVP for accounting office management system, push to GitHub.

Work Log:
- Generated technical specification PDF (سند_تخصصی_معماری_امنیت_ساختار_الگوریتم.pdf) with 8 chapters: architecture, security, structure, algorithm, tech stack, API spec, implementation phases, checklist.
- Generated task list PDF (سند_تسک‌لیست_اجرایی_MVP.pdf) with 51 tasks across 5 phases (13 weeks total).
- Loaded fullstack-dev skill and initialized Next.js 16 project.
- Defined comprehensive Prisma schema with 18 models (User, Company, Task, WorkSubmission, ManagerDecision, ReferenceVersion, etc.).
- Pushed schema to SQLite database successfully.
- Implemented 12 API endpoints:
  - POST /api/auth/login (login with JWT)
  - GET /api/auth/me (current user)
  - GET/POST /api/companies (CRUD with RBAC)
  - GET/POST /api/users (CRUD with role check)
  - GET/POST /api/tasks (with assignments and notifications)
  - GET/PATCH /api/tasks/[id] (task detail and update)
  - POST /api/tasks/[id]/submit (work submission with Excel upload + SHA-256 hash + idempotency check)
  - POST /api/submissions/[id]/decision (4 decision types + score 0-100 + two-level notes)
  - GET/POST /api/reference-versions (versioned reference files)
  - GET/POST /api/leave-requests + decision endpoint
  - POST /api/attendance/check-in, /check-out (daily idempotency)
  - GET /api/dashboard (stats + recent activity)
  - POST /api/seed (initial demo data)
- Built single-page application (SPA) UI in src/app/page.tsx with 5 tabs:
  - Overview (stats cards + recent submissions + activity log)
  - Tasks (list + detail + create + submit + decision)
  - Companies (table + create)
  - Users (table + create) - admin/supervisor/ceo only
  - HR (attendance check-in/out + leave requests)
- Set RTL Persian layout in layout.tsx with lang="fa" dir="rtl".
- Tested with browser automation: login, dashboard, tasks tab, task detail, HR tab - all working.
- Created comprehensive README.md in Persian with setup instructions and feature list.
- Created .env.example with all required environment variables.
- Updated .gitignore to exclude: .env, db/, upload/, scripts/, fonts/, tool-results/, .zscripts/, .z-ai-config/, *.log, *.db.
- Committed with detailed message and pushed to https://github.com/glcco9819-lang/YFGTAXES.git (branch: main).
- Removed GitHub token from remote URL after push for security.

Stage Summary:
- Final deliverables (all saved to /home/z/my-project/download/):
  1. سند_تخصصی_معماری_امنیت_ساختار_الگوریتم.pdf (technical spec, 8 chapters)
  2. سند_تسک‌لیست_اجرایی_MVP.pdf (51 tasks, 5 phases, 13 weeks)
  3. dashboard_screenshot.png (visual proof of working UI)
  4. task_detail_screenshot.png (task detail page)
  5. hr_tab_screenshot.png (HR module)
- GitHub: https://github.com/glcco9819-lang/YFGTAXES.git (main branch, public)
- MVP implemented with all key features from user's text file:
  ✓ Login + RBAC (4 roles)
  ✓ Companies (up to 5000)
  ✓ Tasks with priority, weight, assignments
  ✓ Work submissions with Excel upload + idempotency
  ✓ Optional reference file versioning
  ✓ 4 decision types: approve/exception/return/reject
  ✓ Score 0-100 independent of decision
  ✓ Two-level notes (visible/confidential)
  ✓ Leave requests with approval
  ✓ Attendance check-in/out
  ✓ Audit log
  ✓ Notifications
- Tech stack: Next.js 16, TypeScript, Tailwind, Prisma, SQLite
- Login credentials (after /api/seed): admin/admin123, supervisor/super123, ceo/ceo123, emp1-5/emp123

⚠️ SECURITY: User's GitHub Personal Access Token was exposed in chat. It was used only for push and removed from remote URL. User should rotate this token in GitHub settings.
---
Task ID: settings-pro-v2
Agent: main
Task: حرفه‌ای‌سازی تب تنظیمات — تعریف شرکت (حقیقی/حقوقی)، کاربران با فیلدهای کامل، نقش‌ها و دسترسی‌های ریزفیلد + push

Work Log:
- بررسی ساختار فعلی: users/companies/company_access/role_types schema، endpointها، enhanced.js (IIFE در خط 819 بسته می‌شود؛ کد بعدش global است و از globalهای app.js استفاده می‌کند)
- مهاجرت دیتابیس: companies +9 فیلد (kind, first_name, last_name, national_id, phone, address, postal_code, manager_name, manager_phone)؛ users +4 فیلد (first_name, last_name, phone, permissions JSON)
- سیستم دسترسی ریزفیلد: PERMISSION_CATALOG با ۳۰ مجوز در ۷ گروه؛ effective_permissions/has_perm/require_perm؛ override JSON روی users.permissions؛ محافظت ضد قفل‌شدگی ADMIN
- اعمال require_perm روی ۳۸ endpoint (شرکت‌ها، کاربران، تسک‌ها، تصمیم، مرجع، ممیزی، KPI، انواع، اتوماسیون، ISO، عملکرد، درخواست‌ها)
- endpointهای جدید: GET /api/permissions/catalog، GET/PUT /api/users/{id}/permissions؛ /api/me شامل permissions
- add_user/update_user: password2 mismatch check، ساخت نام از نام+فامیل، جایگزینی کامل company_ids
- add_company/update_company: همه فیلدهای جدید؛ نام خودکار برای حقیقی از نام+فامیل
- فرانت (enhanced.js): renderSettings با ۸ زیرتب (تعریف شرکت، کاربران، نقش‌ها و دسترسی‌ها + ۵ تب قبلی)؛ renderCompaniesRich/renderUsersRich/renderPermsRich با مودال‌های حرفه‌ای به‌جای prompt()؛ ماتریس دسترسی با گروه‌بندی + بخش «شرکت‌های قابل مشاهده» با نکته «هر کاربر فقط اطلاعات شرکت‌های منتخب را می‌بیند»
- delegate کردن renderUserManagement/renderCompanyManagement قدیمی به نسخه‌های rich
- nav gating بر اساس state.me.permissions (audit/users/companies/performance/iso/automations/settings)
- SW v12→v13 + asset versions 20261027a
- سرور restart شد؛ ۲۴ تست E2E همه پاس (ساخت شرکت حقیقی/حقوقی، اعتبارسنجی رمز، ماتریس دسترسی، scoping شرکت، جلوگیری از قفل‌شدگی، ...)
- داده‌های تست از دیتابیس پاک شد (testadmin، tkuserها، شرکت‌های TK/TP)
- watchdog بازسازی و فعال شد (scripts/yfg_watchdog.sh)
- Commit d4d8b68 push شد به yafgtax.git و از URL پاک شد

Stage Summary:
- تب تنظیمات حالا حرفه‌ای: ۸ زیرتب با ۳ زیرتب جدید (تعریف شرکت، کاربران، نقش‌ها و دسترسی‌ها)
- ۳۰ مجوز ریزفیلد سمت سرور اعمال می‌شود؛ تغییر دسترسی فوراً نشست کاربر را باطل می‌کند
- همه‌چیز روی GitHub (commit d4d8b68)؛ سرورها سالم؛ watchdog فعال

---
Task ID: reports-hub-0301
Agent: main
Task: تب گزارشات + رفع دیده‌نشدن تب تنظیمات + رمز ۴ نویسه + نسخه‌گذاری 0.3.0.01 + push

Work Log:
- ریشه‌یابی مشکل «تب تنظیمات دیده نمی‌شود»: public/static یک کپی قدیمی جدا از YFG بود (آخرین sync قبل از commit تنظیمات!) — Next.js همیشه نسخه کهنه سرو می‌کرد
- راه‌حل: public/static با نسخه تازه جایگزین شد + اسکریپت scripts/sync_static.sh ساخته شد (بعد از هر تغییر استاتیک اجرا شود)
- nav کاملاً استاتیک شد در index.html: شرکت‌ها/کاربران/گزارش عملکرد تیم/گزارش ممیزی از سطح بالا حذف → زیرمجموعه تنظیمات و گزارشات؛ کانبان/تایم/گفتگو/اتوماسیون/ISO هم استاتیک شدند
- تب گزارشات (enhanced.js): renderReports با ۴ زیرگزارش — team (کارت امتیاز تسک‌ها)، employees (جدید: ترکیب نمره تسک ۵۰٪ + KPI ۵۰٪ با رتبه‌بندی)، audit (ممیزی با دکمه به‌روزرسانی)، kpi (renderKPIReport با پارامتر target اختیاری)
- رفع تداخل scope: renderKPIReport داخل IIFE بود → window.__renderKPIReport/__userKPIDetail expose شد؛ renderReports و window.__renderSettings در global scope
- app.js: renderView با null-guard + مسیرهای reports/settings/kanban/... + fallback retry؛ titles جدید؛ دکمه سریع «مدیریت شرکت‌ها» → settings
- رمز عبور: min 12→4 در SetupModel/UserCreate (Pydantic)، دو چک دستی backend، فرم setup، openNewUser، مودال کاربر rich، پرامپت تغییر رمز
- نسخه: سایدبار «نسخه 0.3.0.01» با id=appVersion؛ /api/status version=0.3.0.01؛ SW v13→v14؛ register با updateViaCache:none + کوئری ?v=14؛ asset URLs ?v=0.3.0.01
- عنوان گزارش KPI داخل تب گزارشات به «🎯 گزارش KPI» اصلاح شد (قبلاً «گزارش عملکرد تیم» بود و تکراری می‌شد)
- تست E2E مرورگر: login → گزارشات با ۴ زیرتب (۱۹ سطر ممیزی، جدول کارکنان با هدرهای کامل، KPI stats) → تنظیمات با ۸ زیرتب → تغییر رمز ۴ نویسه از API → ساخت کاربر با رمز ۴ نویسه → همه پاس
- پاکسازی: کاربران تست testadmin/pwtest4 از DB حذف شدند
- Commit 206eb27 به yafgtax.git push شد (توکن از remote پاک شد)

Stage Summary:
- نسخه 0.3.0.01 — هر تغییر بعدی = 0.3.0.02 و به همین ترتیب
- ساختار سایدبار: نمای کلی، تسک‌ها، درخواست‌ها، کارکرد، ثبت عملکرد، گزارشات، تنظیمات، کانبان، تایم ترکینگ، گفتگو، اتوماسیون، ISO
- نکته مهم نگهداری: بعد از تغییر فایل‌های استاتیک باید scripts/sync_static.sh اجرا شود (یا watcher اضافه شود)

---
Task ID: push-0301-final
Agent: main
Task: پوش نهایی به GitHub (درخواست کاربر: «پوش»)

Work Log:
- بررسی وضعیت: شاخه main سه کامیت جلوتر از origin/main بود (refs محلی قدیمی بودند)
- Push با توکن به yafgtax.git انجام شد: 206eb27..8a7d45f main -> main
- fetch و تأیید نهایی: local و remote کاملاً همگام (main = 8a7d45f)
- توکن در remote config ذخیره نشد (فقط inline استفاده شد)

Stage Summary:
- GitHub yafgtax.git شامل همه تغییرات است: تب تنظیمات حرفه‌ای (d4d8b68)، تب گزارشات + رمز ۴ نویسه + نسخه 0.3.0.01 (206eb27)
- سرورها سالم: YFG:8000 و Next:3000 هر دو HTTP 200، نسخه 0.3.0.01

---
Task ID: chat-messenger-0302 + customers-0302
Agent: main
Task: ارتقای تب گفتگو به مسنجر کامل (DM + گروه + فایل) و افزودن تب مشتریان با ۶ زیرتب

Work Log:
- Backend main.py: ساختار چت بازنویسی شد — chat_messages به ۷ ستون (attachment_id, reply_to, created_at)؛ chat_channel_members با last_read_at و joined_at؛ جدول جدید chat_attachments
- جدول جدید persons (اشخاص مشتری): code/first_name/last_name/national_id/phone/email/address/postal_code/notes/linked_company_id/active
- ۱۳ endpoint جدید: GET/POST /api/chat/channels, GET/PATCH /api/chat/channels/{id}, POST /members, GET/POST /messages, POST /read, POST /upload (file), GET /attachments/{id}, GET /chat/users, GET/POST /api/persons, GET/PATCH/DELETE /api/persons/{id}
- جلوگیری DM با خود، احتکار DM (یک کانال DIRECT برای هر جفت کاربر)، چک عضویت در همه endpoints
- پیوست‌ها تا ۲۵MB، allowlist پسوند (تصویر/PDF/اکسل/ورد/فشرده)، SHA256 و MIME ذخیره
- مهاجرت دیتابیس زنده: ALTER chat_messages, chat_channel_members + CREATE chat_attachments, persons + ایجاد دایرکتوری attachments
- مجوزهای جدید در PERMISSION_CATALOG: customers.view (ALL) و customers.manage (ADMIN, CEO)
- Frontend enhanced.js:
  • renderChat کامل بازنویسی شد: لیست کانال با unread badge، هدر داینامیک (نام گروه + اکشن‌های فقط مالک/مدیر)، رندر پیام با bubble، textarea multi-line، دکمه پیوست، polling هر ۵s
  • ۳ مودال جدید: openChatUserPicker (DM)، openChatUserMultiPicker (افزودن عضو)، openChatGroupModal (نام+اعضا)
  • renderCustomers با ۶ زیرتب: اشخاص ✓، شرکت‌ها ✓، پورتال/قرارداد/پیش‌فاکتور/فاکتور (همه disabled با نشان «به‌زودی»)
  • renderPersonsList با جستجو + جدول + عملیات ویرایش/حذف (RBAC)
  • openPersonForm با فرم کامل (کد، نام، فامیل، کد ملی، تلفن، ایمیل، کد پستی، شرکت مرتبط، آدرس، یادداشت، فعال)
  • renderCompaniesListForCustomers: فهرست شرکت‌های موجود با نوع (حقیقی/حقوقی)
- Frontend index.html: افزودن nav-item «🤝 مشتریان» + view-customers section
- Frontend app.js: routing customers → window.__renderCustomers؛ عنوان مشتریان
- نسخه: 0.3.0.01 → 0.3.0.02 (در main.py، index.html، app.js، sw.js)
- Service Worker: v14 → v15 + updateViaCache:none + ?v=15 در register
- sync_static.sh اجرا شد تا public/static همگام شود با upload/extracted/YFG-Accounting/app/static
- تست E2E مرورگر: ورود → مشتریان (۶ زیرتب، فرم شخص با همه فیلدها، ساخت P001 علی رضایی ✓) → گفتگو (DM با کارمند تست، ارسال پیام، نمایش در bubble ✓) → گزارشات → تنظیمات همه پاس
- داده‌های تست پاک شدند (persons, chat_messages, chat_channels, chat_channel_members, chat_attachments)

Stage Summary:
- نسخه 0.3.0.02 با تب مشتریان و مسنجر کامل
- گفتگو: DM + گروه، آپلود فایل، polling، unread badge، read receipts
- مشتریان: ۶ زیرتب (۲ فعال، ۴ به‌زودی)
- نکته نگهداری: بعد از تغییر فایل‌های استاتیک باید scripts/sync_static.sh اجرا شود

---
Task ID: customers-company-button-0303
Agent: main
Task: افزودن دکمه «شرکت جدید» به زیرتب شرکت‌ها در تب مشتریان (کاربر: «در شرکت‌ها کلید شرکت جدید نیست بسازش»)

Work Log:
- renderCompaniesListForCustomers بازنویسی شد: افزودن دکمه «＋ شرکت جدید» + عملیات (ویرایش، فعال/غیرفعال، جزئیات)
- مودال جدید openPersonForm/__custCompanyForm: ساخت/ویرایش با همه فیلدها (نوع حقیقی/حقوقی، نام شرکت/نام، کد، شناسه ملی، تماس، کد پستی، آدرس، مدیر، تماس مدیر)
- باگ کلیدی: فیلدهای required در ردیف مخفی (first_name/last_name هنگام LEGAL یا name هنگام REAL) موجب می‌شد HTML5 validation ارسال فرم را مسدود کند — رفع با toggle .required بر اساس kind انتخاب‌شده در syncKind (هم برای فرم مشتریان و هم برای فرم تنظیمات)
- نسخه 0.3.0.02 → 0.3.0.03، SW v15 → v16
- تست E2E مرورگر: ساخت LEGAL (ARMAN001 تولیدی آرمان ✓)، ساخت REAL (REAL001 زهرا کریمی ✓)، ویرایش (زهرا → زهرا علی ✓)، جزئیات ✓، toggle فعال ✓
- داده‌های تست پاک شدند

Stage Summary:
- تب شرکت‌ها در مشتریان حالا مستقل از تب تنظیمات است و می‌توان مستقیماً شرکت جدید ساخت
- رفع باگ validation در فرم‌های تنظیمات هم اعمال شد
