"""
Accounting Office Management System - Updated Report v2.0 (Word DOCX)
Deep analysis of Financial Cents, Karbon, Pixie + all final design decisions.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_BREAK

# Color palette
PRIMARY = RGBColor(0x0F, 0x17, 0x2A)
ACCENT = RGBColor(0x0E, 0x7C, 0x8B)
TEXT_MUTED = RGBColor(0x47, 0x55, 0x69)
SUCCESS = RGBColor(0x16, 0xA3, 0x4A)
WARN = RGBColor(0xD9, 0x77, 0x06)
DANGER = RGBColor(0xDC, 0x26, 0x26)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TABLE_HEADER_BG = "0E7C8B"
TABLE_ALT_BG = "F8FAFC"

# Helpers
def set_paragraph_rtl(paragraph):
    pPr = paragraph._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    pPr.append(bidi)

def set_run_rtl(run):
    rPr = run._element.get_or_add_rPr()
    rtl = OxmlElement('w:rtl')
    rtl.set(qn('w:val'), '1')
    rPr.append(rtl)
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
    rPr = run._element.get_or_add_rPr()
    sz_cs = OxmlElement('w:szCs')
    sz_cs.set(qn('w:val'), str(size * 2))
    rPr.append(sz_cs)
    return run

def add_body(doc, text, justify=True):
    align = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.RIGHT
    p = doc.add_paragraph()
    p.alignment = align
    set_paragraph_rtl(p)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.4
    add_run(p, text, size=11, color=PRIMARY)
    return p

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(12)
    add_run(p, text, bold=True, size=20, color=PRIMARY)
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
    add_run(p, text, bold=True, size=15, color=ACCENT)
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    add_run(p, text, bold=True, size=12.5, color=PRIMARY)
    return p

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
    bg_color = {'info': 'E0F2FE', 'warn': 'FEF3C7', 'success': 'D1FAE5', 'danger': 'FEE2E2'}.get(kind, 'E0F2FE')
    border_color = {'info': '0E7C8B', 'warn': 'D97706', 'success': '16A34A', 'danger': 'DC2626'}.get(kind, '0E7C8B')
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), bg_color)
    tcPr.append(shd)
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '8')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), border_color)
        tcBorders.append(border)
    tcPr.append(tcBorders)
    tcMar = OxmlElement('w:tcMar')
    for edge in ['top', 'left', 'bottom', 'right']:
        mar = OxmlElement(f'w:{edge}')
        mar.set(qn('w:w'), '200')
        mar.set(qn('w:type'), 'dxa')
        tcMar.append(mar)
    tcPr.append(tcMar)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_rtl(p)
    p.paragraph_format.line_spacing = 1.4
    add_run(p, text, bold=False, size=11, color=PRIMARY)
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
    add_run(p, text, bold=bold, size=size, color=color if color else PRIMARY)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

def add_table_styled(doc, data, col_widths_cm=None, has_header=True):
    rows = len(data)
    cols = len(data[0]) if data else 0
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    bidiVisual = OxmlElement('w:bidiVisual')
    tblPr.append(bidiVisual)
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
                set_cell_text(cell, cell_text, bold=True, size=10, color=WHITE, alignment=WD_ALIGN_PARAGRAPH.CENTER)
            else:
                if r_idx % 2 == 0:
                    set_cell_background(cell, TABLE_ALT_BG)
                align = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
                set_cell_text(cell, cell_text, size=9.5, alignment=align)
    if col_widths_cm:
        for row in table.rows:
            for i, w in enumerate(col_widths_cm):
                row.cells[i].width = Cm(w)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)
    return table

def add_page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)

def build_cover(doc):
    section = doc.sections[0]
    section.top_margin = Cm(0)
    section.bottom_margin = Cm(0)
    section.left_margin = Cm(0)
    section.right_margin = Cm(0)
    cover_table = doc.add_table(rows=1, cols=1)
    cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = cover_table.rows[0].cells[0]
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '0F172A')
    tcPr.append(shd)
    trPr = cover_table.rows[0]._tr.get_or_add_trPr()
    trHeight = OxmlElement('w:trHeight')
    trHeight.set(qn('w:val'), '14000')
    trHeight.set(qn('w:hRule'), 'exact')
    trPr.append(trHeight)
    cell.width = Cm(21)
    tcMar = OxmlElement('w:tcMar')
    for edge in ['top', 'left', 'bottom', 'right']:
        mar = OxmlElement(f'w:{edge}')
        mar.set(qn('w:w'), '600' if edge in ['left', 'right'] else '3000' if edge == 'top' else '1500')
        mar.set(qn('w:type'), 'dxa')
        tcMar.append(mar)
    tcPr.append(tcMar)
    
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p1)
    p1.paragraph_format.space_before = Pt(80)
    p1.paragraph_format.space_after = Pt(8)
    add_run(p1, "سامانه مدیریت عملیات دفتر حسابداری", bold=True, size=28, color=WHITE)
    
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p2)
    p2.paragraph_format.space_after = Pt(6)
    add_run(p2, "نسخه ۲.۰ - تحلیل به‌روزرسانی‌شده", size=14, color=RGBColor(0xE2, 0xE8, 0xF0))
    
    p3 = cell.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p3)
    p3.paragraph_format.space_after = Pt(30)
    add_run(p3, "________________________________", size=12, color=ACCENT)
    
    p4 = cell.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p4)
    p4.paragraph_format.space_after = Pt(60)
    add_run(p4, "تحلیل عمیق سه نرم‌افزار Financial Cents، Karbon و Pixie + الگوبرداری + تمام تصمیمات نهایی طراحی", size=12, color=RGBColor(0xE2, 0xE8, 0xF0))
    
    p5 = cell.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p5)
    p5.paragraph_format.space_after = Pt(8)
    add_run(p5, "دفتر حسابداری - ۵۰ شرکت - ۵ کارمند", size=11, color=RGBColor(0x94, 0xA3, 0xB8))
    
    p6 = cell.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_rtl(p6)
    add_run(p6, "پاییز ۱۴۰۵ - نسخه ۲.۰ - سند راهبردی به‌روز", size=11, color=RGBColor(0x94, 0xA3, 0xB8))
    
    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    new_section.top_margin = Cm(2)
    new_section.bottom_margin = Cm(2)
    new_section.left_margin = Cm(2)
    new_section.right_margin = Cm(2)

def build_docx(output_path):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Vazirmatn'
    style.font.size = Pt(11)
    style.font.color.rgb = PRIMARY
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:cs'), 'Vazirmatn')
    rFonts.set(qn('w:ascii'), 'Vazirmatn')
    rFonts.set(qn('w:hAnsi'), 'Vazirmatn')
    
    build_cover(doc)
    
    fa_nums = ['۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '۱۰', '۱۱', '۱۲', '۱۳', '۱۴', '۱۵']
    
    # CHAPTER 1
    add_heading_1(doc, "فصل ۱: خلاصه اجرایی - تغییرات نسخه ۲")
    add_body(doc, "این نسخه از گزارش بر اساس تحلیل عمیق سه نرم‌افزار تخصصی مدیریت دفاتر حسابداری (Financial Cents، Karbon و Pixie) و تمام تصمیمات نهایی طراحی استخراج‌شده از گفت‌وگوهای راهبردی شما تهیه شده است. در نسخه ۲، چهار به‌روزرسانی کلیدی نسبت به نسخه اول اعمال شده است که ساختار نهایی سامانه را به‌طور قابل توجهی متحول می‌کند. این تغییرات بر اساس الگوبرداری هوشمندانه از نرم‌افزارهای آماده و تطبیق آن‌ها با شرایط خاص دفتر شما در ایران طراحی شده‌اند.")
    add_body(doc, "اولین تغییر، تحلیل عمیق ساختار و قابلیت‌های سه نرم‌افزار است. تمرکز این تحلیل بر قابلیت‌ها و گردش کار است، نه بر قیمت یا API، تا بتوانیم الگوهای مفید را برای ساخت سامانه اختصاصی استخراج کنیم. Financial Cents با ۴۰۰+ قالب آماده و قابلیت‌های هوش مصنوعی (AI File Validator، AI File Renaming، AI File Routing)، Karbon با صف‌های FIFO و یکپارچگی عمیق ایمیل، و Pixie با قیمت اسمی مبتنی بر تعداد مشتری و کاربران نامحدود، هرکدام درسی برای سامانه شما دارند.")
    add_body(doc, "دومین تغییر، تصمیم نهایی در مورد شناسه ردیف سند است. شما تأیید کردید که اکسل کارمند باید شامل شناسه ردیف سند از دیتابیس مبدأ باشد و این شناسه پس از حذف و ثبت مجدد سند تغییر می‌کند. این تصمیم، کلید تطبیق را به‌طور بنیادی تعریف می‌کند: ترکیب شرکت + دیتابیس مبدأ + سال مالی + شناسه ردیف مبدأ. این کلید اجازه می‌دهد اصلاح سند را از تکراری واقعی تشخیص دهیم، اما به‌تنهایی کافی نیست، چون شناسه ردیف پس از حذف-ثبت مجدد تغییر می‌کند و نیاز به تطبیق احتمالی با سایر فیلدها دارد.")
    add_body(doc, "سومین تغییر، مفهوم فایل مرجع اختیاری است. شما تصمیم گرفتید که فایل مرجع مرجع تأیید کار است، نه الزام. مدیر هر زمان که بخواهد تسک را راستی‌آزمایی کند، فایل مرجع را بارگذاری می‌کند، اما می‌تواند بدون فایل مرجع هم کار را ۱۰۰٪ تأیید کند. این تصمیم، گردش کار تصمیم مدیر را به‌طور قابل توجهی ساده می‌کند و انعطاف بیشتری به مدیر می‌دهد. فایل مرجع به‌صورت نسخه‌بندی‌شده ذخیره می‌شود و چندین تسک می‌توانند از یک نسخه مرجع استفاده کنند.")
    add_body(doc, "چهارمین تغییر، امتیاز مستقل از تأیید است. شما تصمیم گرفتید که امتیاز هر تسک عددی از ۰ تا ۱۰۰ است که مدیر تعیین می‌کند. این امتیاز، وضعیت تأیید و نتیجه تطبیق سه مفهوم مستقل هستند؛ تأیید کار لزوماً به معنی امتیاز ۱۰۰ نیست. این تصمیم، چارچوب ارزیابی پرسنل را به‌طور بنیادی تغییر می‌دهد و به مدیر اجازه می‌دهد کیفیت کار را به‌صورت پیوسته اندازه بگیرد، نه فقط به‌صورت باینری (تأیید/رد).")
    add_callout(doc, "نکته: تمام تصمیمات نهایی این نسخه بر اساس ۱۴ گام گفت‌وگوی راهبردی شما تنظیم شده است. این سند اکنون یک سند فنی-اجرایی قابل تحویل به تیم توسعه است، نه فقط یک گزارش راهبردی سطح بالا.", 'info')
    add_page_break(doc)
    
    # CHAPTER 2
    add_heading_1(doc, "فصل ۲: تحلیل عمیق سه نرم‌افزار Financial Cents، Karbon و Pixie")
    add_body(doc, "در این فصل، سه نرم‌افزار تخصصی مدیریت دفاتر حسابداری را به‌صورت عمیق و با تمرکز بر ساختار برنامه و قابلیت‌ها (نه قیمت یا API) بررسی می‌کنیم. هدف، استخراج الگوهای قابل الگوبرداری برای سامانه اختصاصی شماست. هر نرم‌افزار درسی برای ما دارد: Financial Cents نشان می‌دهد چگونه با قالب‌های آماده و هوش مصنوعی، فرایندهای تکراری را خودکار کنیم؛ Karbon نشان می‌دهد چگونه با یکپارچگی عمیق ایمیل و صف‌های FIFO، کارهای حجم بالا را مدیریت کنیم؛ و Pixie نشان می‌دهد چگونه با تفکیک تسک به مراحل، امکان ارجاع به همکار را فراهم کنیم.")
    
    add_heading_2(doc, "۲.۱ Financial Cents - ساختار و قابلیت‌ها")
    add_body(doc, "Financial Cents یک پلتفرم همه‌جانبه مدیریت دفاتر حسابداری است که برای دفاتر کوچک و در حال رشد طراحی شده. این نرم‌افزار از یک فلسفه ساده پیروی می‌کند: «هر کار، هر مشتری، هر مهلت - همه در یک پلتفرم». این فلسفه با معماری ماژولار اما یکپارچه پیاده‌سازی شده که هر ماژول به‌طور مستقل کار می‌کند اما با سایر ماژول‌ها به‌صورت یکپارچه ارتباط دارد.")
    
    add_heading_3(doc, "مدیریت گردش کار (Workflow Management)")
    add_body(doc, "قلب Financial Cents، موتور مدیریت گردش کار است. این موتور شامل بیش از ۴۰۰ قالب از پیش ساخته‌شده برای کارهای حسابداری، مالیاتی، حقوق و دستمزد و خدمات حسابداری ابری (CAS) است. این قالب‌ها به‌طور خاص برای صنعت حسابداری طراحی شده‌اند و نیاز به ساخت قالب از صفر را از بین می‌برند. قابلیت تخصیص خودکار تسک بر اساس مشتری، نقش یا نوع خدمت، یکی از نقاط قوت اصلی این نرم‌افزار است. به‌عنوان مثال، وقتی یک کار ماهانه «بستن دفاتر شرکت A» ایجاد می‌شود، سامانه به‌طور خودکار می‌داند که کارمند مسئول، مهلت و مراحل را تعیین می‌کند. تسک‌های شرطی (Conditional Tasks) که با نوع درگیری سازگار می‌شوند، انعطاف بیشتری به مدیر می‌دهند: یک قالب می‌تواند برای کارهای مختلف رفتار متفاوتی داشته باشد.")
    
    add_heading_3(doc, "کارهای تکرارشونده و اتوماسیون")
    add_body(doc, "کارهای تکرارشونده (Recurring Engagements) در Financial Cents به‌صورت کامل خودکار اجرا می‌شوند. به‌عنوان مثال، حسابداری ماهانه، بستن دوره فصلی و آماده‌سازی اظهارنامه مالیاتی سالانه می‌توانند به‌صورت زمان‌بندی‌شده اجرا شوند. تاریخ‌های مقرر به‌طور خودکار به‌روزرسانی و به جلو منتقل می‌شوند. این یعنی مدیر نیازی نیست هر ماه به یاد خودش کار ماهانه را ایجاد کند؛ سامانه این کار را به‌طور خودکار انجام می‌دهد. این قابلیت برای دفتر شما با ۵۰ شرکت بسیار ارزشمند است، زیرا فرض کنید ۵۰ شرکت نیاز به کار ماهانه دارند؛ اگر قرار باشد هر کار را به‌صورت دستی ایجاد کنید، ۵۰۰ کار در سال نیاز به ایجاد دارد.")
    
    add_heading_3(doc, "CRM مشتری و پورتال")
    add_body(doc, "Financial Cents یک CRM (مدیریت ارتباط با مشتری) داخلی دارد که به‌عنوان یک منبع واحد برای هر مشتری عمل می‌کند. هر مشتری خدمات، مخاطبین، یادداشت‌ها، فایل‌ها، تاریخچه و صورت‌حساب خود را در یک نمای یکپارچه دارد. این CRM به تمام گردش کارها، اسناد و فاکتورهای مرتبط با همان مشتری متصل است. یادداشت‌های سطح مشتری، برچسب‌ها و فیلدهای سفارشی امکان دسته‌بندی و جست‌وجوی پیشرفته را فراهم می‌کنند. یکپارچگی بومی با QuickBooks Online به‌طور خودکار اطلاعات مالی مشتری را به‌روزرسانی می‌کند. پورتال مشتری با آپلود امن فایل و امضای الکترونیکی، نیاز به ایمیل‌های رفت-و‌برگشتی را حذف می‌کند.")
    
    add_heading_3(doc, "قابلیت‌های هوش مصنوعی")
    add_body(doc, "Financial Cents در سال‌های اخیر سرمایه‌گذاری قابل توجهی در هوش مصنوعی کرده است. سه قابلیت AI به‌طور خاص برای مدیریت فایل ارزشمند هستند. اول، AI File Validator فایل‌های آپلود شده مشتری را قبل از رسیدن به تیم بررسی می‌کند و فایل‌های نادرست را شناسایی می‌کند. دوم، AI File Renaming به‌طور خودکار فایل‌ها را به قرارداد نام‌گذاری دفتر شما تغییر نام می‌دهد. سوم، AI File Routing فایل‌های آپلود شده مشتری را در پوشه مشتری صحیح قرار می‌دهد. علاوه بر این، Financial Cents MCP (Model Context Protocol) امکان اتصال داده‌های دفتر شما به Claude، ChatGPT و Gemini را فراهم می‌کند.")
    
    add_heading_3(doc, "مدیریت تیم و گزارش‌گیری")
    add_body(doc, "Financial Cents یک نمای ظرفیت تیم در زمان واقعی (Real-time Team Capacity View) ارائه می‌دهد که به مدیر نشان می‌دهد هر کارمند چقدر بار کاری دارد و چه مقدار ظرفیت آزاد باقی مانده است. این قابلیت برای دفتر شما با ۵ کارمند بسیار مهم است، زیرا اجازه می‌دهد کار را به کارمندی که ظرفیت دارد ارجاع دهید، نه فقط به کارمندی که معمولاً آن شرکت را بر عهده دارد. گزارش‌های سطح سودآوری مشتری و زمان، به مدیر نشان می‌دهد کدام مشتری‌ها و کدام خدمات سودآورتر هستند. این قابلیت در دفتر شما می‌تواند به تصمیم‌گیری در مورد قیمت‌گذاری و تخصیص منابع کمک کند.")
    
    add_heading_2(doc, "۲.۲ Karbon - ساختار و قابلیت‌ها")
    add_body(doc, "Karbon یکی از پیچیده‌ترین و قدرتمندترین نرم‌افزارهای مدیریت دفاتر حسابداری است که برای دفاتر متوسط و بزرگ (۵ تا ۵۰ کارمند) طراحی شده. این نرم‌افزار با فلسفه «هماهنگی کار با ایمیل» شناخته می‌شود - یعنی تمام ارتباطات مشتری به‌طور خودکار به کارهای مرتبط متصل می‌شوند. این فلسفه باعث می‌شود هیچ ایمیلی گم نشود و تمام تصمیمات در یک مکان متمرکز باشند.")
    
    add_heading_3(doc, "صف‌های FIFO و مدیریت حجم بالا")
    add_body(doc, "یکی از ویژگی‌های منحصر به فرد Karbon، صف‌های FIFO (First-In-First-Out) برای مدیریت کارهای حجم بالا هستند. این صف‌ها به‌طور خاص برای فصل مالیات طراحی شده‌اند، زمانی که دفتر با صدها اظهارنامه همزمان روبه‌رو است. هر کار به‌طور خودکار در صف قرار می‌گیرد و کارمندان به ترتیب کارها را برمی‌دارند. مدیر می‌تواند کارهای با اولویت بالا را به‌صورت دستی به بالای صف ببرد. این قابلیت برای دفتر شما با ۵۰ شرکت و کارهای ماهانه تکرارشونده بسیار ارزشمند است. به‌عنوان مثال، در پایان هر ماه، ۵۰ کار «بستن دفاتر» باید اجرا شود؛ صف FIFO کمک می‌کند این کارها به‌صورت منظم و عادلانه بین کارمندان توزیع شوند.")
    
    add_heading_3(doc, "قالب‌های مبتنی بر نقش و اتوماسیون")
    add_body(doc, "Karbon از قالب‌های مبتنی بر نقش (Role-based Templates) استفاده می‌کند. هر قالب تعریف می‌کند چه نقشی باید چه مرحله‌ای را انجام دهد. به‌عنوان مثال، در قالب «بستن دفاتر ماهانه»، نقش «کارمند جوان» مرحله «ثبت اسناد» را انجام می‌دهد، نقش «سرپرست» مرحله «بازبینی» را، و نقش «شریک ارشد» مرحله «تأیید نهایی» را. اتوماسیون کاربر (Automators) به‌طور خودکار تسک‌ها را بر اساس نقش‌ها و مهلت‌ها تخصیص می‌دهد. همچنین، اتوماسیون می‌تواند بخش‌هایی از تسک‌ها را بر اساس معیارها یا محرک‌ها فعال یا غیرفعال کند. این یعنی یک قالب می‌تواند برای انواع مختلف مشتریان رفتار متفاوتی داشته باشد.")
    
    add_heading_3(doc, "یکپارچگی عمیق ایمیل")
    add_body(doc, "نقطه قوت اصلی Karbon، یکپارچگی عمیق ایمیل است. تمام ایمیل‌های مشتری به‌طور خودکار به کارهای مرتبط متصل می‌شوند. تیم می‌تواند ایمیل‌ها را به یکدیگر ارجاع دهد، درباره آن‌ها بحث کند و گفت‌وگوها را به‌طور مستقیم به کار در حال انجام متصل کند. این قابلیت باعث می‌شود هیچ ایمیلی گم نشود و تمام تصمیمات در یک مکان متمرکز باشند. مدیر دید کاملی از مسئولیت‌ها، مهلت‌ها و پیشرفت پروژه دارد. این قابلیت برای دفتر شما با ۵۰ شرکت ارزشمند است، زیرا ارتباط با هر شرکت به‌صورت جداگانه و در یک مکان متمرکز انجام می‌شود.")
    
    add_heading_3(doc, "مدیریت اسناد و یکپارچگی‌ها")
    add_body(doc, "Karbon یک سیستم مدیریت اسناد با version control (کنترل نسخه) دارد که فایل‌ها را به‌طور خودکار سازماندهی می‌کند. پوشه‌بندی هوشمند و DMS sync فایل‌ها را در مکان صحیح قرار می‌دهد. یکپارچگی با Google Drive، SharePoint/OneDrive یا Dropbox به دفاتر اجازه می‌دهد از سیستم ذخیره‌سازی موجود خود استفاده کنند. Karbon برای Clients یک پورتال مشتری است که امکان دریافت اسناد، تکمیل سازمان‌دهنده، حاشیه‌نویسی و تأییدها را فراهم می‌کند.")
    
    add_heading_3(doc, "گزارش‌گیری و داشبورد")
    add_body(doc, "Karbon چندین داشبورد تخصصی دارد. Progress Report Dashboard یک نمای بصری و در زمان واقعی از وضعیت کار ارائه می‌دهد. Work Dashboards زمان چرخش، زمان تکمیل پروژه و نرخ تکمیل را نشان می‌دهد. Karbon Analytics Dashboards عملکرد تیم، زمان چرخش و تکمیل پروژه را تحلیل می‌کند. گزارش‌های قابل سفارشی‌سازی بر اساس تیم، بازه زمانی و نوع خدمت امکان تحلیل عمیق را فراهم می‌کنند. این سطح از گزارش‌گیری برای دفتر شما می‌تواند به شناسایی کارمندان با عملکرد پایین، شرکت‌های با تأخیر مکرر، و خدمات با حاشیه سود پایین کمک کند.")
    
    add_heading_3(doc, "زمان‌بند کار و کارهای تکرارشونده")
    add_body(doc, "Work Scheduler کارهای تکرارشونده را به‌طور خودکار زمان‌بندی می‌کند. به‌عنوان مثال، می‌توانید تنظیم کنید که کار «بستن دفاتر شرکت A» در روز اول هر ماه به‌طور خودکار ایجاد شود. این کار به یک کارمند مشخص ارجاع داده می‌شود و مهلت آن تعیین می‌گردد. این قابلیت در دفتر شما می‌تواند ۵۰ کار ماهانه را به‌صورت کامل خودکار کند و نیاز به مدیریت دستی را از بین ببرد.")
    
    add_heading_2(doc, "۲.۳ Pixie - ساختار و قابلیت‌ها")
    add_body(doc, "Pixie یک نرم‌افزار ساده و کاربرپسند برای دفاتر کوچک و در حال رشد حسابداری است. این نرم‌افزار با فلسفه «سادگی و قیمت منصفانه» طراحی شده و هدف آن ارائه تمام قابلیت‌های ضروری بدون پیچیدگی اضافی است. Pixie به‌طور خاص برای دفاتر با تعداد کارمند متغیر ارزشمند است، زیرا قیمت مبتنی بر تعداد مشتری است، نه کارمند.")
    
    add_heading_3(doc, "مدیریت گردش کار با تفکیک به مراحل")
    add_body(doc, "Pixie گردش کار را به مراحل کوچک‌تر تفکیک می‌کند تا بهره‌وری تیم افزایش یابد. هر مرحله یک مسئول مشخص دارد و مدیر می‌تواند وضعیت هر مرحله را به‌صورت جداگانه پیگیری کند. این قابلیت برای دفتر شما بسیار ارزشمند است، زیرا شما خواستار امکان «انجام دادن قسمتی از تسک و ارجاع به همکار» هستید. مدل تفکیک به مراحل Pixie دقیقاً همین نیاز را پوشش می‌دهد: یک تسک به چند مرحله تقسیم می‌شود، هر مرحله مسئول مستقل دارد و ارجاع به همکار به‌سادگی امکان‌پذیر است.")
    
    add_heading_3(doc, "شروع خودکار کارها بر اساس تاریخ‌های کلیدی مشتری")
    add_body(doc, "یکی از قابلیت‌های منحصر به فرد Pixie، شروع خودکار کارها بر اساس تاریخ‌های کلیدی مشتری است. به‌عنوان مثال، اگر تاریخ «مهلت ارائه اظهارنامه مالیاتی» شرکت A در سامانه تعریف شود، Pixie به‌طور خودکار کار «آماده‌سازی اظهارنامه» را ۳۰ روز قبل از مهلت ایجاد می‌کند. این قابلیت برای دفتر شما با ۵۰ شرکت بسیار ارزشمند است، زیرا هر شرکت تاریخ‌های کلیدی متفاوتی دارد (ماهانه، فصلی، سالانه) و پیگیری دستی آن‌ها دشوار است.")
    
    add_heading_3(doc, "اتوماسیون و یادآوری‌های خودکار")
    add_body(doc, "Pixie اتوماسیون‌های متعددی دارد: ایجاد کارهای تکرارشونده، تخصیص خودکار کار به تیم، درخواست خودکار صورتحساب از مشتریان، و ارسال خودکار یادآوری تاریخ‌های کلیدی به مشتری. این اتوماسیون‌ها به مدیر اجازه می‌دهند به‌جای پیگیری دستی، روی کار ارزشمندتر تمرکز کند. یادآوری‌های خودکار به مشتری باعث می‌شوند نیازی نباشد مدیر خودش به مشتری یادآوری کند. این قابلیت در دفتر شما می‌تواند به یادآوری خودکار به شرکت‌ها برای ارسال مدارک ماهانه کمک کند.")
    
    add_heading_3(doc, "CRM با فیلدهای سفارشی و خط زمانی")
    add_body(doc, "Pixie یک CRM متمرکز با فیلدهای سفارشی دارد. مدیر می‌تواند فیلدهای خاص هر دفتر را تعریف کند (مثلاً «نوع نرم‌افزار حسابداری» یا «نام نرم‌افزارکار»). خط زمانی تمام ایمیل‌ها و مکاتبات اسنادی هر مشتری را در یک مکان نشان می‌دهد. این قابلیت برای دفتر شما با ۵۰ شرکت و تنوع نرم‌افزارها ارزشمند است، زیرا به شما اجازه می‌دهد هر شرکت را با نوع نرم‌افزار و روش اتصال دسته‌بندی کنید.")
    
    add_heading_3(doc, "پورتال مشتری و یکپارچگی‌ها")
    add_body(doc, "Pixie یک پورتال مشتری سازگار با GDPR دارد که امکان اشتراک امن اسناد، تسک‌های مشتری و امضای الکترونیکی را فراهم می‌کند. یکپارچگی اصلی Pixie از طریق Zapier است که به ۹۰۰۰ اپ دیگر متصل می‌شود. این یعنی می‌توانید Pixie را با Gmail، Google Drive، Slack، Excel و بسیاری از ابزارهای دیگر متصل کنید. برای دفتر شما، این یعنی می‌توانید گردش کار پیچیده‌ای بسازید که چندین ابزار را با هم ترکیب می‌کند.")
    
    add_heading_3(doc, "قیمت مبتنی بر تعداد مشتری، نه کارمند")
    add_body(doc, "یکی از ویژگی‌های جذاب Pixie، قیمت‌گذاری مبتنی بر تعداد مشتری است، نه کارمند. این یعنی می‌توانید کارمندان نامحدود اضافه کنید بدون اینکه هزینه اضافی بپردازید. این مدل برای دفاتر با کارمندان فصلی یا پاره‌وقت بسیار اقتصادی است. در دفتر شما با ۵ کارمند و ۵۰ شرکت، این مدل می‌تواند هزینه را به‌طور قابل توجهی کاهش دهد.")
    add_page_break(doc)
    
    # CHAPTER 3
    add_heading_1(doc, "فصل ۳: الگوبرداری از نرم‌افزارهای آماده برای سامانه اختصاصی")
    add_body(doc, "هدف از تحلیل سه نرم‌افزار، استخراج الگوهای قابل الگوبرداری برای سامانه اختصاصی شماست. هر نرم‌افزار درسی دارد که می‌توانیم در طراحی سامانه شما به کار بگیریم. در این فصل، الگوهای مفید را از هر نرم‌افزار استخراج می‌کنیم و توضیح می‌دهیم چگونه در سامانه اختصاصی شما پیاده‌سازی شوند. در عین حال، قابلیت‌هایی که برای بازار غربی طراحی شده‌اند و در ایران کاربردی ندارند را نیز مشخص می‌کنیم.")
    
    add_heading_2(doc, "۳.۱ الگوهای قابل الگوبرداری از Financial Cents")
    
    add_heading_3(doc, "قالب‌های آماده برای کارهای حسابداری")
    add_body(doc, "اولین و مهم‌ترین الگو از Financial Cents، استفاده از قالب‌های آماده برای کارهای حسابداری است. شما می‌توانید ۱۰-۲۰ قالب برای کارهای رایج دفتر خود بسازید: ثبت اسناد ماهانه، بستن دوره فصلی، آماده‌سازی اظهارنامه مالیاتی، گزارش ماهانه به مدیر عامل، و غیره. هر قالب شامل مراحل، مسئول پیش‌فرض، مهلت نسبی و چک‌لیست است. وقتی مدیر یک کار جدید ایجاد می‌کند، فقط قالب را انتخاب می‌کند و سامانه تمام جزئیات را به‌طور خودکار پر می‌کند. این قابلیت می‌تواند زمان ایجاد کار را از ۵ دقیقه به ۱۰ ثانیه کاهش دهد.")
    
    add_heading_3(doc, "تخصیص خودکار تسک")
    add_body(doc, "الگوی دوم از Financial Cents، تخصیص خودکار تسک است. در سامانه شما، می‌توانید قاعده‌ای تعریف کنید: «شرکت A همیشه به کارمند الف ارجاع داده شود». وقتی کار جدیدی برای شرکت A ایجاد می‌شود، سامانه به‌طور خودکار کارمند الف را به‌عنوان مسئول تعیین می‌کند. این قابلیت برای دفتر شما که شرکت‌ها را از قبل بین کارمندان تقسیم کرده‌اید، ایده‌آل است. مدیر فقط شرکت را انتخاب می‌کند و سامانه به‌طور خودکار مسئول را می‌داند.")
    
    add_heading_3(doc, "نمای ظرفیت تیم در زمان واقعی")
    add_body(doc, "الگوی سوم از Financial Cents، نمای ظرفیت تیم است. در داشبورد مدیر، هر کارمند با یک نوار نشان داده می‌شود که میزان بار کاری فعلی او را نشان می‌دهد. به‌عنوان مثال، کارمند الف ۸۰٪ پر است، کارمند ب ۵۰٪ و کارمند ج ۲۰٪. وقتی مدیر می‌خواهد کار جدیدی ارجاع دهد، می‌تواند به‌سرعت ببیند کدام کارمند ظرفیت دارد. این قابلیت می‌تواند توزیع کار را عادلانه‌تر کند و از اضافه‌بار یک کارمند خاص جلوگیری کند.")
    
    add_heading_3(doc, "AI File Validator برای اکسل")
    add_body(doc, "الگوی چهارم از Financial Cents، AI File Validator است. در سامانه شما، می‌توانید یک موتور اعتبارسنجی هوشمند برای فایل‌های اکسل بسازید که قبل از رسیدن به مدیر، فایل را بررسی کند. این موتور می‌تواند: ساختار ستون‌ها را بررسی کند، تاریخ‌های نامعتبر را شناسایی کند، مبالغ غیرعددی را گزارش کند، و فایل‌های نادرست را به کارمند برگرداند. این قابلیت می‌تواند بار کاری مدیر را به‌طور قابل توجهی کاهش دهد، زیرا فایل‌های نادرست قبل از رسیدن به مدیر رد می‌شوند.")
    
    add_heading_2(doc, "۳.۲ الگوهای قابل الگوبرداری از Karbon")
    
    add_heading_3(doc, "صف FIFO برای کارهای حجم بالا")
    add_body(doc, "الگوی اول از Karbon، صف FIFO است. در سامانه شما، می‌توانید برای هر کارمند یک صف از کارهای واگذار شده بسازید. وقتی کار جدیدی به کارمند ارجاع داده می‌شود، در صف او قرار می‌گیرد. کارمند کارها را به ترتیب (FIFO) انجام می‌دهد. مدیر می‌تواند کارهای با اولویت بالا را به‌صورت دستی به بالای صف ببرد. این قابلیت برای دفتر شما با ۵۰ شرکت و کارهای ماهانه تکرارشونده ارزشمند است، زیرا کارها به‌صورت منظم بین کارمندان توزیع می‌شوند و هیچ کارمی گم نمی‌شود.")
    
    add_heading_3(doc, "قالب‌های مبتنی بر نقش")
    add_body(doc, "الگوی دوم از Karbon، قالب‌های مبتنی بر نقش است. در سامانه شما، هر قالب می‌تواند تعریف کند چه نقشی باید چه مرحله‌ای را انجام دهد. به‌عنوان مثال، در قالب «بستن دفاتر ماهانه»، مرحله «ثبت اسناد» به کارمند، مرحله «بازبینی» به سرپرست، و مرحله «تأیید نهایی» به مدیر ارجاع می‌شود. این قابلیت به‌صورت خودکار مراحل را به نقش‌های صحیح تخصیص می‌دهد و نیاز به تخصیص دستی را کاهش می‌دهد.")
    
    add_heading_3(doc, "داشبورد پیشرفت در زمان واقعی")
    add_body(doc, "الگوی سوم از Karbon، داشبورد پیشرفت است. در سامانه شما، می‌توانید یک داشبورد ایجاد کنید که وضعیت همه کارهای دفتر را در یک نمای بصری نشان دهد. هر کار به‌عنوان یک کارت با وضعیت (در حال انجام، در انتظار بازبینی، تأیید شده) نمایش داده می‌شود. مدیر می‌تواند به‌سرعت ببیند کدام کارها عقب افتاده، کدام در انتظار تأیید، و کدام تکمیل شده است. این قابلیت برای دفتر شما با ۵۰ شرکت و چندصد کار همزمان بسیار ارزشمند است.")
    
    add_heading_2(doc, "۳.۳ الگوهای قابل الگوبرداری از Pixie")
    
    add_heading_3(doc, "تفکیک تسک به مراحل با مسئول مستقل")
    add_body(doc, "مهم‌ترین الگوی Pixie برای دفتر شما، تفکیک تسک به مراحل با مسئول مستقل است. شما به‌صراحت خواستار امکان «انجام دادن قسمتی از تسک و ارجاع به همکار» بوده‌اید. این دقیقاً همان الگوی Pixie است: یک تسک به چند مرحله تقسیم می‌شود، هر مرحله مسئول مستقل دارد و ارجاع به همکار به‌سادگی امکان‌پذیر است. در سامانه شما، هر تسک می‌تواند چک‌لیستی از مراحل داشته باشد و هر مرحله به کارمند متفاوتی ارجاع داده شود. این قابلیت به‌طور مستقیم نیاز شما به ارجاع بخشی از کار را پوشش می‌دهد.")
    
    add_heading_3(doc, "شروع خودکار کارها بر اساس تاریخ‌های کلیدی")
    add_body(doc, "الگوی دوم از Pixie، شروع خودکار کارها بر اساس تاریخ‌های کلیدی است. در سامانه شما، می‌توانید برای هر شرکت تاریخ‌های کلیدی تعریف کنید (مثلاً «آخرین روز ماه» برای کار ماهانه). سامانه به‌طور خودکار کار جدید را چند روز قبل از مهلت ایجاد می‌کند. این قابلیت برای دفتر شما با ۵۰ شرکت و تاریخ‌های متفاوت بسیار ارزشمند است، زیرا نیازی نیست مدیر به یاد خودش کارهای ماهانه را ایجاد کند.")
    
    add_heading_3(doc, "یادآوری‌های خودکار به مشتری")
    add_body(doc, "الگوی سوم از Pixie، یادآوری‌های خودکار به مشتری است. در سامانه شما، می‌توانید یادآوری‌های خودکار به شرکت‌ها برای ارسال مدارک ماهانه ارسال کنید. به‌عنوان مثال، در روز ۲۵ هر ماه، سامانه به‌طور خودکار به شرکت‌ها یادآوری می‌کند که مدارک ماهانه را بفرستند. این قابلیت می‌تواند بار کاری مدیر را در پیگیری دستی کاهش دهد.")
    
    add_heading_2(doc, "۳.۴ قابلیت‌هایی که نباید الگوبرداری شوند")
    add_body(doc, "تمام قابلیت‌های این نرم‌افزارها برای دفتر شما مناسب نیستند. در ادامه، قابلیت‌هایی که نباید در سامانه شما پیاده‌سازی شوند را فهرست می‌کنیم.")
    
    skip_data = [
        ["قابلیت", "دلیل عدم الگوبرداری"],
        ["یکپارچگی با QuickBooks Online", "نرم‌افزار حسابداری شما متنوع و ایرانی است"],
        ["یکپارچگی با IRS (سازمان مالیاتی آمریکا)", "سیستم مالیاتی ایران متفاوت است"],
        ["امضای الکترونیکی برای اظهارنامه مالیاتی آمریکا", "اظهارنامه مالیاتی ایران فرمت متفاوتی دارد"],
        ["قالب‌های ۱۰۴۰ و ۱۰۹۹ (مالیات آمریکا)", "قالب‌های شما باید بر اساس فرم‌های مالیاتی ایران باشند"],
        ["پورتال مشتری عمومی (با ثبت‌نام مشتری)", "مشتریان شما شرکت‌های داخلی هستند"],
        ["صورت‌حساب و پرداخت آنلاین به مشتری", "صورت‌حساب شما به شرکت‌ها، نه به‌صورت آنلاین پرداخت می‌شود"],
        ["AI MCP برای Claude/ChatGPT/Gemini", "اطلاعات حساس حسابداری نباید به API خارجی ارسال شود"],
        ["یکپارچگی با Adobe Sign", "نیازی به امضای الکترونیکی بین‌المللی ندارید"],
        ["اپ موبایل برای مشتری", "مشتریان شما از طریق پورتال ساده و داخلی کار می‌کنند"],
    ]
    add_table_styled(doc, skip_data, col_widths_cm=[6, 11])
    
    add_callout(doc, "اصل کلیدی: ما از نرم‌افزارهای آماده الگوبرداری می‌کنیم، نه کپی‌برداری. یعنی قابلیت‌هایی که با نیازهای دفتر شما سازگار هستند را با معماری اختصاصی پیاده‌سازی می‌کنیم، نه به‌صورت آماده. این رویکرد، بهترین‌های هر دو دنیا را به شما می‌دهد: بلوغ نرم‌افزارهای آماده + تطبیق کامل با نیازهای خاص شما.", 'info')
    add_page_break(doc)
    
    # CHAPTER 4
    add_heading_1(doc, "فصل ۴: معماری نهایی سامانه - به‌روزرسانی با تمام تصمیمات")
    add_body(doc, "معماری نهایی سامانه بر اساس تمام تصمیمات راهبردی شما طراحی شده است. این معماری بر چهار اصل استوار است: مدیریت کارها از هر جایی قابل انجام باشد، فایل‌های اکسل و ریز اسناد داخل دفتر بمانند، هر گزارش کارمند با اطلاعات واقعی قابل مقایسه باشد، و هر تغییر سابقه غیرقابل‌حذف داشته باشد. این معماری برای ۵ کارمند، ۵۰ شرکت و کمتر از ۱۰ هزار ردیف سند در روز، انتخابی منطقی و مقیاس‌پذیر است.")
    
    add_heading_2(doc, "۴.۱ معماری کلی - سرور مرکزی + عامل محلی")
    add_body(doc, "سامانه از دو بخش مجزا تشکیل شده است. سرور مرکزی مدیریت کارها، وضعیت‌ها، تأییدها و اعلان‌ها را بر عهده دارد و در فضای ابری (ترجیحاً Cloud خصوصی ایران) مستقر است. عامل محلی در دفتر شما نصب می‌شود و مسئولیت دریافت فایل‌های اکسل، پردازش محلی، تطبیق با منابع حسابداری و ذخیره ریز اسناد را بر عهده دارد. این جداسازی، حریم خصوصی اطلاعات حساس را تضمین می‌کند: ریز اسناد، شرح سند، شماره حساب و مبالغ هرگز از دفتر خارج نمی‌شوند.")
    
    arch_data = [
        ["لایه معماری"],
        ["لایه ۱: کاربران (کارمند، سرپرست، مدیرعامل) - مرورگر وب + VPN برای مدیر خارج دفتر"],
        ["لایه ۲: سرور مرکزی - Task API + Identity API + Workflow API + Metadata DB"],
        ["لایه ۳: عامل محلی در دفتر - API محلی + صف پردازش + موتور تطبیق + Local PostgreSQL"],
        ["لایه ۴: اتصال‌دهنده‌ها - Adapter API | Adapter DB فقط‌خواندنی | Adapter خروجی Excel/CSV"],
        ["لایه ۵: منابع داده - دیتابیس همکاران/سپیدار/تندیس | فایل‌های اکسل هلو | سایر"],
    ]
    add_table_styled(doc, arch_data, col_widths_cm=[17])
    
    add_heading_2(doc, "۴.۲ مرز قطعی داده‌ها")
    add_body(doc, "جدول زیر به‌طور دقیق مشخص می‌کند هر نوع اطلاعات کجا ذخیره شود. این جدول، قلب امنیت سامانه است و هرگونه تخلف از آن باید به‌عنوان نقض امنیتی گزارش شود.")
    
    border_data = [
        ["نوع اطلاعات", "سرور مرکزی", "داخل دفتر"],
        ["کاربران، نقش‌ها، فهرست شرکت‌ها", "بله", "اطلاعات مجوز محلی"],
        ["شرح وظیفه، مسئول، مهلت، وضعیت", "بله", "در صورت نیاز، کش"],
        ["نمره ۰-۱۰۰ مدیر به هر تسک", "بله", "—"],
        ["یادداشت قابل مشاهده برای کارمند", "بله", "—"],
        ["یادداشت محرمانه مدیریتی", "بله", "—"],
        ["دلیل رد یا بازگشت تسک", "بله", "—"],
        ["فایل اکسل اصلی کارمند", "خیر", "بله"],
        ["فایل مرجع مدیر (نسخه‌بندی‌شده)", "خیر", "بله"],
        ["ریز ردیف‌های سند (حساب، شرح، مبلغ)", "خیر", "بله"],
        ["رمزها و اطلاعات اتصال حسابداری", "خیر", "بله (مخزن اسرار)"],
        ["جزئیات هر مغایرت", "خیر", "بله"],
        ["وضعیت کلی کار و نتیجه کنترل", "خلاصه مجاز", "بله"],
        ["گزارش تفصیلی مغایرت برای مدیر", "خیر", "بله (از طریق VPN)"],
        ["لاگ عملیات و تأییدها", "بله", "بله (رویدادهای محلی)"],
    ]
    add_table_styled(doc, border_data, col_widths_cm=[7, 5, 5])
    
    add_callout(doc, "قاعده قطعی: هیچ ریز سند حسابداری، شرح، شماره حساب یا مبلغ نباید به سرور مرکزی ارسال شود. اگر مدیر خارج دفتر نیاز به مشاهده جزئیات داشته باشد، از طریق VPN به پنل محلی متصل می‌شود، نه با کپی داده به ابر.", 'danger')
    
    add_heading_2(doc, "۴.۳ پروتکل ارتباط عامل محلی با سرور مرکزی")
    add_body(doc, "عامل محلی ارتباط را آغاز می‌کند؛ سرور مرکزی اتصال مستقیمی به دیتابیس یا رایانه‌های حسابداری برقرار نمی‌کند. این الگو (Outbound-only) امنیت را به‌طور قابل توجهی افزایش می‌دهد، زیرا دیتابیس حسابداری هرگز به اینترنت باز نمی‌شود. عامل محلی به‌صورت دوره‌ای (مثلاً هر ۳۰ ثانیه) درخواست‌های جدید را از سرور مرکزی دریافت می‌کند، پردازش محلی را انجام می‌دهد و نتایج را به سرور ارسال می‌کند. اگر اینترنت قطع شود، عامل محلی درخواست‌ها را در صف محلی نگه می‌دارد و پس از اتصال مجدد ارسال می‌کند.")
    add_page_break(doc)
    
    # CHAPTER 5
    add_heading_1(doc, "فصل ۵: مدل داده و جداول - به‌روزرسانی با تصمیمات نهایی")
    add_body(doc, "در این فصل، مدل داده دقیق سامانه را بر اساس تمام تصمیمات نهایی ارائه می‌دهیم. مدل داده به دو بخش کاملاً مجزا تقسیم می‌شود: جداول سرور مرکزی برای مدیریت کارها و جداول سرور محلی برای اطلاعات حسابداری. این جداسازی هم امنیت را بهبود می‌بخشد و هم توسعه آینده را ساده می‌کند. تمام جداول بر اساس PostgreSQL طراحی شده‌اند.")
    
    add_heading_2(doc, "۵.۱ جداول سرور مرکزی")
    add_body(doc, "جدول زیر جداول اصلی سرور مرکزی را با ستون‌ها و قواعد اصلی نشان می‌دهد. این جداول اطلاعات عملیاتی دفتر را نگه می‌دارند و هیچ ریز سند حسابداری در آن‌ها ذخیره نمی‌شود.")
    
    central_tables = [
        ["جدول", "ستون‌های اصلی", "قواعد کلیدی"],
        ["users", "id، username، display_name، role، is_active", "نقش: employee/supervisor/ceo/admin"],
        ["companies", "id، company_code، display_name، is_active", "هر شرکت شناسه مستقل دارد"],
        ["user_company_access", "user_id، company_id، permission_set", "کلید یکتای (user_id, company_id)"],
        ["fiscal_periods", "id، company_id، start_date، end_date، name", "سال مالی هر شرکت"],
        ["tasks", "id، company_id، title، created_by، due_at، priority، status، template_id", "وضعیت: ۱۰ مقدار مختلف"],
        ["task_assignments", "task_id، user_id، assignment_type، assigned_at", "type: primary/collaborator/reviewer"],
        ["task_checklist_items", "id، task_id， title， assigned_to， is_completed", "تفکیک تسک به مراحل"],
        ["work_submissions", "id، task_id، submitted_by، period_start، period_end， local_job_id، status، submission_score (0-100)", "نمره مدیر ۰-۱۰۰"],
        ["manager_decisions", "id، submission_id، reviewer_id، decision_type， reason_visible， reason_confidential، score (0-100)", "تصمیم مدیر با دو دلیل"],
        ["reference_versions", "id، company_id， fiscal_period_id， version_number، uploaded_by، file_hash", "نسخه‌بندی فایل مرجع"],
        ["task_reference_bindings", "task_id， reference_version_id، bound_at", "هر تسک به نسخه مشخصی متصل"],
        ["reconciliation_runs", "id، submission_id， reference_version_id، algorithm_version， status", "هر اجرای تطبیق مستقل"],
        ["notifications", "id， user_id， event_key， type， read_at", "کلید یکتای رویداد"],
        ["leave_requests", "id， user_id， start_at， end_at， reason_code， status", "گردش تأیید مرخصی"],
        ["attendance_records", "id， user_id， event_type， event_time， source", "ورود/خروج"],
        ["audit_events", "id， actor_id， action， object_type， object_id， occurred_at", "غیرقابل‌حذف"],
        ["local_agent_status", "agent_id， last_seen_at， agent_version， health_status", "وضعیت عامل محلی"],
    ]
    add_table_styled(doc, central_tables, col_widths_cm=[3.5, 7, 5.5])
    
    add_callout(doc, "نکته مهم: جدول work_submissions شامل ستون submission_score (نمره ۰-۱۰۰) است که مستقل از وضعیت تأیید است. این ستون به مدیر اجازه می‌دهد کیفیت کار را به‌صورت پیوسته اندازه بگیرد، نه فقط باینری (تأیید/رد).", 'info')
    
    add_heading_2(doc, "۵.۲ جداول سرور محلی")
    add_body(doc, "جدول زیر جداول اصلی سرور محلی را نشان می‌دهد. تمام اطلاعات حساس حسابداری در این جداول ذخیره می‌شوند و هرگز به سرور مرکزی ارسال نمی‌شوند.")
    
    local_tables = [
        ["جدول", "ستون‌های اصلی", "کاربرد"],
        ["local_companies", "company_id، company_code، display_name، active", "مطابقت با شرکت‌های مرکزی"],
        ["source_connections", "id، company_id، source_type， config_ref， enabled， last_success_at", "تنظیمات اتصال هر نرم‌افزار"],
        ["source_sync_runs", "id، connection_id، started_at， finished_at， status， cursor_before， cursor_after", "تاریخچه دریافت اطلاعات"],
        ["source_documents", "id， company_id， source_id， document_id， document_number， document_date， fiscal_year_id", "اسناد از منبع"],
        ["source_entries", "id， document_id， line_id， account_code， description， debit_minor， credit_minor， row_fingerprint， modified_at", "ردیف‌های سند از مبدأ"],
        ["reference_files", "id， reference_version_id， original_filename， file_hash， stored_path， schema_version， status", "فایل‌های مرجع مدیر"],
        ["reference_entries", "id， reference_file_id， source_line_key， document_number， document_date， line_number， account_code， description， debit， credit", "ردیف‌های استخراج‌شده از مرجع"],
        ["import_jobs", "id， company_id， task_id， submitted_by， file_hash， schema_version， status", "هر بارگذاری اکسل کارمند"],
        ["import_entries", "id， job_id， source_line_key， document_number， document_date， line_number， account_code، description， debit， credit", "ردیف‌های اکسل کارمند"],
        ["reconciliation_runs", "id， job_id， reference_file_id， algorithm_version， status", "هر اجرای تطبیق"],
        ["reconciliation_diffs", "id， run_id， diff_type， source_line_key， field_name， expected_value， actual_value， severity", "جزئیات مغایرت‌ها"],
        ["record_versions", "id， entity_type， entity_id， version_number， change_reason", "نسخه‌های اصلاح‌شده"],
        ["local_audit_events", "id， actor_id， action， object_type， object_id， occurred_at", "تاریخچه عملیات محلی"],
        ["idempotency_keys", "key， operation， result_ref， created_at， expires_at", "جلوگیری از پردازش تکراری"],
    ]
    add_table_styled(doc, local_tables, col_widths_cm=[3.5, 8, 4.5])
    
    add_heading_2(doc, "۵.۳ قرارداد استاندارد ردیف حسابداری")
    add_body(doc, "تمام اتصال‌دهنده‌ها (چه از SQL Server، چه از Excel، چه از API) باید خروجی یکسان تولید کنند. تفاوت نرم‌افزارها نباید به موتور تطبیق منتقل شود. این قرارداد، قلب لایه استانداردسازی است. مبالغ به‌صورت رشته عددی اعشاری منتقل شوند (نه float) تا خطای ممیز شناور ایجاد نشود. تاریخ داخلی ISO 8601 باشد. line_id باید شناسه واقعی ردیف از دیتابیس مبدأ باشد.")
    add_callout(doc, "قاعده کلیدی: line_id باید شناسه واقعی ردیف از دیتابیس مبدأ باشد. مطابق تصمیم شما، این شناسه پس از حذف و ثبت مجدد سند تغییر می‌کند. این رفتار، تشخیص اصلاح از تکرار را ممکن می‌کند، اما نیاز به تطبیق احتمالی با سایر فیلدها دارد.", 'warn')
    add_page_break(doc)
    
    # CHAPTER 6
    add_heading_1(doc, "فصل ۶: فایل مرجع اختیاری و تصمیم مدیر - قابلیت‌های جدید")
    add_body(doc, "این فصل، قابلیت‌های جدیدی را که شما در گفت‌وگوهای راهبردی تأیید کرده‌اید، تشریح می‌کند. این قابلیت‌ها سامانه را از یک ابزار تطبیق اکسل ساده به یک سامانه کامل مدیریت وظایف، تأیید کار و ارزیابی عملکرد تبدیل می‌کنند.")
    
    add_heading_2(doc, "۶.۱ فایل مرجع اختیاری")
    add_body(doc, "مهم‌ترین تصمیم شما، اختیاری بودن فایل مرجع است. مدیر هر زمان که بخواهد کاری را راستی‌آزمایی کند، فایل مرجع را بارگذاری می‌کند. اگر نخواهد تطبیق اکسل انجام دهد، می‌تواند بدون فایل مرجع هم کار را تأیید کند. این تصمیم، گردش کار تصمیم مدیر را به‌طور قابل توجهی ساده و انعطاف‌پذیر می‌کند. در عمل، مدیر می‌تواند با تکیه بر اعتماد یا مشاهده سریع، کار را تأیید کند و فقط برای کارهای مشکوک یا مهم، فایل مرجع را بارگذاری نماید.")
    
    add_heading_2(doc, "۶.۲ نسخه‌بندی فایل مرجع")
    add_body(doc, "هر بار که مدیر فایل مرجع جدیدی برای یک شرکت و دوره مالی بارگذاری می‌کند، یک نسخه جدید ایجاد می‌شود. نسخه قبلی حذف یا بازنویسی نمی‌شود. این قابلیت چندین مزیت دارد. اول، تسک‌های قبلی که با نسخه قدیمی تأیید شده‌اند، همچنان به همان نسخه متصل هستند و تاریخچه ممیزی آن‌ها حفظ می‌شود. دوم، چندین تسک می‌توانند از یک نسخه مرجع استفاده کنند، که از بارگذاری تکراری فایل‌ها جلوگیری می‌کند. سوم، اگر مدیر فایل مرجع را به‌روزرسانی کند، تأییدهای قبلی خودکار تغییر نمی‌کنند؛ برای بررسی مجدد باید نسخه جدید صراحتاً انتخاب شود.")
    
    add_heading_2(doc, "۶.۳ امتیاز ۰ تا ۱۰۰ مستقل از تأیید")
    add_body(doc, "شما تصمیم گرفتید که امتیاز هر تسک عددی از ۰ تا ۱۰۰ است که مدیر تعیین می‌کند. این امتیاز، وضعیت تأیید و نتیجه تطبیق سه مفهوم مستقل هستند. تأیید کار لزوماً به معنی امتیاز ۱۰۰ نیست. این تصمیم، چارچوب ارزیابی پرسنل را به‌طور بنیادی تغییر می‌دهد. به‌عنوان مثال، مدیر می‌تواند کار را تأیید کند اما امتیاز ۷۵ بدهد، که نشان‌دهنده کیفیت متوسط کار است. این امتیاز در ارزیابی ماهانه و سالانه کارمند لحاظ می‌شود.")
    
    add_heading_2(doc, "۶.۴ یادداشت دو سطحی")
    add_body(doc, "شما خواستار یادداشت با دو سطح دسترسی بودید. مدیر می‌تواند یادداشت قابل مشاهده برای کارمند یا یادداشت محرمانه مدیریتی ثبت کند. یادداشت محرمانه در پنل کارمند، خروجی‌های قابل مشاهده او و اعلان‌های ارسالی نمایش داده نمی‌شود. این قابلیت به مدیر اجازه می‌دهد یادداشت‌های خصوصی برای خودش بنویسد (مثلاً «این کارمند معمولاً در ثبت اسناد پیچیده اشتباه می‌کند») بدون اینکه کارمند آن را ببیند. در عین حال، یادداشت قابل مشاهده به کارمند کمک می‌کند بداند چه چیزی خوب انجام شده و چه چیزی نیاز به بهبود دارد.")
    
    add_heading_2(doc, "۶.۵ دلیل اجباری برای رد یا بازگشت")
    add_body(doc, "شما تصمیم گرفتید که در صورت عدم تأیید یا بازگرداندن کار، مدیر باید دلیل روشن و قابل فهم بنویسد. کارمند باید بداند چه چیزی اشتباه بوده، چه اصلاحی لازم است و تا چه زمانی باید آن را انجام دهد. این قابلیت دو هدف دارد. اول، به کارمند کمک می‌کند اشتباه خود را بفهمد و آن را اصلاح کند. دوم، در ارزیابی عملکرد، الگوی اشتباهات مکرر را شناسایی می‌کند. به‌عنوان مثال، اگر کارمند الف سه بار در ماه به‌دلیل «تاریخ اشتباه در سند» برگشت داده شود، مدیر می‌تواند این الگو را شناسایی و با کارمند گفت‌وگو کند.")
    
    add_heading_2(doc, "۶.۶ چهار نوع تصمیم مدیر")
    add_body(doc, "بر اساس تصمیمات شما، مدیر می‌تواند چهار نوع تصمیم برای هر تسک بگیرد. جدول زیر این چهار نوع و اثر هرکدام بر ارزیابی را نشان می‌دهد.")
    
    decisions_data = [
        ["نوع تصمیم", "توضیح", "اثر بر ارزیابی", "نیاز به مرجع", "نیاز به دلیل"],
        ["تأیید عادی", "کار بدون اشکال پذیرفته می‌شود", "نمره ۰-۱۰۰ مدیر", "اختیاری", "خیر"],
        ["تأیید با ارفاق", "کار با اختلاف قابل قبول پذیرفته می‌شود", "نمره + ثبت دلیل ارفاق", "اختیاری", "بله (دلیل ارفاق)"],
        ["بازگشت به کارمند", "کار برای اصلاح برمی‌گردد", "نمره + ثبت دلیل بازگشت", "اختیاری", "بله (دلیل و مهلت)"],
        ["عدم تأیید نهایی", "کار قابل قبول نیست", "نمره ۰ + ثبت دلیل نهایی", "اختیاری", "بله (دلیل نهایی)"],
    ]
    add_table_styled(doc, decisions_data, col_widths_cm=[3, 4, 4, 2.5, 2.5])
    
    add_callout(doc, "قاعده حیاتی: امتیاز منفی خودکار صرفاً بر اساس تعداد اختلاف‌ها اعمال نمی‌شود. مدیر باید بتواند علت و میزان اثر را مشخص کند. یک اختلاف مهم با چند اختلاف جزئی ارزش یکسانی ندارد.", 'warn')
    add_page_break(doc)
    
    # CHAPTER 7
    add_heading_1(doc, "فصل ۷: الگوریتم تطبیق با شناسه ردیف مبدأ")
    add_body(doc, "در این فصل، الگوریتم دقیق تطبیق ردیف‌ها را بر اساس تصمیم نهایی شما (شناسه ردیف از دیتابیس مبدأ) تشریح می‌کنیم. این الگوریتم، قلب موتور کنترل هوشمند است و باید به‌دقت طراحی شود تا اصلاح سند را از تکرار واقعی تشخیص دهد.")
    
    add_heading_2(doc, "۷.۱ کلید تطبیق اصلی")
    add_body(doc, "مطابق تصمیم شما، شناسه ردیف از دیتابیس مبدأ کلید اصلی تطبیق است. کلید کامل شامل ترکیب زیر است:")
    add_body(doc, "کلید = CompanyID + SourceDatabaseID + FiscalYearID + SourceLineID", justify=False)
    add_body(doc, "این کلید چهار جزء دارد تا یکتایی آن تضمین شود. شناسه ردیف به‌تنهایی کافی نیست، زیرا ممکن است دو دیتابیس شناسه‌های عددی مشابه داشته باشند. با ترکیب شرکت، دیتابیس مبدأ، سال مالی و شناسه ردیف، یکتایی کامل تضمین می‌شود.")
    
    add_heading_2(doc, "۷.۲ چالش تغییر شناسه پس از حذف-ثبت مجدد")
    add_body(doc, "شما تأیید کردید که شناسه ردیف پس از حذف و ثبت مجدد سند تغییر می‌کند. این رفتار چالش اصلی الگوریتم است: اگر کارمند سندی را در نرم‌افزار حسابداری حذف و دوباره ثبت کند، شناسه ردیف جدید متفاوت از شناسه قبلی است. سامانه باید بتواند این حالت را از «سند واقعاً جدید» تشخیص دهد.")
    add_body(doc, "راهکار ما سه مرحله‌ای است. اول، اگر شناسه ردیف در فایل اکسل و دیتابیس مبدأ یکسان است، مستقیماً تطبیق می‌شود. دوم، اگر شناسه ردیف در دیتابیس مبدأ حذف شده و شناسه جدیدی با مقادیر مشابه ایجاد شده، تطبیق احتمالی با سایر فیلدها (تاریخ، شماره سند، حساب‌ها، مبلغ، شرح) انجام می‌شود. سوم، اگر تطبیق احتمالی قوی باشد (مثلاً ۸ از ۹ فیلد منطبق)، سامانه آن را به‌عنوان «جایگزینی احتمالی» گزارش می‌کند، اما خودکار تأیید نمی‌کند؛ تصمیم نهایی با مدیر است.")
    
    add_heading_2(doc, "۷.۳ نه مرحله الگوریتم")
    steps = [
        "ثبت تحویل: شناسه تحویل، کارمند، شرکت، دوره ادعایی، هش فایل SHA-256، وضعیت RECEIVED",
        "اعتبارسنجی قالب: نوع فایل، ستون‌های اجباری، نوع داده‌ها، تاریخ‌های شمسی/میلادی، مبالغ عددی",
        "کنترل تکراری فایل: هش فایل در برابر تحویل‌های قبلی همان شرکت بررسی می‌شود",
        "کنترل تکراری ردیف در فایل: ردیف‌هایی با تمام فیلدهای یکسان شناسایی می‌شوند",
        "کنترل بازه تاریخی: حداقل و حداکثر تاریخ فایل با بازه ادعایی کارمند مقایسه می‌شود",
        "دریافت داده مرجع: از فایل مرجع مدیر (در صورت بارگذاری) یا مستقیماً از دیتابیس مبدأ",
        "مقایسه کلید به کلید: کلید تطبیق (شرکت + دیتابیس + سال مالی + شناسه ردیف) در دو مجموعه ساخته می‌شود",
        "تشخیص مغایرت: ردیف‌های فقط در اکسل، فقط در مرجع، و ردیف‌های مشترک با مقادیر متفاوت شناسایی می‌شوند",
        "تشخیص اصلاح از تکرار: سه حالت (ردیف یکسان، جایگزینی احتمالی، ردیف واقعاً جدید) تفکیک می‌شوند",
    ]
    for i, s in enumerate(steps):
        add_numbered(doc, s, fa_nums[i])
    
    add_heading_2(doc, "۷.۴ قواعد تشخیص مغایرت")
    add_body(doc, "مهم‌ترین قاعده: پیدا نشدن ردیف در فایل مرجع، به‌تنهایی اثبات نمی‌کند که کارمند اشتباه کرده است. ممکن است فایل مدیر ناقص باشد یا محدوده زمانی دو فایل متفاوت باشد. در این حالت، نتیجه باید «نیازمند بررسی بیشتر» باشد، نه «مغایرت قطعی».")
    add_body(doc, "همچنین، قطع ارتباط با منبع نباید به‌عنوان «سند مفقود» گزارش شود. اگر دیتابیس مبدأ قطع باشد، نتیجه باید «کنترل انجام نشد» یا «دریافت ناقص» باشد. فقط وقتی دریافت منبع کامل و معتبر است، می‌توان نتیجه مقایسه را مغایرت واقعی تلقی کرد. این تفکیک خطای فنی از مغایرت حسابداری، از هشدارهای کاذب به مدیر جلوگیری می‌کند.")
    
    add_heading_2(doc, "۷.۵ وضعیت‌های استاندارد تطبیق")
    status_data = [
        ["وضعیت", "معنی", "اقدام مدیر"],
        ["RECEIVED", "فایل دریافت شده است", "—"],
        ["INVALID_FILE", "ساختار فایل معتبر نیست", "اطلاع به کارمند"],
        ["DUPLICATE_SUBMISSION", "فایل تکراری شناسایی شده", "اطلاع به کارمند"],
        ["PROCESSING", "در حال پردازش است", "صبر"],
        ["SOURCE_UNAVAILABLE", "منبع در دسترس نیست", "تلاش مجدد"],
        ["SOURCE_STALE", "داده منبع قدیمی است", "به‌روزرسانی منبع"],
        ["MISMATCH_FOUND", "مغایرت واقعی نیازمند بررسی", "بررسی و تصمیم"],
        ["NEEDS_REVIEW", "نتیجه قطعی نیست", "بررسی دستی"],
        ["VERIFIED", "کنترل‌ها موفق بوده‌اند", "تأیید نهایی"],
        ["APPROVED", "مدیر تأیید کرده", "—"],
        ["APPROVED_WITH_EXCEPTION", "با ارفاق تأیید شده", "ثبت دلیل ارفاق"],
        ["RETURNED", "برگشتی به کارمند", "ثبت دلیل بازگشت"],
        ["REJECTED", "رد نهایی شده", "ثبت دلیل رد"],
    ]
    add_table_styled(doc, status_data, col_widths_cm=[4, 6.5, 5.5])
    
    add_callout(doc, "قاعده مهم: VERIFIED به معنی تأیید صحت همه ابعاد حسابداری نیست؛ فقط یعنی کنترل‌های مشخص‌شده موفق بوده‌اند. تأیید مدیریتی مرحله جداگانه‌ای است که با تصمیم مدیر (تأیید/رد/بازگشت) ثبت می‌شود.", 'info')
    add_page_break(doc)
    
    # CHAPTER 8
    add_heading_1(doc, "فصل ۸: چارچوب ارزیابی پرسنل با نمره ۰-۱۰۰")
    add_body(doc, "چارچوب ارزیابی پرسنل در نسخه ۲ به‌طور قابل توجهی بهبود یافته است. مطابق تصمیم شما، نمره ۰-۱۰۰ مدیر به هر تسک، محور اصلی ارزیابی است. این نمره به‌صورت پیوسته کیفیت کار را اندازه می‌گیرد و در ارزیابی ماهانه و سالانه لحاظ می‌شود. در این فصل، چارچوب کامل ارزیابی را تشریح می‌کنیم.")
    
    add_heading_2(doc, "۸.۱ چهار شاخص اصلی عملکرد (KPI)")
    add_body(doc, "چارچوب ارزیابی شامل چهار شاخص وزن‌دار است. نمره ۰-۱۰۰ مدیر، محور شاخص «کیفیت کار» است و وزن ۴۰٪ دارد. سایر شاخص‌ها به‌صورت خودکار از سامانه محاسبه می‌شوند.")
    
    kpi_data = [
        ["شاخص", "وزن", "تعریف", "روش اندازه‌گیری"],
        ["کیفیت کار (نمره مدیر)", "۴۰٪", "میانگین نمره ۰-۱۰۰ مدیر به تسک‌های تأییدشده", "اتوماتیک از manager_decisions"],
        ["تحویل به‌موقع", "۲۵٪", "نسبت تسک‌های تحویلی در مهلت به کل تسک‌ها", "اتوماتیک از تاریخ تحویل"],
        ["حجم/پیچیدگی کار", "۲۰٪", "حجم کار استانداردشده با ضریب پیچیدگی", "نیمه‌خودکار + تأیید مدیر"],
        ["همکاری و ارجاع صحیح", "۱۵٪", "کیفیت ارجاع‌ها و تحویل منظم مراحل", "ارزیابی کیفی ماهانه مدیر"],
    ]
    add_table_styled(doc, kpi_data, col_widths_cm=[3.8, 1.2, 6, 5])
    
    add_heading_2(doc, "۸.۲ محاسبه نمره کل ماهانه")
    add_body(doc, "نمره کل ماهانه هر کارمند از ترکیب چهار شاخص با وزن‌های مشخص محاسبه می‌شود. به‌عنوان مثال، اگر کارمند الف در ماه مهر داشته باشد: نمره کیفیت ۸۲ (میانگین نمره مدیر به ۲۰ تسک)، تحویل به‌موقع ۹۰٪، حجم/پیچیدگی ۸۵، همکاری ۸۸، نمره کل برابر خواهد بود با: (۸۲×۰.۴ + ۹۰×۰.۲۵ + ۸۵×۰.۲ + ۸۸×۰.۱۵) = ۸۵.۹. این نمره در داشبورد مدیر نمایش داده می‌شود و با سایر کارمندان مقایسه می‌گردد.")
    
    add_heading_2(doc, "۸.۳ نمونه کارت امتیاز ماهانه")
    scorecard_data = [
        ["شاخص", "امتیاز ماه", "وزن", "امتیاز وزن‌دار", "تغییر نسبت به قبل"],
        ["کیفیت کار (نمره مدیر)", "۸۲", "۴۰٪", "۳۲٫۸", "+۳"],
        ["تحویل به‌موقع", "۹۰", "۲۵٪", "۲۲٫۵", "+۵"],
        ["حجم/پیچیدگی", "۸۵", "۲۰٪", "۱۷٫۰", "-۲"],
        ["همکاری", "۸۸", "۱۵٪", "۱۳٫۲", "+۱"],
        ["نمره کل ماه", "—", "۱۰۰٪", "۸۵٫۵", "+۳٫۲"],
        ["رتبه در دفتر", "—", "—", "۲ از ۵", "—"],
        ["تعداد تسک‌های تأییدشده", "۲۰", "—", "—", "+۴"],
        ["تعداد تسک‌های برگشتی", "۳", "—", "—", "-۱"],
        ["تعداد تسک‌های با ارفاق", "۲", "—", "—", "۰"],
    ]
    add_table_styled(doc, scorecard_data, col_widths_cm=[4.5, 2.5, 2, 3, 4])
    
    add_heading_2(doc, "۸.۴ گزارش دلایل رد و بازگشت")
    add_body(doc, "یکی از قابلیت‌های ارزشمند سامانه، گزارش دلایل رد و بازگشت است. مدیر می‌تواند در پایان ماه ببیند چه دلاینی بیشترین فراوانی را داشته‌اند. به‌عنوان مثال، اگر ۸ از ۱۰ برگشتی به‌دلیل «تاریخ اشتباه» بوده، مدیر می‌تواند با کارمند گفت‌وگو کند و آموزش لازم را ارائه دهد. این گزارش، بهبود مستمر عملکرد را ممکن می‌کند.")
    
    reasons_data = [
        ["دلیل رد/بازگشت", "تعداد در ماه", "درصد", "کارمندان تأثیرپذیرفته", "اقدام پیشنهادی"],
        ["تاریخ اشتباه در سند", "۸", "۴۰٪", "الف (۵)، ب (۳)", "آموزش تاریخ شمسی"],
        ["مبلغ بده/بستان نامتعادل", "۴", "۲۰٪", "ج (۳)، د (۱)", "بازبینی فرمول تراز"],
        ["شرح سند ناقص", "۳", "۱۵٪", "الف (۲)، ه (۱)", "آموزش نوشتن شرح"],
        ["شماره سند تکراری", "۲", "۱۰٪", "ب (۲)", "کنترل خودکار"],
        ["سند مفقود از فایل", "۲", "۱۰٪", "ج (۲)", "بازبینی جمع‌آوری"],
        ["سایر دلایل", "۱", "۵٪", "د (۱)", "—"],
    ]
    add_table_styled(doc, reasons_data, col_widths_cm=[4, 2, 1.5, 4, 4.5])
    
    add_callout(doc, "اصل ارزیابی: ارزیابی منصفانه است. امتیاز منفی خودکار صرفاً بر اساس تعداد اختلاف‌ها اعمال نمی‌شود. مدیر باید بتواند علت و میزان اثر را مشخص کند. این اصل، اعتماد کارمندان به سامانه ارزیابی را حفظ می‌کند.", 'info')
    add_page_break(doc)
    
    # CHAPTER 9
    add_heading_1(doc, "فصل ۹: الگوی اکسل با شناسه ردیف مبدأ")
    add_body(doc, "قالب اکسل کارمند در نسخه ۲ به‌روزرسانی شده است. مطابق تصمیم شما، ستون «شناسه ردیف سند مبدأ» به‌عنوان اولین ستون و کلید اصلی تشخیص تکراری اضافه شده است. این شناسه از دیتابیس مبدأ (نرم‌افزار حسابداری) استخراج می‌شود و پس از حذف-ثبت مجدد تغییر می‌کند.")
    
    add_heading_2(doc, "۹.۱ ساختار ستون‌های اکسل")
    columns_data = [
        ["شماره", "نام ستون", "نوع داده", "الزامی", "قواعد اعتبارسنجی"],
        ["۱", "شناسه ردیف مبدأ (SourceLineID)", "متن/عدد", "بله", "از دیتابیس مبدأ؛ پس از حذف-ثبت مجدد تغییر می‌کند"],
        ["۲", "شناسه سند مبدأ (SourceDocumentID)", "متن/عدد", "بله", "از دیتابیس مبدأ؛ یکتا در همان سال مالی"],
        ["۳", "ردیف (LineNumber)", "عدد صحیح", "بله", "شماره ردیف نمایشی در سند"],
        ["۴", "شماره سند (DocumentNumber)", "متن/عدد", "بله", "ممکن است پس از حذف-ثبت مجدد تغییر کند"],
        ["۵", "تاریخ سند (DocumentDate)", "تاریخ شمسی", "بله", "فرمت YYYY/MM/DD؛ معتبر و قابل تبدیل"],
        ["۶", "کد کل (AccountLevel1)", "متن/عدد", "بله", "کد حساب کل؛ باید در طرح حساب باشد"],
        ["۷", "کد معین (AccountLevel2)", "متن/عدد", "بله", "کد حساب معین؛ زیرمجموعه کد کل"],
        ["۸", "کد تفصیل (AccountLevel3)", "متن/عدد", "خیر", "کد تفصیل (در صورت پشتیبانی)"],
        ["۹", "شرح سند (Description)", "متن", "خیر", "حداکثر ۵۰۰ کاراکتر"],
        ["۱۰", "بدهکار (Debit)", "عدد اعشاری", "بله*", "دقیقاً یکی از بده یا بستان باید صفر"],
        ["۱۱", "بستانکار (Credit)", "عدد اعشاری", "بله*", "دقیقاً یکی از بده یا بستان باید صفر"],
    ]
    add_table_styled(doc, columns_data, col_widths_cm=[1, 4, 2.2, 1.4, 8])
    
    add_heading_2(doc, "۹.۲ نمونه فایل اکسل استاندارد")
    add_body(doc, "نمونه زیر چهار ردیف فرضی از فایل اکسل یک شرکت را نشان می‌دهد. این نمونه صرفاً برای نمایش قالب است و اعداد واقعی نیستند.")
    
    sample_data = [
        ["SourceLineID", "DocID", "ردیف", "شماره سند", "تاریخ", "کل", "معین", "تفصیل", "شرح", "بده", "بس"],
        ["LID-1001", "DID-101", "۱", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۱", "۱۰۱", "۱۰۱۰۱", "فروش نقدی", "۵٬۰۰۰٬۰۰۰", "۰"],
        ["LID-1002", "DID-101", "۲", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۵", "۵۰۱", "۵۰۱۰۱", "دریافت نقدی", "۰", "۵٬۰۰۰٬۰۰۰"],
        ["LID-1003", "DID-102", "۱", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۲", "۲۰۱", "۲۰۱۰۱", "خرید کالا", "۰", "۳٬۰۰۰٬۰۰۰"],
        ["LID-1004", "DID-102", "۲", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۴", "۴۰۱", "۴۰۱۰۱", "پرداخت نقدی", "۳٬۰۰۰٬۰۰۰", "۰"],
    ]
    add_table_styled(doc, sample_data, col_widths_cm=[1.5, 1.3, 0.9, 1.3, 1.5, 0.8, 0.8, 1.0, 3.2, 1.7, 1.7])
    
    add_callout(doc, "نکته مهم: ستون SourceLineID از دیتابیس مبدأ استخراج می‌شود. اگر کارمند سندی را حذف و دوباره ثبت کند، SourceLineID جدید متفاوت است. سامانه با تطبیق احتمالی (تاریخ، شماره سند، حساب، مبلغ) این حالت را از سند واقعاً جدید تشخیص می‌دهد، اما خودکار تأیید نمی‌کند؛ تصمیم نهایی با مدیر است.", 'warn')
    add_page_break(doc)
    
    # CHAPTER 10
    add_heading_1(doc, "فصل ۱۰: نقشه راه پیاده‌سازی فازبندی‌شده - به‌روزرسانی شده")
    add_body(doc, "نقشه راه پیاده‌سازی در نسخه ۲ بر اساس تمام تصمیمات نهایی به‌روزرسانی شده است. سامانه در پنج فاز پیاده‌سازی می‌شود، به‌گونه‌ای که هر فاز خروجی قابل استفاده و قابل آزمایش داشته باشد. کل زمان تخمینی تا نسخه اولیه قابل استفاده (MVP) حدود ۱۳ هفته است.")
    
    add_heading_2(doc, "فاز ۱: شناخت دیتابیس نمونه (هفته ۱-۲)")
    add_body(doc, "انتخاب یک شرکت با نرم‌افزار همکاران (SQL Server)، یک شرکت با نرم‌افزار سپیدار (SQL Server) و یک شرکت با فایل اکسل. بررسی ساختار جداول اسناد در هر دیتابیس، شناسایی کلیدهای اصلی (به‌ویژه شناسه ردیف مبدأ)، تعیین روش اتصال، و نوشتن اسکریپت آزمایشی برای خواندن چند سند. خروجی: سند فنی ساختار دیتابیس‌ها و نمونه قرارداد استاندارد. مدت زمان: ۲ هفته. ریسک: تفاوت ساختار نرم‌افزارها در نسخه‌های مختلف.")
    
    add_heading_2(doc, "فاز ۲: پنل وب و مدیریت تسک (هفته ۳-۶)")
    add_body(doc, "احراز هویت کاربران، تعریف نقش‌ها، تعریف ۵۰ شرکت و ۵ کارمند، تخصیص تسک، چک‌لیست مراحل (الگوی Pixie)، پیگیری پیشرفت، آپلود فایل اکسل، نمره ۰-۱۰۰ مدیر، یادداشت دو سطحی، دلیل اجباری برای رد، و اعلان‌های پایه. در این فاز، سامانه هنوز تطبیق هوشمند انجام نمی‌دهد اما کارمندان می‌توانند تسک‌ها را مدیریت کنند و مدیر می‌تواند نمره بدهد. خروجی: نسخه قابل استفاده برای مدیریت تسک. مدت: ۴ هفته.")
    
    add_heading_2(doc, "فاز ۳: موتور کنترل هوشمند اکسل (هفته ۷-۱۰)")
    add_body(doc, "پیاده‌سازی ۹ مرحله کنترل، ساخت Adapter‌های SQL Server و Excel، پیاده‌سازی مدل داده استاندارد، تولید گزارش مغایرت، رابط کاربری مدیر برای مشاهده گزارش‌ها، تأیید یا رد با نمره. در این فاز، فایل مرجع اختیاری نیز پیاده‌سازی می‌شود: مدیر می‌تواند بدون فایل مرجع هم کار را تأیید کند. خروجی: نسخه با کنترل کامل اسناد. مدت: ۴ هفته.")
    
    add_heading_2(doc, "فاز ۴: اجرای آزمایشی (هفته ۱۱-۱۳)")
    add_body(doc, "سامانه روی دو یا سه شرکت با کارمندان واقعی استفاده می‌شود. هدف: مقایسه نتایج کنترل با بررسی دستی، شناسایی خطاهای موتور کنترل، تنظیم قواعد تشخیص اصلاح از تکرار، و جمع‌آوری بازخورد کاربران. این فاز نباید حذف شود؛ اجرای آزمایشی روی داده‌های واقعی معمولاً چندین مورد ناهماهنگی آشکار می‌کند. خروجی: نسخه پایدار قابل اعتماد. مدت: ۳ هفته.")
    
    add_heading_2(doc, "فاز ۵: توسعه و خودکارسازی (هفته ۱۴+)")
    add_body(doc, "سایر Adapter‌ها برای نرم‌افزارهای دیگر (تندیس، هلو)، اتصال به دستگاه حضور و غیاب، مرخصی و درخواست‌های پیشرفته، گزارش ارزیابی پرسنل با نمره ۰-۱۰۰، داشبورد مدیریتی کامل، دریافت خودکار ریز اسناد زمان‌بندی‌شده، و API برای اتصال ابزارهای خارجی. مدت: ادامه‌دار.")
    
    add_heading_2(doc, "۱۰.۱ جدول خلاصه فازها")
    phase_data = [
        ["فاز", "مدت", "خروجی اصلی", "ریسک کلیدی"],
        ["۱. شناخت دیتابیس نمونه", "۲ هفته", "سند فنی ساختار دیتابیس", "تفاوت ساختار نرم‌افزارها"],
        ["۲. پنل وب و مدیریت تسک", "۴ هفته", "پنل کار + نمره ۰-۱۰۰", "پذیرش کاربران"],
        ["۳. موتور کنترل هوشمند", "۴ هفته", "تطبیق کامل + فایل مرجع اختیاری", "پیچیدگی الگوریتم"],
        ["۴. اجرای آزمایشی", "۳ هفته", "نسخه پایدار", "خطاهای پنهان در داده"],
        ["۵. توسعه و خودکارسازی", "ادامه‌دار", "تمام Adapter‌ها + داشبورد", "اولویت‌بندی"],
        ["مجموع تا MVP", "۱۳ هفته", "نسخه قابل استفاده روزانه", "—"],
    ]
    add_table_styled(doc, phase_data, col_widths_cm=[4.5, 2, 6, 4.5])
    
    add_callout(doc, "نکته مهم: فاز ۱ (شناخت دیتابیس) نباید حذف شود. ساختار دیتابیس نرم‌افزارهای ایرانی در نسخه‌های مختلف متفاوت است. بدون این شناخت دقیق، Adapter‌ها در فاز ۳ به خطاهای ساختاری روبه‌رو می‌شوند. این فاز، پایه کل پروژه است.", 'warn')
    add_page_break(doc)
    
    # CHAPTER 11
    add_heading_1(doc, "فصل ۱۱: جمع‌بندی و توصیه‌های نهایی نسخه ۲")
    add_body(doc, "نسخه ۲ گزارش، حاصل تحلیل عمیق سه نرم‌افزار تخصصی و تمام تصمیمات راهبردی شماست. در این فصل پایانی، توصیه‌های نهایی و قدم‌های بعدی را به‌صورت عملی ارائه می‌دهیم.")
    
    add_heading_2(doc, "۱۱.۱ توصیه نهایی نسخه ۲")
    add_body(doc, "توصیه نهایی، ساخت یک سامانه اختصاصی با معماری ترکیبی است که از الگوهای مفید سه نرم‌افزار آماده (Financial Cents، Karbon، Pixie) الگوبرداری کرده باشد. این انتخاب بر اساس چهار دلیل اصلی است. اول، هیچ نرم‌افزار آماده‌ای تمام نیازهای شما (به‌ویژه کنترل هوشمند اسناد با شناسه ردیف مبدأ) را پوشش نمی‌دهد. دوم، نمره ۰-۱۰۰ مدیر و یادداشت دو سطحی، قابلیت‌هایی هستند که هیچ نرم‌افزار آماده‌ای ندارند. سوم، فایل مرجع اختیاری، انعطاف‌پذیری است که فقط در سامانه اختصاصی قابل پیاده‌سازی است. چهارم، نگهداری داده‌های خام در دفتر، الزام امنیتی است که نرم‌افزارهای آماده خارجی نمی‌توانند تضمین کنند.")
    
    add_heading_2(doc, "۱۱.۲ قدم‌های بعدی فوری (هفته اول)")
    urgent = [
        "انتخاب یک شرکت نمونه با نرم‌افزار همکاران و یک شرکت با نرم‌افزار سپیدار برای فاز ۱.",
        "تهیه یک فایل اکسل واقعی از اسناد یکی از شرکت‌ها، با ستون SourceLineID (شناسه ردیف مبدأ).",
        "اخذ دسترسی Read-Only به دیتابیس SQL Server شرکت‌های نمونه.",
        "مشاوره با ۲-۳ تیم توسعه ایرانی و ارائه این گزارش به‌عنوان RFP.",
        "تعیین بودجه نهایی (برآورد: ۸۰-۱۵۰ میلیون تومان برای MVP) و زمان‌بندی (۱۳ هفته).",
    ]
    for i, s in enumerate(urgent):
        add_numbered(doc, s, fa_nums[i])
    
    add_heading_2(doc, "۱۱.۳ اقدامات میان‌مدت (۳ ماه)")
    mid = [
        "تأیید تیم توسعه و امضای قرارداد شامل تعرفه‌های روشن برای فازهای ۲ تا ۵.",
        "شروع فاز ۱ (شناخت دیتابیس) و تولید سند فنی ساختار دیتابیس‌ها.",
        "طراحی دقیق مدل داده استاندارد با ستون SourceLineID و بررسی با تیم توسعه.",
        "آغاز فاز ۲ (پنل وب) و آموزش کارمندان به‌صورت موازی با توسعه.",
        "تعریف نقش‌ها و سطوح دسترسی به‌صورت رسمی قبل از راه‌اندازی.",
        "آزمون تطبیق با فایل نمونه و بررسی صحت الگوریتم تشخیص اصلاح از تکرار.",
    ]
    for i, s in enumerate(mid):
        add_numbered(doc, s, fa_nums[i])
    
    add_heading_2(doc, "۱۱.۴ چک‌لیست آماده‌سازی برای شروع پروژه")
    checklist = [
        "فهرست کامل ۵۰ شرکت با نوع نرم‌افزار حسابداری (همکاران/سپیدار/هلو/تندیس) و نسخه آن.",
        "اطلاعات تماس نرم‌افزارکار هر شرکت برای همکاری در دسترسی Read-Only.",
        "نمونه فایل اکسل از ۳ شرکت با ساختار متفاوت، با ستون SourceLineID.",
        "فهرست انواع فعالیت‌های حسابداری که در دفتر انجام می‌شود (برای قالب‌های آماده).",
        "تعریف اولیه چهار شاخص KPI و وزن هر کدام (۴۰/۲۵/۲۰/۱۵ بر اساس این گزارش).",
        "تعیین نقش‌ها: مدیر، مدیرعامل، ۵ کارمند، مسئول کنترل.",
        "تصمیم در مورد گزینه استقرار (پیشنهاد: Cloud خصوصی ایران + عامل محلی در دفتر).",
        "بودجه اولیه و تعیین حداکثر هزینه قابل قبول.",
        "تیم‌سازی: انتخاب تیم توسعه یا برون‌سپاری به یک شرکت توسعه.",
        "زمان‌بندی: تعیین تاریخ شروع و تاریخ تحویل MVP (۱۳ هفته).",
        "تعریف چهار نوع تصمیم مدیر (تأیید عادی، با ارفاق، بازگشت، رد نهایی).",
        "تعریف قواعد نمره‌دهی ۰-۱۰۰ و چارچوب یادداشت دو سطحی.",
    ]
    for it in checklist:
        add_bullet(doc, it)
    
    add_callout(doc, "پیام پایانی نسخه ۲: این گزارش اکنون یک سند فنی-اجرایی کامل است که می‌توانید آن را به تیم توسعه تحویل دهید. تمام تصمیمات راهبردی نهایی شده، الگوهای آماده استخراج شده، و نقشه راه فازبندی‌شده تعیین شده. موفقیت پروژه اکنون به انتخاب تیم توسعه مناسب و پایبندی به نقشه راه وابسته است.", 'success')
    
    doc.save(output_path)
    print(f"DOCX generated: {output_path}")

if __name__ == '__main__':
    output = '/home/z/my-project/download/سامانه_مدیریت_دفتر_حسابداری_نسخه_۲.docx'
    build_docx(output)
    print("Build complete!")
