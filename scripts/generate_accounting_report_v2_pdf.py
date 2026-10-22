"""
Accounting Office Management System - Updated Report v2.0 (Persian RTL)
Deep analysis of Financial Cents, Karbon, Pixie + all final design decisions from user's file.
Generates a comprehensive PDF using ReportLab with Vazirmatn font.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, BaseDocTemplate, Frame, PageTemplate, NextPageTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
import arabic_reshaper
from bidi.algorithm import get_display

# ============================================================
# Font Registration
# ============================================================
FONT_DIR = "/home/z/my-project/fonts"
pdfmetrics.registerFont(TTFont('Vazirmatn', f'{FONT_DIR}/Vazirmatn-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Vazirmatn-Bold', f'{FONT_DIR}/Vazirmatn-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Vazirmatn-Medium', f'{FONT_DIR}/Vazirmatn-Medium.ttf'))
registerFontFamily('Vazirmatn', normal='Vazirmatn', bold='Vazirmatn-Bold')

# ============================================================
# Persian Text Helper
# ============================================================
def fa(text):
    if text is None or text == "":
        return ""
    reshaper = arabic_reshaper.ArabicReshaper()
    reshaped = reshaper.reshape(str(text))
    return get_display(reshaped)

# ============================================================
# Color Palette
# ============================================================
C_PRIMARY = colors.HexColor('#0F172A')
C_ACCENT = colors.HexColor('#0E7C8B')
C_ACCENT2 = colors.HexColor('#1E40AF')
C_BG_LIGHT = colors.HexColor('#F1F5F9')
C_BG_ACCENT = colors.HexColor('#E0F2FE')
C_TEXT_MUTED = colors.HexColor('#475569')
C_TABLE_HEADER = colors.HexColor('#0E7C8B')
C_TABLE_ALT = colors.HexColor('#F8FAFC')
C_BORDER = colors.HexColor('#CBD5E1')
C_SUCCESS = colors.HexColor('#16A34A')
C_WARN = colors.HexColor('#D97706')
C_DANGER = colors.HexColor('#DC2626')

# ============================================================
# Page Setup
# ============================================================
PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

styles = getSampleStyleSheet()

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Vazirmatn-Bold', fontSize=30, leading=40, alignment=TA_CENTER, textColor=colors.white, spaceAfter=12)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Vazirmatn', fontSize=14, leading=22, alignment=TA_CENTER, textColor=colors.HexColor('#E2E8F0'), spaceAfter=8)
style_cover_meta = ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Vazirmatn', fontSize=11, leading=18, alignment=TA_CENTER, textColor=colors.HexColor('#94A3B8'))
style_h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Vazirmatn-Bold', fontSize=20, leading=28, alignment=TA_RIGHT, textColor=C_PRIMARY, spaceBefore=18, spaceAfter=12, borderPadding=4)
style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Vazirmatn-Bold', fontSize=15, leading=22, alignment=TA_RIGHT, textColor=C_ACCENT, spaceBefore=14, spaceAfter=8)
style_h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontName='Vazirmatn-Bold', fontSize=12.5, leading=18, alignment=TA_RIGHT, textColor=C_PRIMARY, spaceBefore=10, spaceAfter=6)
style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Vazirmatn', fontSize=11, leading=20, alignment=TA_JUSTIFY, textColor=C_PRIMARY, spaceAfter=8)
style_bullet_rtl = ParagraphStyle('BulletRTL', parent=style_body, fontName='Vazirmatn', fontSize=11, leading=19, alignment=TA_RIGHT, textColor=C_PRIMARY, rightIndent=18, spaceAfter=4)
style_table_cell = ParagraphStyle('TableCell', parent=style_body, fontName='Vazirmatn', fontSize=9.5, leading=14, alignment=TA_RIGHT, textColor=C_PRIMARY, spaceAfter=0)
style_table_header = ParagraphStyle('TableHeader', parent=style_body, fontName='Vazirmatn-Bold', fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.white, spaceAfter=0)

# ============================================================
# Page Templates
# ============================================================
def draw_cover_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#0F172A'))
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, PAGE_H - 1.5*cm, PAGE_W, 1.5*cm, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, 0, PAGE_W, 0.6*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#1E293B'))
    canvas.rect(0, PAGE_H - 8*cm, PAGE_W, 6*cm, fill=1, stroke=0)
    canvas.restoreState()

def draw_body_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_ACCENT)
    canvas.rect(MARGIN, PAGE_H - 1.2*cm, CONTENT_W, 0.05*cm, fill=1, stroke=0)
    canvas.setFont('Vazirmatn', 9)
    canvas.setFillColor(C_TEXT_MUTED)
    title_text = fa("سامانه مدیریت عملیات دفتر حسابداری - نسخه ۲.۰ (به‌روزرسانی‌شده)")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 1.05*cm, title_text)
    canvas.setFillColor(C_BORDER)
    canvas.rect(MARGIN, 1.0*cm, CONTENT_W, 0.02*cm, fill=1, stroke=0)
    canvas.setFont('Vazirmatn', 9)
    canvas.setFillColor(C_TEXT_MUTED)
    page_num = canvas.getPageNumber()
    page_text = fa(f"صفحه {page_num - 1}")
    canvas.drawRightString(PAGE_W - MARGIN, 0.65*cm, page_text)
    canvas.drawString(MARGIN, 0.65*cm, fa("نسخه ۲.۰ - پاییز ۱۴۰۵"))
    canvas.restoreState()

# ============================================================
# Helpers
# ============================================================
def P(text, style=None):
    if style is None:
        style = style_body
    return Paragraph(fa(text), style)

def bullet_list(items, style=None):
    if style is None:
        style = style_bullet_rtl
    out = []
    for it in items:
        out.append(Paragraph(fa("• " + it), style))
    return out

def numbered_list(items, style=None):
    if style is None:
        style = style_bullet_rtl
    out = []
    fa_nums = ['۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '۱۰', '۱۱', '۱۲', '۱۳', '۱۴', '۱۵', '۱۶', '۱۷', '۱۸', '۱۹', '۲۰']
    for i, it in enumerate(items):
        prefix = fa_nums[i] + ". " if i < len(fa_nums) else str(i+1) + ". "
        out.append(Paragraph(fa(prefix + it), style))
    return out

def make_table(data_raw, col_widths=None, header_bg=C_TABLE_HEADER, alt_rows=True):
    table_data = []
    for r_idx, row in enumerate(data_raw):
        new_row = []
        for c_idx, cell in enumerate(row):
            if isinstance(cell, Paragraph):
                new_row.append(cell)
            elif isinstance(cell, str):
                if r_idx == 0:
                    new_row.append(Paragraph(fa(cell), style_table_header))
                else:
                    new_row.append(Paragraph(fa(cell), style_table_cell))
            else:
                new_row.append(cell)
        table_data.append(new_row)
    if col_widths is None:
        n_cols = len(data_raw[0])
        col_widths = [CONTENT_W / n_cols] * n_cols
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Vazirmatn-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Vazirmatn'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.4, C_BORDER),
    ]
    if alt_rows:
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), C_TABLE_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t

def callout(text, kind='info'):
    bg = {'info': C_BG_ACCENT, 'warn': colors.HexColor('#FEF3C7'),
          'success': colors.HexColor('#D1FAE5'), 'danger': colors.HexColor('#FEE2E2')}.get(kind, C_BG_ACCENT)
    border_c = {'info': C_ACCENT, 'warn': C_WARN, 'success': C_SUCCESS, 'danger': C_DANGER}.get(kind, C_ACCENT)
    style_callout_local = ParagraphStyle('CalloutLocal', parent=style_body, fontName='Vazirmatn-Medium', fontSize=11, leading=19, alignment=TA_RIGHT, textColor=C_PRIMARY, backColor=bg, borderPadding=10, borderWidth=1, borderColor=border_c, leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=12)
    return Paragraph(fa(text), style_callout_local)

def hbar():
    t = Table([['']], colWidths=[CONTENT_W], rowHeights=[3])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), C_ACCENT), ('LINEBELOW', (0,0), (-1,-1), 0, C_ACCENT)]))
    return t

# ============================================================
# Document Builder
# ============================================================
def build_pdf(output_path):
    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.7*cm, bottomMargin=1.5*cm,
        title="سامانه مدیریت عملیات دفتر حسابداری - نسخه ۲.۰",
        author="Z.ai",
        subject="Updated research report on accounting office management system",
        creator="Z.ai PDF Pipeline"
    )
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='cover')
    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=draw_cover_bg)
    body_frame = Frame(MARGIN, 1.5*cm, CONTENT_W, PAGE_H - 3.2*cm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='body')
    body_template = PageTemplate(id='body', frames=[body_frame], onPage=draw_body_header_footer)
    doc.addPageTemplates([cover_template, body_template])

    story = []

    # ============ COVER ============
    story.append(Spacer(1, 5.5*cm))
    story.append(Paragraph(fa("سامانه مدیریت عملیات دفتر حسابداری"), style_cover_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph(fa("نسخه ۲.۰ - تحلیل به‌روزرسانی‌شده"), style_cover_subtitle))
    story.append(Spacer(1, 0.3*cm))
    line_t = Table([['']], colWidths=[6*cm], rowHeights=[2])
    line_t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), C_ACCENT)]))
    story.append(line_t)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(fa("تحلیل عمیق سه نرم‌افزار Financial Cents، Karbon و Pixie + الگوبرداری برای سامانه اختصاصی + تمام تصمیمات نهایی طراحی"), style_cover_subtitle))
    story.append(Spacer(1, 5.5*cm))
    story.append(Paragraph(fa("دفتر حسابداری - ۵۰ شرکت - ۵ کارمند"), style_cover_meta))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(fa("پاییز ۱۴۰۵ - نسخه ۲.۰ - سند راهبردی به‌روز"), style_cover_meta))

    story.append(NextPageTemplate('body'))
    story.append(PageBreak())

    # ============ CHAPTER 1: Executive Summary ============
    story.append(Paragraph(fa("فصل ۱: خلاصه اجرایی - تغییرات نسخه ۲"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))

    story.append(P("این نسخه از گزارش بر اساس تحلیل عمیق سه نرم‌افزار تخصصی مدیریت دفاتر حسابداری (Financial Cents، Karbon و Pixie) و تمام تصمیمات نهایی طراحی استخراج‌شده از گفت‌وگوهای راهبردی شما تهیه شده است. در نسخه ۲، چهار به‌روزرسانی کلیدی نسبت به نسخه اول اعمال شده است که ساختار نهایی سامانه را به‌طور قابل توجهی متحول می‌کند. این تغییرات بر اساس الگوبرداری هوشمندانه از نرم‌افزارهای آماده و تطبیق آن‌ها با شرایط خاص دفتر شما در ایران طراحی شده‌اند."))
    
    story.append(P("اولین تغییر، تحلیل عمیق ساختار و قابلیت‌های سه نرم‌افزار است. تمرکز این تحلیل بر قابلیت‌ها و گردش کار است، نه بر قیمت یا API، تا بتوانیم الگوهای مفید را برای ساخت سامانه اختصاصی استخراج کنیم. Financial Cents با ۴۰۰+ قالب آماده و قابلیت‌های هوش مصنوعی (AI File Validator، AI File Renaming، AI File Routing)، Karbon با صف‌های FIFO و یکپارچگی عمیق ایمیل، و Pixie با قیمت اسمی مبتنی بر تعداد مشتری و کاربران نامحدود، هرکدام درسی برای سامانه شما دارند."))
    
    story.append(P("دومین تغییر، تصمیم نهایی در مورد شناسه ردیف سند است. شما تأیید کردید که اکسل کارمند باید شامل شناسه ردیف سند از دیتابیس مبدأ باشد و این شناسه پس از حذف و ثبت مجدد سند تغییر می‌کند. این تصمیم، کلید تطبیق را به‌طور بنیادی تعریف می‌کند: ترکیب شرکت + دیتابیس مبدأ + سال مالی + شناسه ردیف مبدأ. این کلید اجازه می‌دهد اصلاح سند را از تکراری واقعی تشخیص دهیم، اما به‌تنهایی کافی نیست، چون شناسه ردیف پس از حذف-ثبت مجدد تغییر می‌کند و نیاز به تطبیق احتمالی با سایر فیلدها دارد."))
    
    story.append(P("سومین تغییر، مفهوم فایل مرجع اختیاری است. شما تصمیم گرفتید که فایل مرجع مرجع تأیید کار است، نه الزام. مدیر هر زمان که بخواهد تسک را راستی‌آزمایی کند، فایل مرجع را بارگذاری می‌کند، اما می‌تواند بدون فایل مرجع هم کار را ۱۰۰٪ تأیید کند. این تصمیم، گردش کار تصمیم مدیر را به‌طور قابل توجهی ساده می‌کند و انعطاف بیشتری به مدیر می‌دهد. فایل مرجع به‌صورت نسخه‌بندی‌شده ذخیره می‌شود و چندین تسک می‌توانند از یک نسخه مرجع استفاده کنند."))
    
    story.append(P("چهارمین تغییر، امتیاز مستقل از تأیید است. شما تصمیم گرفتید که امتیاز هر تسک عددی از ۰ تا ۱۰۰ است که مدیر تعیین می‌کند. این امتیاز، وضعیت تأیید و نتیجه تطبیق سه مفهوم مستقل هستند؛ تأیید کار لزوماً به معنی امتیاز ۱۰۰ نیست. این تصمیم، چارچوب ارزیابی پرسنل را به‌طور بنیادی تغییر می‌دهد و به مدیر اجازه می‌دهد کیفیت کار را به‌صورت پیوسته اندازه بگیرد، نه فقط به‌صورت باینری (تأیید/رد)."))
    
    story.append(callout("نکته: تمام تصمیمات نهایی این نسخه بر اساس ۱۴ گام گفت‌وگوی راهبردی شما تنظیم شده است. این سند اکنون یک سند فنی-اجرایی قابل تحویل به تیم توسعه است، نه فقط یک گزارش راهبردی سطح بالا.", 'info'))
    
    story.append(PageBreak())

    # ============ CHAPTER 2: Deep Analysis of Three Softwares ============
    story.append(Paragraph(fa("فصل ۲: تحلیل عمیق سه نرم‌افزار Financial Cents، Karbon و Pixie"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این فصل، سه نرم‌افزار تخصصی مدیریت دفاتر حسابداری را به‌صورت عمیق و با تمرکز بر ساختار برنامه و قابلیت‌ها (نه قیمت یا API) بررسی می‌کنیم. هدف، استخراج الگوهای قابل الگوبرداری برای سامانه اختصاصی شماست. هر نرم‌افزار درسی برای ما دارد: Financial Cents نشان می‌دهد چگونه با قالب‌های آماده و هوش مصنوعی، فرایندهای تکراری را خودکار کنیم؛ Karbon نشان می‌دهد چگونه با یکپارچگی عمیق ایمیل و صف‌های FIFO، کارهای حجم بالا را مدیریت کنیم؛ و Pixie نشان می‌دهد چگونه با قیمت اسمی مبتنی بر تعداد مشتری، دفاتر کوچک را به خدمت بگیریم."))
    
    # 2.1 Financial Cents
    story.append(Paragraph(fa("۲.۱ Financial Cents - ساختار و قابلیت‌ها"), style_h2))
    
    story.append(P("Financial Cents یک پلتفرم همه‌جانبه مدیریت دفاتر حسابداری است که برای دفاتر کوچک و در حال رشد طراحی شده. این نرم‌افزار از یک فلسفه ساده پیروی می‌کند: «هر کار، هر مشتری، هر مهلت - همه در یک پلتفرم». این فلسفه با معماری ماژولار اما یکپارچه پیاده‌سازی شده که هر ماژول به‌طور مستقل کار می‌کند اما با سایر ماژول‌ها به‌صورت یکپارچه ارتباط دارد."))
    
    story.append(Paragraph(fa("مدیریت گردش کار (Workflow Management)"), style_h3))
    story.append(P("قلب Financial Cents، موتور مدیریت گردش کار است. این موتور شامل بیش از ۴۰۰ قالب از پیش ساخته‌شده برای کارهای حسابداری، مالیاتی، حقوق و دستمزد و خدمات حسابداری ابری (CAS) است. این قالب‌ها به‌طور خاص برای صنعت حسابداری طراحی شده‌اند و نیاز به ساخت قالب از صفر را از بین می‌برند. قابلیت تخصیص خودکار تسک بر اساس مشتری، نقش یا نوع خدمت، یکی از نقاط قوت اصلی این نرم‌افزار است. به‌عنوان مثال، وقتی یک کار ماهانه «بستن دفاتر شرکت A» ایجاد می‌شود، سامانه به‌طور خودکار می‌داند که کارمند مسئول، مهلت و مراحل را تعیین می‌کند. تسک‌های شرطی (Conditional Tasks) که با نوع درگیری سازگار می‌شوند، انعطاف بیشتری به مدیر می‌دهند: یک قالب می‌تواند برای کارهای مختلف رفتار متفاوتی داشته باشد."))
    
    story.append(Paragraph(fa("کارهای تکرارشونده و اتوماسیون"), style_h3))
    story.append(P("کارهای تکرارشونده (Recurring Engagements) در Financial Cents به‌صورت کامل خودکار اجرا می‌شوند. به‌عنوان مثال، حسابداری ماهانه، بستن دوره فصلی و آماده‌سازی اظهارنامه مالیاتی سالانه می‌توانند به‌صورت زمان‌بندی‌شده اجرا شوند. تاریخ‌های مقرر به‌طور خودکار به‌روزرسانی و به جلو منتقل می‌شوند. این یعنی مدیر نیازی نیست هر ماه به یاد خودش کار ماهانه را ایجاد کند؛ سامانه این کار را به‌طور خودکار انجام می‌دهد. این قابلیت برای دفتر شما با ۵۰ شرکت بسیار ارزشمند است، زیرا فرض کنید ۵۰ شرکت نیاز به کار ماهانه دارند؛ اگر قرار باشد هر کار را به‌صورت دستی ایجاد کنید، ۵۰۰ کار در سال نیاز به ایجاد دارد."))
    
    story.append(Paragraph(fa("CRM مشتری و پورتال"), style_h3))
    story.append(P("Financial Cents یک CRM (مدیریت ارتباط با مشتری) داخلی دارد که به‌عنوان یک منبع واحد برای هر مشتری عمل می‌کند. هر مشتری خدمات، مخاطبین، یادداشت‌ها، فایل‌ها، تاریخچه و صورت‌حساب خود را در یک نمای یکپارچه دارد. این CRM به تمام گردش کارها، اسناد و فاکتورهای مرتبط با همان مشتری متصل است. یادداشت‌های سطح مشتری، برچسب‌ها و فیلدهای سفارشی امکان دسته‌بندی و جست‌وجوی پیشرفته را فراهم می‌کنند. یکپارچگی بومی با QuickBooks Online به‌طور خودکار اطلاعات مالی مشتری را به‌روزرسانی می‌کند. پورتال مشتری با آپلود امن فایل و امضای الکترونیکی، نیاز به ایمیل‌های رفت-و‌برگشتی را حذف می‌کند."))
    
    story.append(Paragraph(fa("قابلیت‌های هوش مصنوعی"), style_h3))
    story.append(P("Financial Cents در سال‌های اخیر سرمایه‌گذاری قابل توجهی در هوش مصنوعی کرده است. سه قابلیت AI به‌طور خاص برای مدیریت فایل ارزشمند هستند. اول، AI File Validator فایل‌های آپلود شده مشتری را قبل از رسیدن به تیم بررسی می‌کند و فایل‌های نادرست را شناسایی می‌کند. دوم، AI File Renaming به‌طور خودکار فایل‌ها را به قرارداد نام‌گذاری دفتر شما تغییر نام می‌دهد. سوم، AI File Routing فایل‌های آپلود شده مشتری را در پوشه مشتری صحیح قرار می‌دهد. علاوه بر این، Financial Cents MCP (Model Context Protocol) امکان اتصال داده‌های دفتر شما به Claude، ChatGPT و Gemini را فراهم می‌کند. این یعنی می‌توانید از مدل‌های زبانی بزرگ برای تحلیل داده‌های دفتر خود استفاده کنید."))
    
    story.append(Paragraph(fa("مدیریت تیم و گزارش‌گیری"), style_h3))
    story.append(P("Financial Cents یک نمای ظرفیت تیم در زمان واقعی (Real-time Team Capacity View) ارائه می‌دهد که به مدیر نشان می‌دهد هر کارمند چقدر بار کاری دارد و چه مقدار ظرفیت آزاد باقی مانده است. این قابلیت برای دفتر شما با ۵ کارمند بسیار مهم است، زیرا اجازه می‌دهد کار را به کارمندی که ظرفیت دارد ارجاع دهید، نه فقط به کارمندی که معمولاً آن شرکت را بر عهده دارد. گزارش‌های سطح سودآوری مشتری و زمان، به مدیر نشان می‌دهد کدام مشتری‌ها و کدام خدمات سودآورتر هستند. این قابلیت در دفتر شما می‌تواند به تصمیم‌گیری در مورد قیمت‌گذاری و تخصیص منابع کمک کند."))
    
    # 2.2 Karbon
    story.append(Paragraph(fa("۲.۲ Karbon - ساختار و قابلیت‌ها"), style_h2))
    
    story.append(P("Karbon یکی از پیچیده‌ترین و قدرتمندترین نرم‌افزارهای مدیریت دفاتر حسابداری است که برای دفاتر متوسط و بزرگ (۵ تا ۵۰ کارمند) طراحی شده. این نرم‌افزار با فلسفه «هماهنگی کار با ایمیل» شناخته می‌شود - یعنی تمام ارتباطات مشتری به‌طور خودکار به کارهای مرتبط متصل می‌شوند. این فلسفه باعث می‌شود هیچ ایمیلی گم نشود و تمام تصمیمات در یک مکان متمرکز باشند."))
    
    story.append(Paragraph(fa("صف‌های FIFO و مدیریت حجم بالا"), style_h3))
    story.append(P("یکی از ویژگی‌های منحصر به فرد Karbon، صف‌های FIFO (First-In-First-Out) برای مدیریت کارهای حجم بالا هستند. این صف‌ها به‌طور خاص برای فصل مالیات طراحی شده‌اند، زمانی که دفتر با صدها اظهارنامه همزمان روبه‌رو است. هر کار به‌طور خودکار در صف قرار می‌گیرد و کارمندان به ترتیب کارها را برمی‌دارند. مدیر می‌تواند کارهای با اولویت بالا را به‌صورت دستی به بالای صف ببرد. این قابلیت برای دفتر شما با ۵۰ شرکت و کارهای ماهانه تکرارشونده بسیار ارزشمند است. به‌عنوان مثال، در پایان هر ماه، ۵۰ کار «بستن دفاتر» باید اجرا شود؛ صف FIFO کمک می‌کند این کارها به‌صورت منظم و عادلانه بین کارمندان توزیع شوند."))
    
    story.append(Paragraph(fa("قالب‌های مبتنی بر نقش و اتوماسیون"), style_h3))
    story.append(P("Karbon از قالب‌های مبتنی بر نقش (Role-based Templates) استفاده می‌کند. هر قالب تعریف می‌کند چه نقشی باید چه مرحله‌ای را انجام دهد. به‌عنوان مثال، در قالب «بستن دفاتر ماهانه»، نقش «کارمند جوان» مرحله «ثبت اسناد» را انجام می‌دهد، نقش «سرپرست» مرحله «بازبینی» را، و نقش «شریک ارشد» مرحله «تأیید نهایی» را. اتوماسیون کاربر (Automators) به‌طور خودکار تسک‌ها را بر اساس نقش‌ها و مهلت‌ها تخصیص می‌دهد. همچنین، اتوماسیون می‌تواند بخش‌هایی از تسک‌ها را بر اساس معیارها یا محرک‌ها فعال یا غیرفعال کند. این یعنی یک قالب می‌تواند برای انواع مختلف مشتریان رفتار متفاوتی داشته باشد."))
    
    story.append(Paragraph(fa("یکپارچگی عمیق ایمیل"), style_h3))
    story.append(P("نقطه قوت اصلی Karbon، یکپارچگی عمیق ایمیل است. تمام ایمیل‌های مشتری به‌طور خودکار به کارهای مرتبط متصل می‌شوند. تیم می‌تواند ایمیل‌ها را به یکدیگر ارجاع دهد، درباره آن‌ها بحث کند و گفت‌وگوها را به‌طور مستقیم به کار در حال انجام متصل کند. این قابلیت باعث می‌شود هیچ ایمیلی گم نشود و تمام تصمیمات در یک مکان متمرکز باشند. مدیر دید کاملی از مسئولیت‌ها، مهلت‌ها و پیشرفت پروژه دارد. این قابلیت برای دفتر شما با ۵۰ شرکت ارزشمند است، زیرا ارتباط با هر شرکت به‌صورت جداگانه و در یک مکان متمرکز انجام می‌شود."))
    
    story.append(Paragraph(fa("مدیریت اسناد و یکپارچگی‌ها"), style_h3))
    story.append(P("Karbon یک سیستم مدیریت اسناد با version control (کنترل نسخه) دارد که فایل‌ها را به‌طور خودکار سازماندهی می‌کند. پوشه‌بندی هوشمند و DMS sync فایل‌ها را در مکان صحیح قرار می‌دهد. یکپارچگی با Google Drive، SharePoint/OneDrive یا Dropbox به دفاتر اجازه می‌دهد از سیستم ذخیره‌سازی موجود خود استفاده کنند. Karbon برای Clients یک پورتال مشتری است که امکان دریافت اسناد، تکمیل سازمان‌دهنده، حاشیه‌نویسی و تأییدها را فراهم می‌کند. این قابلیت برای دفتر شما می‌تواند به دریافت فایل‌های اکسل از کارمندان (به‌عنوان «مشتری داخلی») کمک کند."))
    
    story.append(Paragraph(fa("گزارش‌گیری و داشبورد"), style_h3))
    story.append(P("Karbon چندین داشبورد تخصصی دارد. Progress Report Dashboard یک نمای بصری و در زمان واقعی از وضعیت کار ارائه می‌دهد. Work Dashboards زمان چرخش، زمان تکمیل پروژه و نرخ تکمیل را نشان می‌دهد. Karbon Analytics Dashboards عملکرد تیم، زمان چرخش و تکمیل پروژه را تحلیل می‌کند. گزارش‌های قابل سفارشی‌سازی بر اساس تیم، بازه زمانی و نوع خدمت امکان تحلیل عمیق را فراهم می‌کنند. این سطح از گزارش‌گیری برای دفتر شما می‌تواند به شناسایی کارمندان با عملکرد پایین، شرکت‌های با تأخیر مکرر، و خدمات با حاشیه سود پایین کمک کند."))
    
    story.append(Paragraph(fa("زمان‌بند کار و کارهای تکرارشونده"), style_h3))
    story.append(P("Work Scheduler کارهای تکرارشونده را به‌طور خودکار زمان‌بندی می‌کند. به‌عنوان مثال، می‌توانید تنظیم کنید که کار «بستن دفاتر شرکت A» در روز اول هر ماه به‌طور خودکار ایجاد شود. این کار به یک کارمند مشخص ارجاع داده می‌شود و مهلت آن تعیین می‌گردد. این قابلیت در دفتر شما می‌تواند ۵۰ کار ماهانه را به‌صورت کامل خودکار کند و نیاز به مدیریت دستی را از بین ببرد."))
    
    # 2.3 Pixie
    story.append(Paragraph(fa("۲.۳ Pixie - ساختار و قابلیت‌ها"), style_h2))
    
    story.append(P("Pixie یک نرم‌افزار ساده و کاربرپسند برای دفاتر کوچک و در حال رشد حسابداری است. این نرم‌افزار با فلسفه «سادگی و قیمت منصفانه» طراحی شده و هدف آن ارائه تمام قابلیت‌های ضروری بدون پیچیدگی اضافی است. Pixie به‌طور خاص برای دفاتر با تعداد کارمند متغیر ارزشمند است، زیرا قیمت مبتنی بر تعداد مشتری است، نه کارمند."))
    
    story.append(Paragraph(fa("مدیریت گردش کار با تفکیک به مراحل"), style_h3))
    story.append(P("Pixie گردش کار را به مراحل کوچک‌تر تفکیک می‌کند تا بهره‌وری تیم افزایش یابد. هر مرحله یک مسئول مشخص دارد و مدیر می‌تواند وضعیت هر مرحله را به‌صورت جداگانه پیگیری کند. این قابلیت برای دفتر شما بسیار ارزشمند است، زیرا شما خواستار امکان «انجام دادن قسمتی از تسک و ارجاع به همکار» هستید. مدل تفکیک به مراحل Pixie دقیقاً همین نیاز را پوشش می‌دهد: یک تسک به چند مرحله تقسیم می‌شود، هر مرحله مسئول مستقل دارد و ارجاع به همکار به‌سادگی امکان‌پذیر است."))
    
    story.append(Paragraph(fa("شروع خودکار کارها بر اساس تاریخ‌های کلیدی مشتری"), style_h3))
    story.append(P("یکی از قابلیت‌های منحصر به فرد Pixie، شروع خودکار کارها بر اساس تاریخ‌های کلیدی مشتری است. به‌عنوان مثال، اگر تاریخ «مهلت ارائه اظهارنامه مالیاتی» شرکت A در سامانه تعریف شود، Pixie به‌طور خودکار کار «آماده‌سازی اظهارنامه» را ۳۰ روز قبل از مهلت ایجاد می‌کند. این قابلیت برای دفتر شما با ۵۰ شرکت بسیار ارزشمند است، زیرا هر شرکت تاریخ‌های کلیدی متفاوتی دارد (ماهانه، فصلی، سالانه) و پیگیری دستی آن‌ها دشوار است."))
    
    story.append(Paragraph(fa("اتوماسیون و یادآوری‌های خودکار"), style_h3))
    story.append(P("Pixie اتوماسیون‌های متعددی دارد: ایجاد کارهای تکرارشونده، تخصیص خودکار کار به تیم، درخواست خودکار صورتحساب از مشتریان، و ارسال خودکار یادآوری تاریخ‌های کلیدی به مشتری. این اتوماسیون‌ها به مدیر اجازه می‌دهند به‌جای پیگیری دستی، روی کار ارزشمندتر تمرکز کند. یادآوری‌های خودکار به مشتری باعث می‌شوند نیازی نباشد مدیر خودش به مشتری یادآوری کند. این قابلیت در دفتر شما می‌تواند به یادآوری خودکار به شرکت‌ها برای ارسال مدارک ماهانه کمک کند."))
    
    story.append(Paragraph(fa("CRM با فیلدهای سفارشی و خط زمانی"), style_h3))
    story.append(P("Pixie یک CRM متمرکز با فیلدهای سفارشی دارد. مدیر می‌تواند فیلدهای خاص هر دفتر را تعریف کند (مثلاً «نوع نرم‌افزار حسابداری» یا «نام نرم‌افزارکار»). خط زمانی تمام ایمیل‌ها و مکاتبات اسنادی هر مشتری را در یک مکان نشان می‌دهد. این قابلیت برای دفتر شما با ۵۰ شرکت و تنوع نرم‌افزارها ارزشمند است، زیرا به شما اجازه می‌دهد هر شرکت را با نوع نرم‌افزار و روش اتصال دسته‌بندی کنید."))
    
    story.append(Paragraph(fa("پورتال مشتری و یکپارچگی‌ها"), style_h3))
    story.append(P("Pixie یک پورتال مشتری سازگار با GDPR دارد که امکان اشتراک امن اسناد، تسک‌های مشتری و امضای الکترونیکی را فراهم می‌کند. یکپارچگی اصلی Pixie از طریق Zapier است که به ۹۰۰۰ اپ دیگر متصل می‌شود. این یعنی می‌توانید Pixie را با Gmail، Google Drive، Slack، Excel و بسیاری از ابزارهای دیگر متصل کنید. برای دفتر شما، این یعنی می‌توانید گردش کار پیچیده‌ای بسازید که چندین ابزار را با هم ترکیب می‌کند."))
    
    story.append(Paragraph(fa("قیمت مبتنی بر تعداد مشتری، نه کارمند"), style_h3))
    story.append(P("یکی از ویژگی‌های جذاب Pixie، قیمت‌گذاری مبتنی بر تعداد مشتری است، نه کارمند. این یعنی می‌توانید کارمندان نامحدود اضافه کنید بدون اینکه هزینه اضافی بپردازید. این مدل برای دفاتر با کارمندان فصلی یا پاره‌وقت بسیار اقتصادی است. در دفتر شما با ۵ کارمند و ۵۰ شرکت، این مدل می‌تواند هزینه را به‌طور قابل توجهی کاهش دهد."))
    
    story.append(PageBreak())

    # ============ CHAPTER 3: Patterns to Borrow ============
    story.append(Paragraph(fa("فصل ۳: الگوبرداری از نرم‌افزارهای آماده برای سامانه اختصاصی"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("هدف از تحلیل سه نرم‌افزار، استخراج الگوهای قابل الگوبرداری برای سامانه اختصاصی شماست. هر نرم‌افزار درسی دارد که می‌توانیم در طراحی سامانه شما به کار بگیریم. در این فصل، الگوهای مفید را از هر نرم‌افزار استخراج می‌کنیم و توضیح می‌دهیم چگونه در سامانه اختصاصی شما پیاده‌سازی شوند. در عین حال، قابلیت‌هایی که برای بازار غربی طراحی شده‌اند و در ایران کاربردی ندارند را نیز مشخص می‌کنیم."))
    
    story.append(Paragraph(fa("۳.۱ الگوهای قابل الگوبرداری از Financial Cents"), style_h2))
    
    story.append(Paragraph(fa("قالب‌های آماده برای کارهای حسابداری"), style_h3))
    story.append(P("اولین و مهم‌ترین الگو از Financial Cents، استفاده از قالب‌های آماده برای کارهای حسابداری است. شما می‌توانید ۱۰-۲۰ قالب برای کارهای رایج دفتر خود بسازید: ثبت اسناد ماهانه، بستن دوره فصلی، آماده‌سازی اظهارنامه مالیاتی، گزارش ماهانه به مدیر عامل، و غیره. هر قالب شامل مراحل، مسئول پیش‌فرض، مهلت نسبی و چک‌لیست است. وقتی مدیر یک کار جدید ایجاد می‌کند، فقط قالب را انتخاب می‌کند و سامانه تمام جزئیات را به‌طور خودکار پر می‌کند. این قابلیت می‌تواند زمان ایجاد کار را از ۵ دقیقه به ۱۰ ثانیه کاهش دهد."))
    
    story.append(Paragraph(fa("تخصیص خودکار تسک"), style_h3))
    story.append(P("الگوی دوم از Financial Cents، تخصیص خودکار تسک است. در سامانه شما، می‌توانید قاعده‌ای تعریف کنید: «شرکت A همیشه به کارمند الف ارجاع داده شود». وقتی کار جدیدی برای شرکت A ایجاد می‌شود، سامانه به‌طور خودکار کارمند الف را به‌عنوان مسئول تعیین می‌کند. این قابلیت برای دفتر شما که شرکت‌ها را از قبل بین کارمندان تقسیم کرده‌اید، ایده‌آل است. مدیر فقط شرکت را انتخاب می‌کند و سامانه به‌طور خودکار مسئول را می‌داند."))
    
    story.append(Paragraph(fa("نمای ظرفیت تیم در زمان واقعی"), style_h3))
    story.append(P("الگوی سوم از Financial Cents، نمای ظرفیت تیم است. در داشبورد مدیر، هر کارمند با یک نوار نشان داده می‌شود که میزان بار کاری فعلی او را نشان می‌دهد. به‌عنوان مثال، کارمند الف ۸۰٪ پر است، کارمند ب ۵۰٪ و کارمند ج ۲۰٪. وقتی مدیر می‌خواهد کار جدیدی ارجاع دهد، می‌تواند به‌سرعت ببیند کدام کارمند ظرفیت دارد. این قابلیت می‌تواند توزیع کار را عادلانه‌تر کند و از اضافه‌بار یک کارمند خاص جلوگیری کند."))
    
    story.append(Paragraph(fa("AI File Validator برای اکسل"), style_h3))
    story.append(P("الگوی چهارم از Financial Cents، AI File Validator است. در سامانه شما، می‌توانید یک موتور اعتبارسنجی هوشمند برای فایل‌های اکسل بسازید که قبل از رسیدن به مدیر، فایل را بررسی کند. این موتور می‌تواند: ساختار ستون‌ها را بررسی کند، تاریخ‌های نامعتبر را شناسایی کند، مبالغ غیرعددی را گزارش کند، و فایل‌های نادرست را به کارمند برگرداند. این قابلیت می‌تواند بار کاری مدیر را به‌طور قابل توجهی کاهش دهد، زیرا فایل‌های نادرست قبل از رسیدن به مدیر رد می‌شوند."))
    
    story.append(Paragraph(fa("۳.۲ الگوهای قابل الگوبرداری از Karbon"), style_h2))
    
    story.append(Paragraph(fa("صف FIFO برای کارهای حجم بالا"), style_h3))
    story.append(P("الگوی اول از Karbon، صف FIFO است. در سامانه شما، می‌توانید برای هر کارمند یک صف از کارهای واگذار شده بسازید. وقتی کار جدیدی به کارمند ارجاع داده می‌شود، در صف او قرار می‌گیرد. کارمند کارها را به ترتیب (FIFO) انجام می‌دهد. مدیر می‌تواند کارهای با اولویت بالا را به‌صورت دستی به بالای صف ببرد. این قابلیت برای دفتر شما با ۵۰ شرکت و کارهای ماهانه تکرارشونده ارزشمند است، زیرا کارها به‌صورت منظم بین کارمندان توزیع می‌شوند و هیچ کارمی گم نمی‌شود."))
    
    story.append(Paragraph(fa("قالب‌های مبتنی بر نقش"), style_h3))
    story.append(P("الگوی دوم از Karbon، قالب‌های مبتنی بر نقش است. در سامانه شما، هر قالب می‌تواند تعریف کند چه نقشی باید چه مرحله‌ای را انجام دهد. به‌عنوان مثال، در قالب «بستن دفاتر ماهانه»، مرحله «ثبت اسناد» به کارمند، مرحله «بازبینی» به سرپرست، و مرحله «تأیید نهایی» به مدیر ارجاع می‌شود. این قابلیت به‌صورت خودکار مراحل را به نقش‌های صحیح تخصیص می‌دهد و نیاز به تخصیص دستی را کاهش می‌دهد."))
    
    story.append(Paragraph(fa("داشبورد پیشرفت در زمان واقعی"), style_h3))
    story.append(P("الگوی سوم از Karbon، داشبورد پیشرفت است. در سامانه شما، می‌توانید یک داشبورد ایجاد کنید که وضعیت همه کارهای دفتر را در یک نمای بصری نشان دهد. هر کار به‌عنوان یک کارت با وضعیت (در حال انجام، در انتظار بازبینی، تأیید شده) نمایش داده می‌شود. مدیر می‌تواند به‌سرعت ببیند کدام کارها عقب افتاده، کدام در انتظار تأیید، و کدام تکمیل شده است. این قابلیت برای دفتر شما با ۵۰ شرکت و چندصد کار همزمان بسیار ارزشمند است."))
    
    story.append(Paragraph(fa("۳.۳ الگوهای قابل الگوبرداری از Pixie"), style_h2))
    
    story.append(Paragraph(fa("تفکیک تسک به مراحل با مسئول مستقل"), style_h3))
    story.append(P("مهم‌ترین الگوی Pixie برای دفتر شما، تفکیک تسک به مراحل با مسئول مستقل است. شما به‌صراحت خواستار امکان «انجام دادن قسمتی از تسک و ارجاع به همکار» بوده‌اید. این دقیقاً همان الگوی Pixie است: یک تسک به چند مرحله تقسیم می‌شود، هر مرحله مسئول مستقل دارد و ارجاع به همکار به‌سادگی امکان‌پذیر است. در سامانه شما، هر تسک می‌تواند چک‌لیستی از مراحل داشته باشد و هر مرحله به کارمند متفاوتی ارجاع داده شود. این قابلیت به‌طور مستقیم نیاز شما به ارجاع بخشی از کار را پوشش می‌دهد."))
    
    story.append(Paragraph(fa("شروع خودکار کارها بر اساس تاریخ‌های کلیدی"), style_h3))
    story.append(P("الگوی دوم از Pixie، شروع خودکار کارها بر اساس تاریخ‌های کلیدی است. در سامانه شما، می‌توانید برای هر شرکت تاریخ‌های کلیدی تعریف کنید (مثلاً «آخرین روز ماه» برای کار ماهانه). سامانه به‌طور خودکار کار جدید را چند روز قبل از مهلت ایجاد می‌کند. این قابلیت برای دفتر شما با ۵۰ شرکت و تاریخ‌های متفاوت بسیار ارزشمند است، زیرا نیازی نیست مدیر به یاد خودش کارهای ماهانه را ایجاد کند."))
    
    story.append(Paragraph(fa("یادآوری‌های خودکار به مشتری"), style_h3))
    story.append(P("الگوی سوم از Pixie، یادآوری‌های خودکار به مشتری است. در سامانه شما، می‌توانید یادآوری‌های خودکار به شرکت‌ها برای ارسال مدارک ماهانه ارسال کنید. به‌عنوان مثال، در روز ۲۵ هر ماه، سامانه به‌طور خودکار به شرکت‌ها یادآوری می‌کند که مدارک ماهانه را بفرستند. این قابلیت می‌تواند بار کاری مدیر را در پیگیری دستی کاهش دهد."))
    
    story.append(Paragraph(fa("۳.۴ قابلیت‌هایی که نباید الگوبرداری شوند"), style_h2))
    story.append(P("تمام قابلیت‌های این نرم‌افزارها برای دفتر شما مناسب نیستند. در ادامه، قابلیت‌هایی که نباید در سامانه شما پیاده‌سازی شوند را فهرست می‌کنیم."))
    
    skip_data = [
        ["قابلیت", "دلیل عدم الگوبرداری"],
        ["یکپارچگی با QuickBooks Online", "نرم‌افزار حسابداری شما متنوع (همکاران، سپیدار، هلو، تندیس) و ایرانی است"],
        ["یکپارچگی با IRS (سازمان مالیاتی آمریکا)", "سیستم مالیاتی ایران متفاوت است"],
        ["امضای الکترونیکی برای اظهارنامه مالیاتی آمریکا", "اظهارنامه مالیاتی ایران فرمت متفاوتی دارد"],
        ["قالب‌های ۱۰۴۰ و ۱۰۹۹ (مالیات آمریکا)", "قالب‌های شما باید بر اساس فرم‌های مالیاتی ایران باشند"],
        ["پورتال مشتری عمومی (با ثبت‌نام مشتری)", "مشتریان شما شرکت‌های داخلی هستند، نه افراد عمومی"],
        ["صورت‌حساب و پرداخت آنلاین به مشتری", "صورت‌حساب شما به شرکت‌ها، نه به‌صورت آنلاین پرداخت می‌شود"],
        ["AI MCP برای Claude/ChatGPT/Gemini", "اطلاعات حساس حسابداری نباید به API خارجی ارسال شود (حریم خصوصی)"],
        ["یکپارچگی با Adobe Sign", "نیازی به امضای الکترونیکی بین‌المللی ندارید"],
        ["اپ موبایل برای مشتری", "مشتریان شما از طریق پورتال ساده و داخلی کار می‌کنند"],
    ]
    col_w_skip = [6*cm, 11*cm]
    factor = CONTENT_W / sum(col_w_skip)
    col_w_skip = [w * factor for w in col_w_skip]
    story.append(make_table(skip_data, col_widths=col_w_skip))
    story.append(Spacer(1, 8))
    
    story.append(callout("اصل کلیدی: ما از نرم‌افزارهای آماده الگوبرداری می‌کنیم، نه کپی‌برداری. یعنی قابلیت‌هایی که با نیازهای دفتر شما سازگار هستند را با معماری اختصاصی پیاده‌سازی می‌کنیم، نه به‌صورت آماده. این رویکرد، بهترین‌های هر دو دنیا را به شما می‌دهد: بلوغ نرم‌افزارهای آماده + تطبیق کامل با نیازهای خاص شما.", 'info'))
    
    story.append(PageBreak())

    # ============ CHAPTER 4: Final Architecture ============
    story.append(Paragraph(fa("فصل ۴: معماری نهایی سامانه - به‌روزرسانی با تمام تصمیمات"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("معماری نهایی سامانه بر اساس تمام تصمیمات راهبردی شما طراحی شده است. این معماری بر چهار اصل استوار است: مدیریت کارها از هر جایی قابل انجام باشد، فایل‌های اکسل و ریز اسناد داخل دفتر بمانند، هر گزارش کارمند با اطلاعات واقعی قابل مقایسه باشد، و هر تغییر سابقه غیرقابل‌حذف داشته باشد. این معماری برای ۵ کارمند، ۵۰ شرکت و کمتر از ۱۰ هزار ردیف سند در روز، انتخابی منطقی و مقیاس‌پذیر است."))
    
    story.append(Paragraph(fa("۴.۱ معماری کلی - سرور مرکزی + عامل محلی"), style_h2))
    story.append(P("سامانه از دو بخش مجزا تشکیل شده است. سرور مرکزی مدیریت کارها، وضعیت‌ها، تأییدها و اعلان‌ها را بر عهده دارد و در فضای ابری (ترجیحاً Cloud خصوصی ایران) مستقر است. عامل محلی در دفتر شما نصب می‌شود و مسئولیت دریافت فایل‌های اکسل، پردازش محلی، تطبیق با منابع حسابداری و ذخیره ریز اسناد را بر عهده دارد. این جداسازی، حریم خصوصی اطلاعات حساس را تضمین می‌کند: ریز اسناد، شرح سند، شماره حساب و مبالغ هرگز از دفتر خارج نمی‌شوند."))
    
    arch_data = [
        [Paragraph(fa("لایه ۱: کاربران (کارمند، سرپرست، مدیرعامل) - مرورگر وب + VPN برای مدیر خارج دفتر"), style_table_header)],
        [Paragraph(fa("لایه ۲: سرور مرکزی - Task API + Identity API + Workflow API + Metadata DB"), style_table_cell)],
        [Paragraph(fa("لایه ۳: عامل محلی در دفتر - API محلی + صف پردازش + موتور تطبیق + Local PostgreSQL"), style_table_cell)],
        [Paragraph(fa("لایه ۴: اتصال‌دهنده‌ها - Adapter API | Adapter DB فقط‌خواندنی | Adapter خروجی Excel/CSV"), style_table_cell)],
        [Paragraph(fa("لایه ۵: منابع داده - دیتابیس همکاران/سپیدار/تندیس | فایل‌های اکسل هلو | سایر"), style_table_cell)],
    ]
    arch_table = Table(arch_data, colWidths=[CONTENT_W])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#DBEAFE')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#FED7AA')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#D1FAE5')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#E0E7FF')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, C_BORDER),
        ('BOX', (0, 0), (-1, -1), 1.5, C_PRIMARY),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(fa("۴.۲ مرز قطعی داده‌ها"), style_h2))
    story.append(P("جدول زیر به‌طور دقیق مشخص می‌کند هر نوع اطلاعات کجا ذخیره شود. این جدول، قلب امنیت سامانه است و هرگونه تخلف از آن باید به‌عنوان نقض امنیتی گزارش شود."))
    
    border_data = [
        ["نوع اطلاعات", "سرور مرکزی", "داخل دفتر (محلی)"],
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
    col_w_border = [7*cm, 5*cm, 5*cm]
    factor = CONTENT_W / sum(col_w_border)
    col_w_border = [w * factor for w in col_w_border]
    story.append(make_table(border_data, col_widths=col_w_border))
    story.append(Spacer(1, 8))
    
    story.append(callout("قاعده قطعی: هیچ ریز سند حسابداری، شرح، شماره حساب یا مبلغ نباید به سرور مرکزی ارسال شود. اگر مدیر خارج دفتر نیاز به مشاهده جزئیات داشته باشد، از طریق VPN به پنل محلی متصل می‌شود، نه با کپی داده به ابر.", 'danger'))
    
    story.append(Paragraph(fa("۴.۳ پروتکل ارتباط عامل محلی با سرور مرکزی"), style_h2))
    story.append(P("عامل محلی ارتباط را آغاز می‌کند؛ سرور مرکزی اتصال مستقیمی به دیتابیس یا رایانه‌های حسابداری برقرار نمی‌کند. این الگو (Outbound-only) امنیت را به‌طور قابل توجهی افزایش می‌دهد، زیرا دیتابیس حسابداری هرگز به اینترنت باز نمی‌شود. عامل محلی به‌صورت دوره‌ای (مثلاً هر ۳۰ ثانیه) درخواست‌های جدید را از سرور مرکزی دریافت می‌کند، پردازش محلی را انجام می‌دهد و نتایج را به سرور ارسال می‌کند. اگر اینترنت قطع شود، عامل محلی درخواست‌ها را در صف محلی نگه می‌دارد و پس از اتصال مجدد ارسال می‌کند."))
    
    story.append(PageBreak())

    # ============ CHAPTER 5: Data Model ============
    story.append(Paragraph(fa("فصل ۵: مدل داده و جداول - به‌روزرسانی با تصمیمات نهایی"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این فصل، مدل داده دقیق سامانه را بر اساس تمام تصمیمات نهایی ارائه می‌دهیم. مدل داده به دو بخش کاملاً مجزا تقسیم می‌شود: جداول سرور مرکزی برای مدیریت کارها و جداول سرور محلی برای اطلاعات حسابداری. این جداسازی هم امنیت را بهبود می‌بخشد و هم توسعه آینده را ساده می‌کند. تمام جداول بر اساس PostgreSQL طراحی شده‌اند."))
    
    story.append(Paragraph(fa("۵.۱ جداول سرور مرکزی"), style_h2))
    story.append(P("جدول زیر جداول اصلی سرور مرکزی را با ستون‌ها و قواعد اصلی نشان می‌دهد. این جداول اطلاعات عملیاتی دفتر را نگه می‌دارند و هیچ ریز سند حسابداری در آن‌ها ذخیره نمی‌شود."))
    
    central_tables = [
        ["جدول", "ستون‌های اصلی", "قواعد کلیدی"],
        ["users", "id UUID PK، username UNIQUE، display_name، role، is_active", "نقش: employee/supervisor/ceo/admin"],
        ["companies", "id UUID PK، company_code UNIQUE، display_name، is_active", "هر شرکت شناسه مستقل دارد"],
        ["user_company_access", "user_id FK، company_id FK، permission_set", "کلید یکتای (user_id, company_id)"],
        ["fiscal_periods", "id UUID PK، company_id FK، start_date، end_date، name", "سال مالی هر شرکت"],
        ["tasks", "id UUID PK، company_id FK، title، description، created_by، due_at، priority، status، template_id", "وضعیت: ۱۰ مقدار مختلف"],
        ["task_assignments", "task_id FK، user_id FK، assignment_type، assigned_at", "type: primary/collaborator/reviewer"],
        ["task_checklist_items", "id UUID PK، task_id FK， title， assigned_to， is_completed， completed_at", "تفکیک تسک به مراحل"],
        ["work_submissions", "id UUID PK، task_id FK، submitted_by، period_start، period_end， local_job_id، status， submission_score (0-100)", "نمره مدیر ۰-۱۰۰"],
        ["manager_decisions", "id UUID PK، submission_id FK، reviewer_id FK، decision_type， reason_visible， reason_confidential، score (0-100)， created_at", "نمونه‌برداری تصمیم مدیر"],
        ["reference_versions", "id UUID PK، company_id FK， fiscal_period_id FK， version_number， uploaded_by， uploaded_at， file_hash， date_range_start， date_range_end， status", "نسخه‌بندی فایل مرجع"],
        ["task_reference_bindings", "task_id FK， reference_version_id FK، bound_at", "هر تسک به نسخه مشخصی متصل است"],
        ["reconciliation_runs", "id UUID PK، submission_id FK， reference_version_id FK， algorithm_version， status， started_at， finished_at", "هر اجرای تطبیق مستقل"],
        ["notifications", "id UUID PK， user_id FK， event_key UNIQUE， type， read_at， created_at", "کلید یکتای رویداد"],
        ["leave_requests", "id UUID PK， user_id FK， start_at， end_at， reason_code， status， reviewed_by", "گردش تأیید مرخصی"],
        ["attendance_records", "id UUID PK， user_id FK， event_type， event_time， source، created_at", "ورود/خروج"],
        ["audit_events", "id UUID PK， actor_id， action， object_type， object_id， occurred_at， correlation_id", "غیرقابل‌حذف (Append-only)"],
        ["local_agent_status", "agent_id UUID PK， last_seen_at， agent_version， health_status", "وضعیت عامل محلی"],
    ]
    col_w_ct = [3.5*cm, 7*cm, 5.5*cm]
    factor = CONTENT_W / sum(col_w_ct)
    col_w_ct = [w * factor for w in col_w_ct]
    story.append(make_table(central_tables, col_widths=col_w_ct))
    story.append(Spacer(1, 8))
    
    story.append(callout("نکته مهم: جدول work_submissions شامل ستون submission_score (نمره ۰-۱۰۰) است که مستقل از وضعیت تأیید است. این ستون به مدیر اجازه می‌دهد کیفیت کار را به‌صورت پیوسته اندازه بگیرد، نه فقط باینری (تأیید/رد).", 'info'))
    
    story.append(Paragraph(fa("۵.۲ جداول سرور محلی"), style_h2))
    story.append(P("جدول زیر جداول اصلی سرور محلی را نشان می‌دهد. تمام اطلاعات حساس حسابداری در این جداول ذخیره می‌شوند و هرگز به سرور مرکزی ارسال نمی‌شوند."))
    
    local_tables = [
        ["جدول", "ستون‌های اصلی", "کاربرد"],
        ["local_companies", "company_id UUID PK, company_code, display_name, active", "مطابقت با شرکت‌های مرکزی"],
        ["source_connections", "id UUID PK, company_id FK, source_type, config_ref, enabled, last_success_at", "تنظیمات اتصال هر نرم‌افزار"],
        ["source_sync_runs", "id UUID PK, connection_id FK, started_at, finished_at, status, cursor_before, cursor_after", "تاریخچه دریافت اطلاعات"],
        ["source_documents", "id UUID PK, company_id, source_id, document_id, document_number, document_date, fiscal_year_id, source_version", "اسناد از منبع"],
        ["source_entries", "id UUID PK, document_id FK, line_id, account_code, description, debit_minor, credit_minor, row_fingerprint, modified_at", "ردیف‌های سند از مبدأ"],
        ["reference_files", "id UUID PK, reference_version_id FK, original_filename, file_hash, stored_path, schema_version, status, created_at", "فایل‌های مرجع مدیر"],
        ["reference_entries", "id UUID PK, reference_file_id FK, source_line_key, document_number, document_date, line_number, account_code, description, debit_minor, credit_minor", "ردیف‌های استخراج‌شده از فایل مرجع"],
        ["import_jobs", "id UUID PK, company_id, task_id, submitted_by, file_hash, schema_version, status, created_at", "هر بارگذاری اکسل کارمند"],
        ["import_entries", "id UUID PK, job_id FK, source_line_key, document_number, document_date, line_number, account_code, description, debit_minor, credit_minor", "ردیف‌های اکسل کارمند"],
        ["reconciliation_runs", "id UUID PK, job_id FK, reference_file_id FK, algorithm_version, status, started_at, finished_at", "هر اجرای تطبیق"],
        ["reconciliation_diffs", "id UUID PK, run_id FK, diff_type, source_line_key, field_name, expected_value, actual_value, severity, employee_value, reference_value", "جزئیات مغایرت‌ها"],
        ["record_versions", "id UUID PK, entity_type, entity_id, version_number, change_reason, changed_at, changed_by", "نسخه‌های اصلاح‌شده"],
        ["local_audit_events", "id UUID PK, actor_id, action, object_type, object_id, occurred_at, correlation_id", "تاریخچه عملیات محلی"],
        ["idempotency_keys", "key PK, operation, result_ref, created_at, expires_at", "جلوگیری از پردازش تکراری"],
    ]
    col_w_lt = [3.5*cm, 8*cm, 4.5*cm]
    factor = CONTENT_W / sum(col_w_lt)
    col_w_lt = [w * factor for w in col_w_lt]
    story.append(make_table(local_tables, col_widths=col_w_lt))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۵.۳ قرارداد استاندارد ردیف حسابداری"), style_h2))
    story.append(P("تمام اتصال‌دهنده‌ها (چه از SQL Server، چه از Excel، چه از API) باید خروجی یکسان تولید کنند. تفاوت نرم‌افزارها نباید به موتور تطبیق منتقل شود. این قرارداد، قلب لایه استانداردسازی است."))
    
    json_sample = '{\n  "schema_version": "1.0",\n  "company_id": "UUID",\n  "source_system_id": "UUID",\n  "source_database_id": "UUID",\n  "fiscal_year_id": "FY-1405",\n  "document_id": "SOURCE-DOC-ID",\n  "document_number": "12345",\n  "document_date": "2026-03-21",\n  "line_id": "SOURCE-LINE-ID",\n  "line_number": 1,\n  "account_code": "101010",\n  "description": "نمونه شرح سند",\n  "debit": "1250000.00",\n  "credit": "0.00",\n  "currency": "IRR",\n  "source_modified_at": null,\n  "source_version": null\n}'
    story.append(P(json_sample))
    
    story.append(callout("قاعده کلیدی: line_id باید شناسه واقعی ردیف از دیتابیس مبدأ باشد. مطابق تصمیم شما، این شناسه پس از حذف و ثبت مجدد سند تغییر می‌کند. این رفتار، تشخیص اصلاح از تکرار را ممکن می‌کند، اما نیاز به تطبیق احتمالی با سایر فیلدها دارد.", 'warn'))
    
    story.append(PageBreak())

    # ============ CHAPTER 6: Reference File + Manager Decision ============
    story.append(Paragraph(fa("فصل ۶: فایل مرجع اختیاری و تصمیم مدیر - قابلیت‌های جدید"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("این فصل، قابلیت‌های جدیدی را که شما در گفت‌وگوهای راهبردی تأیید کرده‌اید، تشریح می‌کند. این قابلیت‌ها سامانه را از یک ابزار تطبیق اکسل ساده به یک سامانه کامل مدیریت وظایف، تأیید کار و ارزیابی عملکرد تبدیل می‌کنند."))
    
    story.append(Paragraph(fa("۶.۱ فایل مرجع اختیاری"), style_h2))
    story.append(P("مهم‌ترین تصمیم شما، اختیاری بودن فایل مرجع است. مدیر هر زمان که بخواهد کاری را راستی‌آزمایی کند، فایل مرجع را بارگذاری می‌کند. اگر نخواهد تطبیق اکسل انجام دهد، می‌تواند بدون فایل مرجع هم کار را تأیید کند. این تصمیم، گردش کار تصمیم مدیر را به‌طور قابل توجهی ساده و انعطاف‌پذیر می‌کند. در عمل، مدیر می‌تواند با تکیه بر اعتماد یا مشاهده سریع، کار را تأیید کند و فقط برای کارهای مشکوک یا مهم، فایل مرجع را بارگذاری نماید."))
    
    story.append(Paragraph(fa("۶.۲ نسخه‌بندی فایل مرجع"), style_h2))
    story.append(P("هر بار که مدیر فایل مرجع جدیدی برای یک شرکت و دوره مالی بارگذاری می‌کند، یک نسخه جدید ایجاد می‌شود. نسخه قبلی حذف یا بازنویسی نمی‌شود. این قابلیت چندین مزیت دارد. اول، تسک‌های قبلی که با نسخه قدیمی تأیید شده‌اند، همچنان به همان نسخه متصل هستند و تاریخچه ممیزی آن‌ها حفظ می‌شود. دوم، چندین تسک می‌توانند از یک نسخه مرجع استفاده کنند، که از بارگذاری تکراری فایل‌ها جلوگیری می‌کند. سوم، اگر مدیر فایل مرجع را به‌روزرسانی کند، تأییدهای قبلی خودکار تغییر نمی‌کنند؛ برای بررسی مجدد باید نسخه جدید صراحتاً انتخاب شود."))
    
    story.append(Paragraph(fa("۶.۳ امتیاز ۰ تا ۱۰۰ مستقل از تأیید"), style_h2))
    story.append(P("شما تصمیم گرفتید که امتیاز هر تسک عددی از ۰ تا ۱۰۰ است که مدیر تعیین می‌کند. این امتیاز، وضعیت تأیید و نتیجه تطبیق سه مفهوم مستقل هستند. تأیید کار لزوماً به معنی امتیاز ۱۰۰ نیست. این تصمیم، چارچوب ارزیابی پرسنل را به‌طور بنیادی تغییر می‌دهد. به‌عنوان مثال، مدیر می‌تواند کار را تأیید کند اما امتیاز ۷۵ بدهد، که نشان‌دهنده کیفیت متوسط کار است. این امتیاز در ارزیابی ماهانه و سالانه کارمند لحاظ می‌شود."))
    
    story.append(Paragraph(fa("۶.۴ یادداشت دو سطحی"), style_h2))
    story.append(P("شما خواستار یادداشت با دو سطح دسترسی بودید. مدیر می‌تواند یادداشت قابل مشاهده برای کارمند یا یادداشت محرمانه مدیریتی ثبت کند. یادداشت محرمانه در پنل کارمند، خروجی‌های قابل مشاهده او و اعلان‌های ارسالی نمایش داده نمی‌شود. این قابلیت به مدیر اجازه می‌دهد یادداشت‌های خصوصی برای خودش بنویسد (مثلاً «این کارمند معمولاً در ثبت اسناد پیچیده اشتباه می‌کند») بدون اینکه کارمند آن را ببیند. در عین حال، یادداشت قابل مشاهده به کارمند کمک می‌کند بداند چه چیزی خوب انجام شده و چه چیزی نیاز به بهبود دارد."))
    
    story.append(Paragraph(fa("۶.۵ دلیل اجباری برای رد یا بازگشت"), style_h2))
    story.append(P("شما تصمیم گرفتید که در صورت عدم تأیید یا بازگرداندن کار، مدیر باید دلیل روشن و قابل فهم بنویسد. کارمند باید بداند چه چیزی اشتباه بوده، چه اصلاحی لازم است و تا چه زمانی باید آن را انجام دهد. این قابلیت دو هدف دارد. اول، به کارمند کمک می‌کند اشتباه خود را بفهمد و آن را اصلاح کند. دوم، در ارزیابی عملکرد، الگوی اشتباهات مکرر را شناسایی می‌کند. به‌عنوان مثال، اگر کارمند الف سه بار در ماه به‌دلیل «تاریخ اشتباه در سند» برگشت داده شود، مدیر می‌تواند این الگو را شناسایی و با کارمند گفت‌وگو کند."))
    
    story.append(Paragraph(fa("۶.۶ چهار نوع تصمیم مدیر"), style_h2))
    story.append(P("بر اساس تصمیمات شما، مدیر می‌تواند چهار نوع تصمیم برای هر تسک بگیرد. جدول زیر این چهار نوع و اثر هرکدام بر ارزیابی را نشان می‌دهد."))
    
    decisions_data = [
        ["نوع تصمیم", "توضیح", "اثر بر ارزیابی", "نیاز به فایل مرجع", "نیاز به دلیل"],
        ["تأیید عادی", "کار بدون اشکال پذیرفته می‌شود", "نمره ۰-۱۰۰ مدیر، بدون امتیاز منفی", "اختیاری", "خیر"],
        ["تأیید با ارفاق", "کار با اختلاف قابل قبول پذیرفته می‌شود", "نمره ۰-۱۰۰ مدیر، با ثبت دلیل ارفاق", "اختیاری", "بله (دلیل ارفاق)"],
        ["بازگشت به کارمند", "کار برای اصلاح برمی‌گردد", "نمره ۰-۱۰۰ مدیر، با ثبت دلیل بازگشت", "اختیاری", "بله (دلیل و مهلت اصلاح)"],
        ["عدم تأیید نهایی", "کار قابل قبول نیست و اصلاح نمی‌شود", "نمره ۰، با ثبت دلیل نهایی", "اختیاری", "بله (دلیل نهایی)"],
    ]
    col_w_dec = [3*cm, 4*cm, 4*cm, 2.5*cm, 2.5*cm]
    factor = CONTENT_W / sum(col_w_dec)
    col_w_dec = [w * factor for w in col_w_dec]
    story.append(make_table(decisions_data, col_widths=col_w_dec))
    story.append(Spacer(1, 8))
    
    story.append(callout("قاعده حیاتی: امتیاز منفی خودکار صرفاً بر اساس تعداد اختلاف‌ها اعمال نمی‌شود. مدیر باید بتواند علت و میزان اثر را مشخص کند. یک اختلاف مهم با چند اختلاف جزئی ارزش یکسانی ندارد.", 'warn'))
    
    story.append(PageBreak())

    # ============ CHAPTER 7: Reconciliation Algorithm ============
    story.append(Paragraph(fa("فصل ۷: الگوریتم تطبیق با شناسه ردیف مبدأ"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این فصل، الگوریتم دقیق تطبیق ردیف‌ها را بر اساس تصمیم نهایی شما (شناسه ردیف از دیتابیس مبدأ) تشریح می‌کنیم. این الگوریتم، قلب موتور کنترل هوشمند است و باید به‌دقت طراحی شود تا اصلاح سند را از تکرار واقعی تشخیص دهد."))
    
    story.append(Paragraph(fa("۷.۱ کلید تطبیق اصلی"), style_h2))
    story.append(P("مطابق تصمیم شما، شناسه ردیف از دیتابیس مبدأ کلید اصلی تطبیق است. کلید کامل شامل ترکیب زیر است:"))
    
    story.append(P("کلید = CompanyID + SourceDatabaseID + FiscalYearID + SourceLineID"))
    
    story.append(P("این کلید چهار جزء دارد تا یکتایی آن تضمین شود. شناسه ردیف به‌تنهایی کافی نیست، زیرا ممکن است دو دیتابیس شناسه‌های عددی مشابه داشته باشند. با ترکیب شرکت، دیتابیس مبدأ، سال مالی و شناسه ردیف، یکتایی کامل تضمین می‌شود."))
    
    story.append(Paragraph(fa("۷.۲ چالش تغییر شناسه پس از حذف-ثبت مجدد"), style_h2))
    story.append(P("شما تأیید کردید که شناسه ردیف پس از حذف و ثبت مجدد سند تغییر می‌کند. این رفتار چالش اصلی الگوریتم است: اگر کارمند سندی را در نرم‌افزار حسابداری حذف و دوباره ثبت کند، شناسه ردیف جدید متفاوت از شناسه قبلی است. سامانه باید بتواند این حالت را از «سند واقعاً جدید» تشخیص دهد."))
    
    story.append(P("راهکار ما سه مرحله‌ای است. اول، اگر شناسه ردیف در فایل اکسل و دیتابیس مبدأ یکسان است، مستقیماً تطبیق می‌شود. دوم، اگر شناسه ردیف در دیتابیس مبدأ حذف شده و شناسه جدیدی با مقادیر مشابه ایجاد شده، تطبیق احتمالی با سایر فیلدها (تاریخ، شماره سند، حساب‌ها، مبلغ، شرح) انجام می‌شود. سوم، اگر تطبیق احتمالی قوی باشد (مثلاً ۸ از ۹ فیلد منطبق)، سامانه آن را به‌عنوان «جایگزینی احتمالی» گزارش می‌کند، اما خودکار تأیید نمی‌کند؛ تصمیم نهایی با مدیر است."))
    
    story.append(Paragraph(fa("۷.۳ نه مرحله الگوریتم"), style_h2))
    story.extend(numbered_list([
        "ثبت تحویل: شناسه تحویل، کارمند، شرکت، دوره ادعایی، هش فایل SHA-256، وضعیت RECEIVED",
        "اعتبارسنجی قالب: نوع فایل، ستون‌های اجباری، نوع داده‌ها، تاریخ‌های شمسی/میلادی، مبالغ عددی",
        "کنترل تکراری فایل: هش فایل در برابر تحویل‌های قبلی همان شرکت بررسی می‌شود",
        "کنترل تکراری ردیف در فایل: ردیف‌هایی با تمام فیلدهای یکسان شناسایی می‌شوند",
        "کنترل بازه تاریخی: حداقل و حداکثر تاریخ فایل با بازه ادعایی کارمند مقایسه می‌شود",
        "دریافت داده مرجع: از فایل مرجع مدیر (در صورت بارگذاری) یا مستقیماً از دیتابیس مبدأ",
        "مقایسه کلید به کلید: کلید تطبیق (شرکت + دیتابیس + سال مالی + شناسه ردیف) در دو مجموعه ساخته می‌شود",
        "تشخیص مغایرت: ردیف‌های فقط در اکسل، فقط در مرجع، و ردیف‌های مشترک با مقادیر متفاوت شناسایی می‌شوند",
        "تشخیص اصلاح از تکرار: سه حالت (ردیف یکسان، جایگزینی احتمالی، ردیف واقعاً جدید) تفکیک می‌شوند",
    ]))
    
    story.append(Paragraph(fa("۷.۴ قواعد تشخیص مغایرت"), style_h2))
    story.append(P("مهم‌ترین قاعده: پیدا نشدن ردیف در فایل مرجع، به‌تنهایی اثبات نمی‌کند که کارمند اشتباه کرده است. ممکن است فایل مدیر ناقص باشد یا محدوده زمانی دو فایل متفاوت باشد. در این حالت، نتیجه باید «نیازمند بررسی بیشتر» باشد، نه «مغایرت قطعی»."))
    
    story.append(P("همچنین، قطع ارتباط با منبع نباید به‌عنوان «سند مفقود» گزارش شود. اگر دیتابیس مبدأ قطع باشد، نتیجه باید «کنترل انجام نشد» یا «دریافت ناقص» باشد. فقط وقتی دریافت منبع کامل و معتبر است، می‌توان نتیجه مقایسه را مغایرت واقعی تلقی کرد. این تفکیک خطای فنی از مغایرت حسابداری، از هشدارهای کاذب به مدیر جلوگیری می‌کند."))
    
    story.append(Paragraph(fa("۷.۵ وضعیت‌های استاندارد تطبیق"), style_h2))
    
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
    col_w_st = [4*cm, 6.5*cm, 5.5*cm]
    factor = CONTENT_W / sum(col_w_st)
    col_w_st = [w * factor for w in col_w_st]
    story.append(make_table(status_data, col_widths=col_w_st))
    story.append(Spacer(1, 8))
    
    story.append(callout("قاعده مهم: VERIFIED به معنی تأیید صحت همه ابعاد حسابداری نیست؛ فقط یعنی کنترل‌های مشخص‌شده موفق بوده‌اند. تأیید مدیریتی مرحله جداگانه‌ای است که با تصمیم مدیر (تأیید/رد/بازگشت) ثبت می‌شود.", 'info'))
    
    story.append(PageBreak())

    # ============ CHAPTER 8: KPI Framework Updated ============
    story.append(Paragraph(fa("فصل ۸: چارچوب ارزیابی پرسنل با نمره ۰-۱۰۰"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("چارچوب ارزیابی پرسنل در نسخه ۲ به‌طور قابل توجهی بهبود یافته است. مطابق تصمیم شما، نمره ۰-۱۰۰ مدیر به هر تسک، محور اصلی ارزیابی است. این نمره به‌صورت پیوسته کیفیت کار را اندازه می‌گیرد و در ارزیابی ماهانه و سالانه لحاظ می‌شود. در این فصل، چارچوب کامل ارزیابی را تشریح می‌کنیم."))
    
    story.append(Paragraph(fa("۸.۱ چهار شاخص اصلی عملکرد (KPI)"), style_h2))
    story.append(P("چارچوب ارزیابی شامل چهار شاخص وزن‌دار است. نمره ۰-۱۰۰ مدیر، محور شاخص «کیفیت کار» است و وزن ۴۰٪ دارد. سایر شاخص‌ها به‌صورت خودکار از سامانه محاسبه می‌شوند."))
    
    kpi_data = [
        ["شاخص", "وزن", "تعریف", "روش اندازه‌گیری"],
        ["کیفیت کار (نمره مدیر)", "۴۰٪", "میانگین نمره ۰-۱۰۰ مدیر به تسک‌های تأییدشده کارمند در دوره", "اتوماتیک از manager_decisions"],
        ["تحویل به‌موقع", "۲۵٪", "نسبت تسک‌های تحویلی در مهلت به کل تسک‌ها", "اتوماتیک از تاریخ تحویل"],
        ["حجم/پیچیدگی کار", "۲۰٪", "حجم کار استانداردشده با ضریب پیچیدگی هر نوع فعالیت", "نیمه‌خودکار + تأیید مدیر"],
        ["همکاری و ارجاع صحیح", "۱۵٪", "کیفیت ارجاع‌ها به همکاران و تحویل منظم مراحل", "ارزیابی کیفی ماهانه مدیر"],
    ]
    col_w_kpi = [3.8*cm, 1.2*cm, 6*cm, 5*cm]
    factor = CONTENT_W / sum(col_w_kpi)
    col_w_kpi = [w * factor for w in col_w_kpi]
    story.append(make_table(kpi_data, col_widths=col_w_kpi))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۸.۲ محاسبه نمره کل ماهانه"), style_h2))
    story.append(P("نمره کل ماهانه هر کارمند از ترکیب چهار شاخص با وزن‌های مشخص محاسبه می‌شود. به‌عنوان مثال، اگر کارمند الف در ماه مهر داشته باشد: نمره کیفیت ۸۲ (میانگین نمره مدیر به ۲۰ تسک)، تحویل به‌موقع ۹۰٪، حجم/پیچیدگی ۸۵، همکاری ۸۸، نمره کل برابر خواهد بود با: (۸۲×۰.۴ + ۹۰×۰.۲۵ + ۸۵×۰.۲ + ۸۸×۰.۱۵) = ۸۵.۹. این نمره در داشبورد مدیر نمایش داده می‌شود و با سایر کارمندان مقایسه می‌گردد."))
    
    story.append(Paragraph(fa("۸.۳ نمونه کارت امتیاز ماهانه"), style_h2))
    
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
    col_w_sc = [4.5*cm, 2.5*cm, 2*cm, 3*cm, 4*cm]
    factor = CONTENT_W / sum(col_w_sc)
    col_w_sc = [w * factor for w in col_w_sc]
    story.append(make_table(scorecard_data, col_widths=col_w_sc))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۸.۴ گزارش دلایل رد و بازگشت"), style_h2))
    story.append(P("یکی از قابلیت‌های ارزشمند سامانه، گزارش دلایل رد و بازگشت است. مدیر می‌تواند در پایان ماه ببیند چه دلاینی بیشترین فراوانی را داشته‌اند. به‌عنوان مثال، اگر ۸ از ۱۰ برگشتی به‌دلیل «تاریخ اشتباه» بوده، مدیر می‌تواند با کارمند گفت‌وگو کند و آموزش لازم را ارائه دهد. این گزارش، بهبود مستمر عملکرد را ممکن می‌کند."))
    
    reasons_data = [
        ["دلیل رد/بازگشت", "تعداد در ماه", "درصد", "کارمندان تأثیرپذیرفته", "اقدام پیشنهادی"],
        ["تاریخ اشتباه در سند", "۸", "۴۰٪", "کارمند الف (۵)، کارمند ب (۳)", "آموزش تبدیل تاریخ شمسی"],
        ["مبلغ بده/بستان نامتعادل", "۴", "۲۰٪", "کارمند ج (۳)، کارمند د (۱)", "بازبینی فرمول تراز سند"],
        ["شرح سند ناقص", "۳", "۱۵٪", "کارمند الف (۲)، کارمند ه (۱)", "آموزش نوشتن شرح"],
        ["شماره سند تکراری", "۲", "۱۰٪", "کارمند ب (۲)", "کنترل خودکار شماره سند"],
        ["سند مفقود از فایل", "۲", "۱۰٪", "کارمند ج (۲)", "بازبینی فرایند جمع‌آوری مدارک"],
        ["سایر دلایل", "۱", "۵٪", "کارمند د (۱)", "—"],
    ]
    col_w_re = [4*cm, 2*cm, 1.5*cm, 4*cm, 4.5*cm]
    factor = CONTENT_W / sum(col_w_re)
    col_w_re = [w * factor for w in col_w_re]
    story.append(make_table(reasons_data, col_widths=col_w_re))
    story.append(Spacer(1, 8))
    
    story.append(callout("اصل ارزیابی: ارزیابی منصفانه است. امتیاز منفی خودکار صرفاً بر اساس تعداد اختلاف‌ها اعمال نمی‌شود. مدیر باید بتواند علت و میزان اثر را مشخص کند. این اصل، اعتماد کارمندان به سامانه ارزیابی را حفظ می‌کند.", 'info'))
    
    story.append(PageBreak())

    # ============ CHAPTER 9: Excel Template with Source Line ID ============
    story.append(Paragraph(fa("فصل ۹: الگوی اکسل با شناسه ردیف مبدأ"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("قالب اکسل کارمند در نسخه ۲ به‌روزرسانی شده است. مطابق تصمیم شما، ستون «شناسه ردیف سند مبدأ» به‌عنوان اولین ستون و کلید اصلی تشخیص تکراری اضافه شده است. این شناسه از دیتابیس مبدأ (نرم‌افزار حسابداری) استخراج می‌شود و پس از حذف-ثبت مجدد تغییر می‌کند."))
    
    story.append(Paragraph(fa("۹.۱ ساختار ستون‌های اکسل"), style_h2))
    
    columns_data = [
        ["شماره", "نام ستون", "نوع داده", "الزامی", "قواعد اعتبارسنجی"],
        ["۱", "شناسه ردیف مبدأ (SourceLineID)", "متن/عدد", "بله", "از دیتابیس مبدأ؛ پس از حذف-ثبت مجدد تغییر می‌کند"],
        ["۲", "شناسه سند مبدأ (SourceDocumentID)", "متن/عدد", "بله", "از دیتابیس مبدأ؛ یکتا در همان سال مالی"],
        ["۳", "ردیف (LineNumber)", "عدد صحیح", "بله", "شماره ردیف نمایشی در سند (ممکن است با SourceLineID متفاوت باشد)"],
        ["۴", "شماره سند (DocumentNumber)", "متن/عدد", "بله", "شماره نمایشی سند (ممکن است پس از حذف-ثبت مجدد تغییر کند)"],
        ["۵", "تاریخ سند (DocumentDate)", "تاریخ شمسی", "بله", "فرمت YYYY/MM/DD؛ معتبر و قابل تبدیل"],
        ["۶", "کد کل (AccountLevel1)", "متن/عدد", "بله", "کد حساب کل؛ باید در طرح حساب شرکت وجود داشته باشد"],
        ["۷", "کد معین (AccountLevel2)", "متن/عدد", "بله", "کد حساب معین؛ زیرمجموعه کد کل"],
        ["۸", "کد تفصیل (AccountLevel3)", "متن/عدد", "خیر", "کد تفصیل (در صورت پشتیبانی شرکت)"],
        ["۹", "شرح سند (Description)", "متن", "خیر", "توضیح ردیف سند؛ حداکثر ۵۰۰ کاراکتر"],
        ["۱۰", "بدهکار (Debit)", "عدد اعشاری", "بله*", "مبلغ بدهکار؛ *دقیقاً یکی از بده یا بستان باید صفر باشد"],
        ["۱۱", "بستانکار (Credit)", "عدد اعشاری", "بله*", "مبلغ بستانکار؛ *دقیقاً یکی از بده یا بستان باید صفر باشد"],
    ]
    col_w_cols = [1*cm, 4*cm, 2.2*cm, 1.4*cm, 8*cm]
    factor = CONTENT_W / sum(col_w_cols)
    col_w_cols = [w * factor for w in col_w_cols]
    story.append(make_table(columns_data, col_widths=col_w_cols))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۹.۲ نمونه فایل اکسل استاندارد"), style_h2))
    story.append(P("نمونه زیر چهار ردیف فرضی از فایل اکسل یک شرکت را نشان می‌دهد. این نمونه صرفاً برای نمایش قالب است و اعداد واقعی نیستند."))
    
    sample_data = [
        ["SourceLineID", "DocID", "ردیف", "شماره سند", "تاریخ", "کل", "معین", "تفصیل", "شرح", "بده", "بس"],
        ["LID-1001", "DID-101", "۱", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۱", "۱۰۱", "۱۰۱۰۱", "فروش نقدی", "۵٬۰۰۰٬۰۰۰", "۰"],
        ["LID-1002", "DID-101", "۲", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۵", "۵۰۱", "۵۰۱۰۱", "دریافت نقدی", "۰", "۵٬۰۰۰٬۰۰۰"],
        ["LID-1003", "DID-102", "۱", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۲", "۲۰۱", "۲۰۱۰۱", "خرید کالا", "۰", "۳٬۰۰۰٬۰۰۰"],
        ["LID-1004", "DID-102", "۲", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۴", "۴۰۱", "۴۰۱۰۱", "پرداخت نقدی", "۳٬۰۰۰٬۰۰۰", "۰"],
    ]
    col_w_sample = [1.5*cm, 1.3*cm, 0.9*cm, 1.3*cm, 1.5*cm, 0.8*cm, 0.8*cm, 1.0*cm, 3.2*cm, 1.7*cm, 1.7*cm]
    factor = CONTENT_W / sum(col_w_sample)
    col_w_sample = [w * factor for w in col_w_sample]
    story.append(make_table(sample_data, col_widths=col_w_sample))
    story.append(Spacer(1, 8))
    
    story.append(callout("نکته مهم: ستون SourceLineID از دیتابیس مبدأ استخراج می‌شود. اگر کارمند سندی را حذف و دوباره ثبت کند، SourceLineID جدید متفاوت است. سامانه با تطبیق احتمالی (تاریخ، شماره سند، حساب، مبلغ) این حالت را از سند واقعاً جدید تشخیص می‌دهد، اما خودکار تأیید نمی‌کند؛ تصمیم نهایی با مدیر است.", 'warn'))
    
    story.append(PageBreak())

    # ============ CHAPTER 10: Phased Roadmap ============
    story.append(Paragraph(fa("فصل ۱۰: نقشه راه پیاده‌سازی فازبندی‌شده - به‌روزرسانی شده"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("نقشه راه پیاده‌سازی در نسخه ۲ بر اساس تمام تصمیمات نهایی به‌روزرسانی شده است. سامانه در پنج فاز پیاده‌سازی می‌شود، به‌گونه‌ای که هر فاز خروجی قابل استفاده و قابل آزمایش داشته باشد. کل زمان تخمینی تا نسخه اولیه قابل استفاده (MVP) حدود ۱۳ هفته است."))
    
    story.append(Paragraph(fa("فاز ۱: شناخت دیتابیس نمونه (هفته ۱-۲)"), style_h2))
    story.append(P("انتخاب یک شرکت با نرم‌افزار همکاران (SQL Server)، یک شرکت با نرم‌افزار سپیدار (SQL Server) و یک شرکت با فایل اکسل. بررسی ساختار جداول اسناد در هر دیتابیس، شناسایی کلیدهای اصلی (به‌ویژه شناسه ردیف مبدأ)، تعیین روش اتصال، و نوشتن اسکریپت آزمایشی برای خواندن چند سند. خروجی: سند فنی ساختار دیتابیس‌ها و نمونه قرارداد استاندارد. مدت زمان: ۲ هفته. ریسک: تفاوت ساختار نرم‌افزارها در نسخه‌های مختلف."))
    
    story.append(Paragraph(fa("فاز ۲: پنل وب و مدیریت تسک (هفته ۳-۶)"), style_h2))
    story.append(P("احراز هویت کاربران، تعریف نقش‌ها، تعریف ۵۰ شرکت و ۵ کارمند، تخصیص تسک، چک‌لیست مراحل (الگوی Pixie)، پیگیری پیشرفت، آپلود فایل اکسل، نمره ۰-۱۰۰ مدیر، یادداشت دو سطحی، دلیل اجباری برای رد، و اعلان‌های پایه. در این فاز، سامانه هنوز تطبیق هوشمند انجام نمی‌دهد اما کارمندان می‌توانند تسک‌ها را مدیریت کنند و مدیر می‌تواند نمره بدهد. خروجی: نسخه قابل استفاده برای مدیریت تسک. مدت: ۴ هفته."))
    
    story.append(Paragraph(fa("فاز ۳: موتور کنترل هوشمند اکسل (هفته ۷-۱۰)"), style_h2))
    story.append(P("پیاده‌سازی ۹ مرحله کنترل، ساخت Adapter‌های SQL Server و Excel، پیاده‌سازی مدل داده استاندارد، تولید گزارش مغایرت، رابط کاربری مدیر برای مشاهده گزارش‌ها، تأیید یا رد با نمره. در این فاز، فایل مرجع اختیاری نیز پیاده‌سازی می‌شود: مدیر می‌تواند بدون فایل مرجع هم کار را تأیید کند. خروجی: نسخه با کنترل کامل اسناد. مدت: ۴ هفته."))
    
    story.append(Paragraph(fa("فاز ۴: اجرای آزمایشی (هفته ۱۱-۱۳)"), style_h2))
    story.append(P("سامانه روی دو یا سه شرکت با کارمندان واقعی استفاده می‌شود. هدف: مقایسه نتایج کنترل با بررسی دستی، شناسایی خطاهای موتور کنترل، تنظیم قواعد تشخیص اصلاح از تکرار، و جمع‌آوری بازخورد کاربران. این فاز نباید حذف شود؛ اجرای آزمایشی روی داده‌های واقعی معمولاً چندین مورد ناهماهنگی آشکار می‌کند. خروجی: نسخه پایدار قابل اعتماد. مدت: ۳ هفته."))
    
    story.append(Paragraph(fa("فاز ۵: توسعه و خودکارسازی (هفته ۱۴+)"), style_h2))
    story.append(P("سایر Adapter‌ها برای نرم‌افزارهای دیگر (تندیس، هلو)، اتصال به دستگاه حضور و غیاب، مرخصی و درخواست‌های پیشرفته، گزارش ارزیابی پرسنل با نمره ۰-۱۰۰، داشبورد مدیریتی کامل، دریافت خودکار ریز اسناد زمان‌بندی‌شده، و API برای اتصال ابزارهای خارجی. مدت: ادامه‌دار."))
    
    story.append(Paragraph(fa("۱۰.۱ جدول خلاصه فازها"), style_h2))
    
    phase_data = [
        ["فاز", "مدت", "خروجی اصلی", "ریسک کلیدی"],
        ["۱. شناخت دیتابیس نمونه", "۲ هفته", "سند فنی ساختار دیتابیس", "تفاوت ساختار نرم‌افزارها"],
        ["۲. پنل وب و مدیریت تسک", "۴ هفته", "پنل کار + نمره ۰-۱۰۰", "پذیرش کاربران"],
        ["۳. موتور کنترل هوشمند", "۴ هفته", "تطبیق کامل اسناد + فایل مرجع اختیاری", "پیچیدگی الگوریتم تشخیص اصلاح"],
        ["۴. اجرای آزمایشی", "۳ هفته", "نسخه پایدار", "خطاهای پنهان در داده واقعی"],
        ["۵. توسعه و خودکارسازی", "ادامه‌دار", "تمام Adapter‌ها + داشبورد کامل", "اولویت‌بندی"],
        ["مجموع تا MVP", "۱۳ هفته", "نسخه قابل استفاده روزانه", "—"],
    ]
    col_w_ph = [4.5*cm, 2*cm, 6*cm, 4.5*cm]
    factor = CONTENT_W / sum(col_w_ph)
    col_w_ph = [w * factor for w in col_w_ph]
    story.append(make_table(phase_data, col_widths=col_w_ph))
    story.append(Spacer(1, 10))
    
    story.append(callout("نکته مهم: فاز ۱ (شناخت دیتابیس) نباید حذف شود. ساختار دیتابیس نرم‌افزارهای ایرانی در نسخه‌های مختلف متفاوت است. بدون این شناخت دقیق، Adapter‌ها در فاز ۳ به خطاهای ساختاری روبه‌رو می‌شوند. این فاز، پایه کل پروژه است.", 'warn'))
    
    story.append(PageBreak())

    # ============ CHAPTER 11: Final Summary ============
    story.append(Paragraph(fa("فصل ۱۱: جمع‌بندی و توصیه‌های نهایی نسخه ۲"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("نسخه ۲ گزارش، حاصل تحلیل عمیق سه نرم‌افزار تخصصی و تمام تصمیمات راهبردی شماست. در این فصل پایانی، توصیه‌های نهایی و قدم‌های بعدی را به‌صورت عملی ارائه می‌دهیم."))
    
    story.append(Paragraph(fa("۱۱.۱ توصیه نهایی نسخه ۲"), style_h2))
    story.append(P("توصیه نهایی، ساخت یک سامانه اختصاصی با معماری ترکیبی است که از الگوهای مفید سه نرم‌افزار آماده (Financial Cents، Karbon، Pixie) الگوبرداری کرده باشد. این انتخاب بر اساس چهار دلیل اصلی است. اول، هیچ نرم‌افزار آماده‌ای تمام نیازهای شما (به‌ویژه کنترل هوشمند اسناد با شناسه ردیف مبدأ) را پوشش نمی‌دهد. دوم، نمره ۰-۱۰۰ مدیر و یادداشت دو سطحی، قابلیت‌هایی هستند که هیچ نرم‌افزار آماده‌ای ندارند. سوم، فایل مرجع اختیاری، انعطاف‌پذیری است که فقط در سامانه اختصاصی قابل پیاده‌سازی است. چهارم، نگهداری داده‌های خام در دفتر، الزام امنیتی است که نرم‌افزارهای آماده خارجی نمی‌توانند تضمین کنند."))
    
    story.append(Paragraph(fa("۱۱.۲ قدم‌های بعدی فوری (هفته اول)"), style_h2))
    story.extend(numbered_list([
        "انتخاب یک شرکت نمونه با نرم‌افزار همکاران و یک شرکت با نرم‌افزار سپیدار برای فاز ۱.",
        "تهیه یک فایل اکسل واقعی از اسناد یکی از شرکت‌ها، با ستون SourceLineID (شناسه ردیف مبدأ).",
        "اخذ دسترسی Read-Only به دیتابیس SQL Server شرکت‌های نمونه.",
        "مشاوره با ۲-۳ تیم توسعه ایرانی و ارائه این گزارش به‌عنوان RFP.",
        "تعیین بودجه نهایی (برآورد: ۸۰-۱۵۰ میلیون تومان برای MVP) و زمان‌بندی (۱۳ هفته).",
    ]))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("۱۱.۳ اقدامات میان‌مدت (۳ ماه)"), style_h2))
    story.extend(numbered_list([
        "تأیید تیم توسعه و امضای قرارداد شامل تعرفه‌های روشن برای فازهای ۲ تا ۵.",
        "شروع فاز ۱ (شناخت دیتابیس) و تولید سند فنی ساختار دیتابیس‌ها.",
        "طراحی دقیق مدل داده استاندارد با ستون SourceLineID و بررسی با تیم توسعه.",
        "آغاز فاز ۲ (پنل وب) و آموزش کارمندان به‌صورت موازی با توسعه.",
        "تعریف نقش‌ها و سطوح دسترسی به‌صورت رسمی قبل از راه‌اندازی.",
        "آزمون تطبیق با فایل نمونه و بررسی صحت الگوریتم تشخیص اصلاح از تکرار.",
    ]))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("۱۱.۴ چک‌لیست آماده‌سازی برای شروع پروژه"), style_h2))
    story.extend(bullet_list([
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
    ]))
    
    story.append(Spacer(1, 10))
    
    story.append(callout("پیام پایانی نسخه ۲: این گزارش اکنون یک سند فنی-اجرایی کامل است که می‌توانید آن را به تیم توسعه تحویل دهید. تمام تصمیمات راهبردی نهایی شده، الگوهای آماده استخراج شده، و نقشه راه فازبندی‌شده تعیین شده. موفقیت پروژه اکنون به انتخاب تیم توسعه مناسب و پایبندی به نقشه راه وابسته است.", 'success'))
    
    story.append(Spacer(1, 20))
    
    final_para = ParagraphStyle('Final', parent=style_body, fontName='Vazirmatn', fontSize=10, leading=16, alignment=TA_CENTER, textColor=C_TEXT_MUTED)
    story.append(Paragraph(fa("پایان گزارش راهبردی - نسخه ۲.۰"), final_para))
    
    doc.build(story)
    print(f"PDF generated: {output_path}")

if __name__ == '__main__':
    output = '/home/z/my-project/download/سامانه_مدیریت_دفتر_حسابداری_نسخه_۲.pdf'
    build_pdf(output)
    print("Build complete!")
