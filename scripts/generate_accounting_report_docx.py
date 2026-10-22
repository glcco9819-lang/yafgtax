"""
Accounting Office Management System - Research Report (Word DOCX)
Generates a Persian RTL Word document using python-docx with Vazirmatn font.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn, nsmap
from docx.oxml import OxmlElement
from docx.enum.section import WD_SECTION
import copy

# Color palette
PRIMARY = RGBColor(0x0F, 0x17, 0x2A)
ACCENT = RGBColor(0x0E, 0x7C, 0x8B)
ACCENT2 = RGBColor(0x1E, 0x40, 0xAF)
TEXT_MUTED = RGBColor(0x47, 0x55, 0x69)
SUCCESS = RGBColor(0x16, 0xA3, 0x4A)
WARN = RGBColor(0xD9, 0x77, 0x06)
DANGER = RGBColor(0xDC, 0x26, 0x26)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TABLE_HEADER_BG = "0E7C8B"
TABLE_ALT_BG = "F8FAFC"

# ============================================================
# Helpers
# ============================================================
def set_paragraph_rtl(paragraph):
    """Set paragraph to RTL."""
    pPr = paragraph._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    pPr.append(bidi)

def set_run_rtl(run):
    """Set run to RTL with proper font."""
    rPr = run._element.get_or_add_rPr()
    rtl = OxmlElement('w:rtl')
    rtl.set(qn('w:val'), '1')
    rPr.append(rtl)
    # Set complex script font
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:cs'), 'Vazirmatn')
    rFonts.set(qn('w:ascii'), 'Vazirmatn')
    rFonts.set(qn('w:hAnsi'), 'Vazirmatn')
    rFonts.set(qn('w:eastAsia'), 'Vazirmatn')

def add_run(paragraph, text, bold=False, size=11, color=PRIMARY, font='Vazirmatn'):
    run = paragraph.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.font.color.rgb = color
    if bold:
        run.bold = True
        run.font.name = 'Vazirmatn'
    set_run_rtl(run)
    # Also set complex script size
    rPr = run._element.get_or_add_rPr()
    sz_cs = OxmlElement('w:szCs')
    sz_cs.set(qn('w:val'), str(size * 2))
    rPr.append(sz_cs)
    return run

def add_paragraph_text(doc, text, style=None, bold=False, size=11, color=PRIMARY,
                       alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, space_before=0):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    p.alignment = alignment
    set_paragraph_rtl(p)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = 1.4
    add_run(p, text, bold=bold, size=size, color=color)
    return p

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(12)
    add_run(p, text, bold=True, size=20, color=PRIMARY, font='Vazirmatn')
    # Add bottom border
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '18')
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), '0E7C8B')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    add_run(p, text, bold=True, size=15, color=ACCENT, font='Vazirmatn')
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    add_run(p, text, bold=True, size=12.5, color=PRIMARY, font='Vazirmatn')
    return p

def add_body(doc, text, justify=True):
    align = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.RIGHT
    return add_paragraph_text(doc, text, alignment=align, size=11, color=PRIMARY, space_after=8)

def add_bullet(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.right_indent = Cm(0.7)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.4
    add_run(p, "• " + text, size=11, color=PRIMARY)
    return p

def add_numbered(doc, text, num):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.right_indent = Cm(0.7)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.4
    add_run(p, f"{num}. " + text, size=11, color=PRIMARY)
    return p

def add_callout(doc, text, kind='info'):
    """Add a callout box (single-cell colored table)."""
    bg_color = {
        'info': 'E0F2FE',
        'warn': 'FEF3C7',
        'success': 'D1FAE5',
        'danger': 'FEE2E2'
    }.get(kind, 'E0F2FE')
    border_color = {
        'info': '0E7C8B',
        'warn': 'D97706',
        'success': '16A34A',
        'danger': 'DC2626'
    }.get(kind, '0E7C8B')
    
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    
    # Set cell background
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), bg_color)
    tcPr.append(shd)
    
    # Set cell borders
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '8')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), border_color)
        tcBorders.append(border)
    tcPr.append(tcBorders)
    
    # Cell padding
    tcMar = OxmlElement('w:tcMar')
    for edge in ['top', 'left', 'bottom', 'right']:
        mar = OxmlElement(f'w:{edge}')
        mar.set(qn('w:w'), '200')
        mar.set(qn('w:type'), 'dxa')
        tcMar.append(mar)
    tcPr.append(tcMar)
    
    # Add text to cell
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.line_spacing = 1.4
    add_run(p, text, bold=False, size=11, color=PRIMARY, font='Vazirmatn')
    
    # Spacer after
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)
    return table

def set_cell_background(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def set_cell_text(cell, text, bold=False, size=10, color=None, alignment=WD_ALIGN_PARAGRAPH.RIGHT):
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = alignment
    set_paragraph_rtl(p)
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    add_run(p, text, bold=bold, size=size, color=color if color else PRIMARY, font='Vazirmatn')
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

def add_table_styled(doc, data, col_widths_cm=None, has_header=True):
    """Build a styled RTL table. data: list of lists of strings."""
    rows = len(data)
    cols = len(data[0]) if data else 0
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Set table direction RTL
    tblPr = table._tbl.tblPr
    bidiVisual = OxmlElement('w:bidiVisual')
    tblPr.append(bidiVisual)
    
    # Set borders
    tblBorders = OxmlElement('w:tblBorders')
    for edge in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'CBD5E1')
        tblBorders.append(border)
    tblPr.append(tblBorders)
    
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx]
        for c_idx, cell_text in enumerate(row_data):
            cell = row.cells[c_idx]
            if has_header and r_idx == 0:
                set_cell_background(cell, TABLE_HEADER_BG)
                set_cell_text(cell, cell_text, bold=True, size=10, color=WHITE,
                             alignment=WD_ALIGN_PARAGRAPH.CENTER)
            else:
                if r_idx % 2 == 0:
                    set_cell_background(cell, TABLE_ALT_BG)
                align = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
                set_cell_text(cell, cell_text, size=9.5, alignment=align)
    
    # Set column widths
    if col_widths_cm:
        for row in table.rows:
            for i, w in enumerate(col_widths_cm):
                row.cells[i].width = Cm(w)
    
    # Spacer after
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)
    return table

def add_page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break()
    # Make break a page break
    from docx.enum.text import WD_BREAK
    p.runs[0].clear()
    p.runs[0].add_break(WD_BREAK.PAGE)

# ============================================================
# Cover Page Builder
# ============================================================
def build_cover(doc):
    # Make first section have dark background by using a single-cell table with shading
    section = doc.sections[0]
    section.top_margin = Cm(0)
    section.bottom_margin = Cm(0)
    section.left_margin = Cm(0)
    section.right_margin = Cm(0)
    
    # Cover table (single cell, full page)
    cover_table = doc.add_table(rows=1, cols=1)
    cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = cover_table.rows[0].cells[0]
    
    # Set cell background to dark
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '0F172A')
    tcPr.append(shd)
    
    # Cell height - we want the cover to take most of the page
    trPr = cover_table.rows[0]._tr.get_or_add_trPr()
    trHeight = OxmlElement('w:trHeight')
    trHeight.set(qn('w:val'), '14000')
    trHeight.set(qn('w:hRule'), 'exact')
    trPr.append(trHeight)
    
    # Cell width - full page
    cell.width = Cm(21)
    
    # Set cell padding
    tcMar = OxmlElement('w:tcMar')
    for edge in ['top', 'left', 'bottom', 'right']:
        mar = OxmlElement(f'w:{edge}')
        mar.set(qn('w:w'), '600' if edge in ['left', 'right'] else '3000' if edge == 'top' else '1500')
        mar.set(qn('w:type'), 'dxa')
        tcMar.append(mar)
    tcPr.append(tcMar)
    
    # Add accent strip on top - via paragraph with background color
    # Add the title
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p1)
    p1.paragraph_format.space_before = Pt(80)
    p1.paragraph_format.space_after = Pt(8)
    add_run(p1, "سامانه مدیریت عملیات دفتر حسابداری", bold=True, size=28, color=WHITE, font='Vazirmatn')
    
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p2)
    p2.paragraph_format.space_after = Pt(6)
    add_run(p2, "گزارش راهبردی و معماری سیستم اختصاصی", size=14, color=RGBColor(0xE2, 0xE8, 0xF0), font='Vazirmatn')
    
    p3 = cell.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p3)
    p3.paragraph_format.space_after = Pt(30)
    add_run(p3, "________________________________", size=12, color=ACCENT, font='Vazirmatn')
    
    p4 = cell.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p4)
    p4.paragraph_format.space_after = Pt(60)
    add_run(p4, "بررسی نرم‌افزارهای آماده، طراحی چارچوب ارزیابی پرسنل، معماری چندپایگاه‌داده و نقشه راه پیاده‌سازی", size=12, color=RGBColor(0xE2, 0xE8, 0xF0), font='Vazirmatn')
    
    p5 = cell.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p5)
    p5.paragraph_format.space_after = Pt(8)
    add_run(p5, "دفتر حسابداری - ۵۰ شرکت - ۵ کارمند", size=11, color=RGBColor(0x94, 0xA3, 0xB8), font='Vazirmatn')
    
    p6 = cell.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p6)
    p6.paragraph_format.space_after = Pt(4)
    add_run(p6, "پاییز ۱۴۰۵", size=11, color=RGBColor(0x94, 0xA3, 0xB8), font='Vazirmatn')
    
    p7 = cell.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p7)
    add_run(p7, "نسخه ۱.۰ - سند راهبردی", size=11, color=RGBColor(0x94, 0xA3, 0xB8), font='Vazirmatn')
    
    # Add a new section for body content
    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    new_section.top_margin = Cm(2)
    new_section.bottom_margin = Cm(2)
    new_section.left_margin = Cm(2)
    new_section.right_margin = Cm(2)

# ============================================================
# Document Builder
# ============================================================
def build_docx(output_path):
    doc = Document()
    
    # Set default style
    style = doc.styles['Normal']
    style.font.name = 'Vazirmatn'
    style.font.size = Pt(11)
    style.font.color.rgb = PRIMARY
    
    # Set Normal style font for complex script (Arabic/Persian)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:cs'), 'Vazirmatn')
    rFonts.set(qn('w:ascii'), 'Vazirmatn')
    rFonts.set(qn('w:hAnsi'), 'Vazirmatn')
    
    # Build cover
    build_cover(doc)
    
    # ============ CHAPTER 1 ============
    add_heading_1(doc, "فصل ۱: شناخت مسئله و نیازشناسی")
    
    add_heading_2(doc, "وضعیت موجود دفتر حسابداری")
    add_body(doc, "شما یک دفتر حسابداری با حدود ۵۰ شرکت به‌عنوان مشتری و ۵ کارمند به‌عنوان نیروی اجرایی اداره می‌کنید. این ساختار در صنعت حسابداری ایران یک دفتر متوسط‌حساب تلقی می‌شود؛ نه آن‌قدر کوچک که با ابزارهای ساده مانند اکسل یا یک لیست پیامرسانی اداره شود، و نه آن‌قدر بزرگ که بتوان از نرم‌افزارهای گران‌قیمت سازمانی (مانند نسخه‌های سازمانی Karbon یا Canopy) با اطمینان از بازگشت سرمایه استفاده کرد. این نقطه میانی چالشی است که در آن باید هم کارایی عملیاتی روزانه حفظ شود و هم نظارت مدیریتی بر کیفیت کار پنج کارمند و پنجاه شرکت به‌صورت مستقل قابل اندازه‌گیری باشد.")
    
    add_body(doc, "تنوع نرم‌افزارهای حسابداری که شرکت‌های شما استفاده می‌کنند، مسئله را پیچیده‌تر می‌کند. در محیط واقعی شما، شرکت‌ها با نرم‌افزارهای گوناگونی مانند همکاران سیستم، سپیدار، هلو و احتمالاً نرم‌افزارهای اختصاصی کار می‌کنند. برخی از این نرم‌افزارها از SQL Server استفاده می‌کنند، برخی روی دیتابیس‌های محلی یا فایل‌های اکسل اجرا می‌شوند، و در مواردی اطلاعات فقط از طریق خروجی استاندارد نرم‌افزار قابل دسترسی است. این عدم یکنواختی فنی به معنی آن است که هیچ راهکار آماده‌ای در بازار وجود ندارد که بتواند به‌صورت بومی و بدون سفارشی‌سازی قابل توجه، با تمام این منابع داده ارتباط برقرار کند و گزارش کنترل یکپارچه تولید کند.")
    
    add_body(doc, "بزرگترین نقطه درد شما این است که در حال حاضر، کنترل کیفیت کار پرسنل به یک فرایند دستی، حافظه‌ای و متکی به اعتماد است. وقتی کارمند الف اعلام می‌کند که اسناد شرکت A را تا تاریخ ۱۴۰۵/۰۷/۲۰ در سیستم ثبت کرده، شما راه مستقیمی برای راستی‌آزمایی این ادعا ندارید مگر اینکه خودتان به دیتابیس حسابداری آن شرکت متصل شوید، ریز اسناد را استخراج کنید، با فایل اکسل پیوست کارمند مقایسه کنید و تطبیق بازه‌های تاریخی، شمارش ردیف‌ها و کنترل تکراری‌ها را به‌صورت دستی انجام دهید. این کار برای یک شرکت زمان‌بر است و برای پنجاه شرکت غیرممکن. در نتیجه، شما به‌جای مدیریت استراتژیک دفتر، در تله کنترل جزئی گرفتار می‌شوید.")
    
    add_heading_2(doc, "اهداف فنی و مدیریتی")
    add_body(doc, "بر اساس تحلیل نیازهای شما، اهداف سامانه پیشنهادی را می‌توان در سه لایه دسته‌بندی کرد. لایه اول اهداف عملیاتی شامل تخصیص تسک، پیگیری پیشرفت، ثبت گزارش کار با قالب استاندارد و پیوست فایل اکسل است. این لایه با ابزارهای آماده مانند Karbon یا TaxDome قابل پوشش است. لایه دوم اهداف کنترلی شامل راستی‌آزمایی هوشمند فایل اکسل در برابر داده‌های واقعی، تشخیص تکراری، تطبیق بازه‌های تاریخی، و گزارش مغایرت برای مدیر است. این لایه با هیچ ابزار آماده‌ای به‌صورت کامل پوشش داده نمی‌شود و باید به‌صورت اختصاصی ساخته شود. لایه سوم اهداف مدیریتی شامل ارزیابی عملکرد پرسنل بر اساس شاخص‌های کلیدی، داشبورد روزانه، ثبت مرخصی و حضور و غیاب، و لاگ غیرقابل ویرایش فعالیت‌هاست که ترکیبی از قابلیت‌های آماده و توسعه اختصاصی را می‌طلبد.")
    
    add_callout(doc, "نکته کلیدی: مسئله اصلی شما «مدیریت تسک» نیست، بلکه «اثبات قابل اندازه‌گیری انجام شدن کار حسابداری» است. این تفاوت ذهنی، انتخاب ابزار و معماری سامانه را به‌طور بنیادی تعیین می‌کند.", 'info')
    
    add_page_break(doc)
    
    # ============ CHAPTER 2 ============
    add_heading_1(doc, "فصل ۲: بررسی نرم‌افزارهای آماده موجود")
    
    add_body(doc, "در این فصل، نرم‌افزارهای تخصصی مدیریت دفاتر حسابداری، نرم‌افزارهای عمومی مدیریت پروژه، و راهکارهای ایرانی برای حضور و غیاب بررسی می‌شوند. هدف، تعیین این است که آیا یک نرم‌افزار آماده وجود دارد که نیازهای شما را به‌طور کامل پوشش دهد، یا اینکه نیاز به ساخت سامانه اختصاصی یا ترکیبی است.")
    
    add_heading_2(doc, "۲.۱ نرم‌افزارهای تخصصی مدیریت دفاتر حسابداری")
    add_body(doc, "این نرم‌افزارها به‌طور خاص برای دفاتر حسابداری، مالیاتی و حسابرسی طراحی شده‌اند. مزیت اصلی آن‌ها درک بومی از گردش کار حسابداری، امکانات تخصیص مشتری، و قالب‌های آماده برای کارهای تکرارشونده ماهانه است. با این حال، اکثر آن‌ها برای بازارهای غربی (به‌ویژه ایالات متحده و بریتانیا) طراحی شده‌اند و از قواعد مالیاتی و حسابداری ایران پشتیبانی نمی‌کنند. این موضوع به‌تنهایی باعث می‌شود استفاده از آن‌ها به‌عنوان هسته اصلی سامانه شما با چالش جدی روبه‌رو شود، اما می‌توانند به‌عنوان منبع الهام برای طراحی گردش کار و به‌عنوان لایه مدیریت تسک در معماری ترکیبی مورد استفاده قرار گیرند.")
    
    add_heading_3(doc, "Karbon")
    add_body(doc, "Karbon یکی از شناخته‌شده‌ترین نرم‌افزارهای مدیریت دفاتر حسابداری است که بر گردش کار Kanban، یکپارچگی ایمیل، و قالب‌های آماده برای فرایندهای تکراری حسابداری تمرکز دارد. این نرم‌افزار برای دفاتر با ۵ تا ۳۰ نفر ایده‌آل است و دید مدیریتی خوبی از وضعیت کارهای هر کارمند و هر مشتری فراهم می‌کند. نقطه قوت اصلی Karbon این است که ایمیل‌های مرتبط با هر مشتری به‌طور خودکار به کارهای آن مشتری متصل می‌شوند، که برای ارتباطات دفتر با ۵۰ شرکت بسیار کاربردی است. با این حال، Karbon قابلیت آپلود فایل اکسل با اعتبارسنجی هوشمند، کنترل تکراری شماره سند، و تطبیق بازه تاریخی با دیتابیس حسابداری را به‌صورت آماده ندارد. این نرم‌افزار برای مدیریت تسک ایده‌آل است اما برای کنترل کیفیت اسناد حسابداری باید با ماژول اختصاصی تکمیل شود. قیمت Karbon بر اساس کاربر محاسبه می‌شود و برای تیم ۵ نفره حدود ۵۹ تا ۸۹ دلار به ازای هر کاربر در ماه است که برای دفتر شما قابل تحمل است، اما چالش پشتیبانی فارسی و عدم اتصال به نرم‌افزارهای ایرانی پاشنه آشیل آن محسوب می‌شود.")
    
    add_heading_3(doc, "Canopy")
    add_body(doc, "Canopy در رتبه‌بندی G2 در سال ۲۰۲۶ به‌عنوان بهترین نرم‌افزار مدیریت دفاتر مالیاتی و حسابداری شناخته شده است. این نرم‌افزار با قابلیت‌های هوش مصنوعی مانند Smart Intake، Smart Prep و Smart Tax Delivery، یکپارچگی عمیق با IRS (سازمان مالیاتی آمریکا)، و پورتال مشتری با اپلیکیشن موبایل، یک سامانه همه‌جانبه است. Canopy برای دفاتر چندخدماتی که می‌خواهند از مهاجرت بین ابزارهای مختلف دوری کنند، ایده‌آل است. اما برای دفتر شما در ایران، Canopy عملاً قابل استفاده نیست، زیرا تمام قابلیت‌های هوش مصنوعی آن بر اساس قواعد مالیاتی آمریکا طراحی شده و یکپارچگی با نرم‌افزارهای حسابداری ایرانی را پشتیبانی نمی‌کند. با این حال، مطالعه معماری و گردش کار Canopy می‌تواند به‌عنوان منبع الهام برای طراحی سامانه اختصاصی شما مفید باشد.")
    
    add_heading_3(doc, "TaxDome")
    add_body(doc, "TaxDome با بیش از ۱۵٬۰۰۰ دفتر کاربر و ۳ میلیون مشتری، یکی از بزرگترین پلتفرم‌های مدیریت دفاتر حسابداری است. این نرم‌افزار شامل خط لوله گردش کار، CRM، پورتال مشتری، مدیریت اسناد، و صورت‌حساب است. سه پلن اصلی آن با قیمت ۵۸، ۷۵ و ۹۲ دلار به ازای هر کاربر در ماه ارائه می‌شود. TaxDome برای دفاتر کوچک و متوسط که می‌خواهند به‌سرعت راه‌اندازی شوند، گزینه مناسبی است. مزیت آن نسبت به Karbon، قیمت پایین‌تر و داشتن پورتال مشتری است. اما مانند Canopy، برای ایران مناسب نیست، زیرا یکپارچگی‌های آن با QuickBooks Online و IRS است و هیچ رابط برنامه‌نویسی برای نرم‌افزارهای ایرانی ارائه نمی‌دهد.")
    
    add_heading_3(doc, "Financial Cents، Pixie و Jetpack Workflow")
    add_body(doc, "این سه نرم‌افزار برای دفاتر کوچک‌تر (۱ تا ۵ نفر) طراحی شده‌اند و قیمت پایین‌تری دارند. Financial Cents با تمرکز بر کارهای تکرارشونده حسابداری، تعیین مسئول و مهلت، و گزارش وضعیت، یک نقطه شروع ساده و شهودی است. Pixie برای دفاتر کوچک و متوسط با تمرکز بر گردش کار، وظایف تکرارشونده، مدیریت مشتری و یادآوری‌ها کار می‌کند. Jetpack Workflow بر وظایف زمان‌بندی‌شده و کارهای تکرارشونده حسابداری تمرکز دارد. هر سه نرم‌افزار قابلیت‌های پایه‌ای مدیریت تسک را دارند اما هیچ‌کدام موتور کنترل هوشمند فایل اکسل و اتصال به چند دیتابیس را پشتیبانی نمی‌کنند. برای دفتر شما، این نرم‌افزارها به‌تنهایی پاسخ‌گو نیستند اما اگر بخواهید از یک ابزار آماده به‌عنوان لایه مدیریت تسک استفاده کنید، Financial Cents یا Pixie گزینه‌های منطقی‌تری هستند زیرا ساده‌تر و ارزان‌تر از Karbon هستند.")
    
    add_heading_2(doc, "۲.۲ نرم‌افزارهای عمومی مدیریت پروژه")
    add_body(doc, "نرم‌افزارهای عمومی مانند Trello، Asana، Monday.com، ClickUp و Smartsheet نیز برای مدیریت تسک‌های دفتر حسابداری قابل استفاده هستند. این ابزارها انعطاف‌پذیر، ارزان و دارای رابط کاربری قوی هستند. اما همه آن‌ها یک ضعف اساسی دارند: هیچ درک بومی از گردش کار حسابداری ندارند. یعنی شما باید قالب‌ها، وضعیت‌ها و گردش کار را از صفر بسازید. این کار برای دفتر شما زمان‌بر است و نیاز به تخصص پیکربندی دارد. همچنین این ابزارها هیچ پورتال مشتری، مدیریت اسناد حسابداری یا قواعد مالیاتی ندارند. در نهایت، هیچ‌کدام اتصال به دیتابیس نرم‌افزارهای حسابداری ایرانی را پشتیبانی نمی‌کنند.")
    
    add_heading_2(doc, "۲.۳ نرم‌افزارهای ایرانی برای حضور و غیاب")
    add_body(doc, "در حوزه منابع انسانی، نرم‌افزارهای ایرانی مانند رادیکال (محصول فراویژن) و مگاپرداز برای مدیریت پرسنلی، مرخصی، حضور و غیاب، و کارتابل درخواست‌های پرسنلی قابل بررسی هستند. رادیکال با داشبورد مدیریتی و گزارش‌گیری از پرسنل، یک گزینه بالغ برای بخش HR سامانه شماست. مگاپرداز نیز کارتابل تأیید درخواست‌های پرسنلی و داشبوردهای منابع انسانی را پشتیبانی می‌کند. اگر ابزار مدیریت تسک انتخابی شما قابلیت‌های حضور و غیاب کافی نداشته باشد، می‌توانید یکی از این نرم‌افزارها را به‌عنوان مکمل به کار بگیرید. اما توجه داشته باشید که این نرم‌افزارها نیز موتور کنترل اسناد حسابداری ندارند و باید با ماژول اختصاصی شما یکپارچه شوند.")
    
    add_heading_2(doc, "۲.۴ ماتریس مقایسه نهایی")
    add_body(doc, "جدول زیر تمام ابزارهای بررسی‌شده را بر اساس معیارهای کلیدی شما مقایسه می‌کند. علامت ✓ نشان‌دهنده پشتیبانی کامل، علامت ◐ نشان‌دهنده پشتیبانی جزئی یا نیاز به سفارشی‌سازی، و علامت ✗ نشان‌دهنده عدم پشتیبانی است. ستون «سامانه پیشنهادی» معماری ترکیبی پیشنهادی ما را نشان می‌دهد که در فصل‌های بعدی به‌طور کامل تشریح می‌شود.")
    
    matrix_data = [
        ["قابلیت", "Karbon", "Canopy", "TaxDome", "Fin.Cents", "Pixie", "HR ایرانی", "ترکیبی"],
        ["تخصیص تسک و مهلت", "✓", "✓", "✓", "✓", "✓", "✗", "✓"],
        ["وظایف تکرارشونده هر شرکت", "✓", "✓", "✓", "✓", "✓", "✗", "✓"],
        ["ثبت گزارش کار و پیوست فایل", "✓", "✓", "✓", "✓", "✓", "✗", "✓"],
        ["کنترل تکراری شماره سند", "✗", "✗", "✗", "✗", "✗", "✗", "✓"],
        ["تطبیق بازه تاریخی با فایل", "✗", "✗", "✗", "✗", "✗", "✗", "✓"],
        ["اتصال به دیتابیس متفاوت", "✗", "✗", "✗", "✗", "✗", "◐", "✓"],
        ["حضور و غیاب و مرخصی", "✗", "✗", "✗", "✗", "✗", "✓", "✓"],
        ["ارجاع بخشی از تسک به همکار", "✓", "✓", "◐", "✓", "✓", "✗", "✓"],
        ["لاگ فعالیت غیرقابل ویرایش", "◐", "◐", "◐", "✗", "✗", "✗", "✓"],
        ["گزارش مدیریتی سفارشی", "◐", "✓", "✗", "✗", "✗", "✓", "✓"],
        ["پشتیبانی فارسی و قواعد ایران", "✗", "✗", "✗", "✗", "✗", "✓", "✓"],
        ["قیمت برای ۵ کاربر ($/ماه)", "۳۰۰-۴۵۰", "تماس", "۳۰۰-۴۶۰", "۲۰۰", "۱۰۰", "۵۰-۲۰۰", "توسعه+۵۰"],
        ["مناسب برای دفتر شما (/۱۰)", "۶", "۳", "۵", "۶", "۶", "۴", "۹"],
    ]
    add_table_styled(doc, matrix_data, col_widths_cm=[4.2, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6])
    
    add_callout(doc, "نتیجه: هیچ نرم‌افزار آماده‌ای در بازار جهانی یا ایرانی، تمام نیازهای شما را به‌صورت یکپارچه پوشش نمی‌دهد. دو قابلیت بحرانی شما - موتور کنترل هوشمند اسناد اکسل و اتصال به دیتابیس‌های متنوع نرم‌افزارهای ایرانی - در هیچ محصول آماده‌ای وجود ندارد. این نتیجه به‌طور طبیعی به سمت یک راهکار ترکیبی (هیبرید) می‌رود.", 'warn')
    
    add_page_break(doc)
    
    # ============ CHAPTER 3 ============
    add_heading_1(doc, "فصل ۳: تحلیل خرید یا ساخت (Build vs Buy)")
    
    add_body(doc, "تصمیم خرید یا ساخت یکی از مهم‌ترین انتخاب‌های راهبردی در این پروژه است. این تصمیم نباید صرفاً بر اساس هزینه اولیه گرفته شود، بلکه باید کل هزینه مالکیت (TCO) در یک دوره سه‌ساله، انعطاف‌پذیری، کنترل داده، و تطابق با نیازهای خاص شما را در نظر بگیرد. در این فصل، سه گزینه اصلی بررسی می‌شود: خرید کامل، ساخت کامل، و راهکار ترکیبی (هیبرید).")
    
    add_heading_2(doc, "۳.۱ گزینه اول: خرید کامل (Buy)")
    add_body(doc, "این گزینه به معنی خرید یک نرم‌افزار آماده مانند Karbon یا TaxDome به‌عنوان هسته اصلی سامانه است. مزیت اصلی این مسیر، سرعت راه‌اندازی (۲ تا ۴ هفته)، رابط کاربری بالغ، و عدم نیاز به تیم توسعه داخلی است. شما فقط کاربران را تعریف می‌کنید، شرکت‌ها را وارد می‌کنید، و قالب‌های تسک تکرارشونده را پیکربندی می‌کنید. اما این مسیر چند نقطه ضعف اساسی دارد. اول، هزینه ماهانه برای ۵ کاربر بین ۳۰۰ تا ۴۵۰ دلار است که در یک دوره سه‌ساله به ۱۰٬۸۰۰ تا ۱۶٬۲۰۰ دلار می‌رسد. دوم، هیچ‌کدام از این نرم‌افزارها قواعد فارسی، تقویم شمسی، یا یکپارچگی با نرم‌افزارهای حسابداری ایرانی را پشتیبانی نمی‌کنند. سوم، و مهم‌تر از همه، موتور کنترل هوشمند اسناد اکسل و تطبیق با دیتابیس‌های متفاوت را ندارند. در نتیجه، شما باید برای راستی‌آزمایی کار هر کارمند همچنان به روش‌های دستی متوسل شوید که عملاً هدف اصلی پروژه را بی‌اثر می‌کند.")
    
    add_heading_2(doc, "۳.۲ گزینه دوم: ساخت کامل (Build)")
    add_body(doc, "این گزینه به معنی ساخت یک سامانه اختصاصی از صفر با پشته فنی انتخابی (مثلاً Next.js + Python + PostgreSQL) است. مزیت اصلی، کنترل کامل بر هر جزء سامانه، انعطاف‌پذیری بالا، عدم پرداخت هزینه ماهانه ابزار، و تطابق کامل با نیازهای خاص شما است. اما ریسک‌های جدی نیز دارد. اول، زمان توسعه اولیه حداقل ۳ تا ۶ ماه است که در این مدت دفتر شما همچنان با روش‌های فعلی کار می‌کند. دوم، هزینه توسعه در صورت برون‌سپاری به یک تیم ایرانی بین ۱۵۰ تا ۳۰۰ میلیون تومان برای نسخه اولیه (MVP) است. سوم، نگهداری و توسعه مستمر سامانه نیاز به تیم فنی داخلی یا قرارداد پشتیبانی دارد. چهارم، تکرار چرخ‌های قبلی صنعت - شما قابلیت‌هایی را از صفر می‌سازید که در Karbon یا TaxDome قبلاً توسعه داده شده‌اند. این تکرار، انرژی و زمانی را که باید صرف قابلیت‌های متمایزکننده شما (موتور کنترل اسناد) شود، صرف کارهای تکراری می‌کند.")
    
    add_heading_2(doc, "۳.۳ گزینه سوم: راهکار ترکیبی (Hybrid) - توصیه شده")
    add_body(doc, "راهکار ترکیبی، ترکیب بهترین ویژگی‌های دو مسیر قبلی است. در این مدل، شما از یک نرم‌افزار آماده (یا نسخه سبک توسعه‌داده‌شده) به‌عنوان لایه مدیریت تسک و کارتابل استفاده می‌کنید، و یک ماژول اختصاصی به‌عنوان «موتور کنترل اسناد حسابداری» می‌سازید که فایل‌های اکسل کارمندان را دریافت، اعتبارسنجی، و با دیتابیس‌های متنوع شرکت‌ها راستی‌آزمایی می‌کند. این دو ماژول از طریق API با هم یکپارچه می‌شوند. به این ترتیب، شما از قابلیت‌های بالغ مدیریت تسک ابزار آماده بهره می‌برید و در عین حال قابلیت‌های متمایزکننده شما (کنترل هوشمند اسناد) به‌صورت اختصاصی ساخته می‌شوند. این مسیر بهترین تعادل بین زمان، هزینه و قابلیت را ارائه می‌دهد.")
    
    add_body(doc, "در عمل، در معماری پیشنهادی ما حتی از یک ابزار آماده خارجی هم صرف‌نظر می‌شود و لایه مدیریت تسک نیز به‌صورت سبک و اختصاصی با Next.js ساخته می‌شود. دلیل این انتخاب این است که ابزارهای آماده خارجی با چالش پشتیبانی فارسی، تقویم شمسی، و یکپارچگی با موتور کنترل اسناد روبه‌رو هستند. ساخت یک پنل سبک اختصاصی با Next.js تنها ۳ تا ۴ هفته زمان می‌برد و کنترل کامل بر تجربه کاربری، یکپارچگی، و توسعه آینده را فراهم می‌کند.")
    
    add_heading_2(doc, "۳.۴ ماتریس مقایسه‌ای سه گزینه")
    add_body(doc, "جدول زیر سه گزینه را بر اساس هفت معیار کلیدی مقایسه می‌کند. اعداد برآوردی و بر اساس شرایط دفتر ۵۰ شرکت/۵ کارمند و بازار ایران است.")
    
    bvb_data = [
        ["معیار", "خرید کامل", "ساخت کامل", "راهکار ترکیبی"],
        ["هزینه اولیه (تومان)", "نزدیک صفر", "۱۵۰-۳۰۰ میلیون", "۸۰-۱۵۰ میلیون"],
        ["هزینه ماهانه (۳ سال)", "۱۰٬۸۰۰-۱۶٬۲۰۰$", "۵۰$/ماه سرور", "۵۰$/ماه سرور + پشتیبانی"],
        ["زمان راه‌اندازی MVP", "۲-۴ هفته", "۳-۶ ماه", "۸-۱۲ هفته"],
        ["پشتیبانی فارسی و شمسی", "✗", "✓", "✓"],
        ["کنترل هوشمند اسناد", "✗", "✓", "✓"],
        ["اتصال به دیتابیس ایرانی", "✗", "✓", "✓"],
        ["انعطاف‌پذیری توسعه", "محدود به API", "کامل", "کامل"],
        ["ریسک پروژه", "پایین (کارکرد ناقص)", "بالا", "متوسط"],
        ["بازگشت سرمایه ۳ ساله", "منفی", "مثبت", "مثبت قوی"],
    ]
    add_table_styled(doc, bvb_data, col_widths_cm=[5, 3.5, 3.5, 4.5])
    
    add_callout(doc, "توصیه نهایی: راهکار ترکیبی با ساخت لایه مدیریت تسک اختصاصی به‌صورت سبک و موتور کنترل اسناد اختصاصی به‌صورت کامل، بهترین تعادل بین زمان، هزینه و کارکرد را ارائه می‌دهد. کل هزینه توسعه MVP حدود ۸۰ تا ۱۵۰ میلیون تومان و زمان ۸ تا ۱۲ هفته است.", 'success')
    
    add_page_break(doc)
    
    # ============ CHAPTER 4 ============
    add_heading_1(doc, "فصل ۴: معماری کلی سامانه پیشنهادی")
    
    add_body(doc, "معماری پیشنهادی سامانه بر اساس اصل جداسازی مسئولیت‌ها (Separation of Concerns) و الگوی Adapter طراحی شده است. هدف این است که هر لایه مسئولیت مشخصی داشته باشد، بدون دانش از جزئیات لایه‌های دیگر کار کند، و بتواند به‌صورت مستقل توسعه و تست شود. این معماری در طول زمان به شما اجازه می‌دهد شرکت‌های جدید و نرم‌افزارهای حسابداری جدید را بدون تغییر در هسته سامانه اضافه کنید.")
    
    add_heading_2(doc, "۴.۱ لایه‌های معماری")
    add_body(doc, "سامانه از پنج لایه منطقی تشکیل شده است. هر لایه یک قرارداد (Contract) مشخص با لایه‌های مجاور دارد. این قراردادها به‌صورت رابط‌های برنامه‌نویسی (API) و مدل داده استاندارد پیاده‌سازی می‌شوند. در ادامه هر لایه به‌طور کامل توضیح داده می‌شود.")
    
    add_heading_3(doc, "لایه ۱: پنل وب و مدیریت کاربران")
    add_body(doc, "این لایه رابط کاربری سامانه است که توسط مدیر، مدیرعامل، کارکنان و مسئول کنترل استفاده می‌شود. این پنل با Next.js و React ساخته می‌شود و شامل صفحه‌های داشبورد، مدیریت تسک، گزارش کار، آپلود فایل، درخواست مرخصی، و گزارش‌های مدیریتی است. پشتیبانی از زبان فارسی، راست‌چین (RTL)، تقویم شمسی، و تم تاریک/روشن از ویژگی‌های این لایه است. احراز هویت با JWT یا Session و کنترل دسترسی مبتنی بر نقش (RBAC) پیاده‌سازی می‌شود.")
    
    add_heading_3(doc, "لایه ۲: موتور گردش کار و مدیریت تسک")
    add_body(doc, "این لایه مسئولیت مدیریت چرخه حیات تسک‌ها را بر عهده دارد. هر تسک شامل شرکت، نوع فعالیت، مسئول اصلی، همکاران، تاریخ شروع، مهلت، چک‌لیست مراحل، پیشرفت، فایل‌های پیوست و وضعیت است. وضعیت تسک می‌تواند یکی از مقادیر «تازه، در حال انجام، ارجاع‌شده به همکار، در انتظار کنترل، نیازمند اصلاح، تأیید شده، رد شده» باشد. این لایه همچنین مسئولیت ثبت گزارش کار کارمند، ارجاع بخشی از تسک به همکار، و ارسال اعلان‌ها است.")
    
    add_heading_3(doc, "لایه ۳: موتور کنترل هوشمند فایل اکسل")
    add_body(doc, "این لایه قلب متمایزکننده سامانه شماست. هر زمان که کارمندی فایل اکسل اسناد را بارگذاری می‌کند، این لایه فعال می‌شود. ابتدا فایل را از نظر قالب و ساختار ستون‌ها اعتبارسنجی می‌کند، سپس ردیف‌های تکراری را در فایل و میان گزارش‌های قبلی شناسایی می‌کند، شماره اسناد را کنترل می‌کند، بازه‌های تاریخی را محاسبه و با ادعای کارمند مقایسه می‌کند، و در نهایت اسناد فایل را با اسناد واقعی دیتابیس شرکت راستی‌آزمایی می‌کند. خروجی این لایه یک گزارش کنترل ساختاریافته است که به مدیر نمایش داده می‌شود.")
    
    add_heading_3(doc, "لایه ۴: لایه استانداردسازی داده حسابداری")
    add_body(doc, "این لایه یک قرارداد داده مشترک برای تمام نرم‌افزارهای حسابداری است. صرف‌نظر از اینکه اسناد از SQL Server، Excel یا API خوانده می‌شوند، خروجی همیشه در قالب مدل داده استاندارد واحد است. این قرارداد شامل فیلدهای شناسه شرکت، شناسه دیتابیس مبدأ، شناسه یکتای سند، شماره سند، تاریخ سند، ردیف سند، کد حساب (کل/معین/تفصیل)، شرح، بدهکار و بستانکار است. به این ترتیب، منطق کنترل اسناد فقط یک بار نوشته می‌شود و با تمام نرم‌افزارهای حسابداری کار می‌کند.")
    
    add_heading_3(doc, "لایه ۵: لایه اتصال به دیتابیس‌ها (Adapter Layer)")
    add_body(doc, "این لایه شامل مجموعه‌ای از Adapter‌ها است که هر کدام برای یک نوع دیتابیس یا نرم‌افزار حسابداری طراحی شده‌اند. به عنوان مثال، یک Adapter برای SQL Server نرم‌افزار همکاران، یک Adapter برای SQL Server سپیدار، یک Adapter برای فایل‌های Excel، و یک Adapter برای API یک نرم‌افزار اختصاصی. هر Adapter اطلاعات خام را از منبع می‌خواند و آن را به مدل داده استاندارد تبدیل می‌کند. تمام Adapter‌ها یک رابط واحد (interface) را پیاده‌سازی می‌کنند، به این ترتیب لایه بالاتر (کنترل اسناد) نیازی به دانستن جزئیات هر نرم‌افزار ندارد.")
    
    add_heading_2(doc, "۴.۲ نمودار معماری")
    add_body(doc, "نمودار زیر معماری لایه‌ای سامانه و جریان داده بین لایه‌ها را نشان می‌دهد. هر بلوک یک لایه منطقی است و پیکان‌ها نشان‌دهنده جهت جریان داده و کنترل است.")
    
    arch_data = [
        ["پنل وب (مدیر، مدیرعامل، کارکنان)"],
        ["لایه ۲: موتور گردش کار و مدیریت تسک"],
        ["لایه ۳: موتور کنترل هوشمند فایل اکسل"],
        ["لایه ۴: استانداردسازی داده حسابداری"],
        ["لایه ۵: Adapter SQL Server | Adapter Excel | Adapter API"],
        ["دیتابیس شرکت A | دیتابیس شرکت B | فایل Excel شرکت C"],
    ]
    add_table_styled(doc, arch_data, col_widths_cm=[17])
    
    add_heading_2(doc, "۴.۳ مدل داده استاندارد")
    add_body(doc, "مدل داده استاندارد، قلب لایه ۴ است. تمام Adapter‌ها باید اطلاعات خام خود را به این مدل تبدیل کنند. جدول زیر فیلدهای این مدل را توضیح می‌دهد.")
    
    model_data = [
        ["فیلد استاندارد", "نوع", "الزامی", "توضیح"],
        ["company_id", "UUID", "بله", "شناسه یکتای شرکت در سامانه شما"],
        ["source_database_id", "UUID", "بله", "شناسه دیتابیس/نرم‌افزار مبدأ"],
        ["document_id", "String", "بله", "شناسه یکتای سند در سیستم مبدأ"],
        ["document_number", "String", "بله", "شماره سند (ممکن است تکراری بین ردیف‌های یک سند باشد)"],
        ["document_date", "Date (شمسی)", "بله", "تاریخ سند به فرمت YYYY/MM/DD شمسی"],
        ["row_number", "Integer", "بله", "شماره ردیف داخل سند"],
        ["account_code_kol", "String", "بله", "کد حساب کل"],
        ["account_code_moin", "String", "بله", "کد حساب معین"],
        ["account_code_tafsil", "String", "خیر", "کد حساب تفصیل (در صورت پشتیبانی)"],
        ["description", "Text", "خیر", "شرح سند"],
        ["debit", "Decimal(18,2)", "بله", "مبلغ بدهکار"],
        ["credit", "Decimal(18,2)", "بله", "مبلغ بستانکار"],
        ["last_modified_at", "Timestamp", "خیر", "زمان آخرین تغییر در مبدأ"],
        ["source_metadata", "JSON", "خیر", "متادیتای اختصاصی نرم‌افزار مبدأ"],
    ]
    add_table_styled(doc, model_data, col_widths_cm=[4.5, 3, 2, 7.5])
    
    add_callout(doc, "اصل کلیدی: منطق کنترل اسناد (لایه ۳) فقط با مدل داده استاندارد کار می‌کند. این یعنی اگر فردا نرم‌افزار حسابداری جدیدی اضافه شود، فقط باید یک Adapter جدید برای لایه ۵ بنویسید، بدون آنکه هیچ تغییری در لایه‌های ۲، ۳ و ۴ لازم باشد.", 'info')
    
    add_page_break(doc)
    
    # ============ CHAPTER 5 ============
    add_heading_1(doc, "فصل ۵: معماری چندپایگاه‌داده با Adapter Pattern")
    
    add_body(doc, "در دفتر شما، شرکت‌ها از نرم‌افزارهای متنوعی استفاده می‌کنند و دیتابیس‌های آن‌ها از انواع مختلفی (SQL Server، Excel، فایل‌های محلی، API) تشکیل شده است. این تنوع اگر به‌درستی مدیریت نشود، باعث پیچیدگی شدید در سامانه می‌شود. راهکار ما الگوی Adapter است: یک رابط واحد برای تمام منابع داده، و پیاده‌سازی‌های جداگانه برای هر نوع منبع. در این فصل، نحوه طراحی و پیاده‌سازی این الگو به‌طور کامل تشریح می‌شود.")
    
    add_heading_2(doc, "۵.۱ رابط مشترک Adapter")
    add_body(doc, "هر Adapter باید یک رابط (interface) واحد را پیاده‌سازی کند. این رابط چهار عملیات اصلی را تعریف می‌کند: اتصال، خواندن اسناد در یک بازه زمانی، خواندن یک سند با شناسه، و تست اتصال. به این ترتیب لایه کنترل اسناد با تمام Adapter‌ها به یک شکل کار می‌کند. در زبان Python، این رابط با استفاده از کتابخانه abc (Abstract Base Class) تعریف می‌شود.")
    
    add_heading_2(doc, "۵.۲ انواع Adapter مورد نیاز")
    add_body(doc, "بر اساس تنوع دیتابیس‌های شما، حداقل چهار نوع Adapter نیاز دارید. در ادامه هر یک به‌طور خلاصه توضیح داده می‌شود.")
    
    add_heading_3(doc, "Adapter ۱: SQL Server (همکاران سیستم)")
    add_body(doc, "نرم‌افزار همکاران سیستم از SQL Server استفاده می‌کند و دیتابیس آن ساختار شناخته‌شده‌ای دارد. این Adapter با استفاده از کتابخانه pyodbc یا SQLAlchemy به دیتابیس متصل می‌شود، جدول‌های اسناد (معمولاً با نام‌هایی مانند DocHeader و DocDetail) را کوئری می‌کند، و خروجی را به مدل استاندارد تبدیل می‌کند. یک چالش مهم این است که ساختار دقیق دیتابیس همکاران در نسخه‌های مختلف متفاوت است؛ بنابراین Adapter باید نسخه نرم‌افزار را تشخیص دهد و کوئری مناسب را اجرا کند. نکته امنیتی: اتصال باید فقط خواندنی (Read-Only) باشد. کاربر SQL که به Adapter داده می‌شود باید فقط دسترسی SELECT داشته باشد و دسترسی INSERT، UPDATE یا DELETE نداشته باشد.")
    
    add_heading_3(doc, "Adapter ۲: SQL Server (سپیدار)")
    add_body(doc, "نرم‌افزار سپیدار نیز از SQL Server استفاده می‌کند اما ساختار دیتابیس آن با همکاران متفاوت است. این Adapter مشابه Adapter همکاران پیاده‌سازی می‌شود، اما کوئری‌ها و نگاشت فیلدها متفاوت است. در عمل، کلاس پایه یکسانی دارند اما کوئری‌های SQL متفاوت اجرا می‌کنند. مهم: سپیدار در نسخه‌های اخیر از یک دیتابیس مرکزی برای چند شرکت استفاده می‌کند و شناسایی شرکت داخل کوئری باید با فیلتر روی فیلد CompanyID انجام شود.")
    
    add_heading_3(doc, "Adapter ۳: Excel/CSV Files")
    add_body(doc, "برای شرکت‌هایی که از نرم‌افزار حسابداری با خروجی Excel یا CSV استفاده می‌کنند، این Adapter فایل‌ها را از مسیر تعیین‌شده (یا از طریق آپلود خودکار) می‌خواند. این Adapter با کتابخانه pandas یا openpyxl کار می‌کند و باید با چالش‌های فرمت تاریخ شمسی در اکسل، تنوع کدگذاری (UTF-8، Windows-1256)، و وجود ستون‌های اضافی کنار بیاید. مزیت این Adapter این است که فایل‌های اکسل اغلب در مسیرهای شبکه‌ای ذخیره می‌شوند و می‌توان با یک سرویس زمان‌بندی‌شده آن‌ها را به‌صورت خودکار خواند.")
    
    add_heading_3(doc, "Adapter ۴: REST API")
    add_body(doc, "برای نرم‌افزارهای حسابداری که API ارائه می‌دهند (مانند برخی نرم‌افزارهای ابری ایرانی)، این Adapter با درخواست‌های HTTP به API متصل می‌شود. این Adapter معمولاً احراز هویت با توکن (Bearer Token یا API Key) نیاز دارد. مزیت این روش این است که از تغییرات ساختار دیتابیس داخلی نرم‌افزار مستقل است؛ تا زمانی که API پایدار بماند، Adapter بدون تغییر کار می‌کند.")
    
    add_heading_2(doc, "۵.۳ مدیریت تنظیمات اتصال")
    add_body(doc, "هر شرکت در دفتر شما نیاز به تنظیمات اتصال مستقل دارد. این تنظیمات شامل نوع Adapter، رشته اتصال (connection string)، نام دیتابیس، شناسه شرکت در نرم‌افزار مبدأ، و سایر پارامترها است. این تنظیمات در یک جدول پیکربندی در دیتابیس مرکزی سامانه ذخیره می‌شود و رمزگذاری می‌شود. وقتی کارمندی فایل اکسل شرکت A را بارگذاری می‌کند، سامانه به‌طور خودکار با استفاده از تنظیمات اتصال شرکت A، Adapter مناسب را فعال می‌کند، اسناد واقعی را می‌خواند، و با فایل اکسل مقایسه می‌کند.")
    
    settings_data = [
        ["فیلد", "توضیح"],
        ["company_id", "شناسه یکتای شرکت در سامانه"],
        ["adapter_type", "نوع Adapter: mssql_hamkaran | mssql_sepidar | excel | api"],
        ["connection_string", "رشته اتصال رمزگذاری‌شده"],
        ["source_company_id", "شناسه شرکت در نرم‌افزار مبدأ"],
        ["last_sync_at", "زمان آخرین همگام‌سازی موفق"],
        ["enabled", "وضعیت فعال/غیرفعال"],
        ["read_only_user", "آیا کاربر اتصال فقط خواندنی است؟"],
        ["features_cache_minutes", "مدت کش کردن اسناد (برای کاهش بار دیتابیس)"],
    ]
    add_table_styled(doc, settings_data, col_widths_cm=[4.5, 12.5])
    
    add_callout(doc, "هشدار امنیتی: اتصال به دیتابیس‌های حسابداری باید صرفاً Read-Only باشد. هیچ شرایطی نباید به سامانه اجازه دهد داده‌های حسابداری شرکت‌ها را تغییر دهد. این اصل، حفاظت از اطلاعات مالی مشتریان شما را تضمین می‌کند.", 'danger')
    
    add_page_break(doc)
    
    # ============ CHAPTER 6 ============
    add_heading_1(doc, "فصل ۶: الگوی اکسل اسناد حسابداری")
    
    add_body(doc, "فایل اکسلی که کارمندان بارگذاری می‌کنند، باید یک قالب استاندارد مشخص داشته باشد تا موتور کنترل بتواند به‌طور خودکار آن را پردازش کند. در این فصل، ساختار دقیق ستون‌ها، قواعد اعتبارسنجی هر ستون، و یک نمونه رکورد ارائه می‌شود. این قالب بر اساس استانداردهای رایج حسابداری ایران (ساختار کل/معین/تفصیل و تراز بدهکار/بستانکار) طراحی شده است.")
    
    add_heading_2(doc, "۶.۱ ساختار ستون‌ها")
    add_body(doc, "فایل اکسل باید شامل دقیقاً این ۹ ستون با این ترتیب باشد. ردیف اول فایل باید هدر (نام ستون‌ها) باشد و داده‌ها از ردیف دوم شروع شوند. سامانه در صورت مشاهده هرگونه انحراف از این قالب، فایل را رد می‌کند و دلیل را به کارمند گزارش می‌دهد.")
    
    columns_data = [
        ["شماره", "نام ستون", "نوع داده", "الزامی", "قواعد اعتبارسنجی"],
        ["۱", "ردیف", "عدد صحیح", "بله", "باید یکتا در داخل فایل باشد؛ از ۱ شروع و متوالی"],
        ["۲", "شماره سند", "متن/عدد", "بله", "می‌تواند تکراری باشد (چند ردیف یک سند)"],
        ["۳", "تاریخ سند", "تاریخ شمسی", "بله", "فرمت YYYY/MM/DD یا YY/MM/DD؛ معتبر و قابل تبدیل"],
        ["۴", "کد کل", "متن/عدد", "بله", "کد حساب کل؛ باید در طرح حساب شرکت وجود داشته باشد"],
        ["۵", "کد معین", "متن/عدد", "بله", "کد حساب معین؛ باید زیرمجموعه کد کل همان ردیف باشد"],
        ["۶", "کد تفصیل", "متن/عدد", "خیر", "کد تفصیل (در صورت پشتیبانی شرکت)"],
        ["۷", "شرح سند", "متن", "خیر", "توضیح ردیف سند؛ حداکثر ۵۰۰ کاراکتر"],
        ["۸", "بدهکار", "عدد اعشاری", "بله*", "مبلغ بدهکار؛ *دقیقاً یکی از بده یا بستان باید صفر باشد"],
        ["۹", "بستانکار", "عدد اعشاری", "بله*", "مبلغ بستانکار؛ *دقیقاً یکی از بده یا بستان باید صفر باشد"],
    ]
    add_table_styled(doc, columns_data, col_widths_cm=[1.2, 2.8, 2.4, 1.6, 9])
    
    add_heading_2(doc, "۶.۲ قواعد اعتبارسنجی هوشمند")
    add_body(doc, "سیستم در زمان بارگذاری فایل، چندین لایه اعتبارسنجی را به‌ترتیب اجرا می‌کند. اگر هر لایه با شکست روبه‌رو شود، پردازش متوقف می‌شود و خطای مربوطه گزارش می‌شود. این طراحی چندلایه باعث می‌شود خطاهای ساختاری قبل از خطاهای منطقی شناسایی شوند و گزارش‌های مفیدتری به کارمند ارائه شود.")
    
    add_heading_3(doc, "لایه ۱: اعتبارسنجی قالب")
    add_body(doc, "فایل باید یک فایل اکسل معتبر با پسوند .xlsx یا .xls باشد. صرف تغییر پسوند یک فایل غیر اکسل به .xlsx قابل قبول نیست؛ سامانه با خواندن سرآیند فایل (magic bytes) نوع واقعی را تشخیص می‌دهد. سپس تعداد ستون‌ها و نام هدرها بررسی می‌شوند. اگر نام ستون‌ها با قالب استاندارد مطابقت نداشته باشد، سامانه سعی می‌کند با الگوریتم تطبیق فازی، نام‌های نزدیک را شناسایی و به کارمند پیشنهاد اصلاح دهد.")
    
    add_heading_3(doc, "لایه ۲: اعتبارسنجی نوع داده")
    add_body(doc, "هر ستون باید نوع داده مشخصی داشته باشد. ستون «ردیف» باید عدد صحیح مثبت باشد. ستون «تاریخ سند» باید یک تاریخ معتبر شمسی باشد. سامانه فرمت‌های مختلف تاریخ شمسی (۱۴۰۵/۰۷/۲۰، ۱۴۰۵-۰۷-۲۰، ۲۰/۰۷/۱۴۰۵) را تشخیص می‌دهد و آن‌ها را به یک فرمت استاندارد داخلی (ISO) تبدیل می‌کند. ستون‌های «بدهکار» و «بستانکار» باید عدد اعشاری نامنفی باشند.")
    
    add_heading_3(doc, "لایه ۳: اعتبارسنجی منطقی حسابداری")
    add_body(doc, "چند قاعده منطقی باید برقرار باشد. اول، در هر ردیف، دقیقاً یکی از بدهکار یا بستانکار باید صفر باشد. دوم، در هر سند، مجموع بدهکار باید با مجموع بستانکار برابر باشد (تراز سند). سوم، کد معین باید زیرمجموعه کد کل همان ردیف باشد. این قواعد منطقی باعث می‌شوند فایل‌های نادرست قبل از مقایسه با دیتابیس شناسایی شوند.")
    
    add_heading_3(doc, "لایه ۴: کنترل تکراری")
    add_body(doc, "این لایه تخصصی‌ترین بخش موتور کنترل است. تکراری بودن را در سه سطح بررسی می‌کند. سطح اول: ردیف‌های تکراری در داخل فایل. سطح دوم: ردیف‌های تکراری میان فایل فعلی و فایل‌های قبلی همان شرکت. سطح سوم: تشخیص اصلاح سند از تکراری واقعی - اگر سندی در فایل قبلی بارگذاری شده و در فایل جدید با همان شماره سند و تاریخ اما با مبالغ متفاوت ظاهر شود، این یک «اصلاح سند» است، نه تکراری. سامانه باید این دو حالت را از هم تشخیص دهد.")
    
    add_heading_3(doc, "لایه ۵: تطبیق با دیتابیس واقعی")
    add_body(doc, "پس از اعتبارسنجی داخلی فایل، سامانه با استفاده از Adapter مناسب، اسناد واقعی شرکت را در بازه تاریخی ادعایی کارمند از دیتابیس می‌خواند. سپس دو مجموعه اسناد را بر اساس یک کلید منطقی (ترکیب شماره سند + تاریخ + ردیف) مقایسه می‌کند. اسنادی که در فایل هستند اما در دیتابیس نیستند، به‌عنوان «اسناد ادعایی بدون پایه» شناسایی می‌شوند. اسنادی که در دیتابیس هستند اما در فایل نیستند، به‌عنوان «اسناد مفقود از فایل» شناسایی می‌شوند. اسنادی که در هر دو هستند اما با مبالغ متفاوت، به‌عنوان «مغایرت مقدار» شناسایی می‌شوند.")
    
    add_heading_2(doc, "۶.۳ نمونه فایل اکسل استاندارد")
    add_body(doc, "نمونه زیر سه ردیف فرضی از فایل اکسل یک شرکت را نشان می‌دهد. این نمونه صرفاً برای نمایش قالب است و اعداد واقعی نیستند.")
    
    sample_data = [
        ["ردیف", "شماره سند", "تاریخ", "کد کل", "کد معین", "تفصیل", "شرح سند", "بدهکار", "بستانکار"],
        ["۱", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۱", "۱۰۱", "۱۰۱۰۱", "فروش نقدی به شرکت الف", "۵٬۰۰۰٬۰۰۰", "۰"],
        ["۲", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۵", "۵۰۱", "۵۰۱۰۱", "دریافت نقدی", "۰", "۵٬۰۰۰٬۰۰۰"],
        ["۳", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۲", "۲۰۱", "۲۰۱۰۱", "خرید کالا", "۰", "۳٬۰۰۰٬۰۰۰"],
        ["۴", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۴", "۴۰۱", "۴۰۱۰۱", "پرداخت نقدی", "۳٬۰۰۰٬۰۰۰", "۰"],
    ]
    add_table_styled(doc, sample_data, col_widths_cm=[1, 1.5, 1.7, 1, 1, 1.2, 4.6, 2, 2])
    
    add_callout(doc, "نکته: در سند ۱۰۰۱ و ۱۰۰۲، مجموع بدهکار با مجموع بستانکار برابر است؛ یعنی تراز سند برقرار است. این یک ویژگی منطقی است که موتور کنترل به‌صورت خودکار بررسی می‌کند.", 'info')
    
    add_page_break(doc)
    
    # ============ CHAPTER 7 ============
    add_heading_1(doc, "فصل ۷: موتور کنترل هوشمند اسناد")
    
    add_body(doc, "موتور کنترل هوشمند اسناد، قلب متمایزکننده سامانه شماست. این موتور مسئولیت پردازش هر فایل اکسل بارگذاری‌شده را بر عهده دارد و خروجی آن یک گزارش کنترل ساختاریافته است که به مدیر نمایش داده می‌شود. در این فصل، ۹ مرحله کنترل، قواعد تشخیص اصلاح از تکرار، و نمونه گزارش مغایرت به‌طور کامل تشریح می‌شود.")
    
    add_heading_2(doc, "۷.۱ نه مرحله کنترل")
    add_body(doc, "هر بارگذاری فایل اکسل، موتور کنترل ۹ مرحله متوالی را روی آن اجرا می‌کند. این مراحل به‌صورت لایه‌ای طراحی شده‌اند: اگر یک مرحله با خطای مهره‌ای روبه‌رو شود، مراحل بعدی اجرا نمی‌شوند و خطا به کارمند گزارش می‌شود. اما اگر خطا قابل بازیابی باشد (مثلاً چند ردیف نامعتبر)، سامانه ادامه می‌دهد و در پایان تمام خطاها را در یک گزارش واحد ارائه می‌کند.")
    
    fa_nums = ['۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    steps = [
        "کنترل قالب و ساختار: بررسی نوع فایل، تعداد ستون‌ها، نام هدرها و تطبیق با الگو.",
        "شمارش ردیف‌ها: شمارش کل ردیف‌ها، ردیف‌های معتبر، ردیف‌های نامعتبر و ردیف‌های خالی.",
        "تشخیص بارگذاری مجدد: محاسبه هش فایل و مقایسه با فایل‌های قبلی همان شرکت.",
        "تشخیص ردیف‌های تکراری در فایل: شناسایی ردیف‌هایی که تمام فیلدهای آن‌ها یکسان است.",
        "کنترل شماره سند تکراری: تفکیک ردیف‌های متعلق به یک سند (مجاز) از تکرار واقعی سند.",
        "تطبیق بازه تاریخی ادعا با فایل: محاسبه حداقل و حداکثر تاریخ در فایل و مقایسه با ادعا.",
        "مقایسه اسناد فایل با دیتابیس شرکت: خواندن اسناد واقعی و مقایسه با فایل.",
        "شناسایی اسناد مفقود و خارج از بازه: اسنادی که در دیتابیس هستند اما در فایل نیستند.",
        "کنترل تراز بدهکار/بستانکار: محاسبه مجموع بدهکار و بستانکار هر سند و کنترل تراز.",
    ]
    for i, s in enumerate(steps):
        add_numbered(doc, s, fa_nums[i])
    
    add_heading_2(doc, "۷.۲ قواعد تشخیص اصلاح سند از تکرار")
    add_body(doc, "یکی از پیچیده‌ترین بخش‌های موتور کنترل، تشخیص اصلاح سند از تکرار واقعی است. این تشخیص بر اساس وضعیت سند در دیتابیس و فایل انجام می‌شود. در ادامه، پنج حالت اصلی و قاعده کنترل هر یک تشریح می‌شود.")
    
    rules_data = [
        ["حالت", "فایل قبلی", "فایل جدید", "دیتابیس", "تشخیص", "اقدام"],
        ["۱", "ندارد", "دارد", "دارد", "سند جدید", "تأیید"],
        ["۲", "دارد", "ندارد", "دارد", "حذف از گزارش", "اخطار"],
        ["۳", "دارد", "دارد (یکسان)", "دارد", "تکرار فایل", "خطا - رد فایل"],
        ["۴", "دارد", "دارد (متفاوت)", "دارد (مقادیر جدید)", "اصلاح سند", "تأیید با ثبت نسخه قبلی"],
        ["۵", "ندارد", "دارد", "ندارد", "سند بدون پایه", "خطا - ادعای بی‌اساس"],
    ]
    add_table_styled(doc, rules_data, col_widths_cm=[1.2, 2.2, 2.8, 2.5, 2.5, 3])
    
    add_callout(doc, "نکته فنی: تشخیص صحیح حالت ۴ (اصلاح سند) نیازمند آن است که نرم‌افزار حسابداری مبدأ شناسه پایدار برای سند داشته باشد. اگر نرم‌افزار این قابلیت را نداشته باشد، باید بر اساس ترکیب شماره سند + تاریخ سند شناسایی کرد که ممکن است در موارد نادر (تغییر تاریخ یک سند) منجر به تشخیص نادرست شود.", 'warn')
    
    add_heading_2(doc, "۷.۳ نمونه گزارش کنترل اسناد")
    add_body(doc, "نمونه زیر یک گزارش کنترل واقعی را برای یک فایل فرضی نشان می‌دهد. این گزارش به مدیر نمایش داده می‌شود و او می‌تواند آن را تأیید یا برای اصلاح به کارمند برگرداند. اعداد فرضی هستند.")
    
    summary_data = [
        ["شاخص", "مقدار", "وضعیت"],
        ["تعداد کل ردیف‌های فایل", "۱٬۲۵۲", "—"],
        ["تعداد ردیف‌های معتبر", "۱٬۲۴۰", "✓"],
        ["تعداد ردیف‌های نامعتبر", "۱۲", "✗"],
        ["تعداد اسناد یکتا", "۳۸۵", "✓"],
        ["تعداد ردیف‌های تکراری در فایل", "۰", "✓"],
        ["تعداد اسناد مفقود از دیتابیس در فایل", "۵", "✗"],
        ["تعداد اسناد ادعایی بدون پایه", "۲", "✗"],
        ["مغایرت بازه تاریخی", "۲ روز", "✗"],
        ["تراز بدهکار کل", "۴۵٬۲۳۰٬۰۰۰ تومان", "✓"],
        ["تراز بستانکار کل", "۴۵٬۲۳۰٬۰۰۰ تومان", "✓"],
        ["مغایرت مقدار در ردیف‌ها", "۳ مورد", "✗"],
        ["وضعیت کلی", "نیازمند بررسی مدیر", "⚠"],
    ]
    add_table_styled(doc, summary_data, col_widths_cm=[7, 5, 3])
    
    add_heading_3(doc, "جزئیات مغایرت‌ها (نمونه)")
    detail_data = [
        ["نوع مغایرت", "شماره سند", "تاریخ", "شرح", "اقدام پیشنهادی"],
        ["سند مفقود از فایل", "۱۰۳۲", "۱۴۰۵/۰۷/۱۰", "سند در دیتابیس است اما در فایل نیست", "بررسی با کارمند"],
        ["سند مفقود از فایل", "۱۰۵۸", "۱۴۰۵/۰۷/۱۵", "سند در دیتابیس است اما در فایل نیست", "بررسی با کارمند"],
        ["مغایرت مقدار", "۱۰۴۲", "۱۴۰۵/۰۷/۱۲", "فایل: ۳M / دیتابیس: ۳.۵M", "اصلاح فایل"],
        ["خارج از بازه", "۱۰۷۰", "۱۴۰۵/۰۷/۲۵", "خارج از بازه ادعایی (۰۱-۲۰)", "اصلاح بازه"],
    ]
    add_table_styled(doc, detail_data, col_widths_cm=[3.5, 1.8, 2.2, 6, 3.5])
    
    add_callout(doc, "طراحی کلیدی: سامانه نباید صرفاً یک پیام «فایل صحیح است» یا «فایل دارای خطاست» نشان دهد. هر بارگذاری باید یک گزارش کنترل مستقل تولید کند که شامل تمام مغایرت‌ها، ریشه‌یابی و اقدام پیشنهادی باشد. این شفافیت به مدیر اجازه می‌دهد تصمیم آگاهانه بگیرد.", 'info')
    
    add_page_break(doc)
    
    # ============ CHAPTER 8 ============
    add_heading_1(doc, "فصل ۸: چارچوب ارزیابی عملکرد پرسنل")
    
    add_body(doc, "ارزیابی عملکرد پنج کارمند شما نباید صرفاً بر اساس «تعداد تسک‌های بسته‌شده» باشد. این معیار ساده، انگیزه نادرستی ایجاد می‌کند: کارمند برای افزایش تعداد تسک‌ها، ممکن است کارهای کوچک و ساده را ترجیح دهد و از کارهای پیچیده و زمان‌بر شانه خالی کند. چارچوب پیشنهادی ما بر اساس پنج شاخص وزن‌دار است که کیفیت، تحویل به‌موقع، حجم/پیچیدگی، مستندات و همکاری را به‌صورت متوازن ارزیابی می‌کند.")
    
    add_heading_2(doc, "۸.۱ پنج شاخص کلیدی عملکرد (KPI)")
    
    kpi_data = [
        ["شاخص", "وزن", "تعریف", "روش اندازه‌گیری", "دامنه"],
        ["کیفیت و صحت کار تأییدشده", "۳۵٪", "نسبت تسک‌های تأییدشده به کل تسک‌ها با توجه به شدت مغایرت", "اتوماتیک + بازبینی مدیر", "۰-۱۰۰"],
        ["تحویل به‌موقع", "۲۵٪", "نسبت تسک‌های تحویلی در مهلت به کل تسک‌ها", "اتوماتیک از تاریخ تحویل", "۰-۱۰۰"],
        ["حجم کار نسبت به پیچیدگی", "۲۰٪", "حجم کار استانداردشده با ضریب پیچیدگی", "نیمه‌خودکار + تأیید مدیر", "۰-۱۰۰"],
        ["کامل بودن مستندات", "۱۰٪", "کیفیت فایل اکسل، گزارش کار، شرح و پیوست‌ها", "اتوماتیک + بازبینی مدیر", "۰-۱۰۰"],
        ["همکاری و ارجاع صحیح", "۱۰٪", "کیفیت ارجاع‌ها به همکاران و تحویل منظم", "ارزیابی کیفی ماهانه مدیر", "۰-۱۰۰"],
    ]
    add_table_styled(doc, kpi_data, col_widths_cm=[3.5, 1.2, 5, 4.3, 1.8])
    
    add_heading_2(doc, "۸.۲ دلیل وزن‌دهی به این شکل")
    add_body(doc, "وزن ۳۵٪ برای کیفیت بالاترین وزن را دارد زیرا در دفتر حسابداری، کیفیت کار با اعتبار دفتر و رضایت مشتریان رابطه مستقیم دارد. یک کار نادرست می‌تواند به زیان مالی شرکت و در نتیجه به دعوای حقوقی با دفتر منجر شود. وزن ۲۵٪ برای تحویل به‌موقع نشان‌دهنده اهمیت پایبندی به توافق با مشتری است. وزن ۲۰٪ برای حجم/پیچیدگی به این دلیل طراحی شده که کارمندی که کارهای پیچیده‌تر انجام می‌دهد، تشویق شود؛ اما بدون کیفیت، حجم به‌تنهایی کافی نیست. وزن ۱۰+۱۰٪ برای مستندات و همکاری نشان‌دهنده این است که این دو عامل اهمیت دارند اما نباید بر کیفیت غلبه کنند. این وزن‌دهی نقطه شروع است و باید پس از یک تا دو ماه داده واقعی، بر اساس مشاهدات شما بازتنظیم شود.")
    
    add_heading_2(doc, "۸.۳ نمونه کارت امتیاز ماهانه")
    add_body(doc, "نمونه زیر یک کارت امتیاز ماهانه فرضی برای یک کارمند را نشان می‌دهد. این کارت در پایان هر ماه به‌صورت اتوماتیک تولید و در داشبورد مدیر نمایش داده می‌شود.")
    
    scorecard_data = [
        ["شاخص", "امتیاز ماه", "وزن", "امتیاز وزن‌دار", "تغییر نسبت به قبل"],
        ["کیفیت کار", "۸۸", "۳۵٪", "۳۰٫۸", "+۵"],
        ["تحویل به‌موقع", "۹۲", "۲۵٪", "۲۳٫۰", "+۲"],
        ["حجم/پیچیدگی", "۸۵", "۲۰٪", "۱۷٫۰", "-۳"],
        ["مستندات", "۹۰", "۱۰٪", "۹٫۰", "۰"],
        ["همکاری", "۸۷", "۱۰٪", "۸٫۷", "+۱"],
        ["امتیاز کل ماه", "—", "۱۰۰٪", "۸۸٫۵", "+۳٫۲"],
        ["رتبه در دفتر", "—", "—", "۲ از ۵", "—"],
    ]
    add_table_styled(doc, scorecard_data, col_widths_cm=[4.5, 2.5, 2, 3, 4])
    
    add_heading_2(doc, "۸.۴ داشبورد روزانه مدیر")
    add_body(doc, "علاوه بر کارت امتیاز ماهانه، مدیر باید یک داشبورد روزانه داشته باشد که نگاهی فوری به وضعیت جاری دفتر ارائه دهد. این داشبورد باید در یک صفحه، مهم‌ترین اطلاعات را بدون نیاز به کلیک چندباره نمایش دهد.")
    
    dashboard_items = [
        "تسک‌های باز: تعداد کل، تفکیک به مسئول، تعداد عقب‌افتاده",
        "تسک‌های عقب‌افتاده: بر اساس مهلت، با هایلایت قرمز برای بیش از ۳ روز",
        "گزارش‌های تأییدشده امروز: تعداد، تفکیک به شرکت",
        "مغایرت‌های مهم نیازمند رسیدگی: فهرست با اولویت‌بندی",
        "درخواست‌های پرسنلی در انتظار تأیید: مرخصی، مساعده، درخواست به مدیرعامل",
        "فعالیت امروز کارکنان: ورود/خروج، تسک‌های شروع‌شده، گزارش‌های ارسالی",
        "نمودار پیشرفت ماهانه: مقایسه عملکرد پنج کارمند",
        "خلاصه هشدارها: تکراری‌های شناسایی‌شده، مغایرت‌های تکراری، فایل‌های رد‌شده",
    ]
    for it in dashboard_items:
        add_bullet(doc, it)
    
    add_callout(doc, "اصل طراحی داشبورد: کمتر، بهتر. مدیر نباید با اطلاعات جزئی غرق شود. داشبورد باید سؤال‌های اصلی را پاسخ دهد: «چه چیزی نیاز به توجه من دارد؟» و «وضعیت کلی چگونه است؟». جزئیات باید در گزارش‌های پایین‌دست قابل دسترسی باشند.", 'info')
    
    add_page_break(doc)
    
    # ============ CHAPTER 9 ============
    add_heading_1(doc, "فصل ۹: گردش کار تسک و ارجاع به همکار")
    
    add_body(doc, "مدل داده تسک و گردش کار آن باید به‌گونه‌ای طراحی شود که ارجاع بخشی از یک تسک به همکار، تأیید چندمرحله‌ای مدیر، و پیگیری پیشرفت واقعی به‌صورت شفاف انجام شود. در این فصل، مدل کامل تسک، چرخه وضعیت‌ها، و قواعد ارجاع به همکار تشریح می‌شود.")
    
    add_heading_2(doc, "۹.۱ مدل داده تسک")
    add_body(doc, "هر تسک شامل مجموعه‌ای از فیلدها است که در جدول زیر نشان داده شده است. این فیلدها به‌گونه‌ای طراحی شده‌اند که تمام اطلاعات لازم برای کنترل، ارزیابی و گزارش‌گیری را در خود نگه دارند.")
    
    task_data = [
        ["فیلد", "نوع", "توضیح"],
        ["task_id", "UUID", "شناسه یکتای تسک"],
        ["company_id", "UUID", "شرکت مربوط به تسک"],
        ["activity_type", "Enum", "نوع: ثبت اسناد/اصلاح/گزارش/مالیات/سایر"],
        ["title", "String", "عنوان کوتاه تسک"],
        ["description", "Text", "توضیح کامل"],
        ["assigned_to", "UUID", "کارمند مسئول اصلی"],
        ["collaborators", "Array<UUID>", "فهرست همکاران (در صورت ارجاع)"],
        ["date_start", "Date", "تاریخ شروع واقعی"],
        ["date_due", "Date", "مهلت انجام"],
        ["date_completed", "Date", "تاریخ تکمیل واقعی"],
        ["checklist", "Array<Item>", "چک‌لیست مراحل با وضعیت انجام/نادان"],
        ["progress_percent", "Integer 0-100", "درصد پیشرفت واقعی"],
        ["attached_files", "Array<File>", "فایل‌های پیوست (شامل اکسل)"],
        ["control_status", "Enum", "در انتظار/تأیید/رد/نیازمند اصلاح"],
        ["control_report_id", "UUID", "شناسه گزارش کنترل مرتبط"],
        ["approved_by", "UUID", "کاربری که تأیید کرده"],
        ["approved_at", "Timestamp", "زمان تأیید"],
        ["change_history", "Array<Event>", "تاریخچه کامل تغییرات (immutable)"],
    ]
    add_table_styled(doc, task_data, col_widths_cm=[4.5, 3.5, 9])
    
    add_heading_2(doc, "۹.۲ چرخه وضعیت تسک")
    add_body(doc, "تسک از یک ماشین وضعیت (state machine) پیروی می‌کند. انتقال از یک وضعیت به وضعیت دیگر فقط از مسیرهای مجاز ممکن است. این کنترل از رفتارهای غیرمجاز (مثلاً تأیید یک تسک که هنوز کنترل نشده) جلوگیری می‌کند.")
    
    status_data = [
        ["وضعیت", "توضیح", "انتقال‌های مجاز بعدی"],
        ["تازه (Created)", "تسک ایجاد شده اما کارمند هنوز شروع نکرده", "در حال انجام، رد شده، کنسل"],
        ["در حال انجام (In Progress)", "کارمند اعلام شروع کرده", "در انتظار کنترل، ارجاع به همکار، رد"],
        ["ارجاع به همکار (Delegated)", "بخشی از کار به همکار واگذار شده", "در حال انجام، در انتظار کنترل"],
        ["در انتظار کنترل (Pending Review)", "کارمند فایل آپلود کرده", "تأیید، رد، نیازمند اصلاح"],
        ["نیازمند اصلاح (Revision)", "مدیر مغایرت‌هایی یافته", "در حال انجام، رد شده"],
        ["تأیید شده (Approved)", "مدیر کار را تأیید کرده", "بسته شده"],
        ["رد شده (Rejected)", "کار قابل قبول نبوده", "بسته شده"],
        ["کنسل (Cancelled)", "تسک قبل از شروع لغو شده", "بسته شده"],
    ]
    add_table_styled(doc, status_data, col_widths_cm=[3.5, 5.5, 8])
    
    add_heading_2(doc, "۹.۳ ارجاع بخشی از تسک به همکار")
    add_body(doc, "یکی از ویژگی‌های کلیدی شما، امکان ارجاع بخشی از یک تسک به همکار است. به عنوان مثال، کارمند الف ممکن است بخش «ثبت اسناد خرید» از یک تسک بزرگ «بستن ماهانه شرکت A» را به کارمند ب ارجاع دهد. در این حالت، سامانه باید سهم هر فرد را به‌صورت شفاف پیگیری کند تا در ارزیابی عملکرد، یک کار دو بار به‌عنوان خروجی کامل دو کارمند حساب نشود.")
    
    add_body(doc, "راهکار ما این است: هر ارجاع به یک SubTask از تسک اصلی تبدیل می‌شود. SubTask مسئول، مهلت و وضعیت مستقل دارد، اما به تسک اصلی متصل است. در گزارش ارزیابی، تسک اصلی به نسبت کارمندی که بیشترین سهم را داشته اختصاص می‌یابد و سهم سایر کارمندان به‌صورت وزن‌دار محاسبه می‌شود. به‌عنوان مثال، اگر کارمند الف ۷۰٪ زمان را صرف کرده و کارمند ب ۳۰٪، امتیاز حجم کار به نسبت ۷۰/۳۰ تقسیم می‌شود.")
    
    add_callout(doc, "قاعده کلیدی: یک تسک نباید به‌عنوان خروجی کامل دو کارمند حساب شود. سامانه باید سهم هر فرد را به‌صورت عددی پیگیری کند و در محاسبه امتیاز حجم کار، این سهم را لحاظ نماید.", 'warn')
    
    add_page_break(doc)
    
    # ============ CHAPTER 10 ============
    add_heading_1(doc, "فصل ۱۰: حضور و غیاب، مرخصی، درخواست‌ها و لاگ فعالیت")
    
    add_body(doc, "در این فصل، قابلیت‌های جانبی اما مهم سامانه بررسی می‌شود: ثبت مرخصی، ورود و خروج، درخواست‌ها به مدیر و مدیرعامل، و لاگ فعالیت غیرقابل ویرایش. این قابلیت‌ها در فاز اولیه به‌صورت ساده پیاده‌سازی می‌شوند و در فازهای بعدی به دستگاه حضور و غیاب متصل می‌شوند.")
    
    add_heading_2(doc, "۱۰.۱ ثبت مرخصی")
    add_body(doc, "کارمند می‌تواند درخواست مرخصی روزانه، ساعتی، استعلاگی یا استحقاقی ثبت کند. درخواست شامل نوع مرخصی، بازه زمانی، دلیل و وضعیت تأیید است. گردش تأیید بسته به نوع مرخصی متفاوت است: مرخصی استحقاقی فقط نیاز به تأیید مدیر مستقیم دارد. مرخصی استعلاگی نیاز به تأیید مدیر و مدیرعامل دارد. مرخصی بیش از ۳ روز نیاز به تأیید مدیرعامل دارد. در صورت عدم پاسخ مدیر در مدت مشخص (پیشنهاد: ۲۴ ساعت)، مرخصی به‌صورت خودکار به مدیرعامل ارجاع می‌شود.")
    
    add_heading_2(doc, "۱۰.۲ ثبت ورود و خروج")
    add_body(doc, "در فاز اول، ثبت ورود و خروج به‌صورت دستی از طریق پنل کارمند انجام می‌شود. کارمند در شروع روز کاری «ورود» و در پایان «خروج» را ثبت می‌کند. سامانه ساعت، تاریخ و کارمند را به‌صورت خودکار ثبت می‌کند. در فاز دوم، این قابلیت به دستگاه حضور و غیاب فیزیکی متصل می‌شود و ثبت به‌صورت خودکار انجام می‌شود. در هر دو حالت، گزارش ماهانه حضور و غیاب به‌صورت اتوماتیک تولید می‌شود.")
    
    add_heading_2(doc, "۱۰.۳ درخواست به مدیر و مدیرعامل")
    add_body(doc, "کارمند می‌تواند درخواست‌های مختلفی ثبت کند: درخواست مساعده، درخواست ارتقای شغلی، درخواست تجهیزات، درخواست تغییر شیفت، و درخواست‌های دلخواه. هر درخواست نوع، عنوان، توضیح، پیوست و وضعیت تأیید دارد. گردش تأیید بسته به نوع درخواست متفاوت است. تمام درخواست‌ها در کارتابل مدیر یا مدیرعامل نمایش داده می‌شوند و می‌توانند تأیید، رد یا برای اطلاعات بیشتر برگردانده شوند.")
    
    add_heading_2(doc, "۱۰.۴ لاگ فعالیت غیرقابل ویرایش (Immutable Audit Log)")
    add_body(doc, "یکی از مهم‌ترین ویژگی‌های امنیتی سامانه، لاگ فعالیت غیرقابل ویرایش است. این لاگ رویدادهای مهم را ثبت می‌کند: ورود/خروج کاربر، ایجاد/ویرایش/حذف تسک، بارگذاری فایل، تأیید یا رد گزارش، تغییر تنظیمات اتصال، و سایر رویدادهای حساس. هر رویداد شامل نوع، زمان، کاربر، آدرس IP، توضیح و داده‌های مرتبط است.")
    
    add_body(doc, "مهم‌ترین ویژگی این لاگ، غیرقابل ویرایش بودن آن است. این یعنی حتی مدیر هم نمی‌تواند رویدادهای ثبت‌شده را ویرایش یا حذف کند. این قابلیت با دو روش پیاده‌سازی می‌شود. روش اول: استفاده از یک جدول دیتابیس که فقط INSERT مجاز است و UPDATE/DELETE در سطح کاربر دیتابیس غیرفعال است. روش دوم (پیشنهادی برای حساس‌ترین داده‌ها): نوشتن لاگ به یک سیستم لاگ خارجی (مانند Elasticsearch یا یک سرور لاگ مستقل) که حتی اگر دیتابیس اصلی دفتر دستکاری شود، لاگ دست‌نخورده باقی بماند.")
    
    log_data = [
        ["نوع رویداد", "کاربر", "زمان", "توضیح نمونه", "اولویت"],
        ["AUTH_LOGIN", "کارمند", "۱۴۰۵/۰۷/۲۰ ۰۸:۳۲", "ورود موفق از IP 192.168.1.5", "متوسط"],
        ["TASK_CREATED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۰۹:۱۵", "ایجاد تسک ۱۲۳۴ برای شرکت A", "متوسط"],
        ["FILE_UPLOADED", "کارمند", "۱۴۰۵/۰۷/۲۰ ۱۰:۴۵", "آپلود فایل اسناد_شرکت_A.xlsx", "بالا"],
        ["TASK_APPROVED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۱۱:۲۰", "تأیید تسک ۱۲۳۴ با امتیاز ۸۸", "بالا"],
        ["TASK_REJECTED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۱۱:۳۵", "رد تسک ۱۲۳۵ - مغایرت ۵ سند", "بالا"],
        ["CONN_CONFIG_CHANGED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۱۴:۰۰", "تغییر تنظیمات اتصال شرکت B", "بحرانی"],
        ["LEAVE_REQUESTED", "کارمند", "۱۴۰۵/۰۷/۲۰ ۱۵:۲۰", "درخواست مرخصی ۱۴۰۵/۰۸/۰۱-۰۳", "متوسط"],
    ]
    add_table_styled(doc, log_data, col_widths_cm=[3.5, 1.8, 3.5, 6, 2.2])
    
    add_callout(doc, "اصل امنیتی: لاگ فعالیت نباید صرفاً یک متن قابل ویرایش باشد. رویدادهای مهم باید در یک سابقه محافظت‌شده ثبت شوند که حتی مدیر سیستم هم نتواند آن را تغییر دهد. این اصل، اعتماد به گزارش‌های ارزیابی پرسنل و رسیدگی به مغایرت‌ها را تضمین می‌کند.", 'danger')
    
    add_page_break(doc)
    
    # ============ CHAPTER 11 ============
    add_heading_1(doc, "فصل ۱۱: نقشه راه پیاده‌سازی فازبندی شده")
    
    add_body(doc, "ساخت تمام قابلیت‌های سامانه به‌صورت یکجا، ریسک پروژه را به‌شدت افزایش می‌دهد. بهتر است سامانه در پنج فاز پیاده‌سازی شود، به‌گونه‌ای که هر فاز خروجی قابل استفاده و قابل آزمایش داشته باشد. این رویکرد Incremental به شما اجازه می‌دهد در هر فاز، ارزشی به دفتر ببخشید و بازخورد واقعی کاربران را برای فاز بعدی جمع‌آوری کنید.")
    
    add_heading_2(doc, "فاز ۱: شناخت دیتابیس نمونه (هفته ۱-۲)")
    add_body(doc, "در این فاز، هدف اصلی این است که قبل از هر گونه توسعه، یک شرکت نمونه و یک فایل اکسل واقعی انتخاب شود و ساختار دیتابیس آن به‌طور کامل شناخته شود. این فاز شامل: انتخاب یک شرکت با نرم‌افزار همکاران، یک شرکت با نرم‌افزار سپیدار، و یک شرکت با فایل اکسل، بررسی ساختار جداول اسناد در هر دیتابیس، شناسایی کلیدهای اصلی و فیلدهای مهم، تعیین روش اتصال (مستقیم یا API)، و نوشتن یک اسکریپت آزمایشی برای خواندن چند سند. خروجی این فاز یک سند فنی است که به‌عنوان ورودی فاز بعد استفاده می‌شود. مدت زمان: ۲ هفته. ریسک: اگر ساختار دیتابیس نرم‌افزارهای مختلف به‌طور قابل توجهی متفاوت باشد، ممکن است نیاز به Adapter‌های بیشتری باشد.")
    
    add_heading_2(doc, "فاز ۲: نسخه اولیه مدیریت کار (هفته ۳-۶)")
    add_body(doc, "در این فاز، هسته پنل وب و مدیریت تسک ساخته می‌شود. شامل: احراز هویت کاربران، تعریف نقش‌ها (مدیر، مدیرعامل، کارمند)، تعریف شرکت‌ها و کارمندان، تخصیص تسک، چک‌لیست مراحل، پیگیری پیشرفت، آپلود فایل اکسل (بدون کنترل هوشمند)، و اعلان‌های پایه. در این فاز، سامانه هنوز راستی‌آزمایی هوشمند انجام نمی‌دهد اما کارمندان می‌توانند تسک‌ها را مدیریت کنند. این نسخه به‌تنهایی ارزش دارد و می‌تواند جایگزین روش‌های دستی شود. مدت زمان: ۴ هفته. خروجی: نسخه قابل استفاده دفتر برای مدیریت تسک.")
    
    add_heading_2(doc, "فاز ۳: موتور کنترل هوشمند اکسل (هفته ۷-۱۰)")
    add_body(doc, "این فاز قلب متمایزکننده سامانه است. شامل: پیاده‌سازی ۹ مرحله کنترل، ساخت Adapter‌های SQL Server و Excel، پیاده‌سازی مدل داده استاندارد، تولید گزارش مغایرت، رابط کاربری مدیر برای مشاهده گزارش‌ها، تأیید یا رد گزارش. در پایان این فاز، سامانه می‌تواند فایل اکسل را راستی‌آزمایی کند. مدت زمان: ۴ هفته. خروجی: نسخه با کنترل کامل اسناد برای یک شرکت نمونه.")
    
    add_heading_2(doc, "فاز ۴: اجرای آزمایشی (هفته ۱۱-۱۳)")
    add_body(doc, "سامانه روی دو یا سه شرکت با کارمندان واقعی استفاده می‌شود. هدف: مقایسه نتایج کنترل با بررسی دستی، شناسایی خطاهای موتور کنترل، تنظیم قواعد تکراری، و جمع‌آوری بازخورد کاربران. این فاز نباید حذف شود؛ حتی اگر فاز قبلی موفق به نظر برسد، اجرای آزمایشی روی داده‌های واقعی معمولاً چندین مورد ناهماهنگی آشکار می‌کند. مدت زمان: ۳ هفته. خروجی: نسخه پایدار قابل اعتماد.")
    
    add_heading_2(doc, "فاز ۵: توسعه و خودکارسازی (هفته ۱۴+)")
    add_body(doc, "در این فاز، قابلیت‌های پیشرفته اضافه می‌شوند: سایر Adapter‌ها برای نرم‌افزارهای دیگر، اتصال به دستگاه حضور و غیاب، مرخصی و درخواست‌های پیشرفته، گزارش ارزیابی پرسنل، داشبورد مدیریتی کامل، دریافت خودکار ریز اسناد زمان‌بندی‌شده، و API برای اتصال ابزارهای خارجی. این فاز باز است و بر اساس نیازهای واقعی دفتر ادامه می‌یابد. مدت زمان: ادامه‌دار.")
    
    add_heading_2(doc, "۱۱.۱ جدول خلاصه فازها")
    
    phase_data = [
        ["فاز", "مدت", "خروجی اصلی", "ریسک"],
        ["۱. شناخت دیتابیس نمونه", "۲ هفته", "سند فنی ساختار دیتابیس", "تفاوت ساختار نرم‌افزارها"],
        ["۲. نسخه اولیه مدیریت کار", "۴ هفته", "پنل وب + مدیریت تسک", "پذیرش کاربران"],
        ["۳. موتور کنترل هوشمند", "۴ هفته", "کنترل کامل اسناد", "پیچیدگی منطق کنترل"],
        ["۴. اجرای آزمایشی", "۳ هفته", "نسخه پایدار", "خطاهای پنهان در داده واقعی"],
        ["۵. توسعه و خودکارسازی", "ادامه‌دار", "قابلیت‌های پیشرفته", "اولویت‌بندی"],
        ["مجموع تا MVP", "۱۳ هفته", "نسخه قابل استفاده", "—"],
    ]
    add_table_styled(doc, phase_data, col_widths_cm=[4.5, 2, 5.5, 5])
    
    add_callout(doc, "نکته مهم: فاز ۱ (شناخت دیتابیس) نباید حذف شود. حتی اگر تجربه شما با نرم‌افزارهای همکاران و سپیدار زیاد است، ساختار دیتابیس این نرم‌افزارها در نسخه‌های مختلف متفاوت است. بدون این شناخت دقیق، Adapter‌ها در فاز ۳ به خطاهای ساختاری روبه‌رو می‌شوند.", 'warn')
    
    add_page_break(doc)
    
    # ============ CHAPTER 12 ============
    add_heading_1(doc, "فصل ۱۲: تحلیل هزینه، زمان و توصیه استقرار")
    
    add_body(doc, "در این فصل، تحلیل هزینه و زمان پیاده‌سازی سامانه، انتخاب پشته فنی، و گزینه‌های استقرار (On-Premise، Cloud خصوصی ایران، Cloud عمومی) بررسی می‌شود. هدف این است که شما بتوانید بر اساس بودجه و شرایط دفتر، تصمیم آگاهانه بگیرید.")
    
    add_heading_2(doc, "۱۲.۱ برآورد هزینه")
    add_body(doc, "هزینه کل پروژه شامل سه بخش است: هزینه توسعه اولیه، هزینه زیرساخت (سرور و دیتابیس)، و هزینه نگهداری و پشتیبانی ماهانه. جدول زیر برآوردی برای یک تیم توسعه ایرانی با نرخ ساعت ۲۵۰ هزار تومان است.")
    
    cost_data = [
        ["بخش", "توضیح", "هزینه برآوردی (تومان)"],
        ["تحلیل و طراحی", "۲ هفته، تحلیل‌گر + معمار", "۲۰-۳۰ میلیون"],
        ["توسعه فاز ۲ (پنل وب)", "۴ هفته، ۲ توسعه‌دهنده", "۵۰-۷۰ میلیون"],
        ["توسعه فاز ۳ (موتور کنترل)", "۴ هفته، ۲ توسعه‌دهنده + کارشناس حسابداری", "۶۰-۸۰ میلیون"],
        ["اجرای آزمایشی و رفع باگ", "۳ هفته", "۲۰-۳۰ میلیون"],
        ["زیرساخت سال اول (سرور VPS)", "VPS ۸GB RAM، ۲۰۰GB SSD", "۶-۱۰ میلیون"],
        ["نام دامنه و گواهی SSL", "سالانه", "۱-۲ میلیون"],
        ["پشتیبانی ماهانه سال اول", "۲۰٪ هزینه توسعه، گزینه‌ای", "۲۰-۳۰ میلیون در سال"],
        ["مجموع سال اول (بدون پشتیبانی)", "—", "۱۵۷-۲۱۲ میلیون"],
        ["مجموع سال اول (با پشتیبانی)", "—", "۱۷۷-۲۴۲ میلیون"],
    ]
    add_table_styled(doc, cost_data, col_widths_cm=[4.5, 6.5, 5])
    
    add_heading_2(doc, "۱۲.۲ مقایسه با هزینه ابزار آماده")
    add_body(doc, "اگر بخواهید از یک ابزار آماده خارجی مانند Karbon استفاده کنید، هزینه ماهانه برای ۵ کاربر بین ۳۰۰ تا ۴۵۰ دلار است. در سه سال، این رقم به ۱۰٬۸۰۰ تا ۱۶٬۲۰۰ دلار می‌رسد (معادل ۶۰۰ تا ۹۰۰ میلیون تومان با نرخ فعلی). این رقم تقریباً سه برابر هزینه ساخت سامانه اختصاصی است، و این در حالی است که ابزار آماده نیازمندی‌های اصلی شما (کنترل هوشمند اسناد، اتصال به دیتابیس‌های ایرانی) را پوشش نمی‌دهد. به‌علاوه، ابزار آماده هرگز با نیازهای خاص شما رشد نمی‌کند و شما به‌صورت دائم به‌صلب یا محدودیت‌های آن روبه‌رو خواهید بود.")
    
    add_heading_2(doc, "۱۲.۳ پشته فنی پیشنهادی")
    add_body(doc, "پشته فنی پیشنهادی بر اساس سه معیار انتخاب شده: بلوغ و پشتیبانی گسترده جامعه، در دسترس بودن نیروی متخصص در ایران، و تناسب با نوع کارکرد. جدول زیر پشته پیشنهادی را نشان می‌دهد.")
    
    stack_data = [
        ["لایه", "فناوری", "دلیل انتخاب"],
        ["Frontend", "Next.js 14 + React + TypeScript + Tailwind", "محبوب، مستندات فراوان، SSR قوی"],
        ["Backend API", "Python + FastAPI", "سریع، توسعه آسان، کتابخانه داده فراوان"],
        ["دیتابیس اصلی", "PostgreSQL 15+", "قوی، Open Source، پشتیبانی JSON"],
        ["Adapter Layer", "Python + SQLAlchemy + pyodbc + openpyxl", "اتصال به SQL Server و اکسل"],
        ["Authentication", "JWT + NextAuth.js", "محبوب، امن، پشتیبانی OAuth"],
        ["Message Queue", "Redis + RQ یا Celery", "پردازش غیرهمزمان فایل‌های اکسل"],
        ["File Storage", "محلی + S3-compatible (MinIO)", "ذخیره فایل‌های اکسل با نسخه‌بندی"],
        ["Monitoring", "Sentry + Prometheus + Grafana", "رصد خطاها و عملکرد"],
        ["Deployment", "Docker + Docker Compose", "استقرار ساده و قابل تکرار"],
        ["CI/CD", "GitHub Actions یا GitLab CI", "خودکارسازی تست و استقرار"],
    ]
    add_table_styled(doc, stack_data, col_widths_cm=[3.5, 5, 7.5])
    
    add_heading_2(doc, "۱۲.۴ گزینه‌های استقرار")
    add_body(doc, "سه گزینه برای استقرار سامانه وجود دارد که هر کدام مزایا و معایب خود را دارند. انتخاب گزینه به شرایط فنی، بودجه و میزان حساسیت داده‌ها بستگی دارد.")
    
    deploy_data = [
        ["گزینه", "مزایا", "معایب", "هزینه ماهانه تقریبی"],
        ["On-Premise (سرور دفتر)", "کنترل کامل داده، عدم وابستگی به اینترنت", "نگهداری سخت‌افزاری، پشتیبان‌گیری دستی", "هزینه اولیه + برق"],
        ["Cloud خصوصی ایران", "دسترسی راه‌دور، پشتیبان‌گیری، مقرر بودن", "وابستگی به ارائه‌دهنده", "۵۰۰-۲۰۰۰ هزار تومان"],
        ["Cloud عمومی (AWS/Hetzner)", "ارزان، مقیاس‌پذیر، خدمات فراوان", "تحریم‌پذیر، نگرانی حریم خصوصی", "۲۰۰-۸۰۰ هزار تومان"],
    ]
    add_table_styled(doc, deploy_data, col_widths_cm=[3.5, 4.5, 4.5, 3.5])
    
    add_callout(doc, "توصیه: برای دفتر شما، گزینه Cloud خصوصی ایران (مثل لیارا یا پارس‌پک) بهترین تعادل بین هزینه، راحتی و مقررات ایران را ارائه می‌دهد. هزینه ماهانه ۵۰۰ تا ۲۰۰۰ هزار تومان برای VPS با ۸ گیگابایت RAM و ۲۰۰ گیگابایت SSD کافی است.", 'success')
    
    add_page_break(doc)
    
    # ============ CHAPTER 13 ============
    add_heading_1(doc, "فصل ۱۳: جمع‌بندی و توصیه‌های نهایی")
    
    add_body(doc, "در این گزارش، نیازهای دفتر حسابداری شما را به‌طور کامل بررسی کردیم: نرم‌افزارهای آماده موجود در بازار جهانی و ایرانی، چارچوب ارزیابی پرسنل، معماری چندپایگاه‌داده با Adapter Pattern، الگوی اکسل اسناد، موتور کنترل هوشمند، و نقشه راه پیاده‌سازی فازبندی شده. در این فصل پایانی، توصیه‌های نهایی و قدم‌های بعدی را به‌صورت عملی ارائه می‌دهیم.")
    
    add_heading_2(doc, "۱۳.۱ توصیه نهایی")
    add_body(doc, "توصیه نهایی ما ساخت یک سامانه اختصاصی با معماری ترکیبی است. این انتخاب بر اساس چهار دلیل اصلی است. اول، هیچ نرم‌افزار آماده‌ای در بازار جهانی یا ایرانی، تمام نیازهای شما را به‌صورت یکپارچه پوشش نمی‌دهد، به‌ویژه موتور کنترل هوشمند اسناد و اتصال به دیتابیس‌های متنوع نرم‌افزارهای ایرانی. دوم، هزینه ساخت اختصاصی در یک دوره سه‌ساله تقریباً یک‌سوم هزینه اشتراک ابزار آماده است. سوم، سامانه اختصاصی به‌صورت کامل با نیازهای شما رشد می‌کند و شما را به‌صلب یا محدودیت ابزار خارجی محدود نمی‌کند. چهارم، داده‌های حساس دفتر شما (اسناد ۵۰ شرکت) در ایران نگه‌داری می‌شود و از ریسک تحریم یا قطع دسترسی به ابر خارجی در امان است.")
    
    add_heading_2(doc, "۱۳.۲ قدم‌های بعدی فوری (هفته اول)")
    next_steps_urgent = [
        "انتخاب یک شرکت نمونه با نرم‌افزار همکاران و یک شرکت با نرم‌افزار سپیدار برای فاز ۱.",
        "تهیه یک فایل اکسل واقعی از اسناد یکی از شرکت‌ها برای آزمون موتور کنترل.",
        "اخذ دسترسی Read-Only به دیتابیس SQL Server شرکت‌های نمونه.",
        "مشاوره با یک تیم توسعه ایرانی برای دریافت پیشنهاد قیمت و زمان دقیق (با این گزارش به‌عنوان RFP).",
        "تعیین بودجه نهایی و زمان‌بندی پروژه بر اساس پیشنهاد تیم توسعه.",
    ]
    for i, s in enumerate(next_steps_urgent):
        add_numbered(doc, s, fa_nums[i])
    
    add_heading_2(doc, "۱۳.۳ اقدامات میان‌مدت (۳ ماه)")
    next_steps_mid = [
        "تأیید تیم توسعه و امضای قرارداد شامل تعرفه‌های روشن برای فازهای ۲ تا ۵.",
        "شروع فاز ۱ (شناخت دیتابیس) و تولید سند فنی ساختار.",
        "طراحی دقیق مدل داده استاندارد و بررسی با تیم توسعه.",
        "آغاز فاز ۲ (پنل وب) و آموزش کارمندان به‌صورت موازی با توسعه.",
        "تعریف نقش‌ها و سطوح دسترسی به‌صورت رسمی قبل از راه‌اندازی.",
    ]
    for i, s in enumerate(next_steps_mid):
        add_numbered(doc, s, fa_nums[i])
    
    add_heading_2(doc, "۱۳.۴ چک‌لیست آماده‌سازی برای شروع پروژه")
    checklist = [
        "فهرست کامل ۵۰ شرکت با نوع نرم‌افزار حسابداری و نسخه آن.",
        "اطلاعات تماس نرم‌افزارکار هر شرکت برای همکاری در دسترسی Read-Only.",
        "نمونه فایل اکسل از ۳ شرکت با ساختار متفاوت برای آزمون.",
        "فهرست انواع فعالیت‌های حسابداری که در دفتر انجام می‌شود.",
        "تعریف اولیه پنج شاخص KPI و وزن هر کدام (بر اساس این گزارش).",
        "تعیین نقش‌ها: مدیر، مدیرعامل، ۵ کارمند، مسئول کنترل.",
        "تصمیم در مورد گزینه استقرار (پیشنهاد: Cloud خصوصی ایران).",
        "بودجه اولیه و تعیین حداکثر هزینه قابل قبول.",
        "تیم‌سازی: انتخاب تیم توسعه یا برون‌سپاری به یک شرکت توسعه.",
        "زمان‌بندی: تعیین تاریخ شروع و تاریخ تحویل MVP.",
    ]
    for it in checklist:
        add_bullet(doc, it)
    
    add_callout(doc, "پیام پایانی: این پروژه یک سرمایه‌گذاری راهبردی برای دفتر شماست. اگر به‌درستی پیاده‌سازی شود، علاوه بر کنترل کامل عملیات دفتر، مزیت رقابتی قابل توجهی به شما می‌دهد - توانایی پذیرش شرکت‌های بیشتر بدون افزایش متناسب کارکنان، کاهش خطاهای حسابداری، و اعتبار بالاتر در بازار. با این حال، موفقیت پروژه به‌شدت به انتخاب تیم توسعه مناسب و پایبندی به نقشه راه فازبندی شده وابسته است.", 'success')
    
    # Save document
    doc.save(output_path)
    print(f"DOCX generated: {output_path}")

if __name__ == '__main__':
    output = '/home/z/my-project/download/سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.docx'
    build_docx(output)
    print("Build complete!")
