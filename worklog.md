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
