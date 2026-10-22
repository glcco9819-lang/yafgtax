"""
Accounting Office Management System - Research Report (Persian RTL)
Generates a deep 20+ page PDF using ReportLab with Vazirmatn font.
Uses arabic-reshaper + python-bidi for proper Persian text rendering.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image, Frame, PageTemplate, BaseDocTemplate
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
# Persian Text Helper - reshape + bidi for ReportLab
# ============================================================
def fa(text):
    """Reshape Persian text for ReportLab (RTL display)."""
    if text is None or text == "":
        return ""
    reshaper = arabic_reshaper.ArabicReshaper()
    reshaped = reshaper.reshape(str(text))
    return get_display(reshaped)

# ============================================================
# Color Palette - Professional Business
# ============================================================
C_PRIMARY = colors.HexColor('#0F172A')    # Deep slate
C_ACCENT  = colors.HexColor('#0E7C8B')    # Teal
C_ACCENT2 = colors.HexColor('#1E40AF')    # Blue
C_BG_LIGHT = colors.HexColor('#F1F5F9')  # Light slate
C_BG_ACCENT = colors.HexColor('#E0F2FE')  # Light cyan
C_TEXT_MUTED = colors.HexColor('#475569') # Slate-600
C_TABLE_HEADER = colors.HexColor('#0E7C8B')
C_TABLE_ALT = colors.HexColor('#F8FAFC')
C_BORDER = colors.HexColor('#CBD5E1')
C_SUCCESS = colors.HexColor('#16A34A')
C_WARN = colors.HexColor('#D97706')
C_DANGER = colors.HexColor('#DC2626')

# ============================================================
# Paragraph Styles (Persian RTL)
# ============================================================
PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

styles = getSampleStyleSheet()

# Cover styles
style_cover_title = ParagraphStyle(
    'CoverTitle', parent=styles['Normal'],
    fontName='Vazirmatn-Bold', fontSize=32, leading=42,
    alignment=TA_CENTER, textColor=colors.white,
    spaceAfter=12
)
style_cover_subtitle = ParagraphStyle(
    'CoverSubtitle', parent=styles['Normal'],
    fontName='Vazirmatn', fontSize=14, leading=22,
    alignment=TA_CENTER, textColor=colors.HexColor('#E2E8F0'),
    spaceAfter=8
)
style_cover_meta = ParagraphStyle(
    'CoverMeta', parent=styles['Normal'],
    fontName='Vazirmatn', fontSize=11, leading=18,
    alignment=TA_CENTER, textColor=colors.HexColor('#94A3B8'),
)

# Heading styles
style_h1 = ParagraphStyle(
    'H1', parent=styles['Heading1'],
    fontName='Vazirmatn-Bold', fontSize=20, leading=28,
    alignment=TA_RIGHT, textColor=C_PRIMARY,
    spaceBefore=18, spaceAfter=12,
    borderPadding=4
)
style_h2 = ParagraphStyle(
    'H2', parent=styles['Heading2'],
    fontName='Vazirmatn-Bold', fontSize=15, leading=22,
    alignment=TA_RIGHT, textColor=C_ACCENT,
    spaceBefore=14, spaceAfter=8
)
style_h3 = ParagraphStyle(
    'H3', parent=styles['Heading3'],
    fontName='Vazirmatn-Bold', fontSize=12.5, leading=18,
    alignment=TA_RIGHT, textColor=C_PRIMARY,
    spaceBefore=10, spaceAfter=6
)

# Body text
style_body = ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontName='Vazirmatn', fontSize=11, leading=20,
    alignment=TA_JUSTIFY, textColor=C_PRIMARY,
    spaceAfter=8, firstLineIndent=0
)
style_body_right = ParagraphStyle(
    'BodyRight', parent=style_body,
    alignment=TA_RIGHT, firstLineIndent=0
)

# Bullet/numbered list
style_bullet = ParagraphStyle(
    'Bullet', parent=style_body,
    fontName='Vazirmatn', fontSize=11, leading=19,
    alignment=TA_RIGHT, textColor=C_PRIMARY,
    rightIndent=14, leftIndent=0, spaceAfter=4,
    bulletIndent=-10
)
style_bullet_rtl = ParagraphStyle(
    'BulletRTL', parent=style_body,
    fontName='Vazirmatn', fontSize=11, leading=19,
    alignment=TA_RIGHT, textColor=C_PRIMARY,
    rightIndent=18, spaceAfter=4,
)

# Quote / callout
style_callout = ParagraphStyle(
    'Callout', parent=style_body,
    fontName='Vazirmatn-Medium', fontSize=11, leading=19,
    alignment=TA_RIGHT, textColor=C_PRIMARY,
    backColor=C_BG_ACCENT, borderPadding=8,
    borderWidth=0.5, borderColor=C_ACCENT,
    leftIndent=10, rightIndent=10, spaceBefore=6, spaceAfter=10
)

# Table cell styles
style_table_cell = ParagraphStyle(
    'TableCell', parent=style_body,
    fontName='Vazirmatn', fontSize=9.5, leading=14,
    alignment=TA_RIGHT, textColor=C_PRIMARY, spaceAfter=0
)
style_table_header = ParagraphStyle(
    'TableHeader', parent=style_body,
    fontName='Vazirmatn-Bold', fontSize=10, leading=14,
    alignment=TA_CENTER, textColor=colors.white, spaceAfter=0
)

# ============================================================
# Page Templates: Cover + Body with header/footer
# ============================================================
def draw_cover_bg(canvas, doc):
    """Cover page background - dark gradient effect."""
    canvas.saveState()
    # Dark background
    canvas.setFillColor(colors.HexColor('#0F172A'))
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Accent strip on top
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, PAGE_H - 1.5*cm, PAGE_W, 1.5*cm, fill=1, stroke=0)
    # Accent strip bottom
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, 0, PAGE_W, 0.6*cm, fill=1, stroke=0)
    # Decorative diagonal accent
    canvas.setFillColor(colors.HexColor('#1E293B'))
    canvas.rect(0, PAGE_H - 8*cm, PAGE_W, 6*cm, fill=1, stroke=0)
    canvas.restoreState()

def draw_body_header_footer(canvas, doc):
    """Header & footer for body pages."""
    canvas.saveState()
    # Header bar
    canvas.setFillColor(C_ACCENT)
    canvas.rect(MARGIN, PAGE_H - 1.2*cm, CONTENT_W, 0.05*cm, fill=1, stroke=0)
    # Header text - report title (right-aligned)
    canvas.setFont('Vazirmatn', 9)
    canvas.setFillColor(C_TEXT_MUTED)
    title_text = fa("سامانه مدیریت عملیات دفتر حسابداری - گزارش راهبردی")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 1.05*cm, title_text)
    # Footer
    canvas.setFillColor(C_BORDER)
    canvas.rect(MARGIN, 1.0*cm, CONTENT_W, 0.02*cm, fill=1, stroke=0)
    canvas.setFont('Vazirmatn', 9)
    canvas.setFillColor(C_TEXT_MUTED)
    page_num = canvas.getPageNumber()
    page_text = fa(f"صفحه {page_num - 1}")  # -1 to skip cover
    canvas.drawRightString(PAGE_W - MARGIN, 0.65*cm, page_text)
    canvas.drawString(MARGIN, 0.65*cm, fa("گزارش راهبردی - پاییز ۱۴۰۵"))
    canvas.restoreState()

# ============================================================
# Helpers for building content blocks
# ============================================================
def P(text, style=None):
    """Persian paragraph (auto-reshaped)."""
    if style is None:
        style = style_body
    return Paragraph(fa(text), style)

def Praw(html, style=None):
    """Raw paragraph (no reshaping) - for inline HTML like <b>."""
    if style is None:
        style = style_body
    # We still reshape the plain text parts. For simplicity, just reshape the whole string.
    # If the string has <b> tags, we need to be careful.
    return Paragraph(fa(html), style)

def bullet_list(items, style=None):
    """Build a list of bullet paragraphs with proper Persian bullet."""
    if style is None:
        style = style_bullet_rtl
    out = []
    for it in items:
        out.append(Paragraph(fa("• " + it), style))
    return out

def numbered_list(items, style=None):
    """Numbered list - Persian numerals."""
    if style is None:
        style = style_bullet_rtl
    out = []
    fa_nums = ['۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '۱۰', '۱۱', '۱۲', '۱۳', '۱۴', '۱۵']
    for i, it in enumerate(items):
        prefix = fa_nums[i] + ". " if i < len(fa_nums) else str(i+1) + ". "
        out.append(Paragraph(fa(prefix + it), style))
    return out

def make_table(data_raw, col_widths=None, header_bg=C_TABLE_HEADER, alt_rows=True):
    """Build a styled table. data_raw is list of lists; first row is header.
       Cells can be strings (auto-reshaped) or Paragraph objects.
    """
    # Convert strings to Paragraphs
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
    """Color callout box."""
    bg = {'info': C_BG_ACCENT, 'warn': colors.HexColor('#FEF3C7'),
          'success': colors.HexColor('#D1FAE5'), 'danger': colors.HexColor('#FEE2E2')}.get(kind, C_BG_ACCENT)
    border_c = {'info': C_ACCENT, 'warn': C_WARN, 'success': C_SUCCESS, 'danger': C_DANGER}.get(kind, C_ACCENT)
    style_callout_local = ParagraphStyle(
        'CalloutLocal', parent=style_body,
        fontName='Vazirmatn-Medium', fontSize=11, leading=19,
        alignment=TA_RIGHT, textColor=C_PRIMARY,
        backColor=bg, borderPadding=10,
        borderWidth=1, borderColor=border_c,
        leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=12
    )
    return Paragraph(fa(text), style_callout_local)

def hbar():
    """Horizontal accent bar."""
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
        title="سامانه مدیریت عملیات دفتر حسابداری - گزارش راهبردی",
        author="Z.ai",
        subject="Research report on accounting office management system",
        creator="Z.ai PDF Pipeline"
    )
    
    # Cover frame
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                       topPadding=0, bottomPadding=0, id='cover')
    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=draw_cover_bg)
    
    # Body frame
    body_frame = Frame(MARGIN, 1.5*cm, CONTENT_W, PAGE_H - 3.2*cm,
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='body')
    body_template = PageTemplate(id='body', frames=[body_frame], onPage=draw_body_header_footer)
    
    doc.addPageTemplates([cover_template, body_template])
    
    story = []
    
    # ============================ COVER PAGE ============================
    story.append(Spacer(1, 5*cm))
    # Title
    story.append(Paragraph(fa("سامانه مدیریت عملیات دفتر حسابداری"), style_cover_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph(fa("گزارش راهبردی و معماری سیستم اختصاصی"), style_cover_subtitle))
    story.append(Spacer(1, 0.3*cm))
    # Decorative line
    line_t = Table([['']], colWidths=[6*cm], rowHeights=[2])
    line_t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), C_ACCENT)]))
    story.append(line_t)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(fa("بررسی نرم‌افزارهای آماده، طراحی چارچوب ارزیابی پرسنل، معماری چندپایگاه‌داده و نقشه راه پیاده‌سازی"), style_cover_subtitle))
    story.append(Spacer(1, 5*cm))
    story.append(Paragraph(fa("دفتر حسابداری - ۵۰ شرکت - ۵ کارمند"), style_cover_meta))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(fa("پاییز ۱۴۰۵"), style_cover_meta))
    story.append(Paragraph(fa("نسخه ۱.۰ - محرمانه"), style_cover_meta))
    
    # Switch to body template
    story.append(PageBreak())
    from reportlab.platypus.doctemplate import NextPageTemplate
    # Insert NextPageTemplate BEFORE the PageBreak actually. But since we are switching, we'll add now.
    # Actually, the cleanest way: restructure. Let's use NextPageTemplate before PageBreak.
    
    # We need to rebuild - the above approach doesn't switch templates. Let me redo:
    pass

# Better approach: use NextPageTemplate properly
def build_pdf_v2(output_path):
    from reportlab.platypus.doctemplate import NextPageTemplate
    
    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.7*cm, bottomMargin=1.5*cm,
        title="سامانه مدیریت عملیات دفتر حسابداری - گزارش راهبردی",
        author="Z.ai",
        subject="Research report",
        creator="Z.ai PDF Pipeline"
    )
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                       topPadding=0, bottomPadding=0, id='cover')
    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=draw_cover_bg)
    body_frame = Frame(MARGIN, 1.5*cm, CONTENT_W, PAGE_H - 3.2*cm,
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='body')
    body_template = PageTemplate(id='body', frames=[body_frame], onPage=draw_body_header_footer)
    doc.addPageTemplates([cover_template, body_template])
    
    story = []
    
    # COVER PAGE
    story.append(Spacer(1, 5.5*cm))
    story.append(Paragraph(fa("سامانه مدیریت عملیات دفتر حسابداری"), style_cover_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph(fa("گزارش راهبردی و معماری سیستم اختصاصی"), style_cover_subtitle))
    story.append(Spacer(1, 0.3*cm))
    line_t = Table([['']], colWidths=[6*cm], rowHeights=[2])
    line_t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), C_ACCENT)]))
    story.append(line_t)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(fa("بررسی نرم‌افزارهای آماده، طراحی چارچوب ارزیابی پرسنل، معماری چندپایگاه‌داده و نقشه راه پیاده‌سازی"), style_cover_subtitle))
    story.append(Spacer(1, 5.5*cm))
    story.append(Paragraph(fa("دفتر حسابداری - ۵۰ شرکت - ۵ کارمند"), style_cover_meta))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(fa("پاییز ۱۴۰۵"), style_cover_meta))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(fa("نسخه ۱.۰ - سند راهبردی"), style_cover_meta))
    
    # Switch to body template
    story.append(NextPageTemplate('body'))
    story.append(PageBreak())
    
    # ============================ CHAPTER 1 ============================
    story.append(Paragraph(fa("فصل ۱: شناخت مسئله و نیازشناسی"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("وضعیت موجود دفتر حسابداری"), style_h2))
    story.append(P("شما یک دفتر حسابداری با حدود ۵۰ شرکت به‌عنوان مشتری و ۵ کارمند به‌عنوان نیروی اجرایی اداره می‌کنید. این ساختار در صنعت حسابداری ایران یک دفتر متوسط‌حساب تلقی می‌شود؛ نه آن‌قدر کوچک که با ابزارهای ساده مانند اکسل یا یک لیست پیامرسانی اداره شود، و نه آن‌قدر بزرگ که بتوان از نرم‌افزارهای گران‌قیمت سازمانی (مانند نسخه‌های سازمانی Karbon یا Canopy) با اطمینان از بازگشت سرمایه استفاده کرد. این نقطه میانی چالشی است که در آن باید هم کارایی عملیاتی روزانه حفظ شود و هم نظارت مدیریتی بر کیفیت کار پنج کارمند و پنجاه شرکت به‌صورت مستقل قابل اندازه‌گیری باشد."))
    
    story.append(P("تنوع نرم‌افزارهای حسابداری که شرکت‌های شما استفاده می‌کنند، مسئله را پیچیده‌تر می‌کند. در محیط واقعی شما، شرکت‌ها با نرم‌افزارهای گوناگونی مانند همکاران سیستم، سپیدار، هلو و احتمالاً نرم‌افزارهای اختصاصی کار می‌کنند. برخی از این نرم‌افزارها از SQL Server استفاده می‌کنند، برخی روی دیتابیس‌های محلی یا فایل‌های اکسل اجرا می‌شوند، و در مواردی اطلاعات فقط از طریق خروجی استاندارد نرم‌افزار قابل دسترسی است. این عدم یکنواختی فنی به معنی آن است که هیچ راهکار آماده‌ای در بازار وجود ندارد که بتواند به‌صورت بومی و بدون سفارشی‌سازی قابل توجه، با تمام این منابع داده ارتباط برقرار کند و گزارش کنترل یکپارچه تولید کند."))
    
    story.append(P("بزرگترین نقطه درد شما این است که در حال حاضر، کنترل کیفیت کار پرسنل به یک فرایند دستی، حافظه‌ای و متکی به اعتماد است. وقتی کارمند الف اعلام می‌کند که اسناد شرکت A را تا تاریخ ۱۴۰۵/۰۷/۲۰ در سیستم ثبت کرده، شما راه مستقیمی برای راستی‌آزمایی این ادعا ندارید مگر اینکه خودتان به دیتابیس حسابداری آن شرکت متصل شوید، ریز اسناد را استخراج کنید، با فایل اکسل پیوست کارمند مقایسه کنید و تطبیق بازه‌های تاریخی، شمارش ردیف‌ها و کنترل تکراری‌ها را به‌صورت دستی انجام دهید. این کار برای یک شرکت زمان‌بر است و برای پنجاه شرکت غیرممکن. در نتیجه، شما به‌جای مدیریت استراتژیک دفتر، در تله کنترل جزئی گرفتار می‌شوید."))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("اهداف فنی و مدیریتی"), style_h2))
    story.append(P("بر اساس تحلیل نیازهای شما، اهداف سامانه پیشنهادی را می‌توان در سه لایه دسته‌بندی کرد. لایه اول اهداف عملیاتی شامل تخصیص تسک، پیگیری پیشرفت، ثبت گزارش کار با قالب استاندارد و پیوست فایل اکسل است. این لایه با ابزارهای آماده مانند Karbon یا TaxDome قابل پوشش است. لایه دوم اهداف کنترلی شامل راستی‌آزمایی هوشمند فایل اکسل در برابر داده‌های واقعی، تشخیص تکراری، تطبیق بازه‌های تاریخی، و گزارش مغایرت برای مدیر است. این لایه با هیچ ابزار آماده‌ای به‌صورت کامل پوشش داده نمی‌شود و باید به‌صورت اختصاصی ساخته شود. لایه سوم اهداف مدیریتی شامل ارزیابی عملکرد پرسنل بر اساس شاخص‌های کلیدی، داشبورد روزانه، ثبت مرخصی و حضور و غیاب، و لاگ غیرقابل ویرایش فعالیت‌هاست که ترکیبی از قابلیت‌های آماده و توسعه اختصاصی را می‌طلبد."))
    
    story.append(callout("نکته کلیدی: مسئله اصلی شما «مدیریت تسک» نیست، بلکه «اثبات قابل اندازه‌گیری انجام شدن کار حسابداری» است. این تفاوت ذهنی، انتخاب ابزار و معماری سامانه را به‌طور بنیادی تعیین می‌کند.", 'info'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 2 ============================
    story.append(Paragraph(fa("فصل ۲: بررسی نرم‌افزارهای آماده موجود"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این فصل، نرم‌افزارهای تخصصی مدیریت دفاتر حسابداری، نرم‌افزارهای عمومی مدیریت پروژه، و راهکارهای ایرانی برای حضور و غیاب بررسی می‌شوند. هدف، تعیین این است که آیا یک نرم‌افزار آماده وجود دارد که نیازهای شما را به‌طور کامل پوشش دهد، یا اینکه نیاز به ساخت سامانه اختصاصی یا ترکیبی است."))
    
    story.append(Paragraph(fa("۲.۱ نرم‌افزارهای تخصصی مدیریت دفاتر حسابداری"), style_h2))
    story.append(P("این نرم‌افزارها به‌طور خاص برای دفاتر حسابداری، مالیاتی و حسابرسی طراحی شده‌اند. مزیت اصلی آن‌ها درک بومی از گردش کار حسابداری، امکانات تخصیص مشتری، و قالب‌های آماده برای کارهای تکرارشونده ماهانه است. با این حال، اکثر آن‌ها برای بازارهای غربی (به‌ویژه ایالات متحده و بریتانیا) طراحی شده‌اند و از قواعد مالیاتی و حسابداری ایران پشتیبانی نمی‌کنند. این موضوع به‌تنهایی باعث می‌شود استفاده از آن‌ها به‌عنوان هسته اصلی سامانه شما با چالش جدی روبه‌رو شود، اما می‌توانند به‌عنوان منبع الهام برای طراحی گردش کار و به‌عنوان لایه مدیریت تسک در معماری ترکیبی مورد استفاده قرار گیرند."))
    
    story.append(Paragraph(fa("Karbon"), style_h3))
    story.append(P("Karbon یکی از شناخته‌شده‌ترین نرم‌افزارهای مدیریت دفاتر حسابداری است که بر گردش کار Kanban، یکپارچگی ایمیل، و قالب‌های آماده برای فرایندهای تکراری حسابداری تمرکز دارد. این نرم‌افزار برای دفاتر با ۵ تا ۳۰ نفر ایده‌آل است و دید مدیریتی خوبی از وضعیت کارهای هر کارمند و هر مشتری فراهم می‌کند. نقطه قوت اصلی Karbon این است که ایمیل‌های مرتبط با هر مشتری به‌طور خودکار به کارهای آن مشتری متصل می‌شوند، که برای ارتباطات دفتر با ۵۰ شرکت بسیار کاربردی است. با این حال، Karbon قابلیت آپلود فایل اکسل با اعتبارسنجی هوشمند، کنترل تکراری شماره سند، و تطبیق بازه تاریخی با دیتابیس حسابداری را به‌صورت آماده ندارد. این نرم‌افزار برای مدیریت تسک ایده‌آل است اما برای کنترل کیفیت اسناد حسابداری باید با ماژول اختصاصی تکمیل شود. قیمت Karbon بر اساس کاربر محاسبه می‌شود و برای تیم ۵ نفره حدود ۵۹ تا ۸۹ دلار به ازای هر کاربر در ماه است که برای دفتر شما قابل تحمل است، اما چالش پشتیبانی فارسی و عدم اتصال به نرم‌افزارهای ایرانی پاشنه آشیل آن محسوب می‌شود."))
    
    story.append(Paragraph(fa("Canopy"), style_h3))
    story.append(P("Canopy در رتبه‌بندی G2 در سال ۲۰۲۶ به‌عنوان بهترین نرم‌افزار مدیریت دفاتر مالیاتی و حسابداری شناخته شده است. این نرم‌افزار با قابلیت‌های هوش مصنوعی مانند Smart Intake، Smart Prep و Smart Tax Delivery، یکپارچگی عمیق با IRS (سازمان مالیاتی آمریکا)، و پورتال مشتری با اپلیکیشن موبایل، یک سامانه همه‌جانبه است. Canopy برای دفاتر چندخدماتی که می‌خواهند از مهاجرت بین ابزارهای مختلف دوری کنند، ایده‌آل است. اما برای دفتر شما در ایران، Canopy عملاً قابل استفاده نیست، زیرا تمام قابلیت‌های هوش مصنوعی آن بر اساس قواعد مالیاتی آمریکا طراحی شده و یکپارچگی با نرم‌افزارهای حسابداری ایرانی را پشتیبانی نمی‌کند. با این حال، مطالعه معماری و گردش کار Canopy می‌تواند به‌عنوان منبع الهام برای طراحی سامانه اختصاصی شما مفید باشد."))
    
    story.append(Paragraph(fa("TaxDome"), style_h3))
    story.append(P("TaxDome با بیش از ۱۵٬۰۰۰ دفتر کاربر و ۳ میلیون مشتری، یکی از بزرگترین پلتفرم‌های مدیریت دفاتر حسابداری است. این نرم‌افزار شامل خط لوله گردش کار، CRM، پورتال مشتری، مدیریت اسناد، و صورت‌حساب است. سه پلن اصلی آن با قیمت ۵۸، ۷۵ و ۹۲ دلار به ازای هر کاربر در ماه ارائه می‌شود. TaxDome برای دفاتر کوچک و متوسط که می‌خواهند به‌سرعت راه‌اندازی شوند، گزینه مناسبی است. مزیت آن نسبت به Karbon، قیمت پایین‌تر و داشتن پورتال مشتری است. اما مانند Canopy، برای ایران مناسب نیست، زیرا یکپارچگی‌های آن با QuickBooks Online و IRS است و هیچ رابط برنامه‌نویسی برای نرم‌افزارهای ایرانی ارائه نمی‌دهد. "))
    
    story.append(Paragraph(fa("Financial Cents، Pixie و Jetpack Workflow"), style_h3))
    story.append(P("این سه نرم‌افزار برای دفاتر کوچک‌تر (۱ تا ۵ نفر) طراحی شده‌اند و قیمت پایین‌تری دارند. Financial Cents با تمرکز بر کارهای تکرارشونده حسابداری، تعیین مسئول و مهلت، و گزارش وضعیت، یک نقطه شروع ساده و شهودی است. Pixie برای دفاتر کوچک و متوسط با تمرکز بر گردش کار، وظایف تکرارشونده، مدیریت مشتری و یادآوری‌ها کار می‌کند. Jetpack Workflow بر وظایف زمان‌بندی‌شده و کارهای تکرارشونده حسابداری تمرکز دارد. هر سه نرم‌افزار قابلیت‌های پایه‌ای مدیریت تسک را دارند اما هیچ‌کدام موتور کنترل هوشمند فایل اکسل و اتصال به چند دیتابیس را پشتیبانی نمی‌کنند. برای دفتر شما، این نرم‌افزارها به‌تنهایی پاسخ‌گو نیستند اما اگر بخواهید از یک ابزار آماده به‌عنوان لایه مدیریت تسک استفاده کنید، Financial Cents یا Pixie گزینه‌های منطقی‌تری هستند زیرا ساده‌تر و ارزان‌تر از Karbon هستند."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۲.۲ نرم‌افزارهای عمومی مدیریت پروژه"), style_h2))
    story.append(P("نرم‌افزارهای عمومی مانند Trello، Asana، Monday.com، ClickUp و Smartsheet نیز برای مدیریت تسک‌های دفتر حسابداری قابل استفاده هستند. این ابزارها انعطاف‌پذیر، ارزان و دارای رابط کاربری قوی هستند. اما همه آن‌ها یک ضعف اساسی دارند: هیچ درک بومی از گردش کار حسابداری ندارند. یعنی شما باید قالب‌ها، وضعیت‌ها و گردش کار را از صفر بسازید. این کار برای دفتر شما زمان‌بر است و نیاز به تخصص پیکربندی دارد. همچنین این ابزارها هیچ پورتال مشتری، مدیریت اسناد حسابداری یا قواعد مالیاتی ندارند. در نهایت، هیچ‌کدام اتصال به دیتابیس نرم‌افزارهای حسابداری ایرانی را پشتیبانی نمی‌کنند."))
    
    story.append(Paragraph(fa("۲.۳ نرم‌افزارهای ایرانی برای حضور و غیاب"), style_h2))
    story.append(P("در حوزه منابع انسانی، نرم‌افزارهای ایرانی مانند رادیکال (محصول فراویژن) و مگاپرداز برای مدیریت پرسنلی، مرخصی، حضور و غیاب، و کارتابل درخواست‌های پرسنلی قابل بررسی هستند. رادیکال با داشبورد مدیریتی و گزارش‌گیری از پرسنل، یک گزینه بالغ برای بخش HR سامانه شماست. مگاپرداز نیز کارتابل تأیید درخواست‌های پرسنلی و داشبوردهای منابع انسانی را پشتیبانی می‌کند. اگر ابزار مدیریت تسک انتخابی شما قابلیت‌های حضور و غیاب کافی نداشته باشد، می‌توانید یکی از این نرم‌افزارها را به‌عنوان مکمل به کار بگیرید. اما توجه داشته باشید که این نرم‌افزارها نیز موتور کنترل اسناد حسابداری ندارند و باید با ماژول اختصاصی شما یکپارچه شوند."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۲.۴ ماتریس مقایسه نهایی"), style_h2))
    story.append(P("جدول زیر تمام ابزارهای بررسی‌شده را بر اساس معیارهای کلیدی شما مقایسه می‌کند. علامت ✓ نشان‌دهنده پشتیبانی کامل، علامت ◐ نشان‌دهنده پشتیبانی جزئی یا نیاز به سفارشی‌سازی، و علامت ✗ نشان‌دهنده عدم پشتیبانی است. ستون «سامانه پیشنهادی» معماری ترکیبی پیشنهادی ما را نشان می‌دهد که در فصل‌های بعدی به‌طور کامل تشریح می‌شود."))
    
    # Build comparison matrix
    matrix_data = [
        ["قابلیت", "Karbon", "Canopy", "TaxDome", "Fin.Cents", "Pixie", "راهکار ایرانی HR", "سامانه ترکیبی پیشنهادی"],
        ["تخصیص تسک و مهلت", "✓", "✓", "✓", "✓", "✓", "✗", "✓"],
        ["وظایف تکرارشونده برای هر شرکت", "✓", "✓", "✓", "✓", "✓", "✗", "✓"],
        ["ثبت گزارش کار و پیوست فایل", "✓", "✓", "✓", "✓", "✓", "✗", "✓"],
        ["کنترل تکراری شماره سند", "✗", "✗", "✗", "✗", "✗", "✗", "✓"],
        ["تطبیق بازه تاریخی ادعا با فایل", "✗", "✗", "✗", "✗", "✗", "✗", "✓"],
        ["اتصال به دیتابیس متفاوت (SQL/Excel)", "✗", "✗", "✗", "✗", "✗", "◐", "✓"],
        ["حضور و غیاب و مرخصی", "✗", "✗", "✗", "✗", "✗", "✓", "✓"],
        ["ارجاع بخشی از تسک به همکار", "✓", "✓", "◐", "✓", "✓", "✗", "✓"],
        ["لاگ فعالیت غیرقابل ویرایش", "◐", "◐", "◐", "✗", "✗", "✗", "✓"],
        ["گزارش مدیریتی سفارشی", "◐", "✓", "✗", "✗", "✗", "✓", "✓"],
        ["پشتیبانی فارسی و قواعد ایران", "✗", "✗", "✗", "✗", "✗", "✓", "✓"],
        ["قیمت ماهانه برای ۵ کاربر (دلار)", "۳۰۰-۴۵۰", "تماس", "۳۰۰-۴۶۰", "۲۰۰", "۱۰۰", "۵۰-۲۰۰", "هزینه توسعه + ۵۰/ماه"],
        ["مناسب برای دفتر شما (۱۰امتیاز)", "۶", "۳", "۵", "۶", "۶", "۴", "۹"],
    ]
    col_w = [4.5*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.7*cm, 2.0*cm]
    # Reduce slightly to fit A4
    total = sum(col_w)
    factor = CONTENT_W / total
    col_w = [w * factor for w in col_w]
    story.append(make_table(matrix_data, col_widths=col_w))
    story.append(Spacer(1, 10))
    
    story.append(callout("نتیجه: هیچ نرم‌افزار آماده‌ای در بازار جهانی یا ایرانی، تمام نیازهای شما را به‌صورت یکپارچه پوشش نمی‌دهد. دو قابلیت بحرانی شما - موتور کنترل هوشمند اسناد اکسل و اتصال به دیتابیس‌های متنوع نرم‌افزارهای ایرانی - در هیچ محصول آماده‌ای وجود ندارد. این نتیجه به‌طور طبیعی به سمت یک راهکار ترکیبی (هیبرید) می‌رود.", 'warn'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 3 ============================
    story.append(Paragraph(fa("فصل ۳: تحلیل خرید یا ساخت (Build vs Buy)"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("تصمیم خرید یا ساخت یکی از مهم‌ترین انتخاب‌های راهبردی در این پروژه است. این تصمیم نباید صرفاً بر اساس هزینه اولیه گرفته شود، بلکه باید کل هزینه مالکیت (TCO) در یک دوره سه‌ساله، انعطاف‌پذیری، کنترل داده، و تطابق با نیازهای خاص شما را در نظر بگیرد. در این فصل، سه گزینه اصلی بررسی می‌شود: خرید کامل، ساخت کامل، و راهکار ترکیبی (هیبرید)."))
    
    story.append(Paragraph(fa("۳.۱ گزینه اول: خرید کامل (Buy)"), style_h2))
    story.append(P("این گزینه به معنی خرید یک نرم‌افزار آماده مانند Karbon یا TaxDome به‌عنوان هسته اصلی سامانه است. مزیت اصلی این مسیر، سرعت راه‌اندازی (۲ تا ۴ هفته)، رابط کاربری بالغ، و عدم نیاز به تیم توسعه داخلی است. شما فقط کاربران را تعریف می‌کنید، شرکت‌ها را وارد می‌کنید، و قالب‌های تسک تکرارشونده را پیکربندی می‌کنید. اما این مسیر چند نقطه ضعف اساسی دارد. اول، هزینه ماهانه برای ۵ کاربر بین ۳۰۰ تا ۴۵۰ دلار است که در یک دوره سه‌ساله به ۱۰٬۸۰۰ تا ۱۶٬۲۰۰ دلار می‌رسد. دوم، هیچ‌کدام از این نرم‌افزارها قواعد فارسی، تقویم شمسی، یا یکپارچگی با نرم‌افزارهای حسابداری ایرانی را پشتیبانی نمی‌کنند. سوم، و مهم‌تر از همه، موتور کنترل هوشمند اسناد اکسل و تطبیق با دیتابیس‌های متفاوت را ندارند. در نتیجه، شما باید برای راستی‌آزمایی کار هر کارمند همچنان به روش‌های دستی متوسل شوید که عملاً هدف اصلی پروژه را بی‌اثر می‌کند."))
    
    story.append(Paragraph(fa("۳.۲ گزینه دوم: ساخت کامل (Build)"), style_h2))
    story.append(P("این گزینه به معنی ساخت یک سامانه اختصاصی از صفر با پشته فنی انتخابی (مثلاً Next.js + Python + PostgreSQL) است. مزیت اصلی، کنترل کامل بر هر جزء سامانه، انعطاف‌پذیری بالا، عدم پرداخت هزینه ماهانه ابزار، و تطابق کامل با نیازهای خاص شما است. اما ریسک‌های جدی نیز دارد. اول، زمان توسعه اولیه حداقل ۳ تا ۶ ماه است که در این مدت دفتر شما همچنان با روش‌های فعلی کار می‌کند. دوم، هزینه توسعه در صورت برون‌سپاری به یک تیم ایرانی بین ۱۵۰ تا ۳۰۰ میلیون تومان برای نسخه اولیه (MVP) است. سوم، نگهداری و توسعه مستمر سامانه نیاز به تیم فنی داخلی یا قرارداد پشتیبانی دارد. چهارم، تکرار چرخ‌های قبلی صنعت - شما قابلیت‌هایی را از صفر می‌سازید که در Karbon یا TaxDome قبلاً توسعه داده شده‌اند. این تکرار، انرژی و زمانی را که باید صرف قابلیت‌های متمایزکننده شما (موتور کنترل اسناد) شود، صرف کارهای تکراری می‌کند."))
    
    story.append(Paragraph(fa("۳.۳ گزینه سوم: راهکار ترکیبی (Hybrid) - توصیه شده"), style_h2))
    story.append(P("راهکار ترکیبی، ترکیب بهترین ویژگی‌های دو مسیر قبلی است. در این مدل، شما از یک نرم‌افزار آماده (یا نسخه سبک توسعه‌داده‌شده) به‌عنوان لایه مدیریت تسک و کارتابل استفاده می‌کنید، و یک ماژول اختصاصی به‌عنوان «موتور کنترل اسناد حسابداری» می‌سازید که فایل‌های اکسل کارمندان را دریافت، اعتبارسنجی، و با دیتابیس‌های متنوع شرکت‌ها راستی‌آزمایی می‌کند. این دو ماژول از طریق API با هم یکپارچه می‌شوند. به این ترتیب، شما از قابلیت‌های بالغ مدیریت تسک ابزار آماده بهره می‌برید و در عین حال قابلیت‌های متمایزکننده شما (کنترل هوشمند اسناد) به‌صورت اختصاصی ساخته می‌شوند. این مسیر بهترین تعادل بین زمان، هزینه و قابلیت را ارائه می‌دهد."))
    
    story.append(P("در عمل، در معماری پیشنهادی ما حتی از یک ابزار آماده خارجی هم صرف‌نظر می‌شود و لایه مدیریت تسک نیز به‌صورت سبک و اختصاصی با Next.js ساخته می‌شود. دلیل این انتخاب این است که ابزارهای آماده خارجی با چالش پشتیبانی فارسی، تقویم شمسی، و یکپارچگی با موتور کنترل اسناد روبه‌رو هستند. ساخت یک پنل سبک اختصاصی با Next.js تنها ۳ تا ۴ هفته زمان می‌برد و کنترل کامل بر تجربه کاربری، یکپارچگی، و توسعه آینده را فراهم می‌کند."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۳.۴ ماتریس مقایسه‌ای سه گزینه"), style_h2))
    story.append(P("جدول زیر سه گزینه را بر اساس هفت معیار کلیدی مقایسه می‌کند. اعداد برآوردی و بر اساس شرایط دفتر ۵۰ شرکت/۵ کارمند و بازار ایران است."))
    
    build_vs_buy_data = [
        ["معیار", "خرید کامل", "ساخت کامل", "راهکار ترکیبی"],
        ["هزینه اولیه (تومان)", "نزدیک صفر", "۱۵۰-۳۰۰ میلیون", "۸۰-۱۵۰ میلیون"],
        ["هزینه ماهانه (۳ سال)", "۱۰٬۸۰۰-۱۶٬۲۰۰$", "۵۰$/ماه سرور", "۵۰$/ماه سرور + پشتیبانی"],
        ["زمان راه‌اندازی MVP", "۲-۴ هفته", "۳-۶ ماه", "۸-۱۲ هفته"],
        ["پشتیبانی فارسی و شمسی", "✗", "✓", "✓"],
        ["کنترل هوشمند اسناد", "✗", "✓", "✓"],
        ["اتصال به دیتابیس ایرانی", "✗", "✓", "✓"],
        ["انعطاف‌پذیری توسعه", "محدود به API", "کامل", "کامل"],
        ["ریسک پروژه", "پایین (اما کارکرد ناقص)", "بالا", "متوسط"],
        ["بازگشت سرمایه ۳ ساله", "منفی (کارکرد ناقص)", "مثبت", "مثبت قوی"],
    ]
    col_w_bvb = [5*cm, 3.2*cm, 3.2*cm, 4.3*cm]
    factor = CONTENT_W / sum(col_w_bvb)
    col_w_bvb = [w * factor for w in col_w_bvb]
    story.append(make_table(build_vs_buy_data, col_widths=col_w_bvb))
    story.append(Spacer(1, 10))
    
    story.append(callout("توصیه نهایی: راهکار ترکیبی با ساخت لایه مدیریت تسک اختصاصی به‌صورت سبک و موتور کنترل اسناد اختصاصی به‌صورت کامل، بهترین تعادل بین زمان، هزینه و کارکرد را ارائه می‌دهد. کل هزینه توسعه MVP حدود ۸۰ تا ۱۵۰ میلیون تومان و زمان ۸ تا ۱۲ هفته است.", 'success'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 4 ============================
    story.append(Paragraph(fa("فصل ۴: معماری کلی سامانه پیشنهادی"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("معماری پیشنهادی سامانه بر اساس اصل جداسازی مسئولیت‌ها (Separation of Concerns) و الگوی Adapter طراحی شده است. هدف این است که هر لایه مسئولیت مشخصی داشته باشد، بدون دانش از جزئیات لایه‌های دیگر کار کند، و بتواند به‌صورت مستقل توسعه و تست شود. این معماری در طول زمان به شما اجازه می‌دهد شرکت‌های جدید و نرم‌افزارهای حسابداری جدید را بدون تغییر در هسته سامانه اضافه کنید."))
    
    story.append(Paragraph(fa("۴.۱ لایه‌های معماری"), style_h2))
    story.append(P("سامانه از پنج لایه منطقی تشکیل شده است. هر لایه یک قرارداد (Contract) مشخص با لایه‌های مجاور دارد. این قراردادها به‌صورت رابط‌های برنامه‌نویسی (API) و مدل داده استاندارد پیاده‌سازی می‌شوند. در ادامه هر لایه به‌طور کامل توضیح داده می‌شود."))
    
    story.append(Paragraph(fa("لایه ۱: پنل وب و مدیریت کاربران"), style_h3))
    story.append(P("این لایه رابط کاربری سامانه است که توسط مدیر، مدیرعامل، کارکنان و مسئول کنترل استفاده می‌شود. این پنل با Next.js و React ساخته می‌شود و شامل صفحه‌های داشبورد، مدیریت تسک، گزارش کار، آپلود فایل، درخواست مرخصی، و گزارش‌های مدیریتی است. پشتیبانی از زبان فارسی، راست‌چین (RTL)، تقویم شمسی، و تم تاریک/روشن از ویژگی‌های این لایه است. احراز هویت با JWT یا Session و کنترل دسترسی مبتنی بر نقش (RBAC) پیاده‌سازی می‌شود."))
    
    story.append(Paragraph(fa("لایه ۲: موتور گردش کار و مدیریت تسک"), style_h3))
    story.append(P("این لایه مسئولیت مدیریت چرخه حیات تسک‌ها را بر عهده دارد. هر تسک شامل شرکت، نوع فعالیت، مسئول اصلی، همکاران، تاریخ شروع، مهلت، چک‌لیست مراحل، پیشرفت، فایل‌های پیوست و وضعیت است. وضعیت تسک می‌تواند یکی از مقادیر «تازه، در حال انجام، ارجاع‌شده به همکار، در انتظار کنترل، نیازمند اصلاح، تأیید شده، رد شده» باشد. این لایه همچنین مسئولیت ثبت گزارش کار کارمند، ارجاع بخشی از تسک به همکار، و ارسال اعلان‌ها است."))
    
    story.append(Paragraph(fa("لایه ۳: موتور کنترل هوشمند فایل اکسل"), style_h3))
    story.append(P("این لایه قلب متمایزکننده سامانه شماست. هر زمان که کارمندی فایل اکسل اسناد را بارگذاری می‌کند، این لایه فعال می‌شود. ابتدا فایل را از نظر قالب و ساختار ستون‌ها اعتبارسنجی می‌کند، سپس ردیف‌های تکراری را در فایل و میان گزارش‌های قبلی شناسایی می‌کند، شماره اسناد را کنترل می‌کند، بازه‌های تاریخی را محاسبه و با ادعای کارمند مقایسه می‌کند، و در نهایت اسناد فایل را با اسناد واقعی دیتابیس شرکت راستی‌آزمایی می‌کند. خروجی این لایه یک گزارش کنترل ساختاریافته است که به مدیر نمایش داده می‌شود."))
    
    story.append(Paragraph(fa("لایه ۴: لایه استانداردسازی داده حسابداری"), style_h3))
    story.append(P("این لایه یک قرارداد داده مشترک برای تمام نرم‌افزارهای حسابداری است. صرف‌نظر از اینکه اسناد از SQL Server، Excel یا API خوانده می‌شوند، خروجی همیشه در قالب مدل داده استاندارد واحد است. این قرارداد شامل فیلدهای شناسه شرکت، شناسه دیتابیس مبدأ، شناسه یکتای سند، شماره سند، تاریخ سند، ردیف سند، کد حساب (کل/معین/تفصیل)، شرح، بدهکار و بستانکار است. به این ترتیب، منطق کنترل اسناد فقط یک بار نوشته می‌شود و با تمام نرم‌افزارهای حسابداری کار می‌کند."))
    
    story.append(Paragraph(fa("لایه ۵: لایه اتصال به دیتابیس‌ها (Adapter Layer)"), style_h3))
    story.append(P("این لایه شامل مجموعه‌ای از Adapter‌ها است که هر کدام برای یک نوع دیتابیس یا نرم‌افزار حسابداری طراحی شده‌اند. به عنوان مثال، یک Adapter برای SQL Server نرم‌افزار همکاران، یک Adapter برای SQL Server سپیدار، یک Adapter برای فایل‌های Excel، و یک Adapter برای API یک نرم‌افزار اختصاصی. هر Adapter اطلاعات خام را از منبع می‌خواند و آن را به مدل داده استاندارد تبدیل می‌کند. تمام Adapter‌ها یک رابط واحد (interface) را پیاده‌سازی می‌کنند، به این ترتیب لایه بالاتر (کنترل اسناد) نیازی به دانستن جزئیات هر نرم‌افزار ندارد."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۴.۲ نمودار معماری"), style_h2))
    story.append(P("نمودار زیر معماری لایه‌ای سامانه و جریان داده بین لایه‌ها را نشان می‌دهد. هر بلوک یک لایه منطقی است و پیکان‌ها نشان‌دهنده جهت جریان داده و کنترل است."))
    
    # Architecture diagram as a table-based visualization
    arch_data = [
        [Paragraph(fa("پنل وب (مدیر، مدیرعامل، کارکنان)"), style_table_header)],
        [Paragraph(fa("لایه ۲: موتور گردش کار و مدیریت تسک"), style_table_cell)],
        [Paragraph(fa("لایه ۳: موتور کنترل هوشمند فایل اکسل"), style_table_cell)],
        [Paragraph(fa("لایه ۴: استانداردسازی داده حسابداری (مدل داده موحد)"), style_table_cell)],
        [Paragraph(fa("لایه ۵: Adapter SQL Server | Adapter Excel | Adapter API | ..."), style_table_cell)],
        [Paragraph(fa("دیتابیس شرکت A | دیتابیس شرکت B | فایل Excel شرکت C | ..."), style_table_cell)],
    ]
    arch_table = Table(arch_data, colWidths=[CONTENT_W])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#DBEAFE')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#FED7AA')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FEF3C7')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#D1FAE5')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#E0E7FF')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, C_BORDER),
        ('BOX', (0, 0), (-1, -1), 1.5, C_PRIMARY),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(fa("۴.۳ مدل داده استاندارد"), style_h2))
    story.append(P("مدل داده استاندارد، قلب لایه ۴ است. تمام Adapter‌ها باید اطلاعات خام خود را به این مدل تبدیل کنند. جدول زیر فیلدهای این مدل را توضیح می‌دهد."))
    
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
        ["last_modified_at", "Timestamp", "خیر", "زمان آخرین تغییر در مبدأ (در صورت پشتیبانی)"],
        ["source_metadata", "JSON", "خیر", "متادیتای اختصاصی نرم‌افزار مبدأ"],
    ]
    col_w_model = [4.5*cm, 2.8*cm, 2.0*cm, 7.5*cm]
    factor = CONTENT_W / sum(col_w_model)
    col_w_model = [w * factor for w in col_w_model]
    story.append(make_table(model_data, col_widths=col_w_model))
    story.append(Spacer(1, 8))
    
    story.append(callout("اصل کلیدی: منطق کنترل اسناد (لایه ۳) فقط با مدل داده استاندارد کار می‌کند. این یعنی اگر فردا نرم‌افزار حسابداری جدیدی اضافه شود، فقط باید یک Adapter جدید برای لایه ۵ بنویسید، بدون آنکه هیچ تغییری در لایه‌های ۲، ۳ و ۴ لازم باشد.", 'info'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 5 ============================
    story.append(Paragraph(fa("فصل ۵: معماری چندپایگاه‌داده با Adapter Pattern"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در دفتر شما، شرکت‌ها از نرم‌افزارهای متنوعی استفاده می‌کنند و دیتابیس‌های آن‌ها از انواع مختلفی (SQL Server، Excel، فایل‌های محلی، API) تشکیل شده است. این تنوع اگر به‌درستی مدیریت نشود، باعث پیچیدگی شدید در سامانه می‌شود. راهکار ما الگوی Adapter است: یک رابط واحد برای تمام منابع داده، و پیاده‌سازی‌های جداگانه برای هر نوع منبع. در این فصل، نحوه طراحی و پیاده‌سازی این الگو به‌طور کامل تشریح می‌شود."))
    
    story.append(Paragraph(fa("۵.۱ رابط مشترک Adapter"), style_h2))
    story.append(P("هر Adapter باید یک رابط (interface) واحد را پیاده‌سازی کند. این رابط چهار عملیات اصلی را تعریف می‌کند: اتصال، خواندن اسناد در یک بازه زمانی، خواندن یک سند با شناسه، و تست اتصال. به این ترتیب لایه کنترل اسناد با تمام Adapter‌ها به یک شکل کار می‌کند. در زبان Python، این رابط با استفاده از کتابخانه abc (Abstract Base Class) تعریف می‌شود."))
    
    # Code block
    code_style = ParagraphStyle(
        'Code', parent=style_body,
        fontName='Vazirmatn', fontSize=9, leading=13,
        alignment=TA_LEFT, textColor=C_PRIMARY,
        backColor=colors.HexColor('#1E293B'), borderPadding=8,
        leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=10,
    )
    # Use a custom approach: code is on a dark background
    code_text = """
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

class AccountingAdapter(ABC):
    @abstractmethod
    def test_connection(self) -> bool: ...
    
    @abstractmethod
    def fetch_documents(
        self, date_from: date, date_to: date
    ) -> List[StandardDocument]: ...
    
    @abstractmethod
    def fetch_document_by_id(
        self, document_id: str
    ) -> Optional[StandardDocument]: ...
    
    @abstractmethod
    def get_supported_features(self) -> dict: ...
"""
    # For code, we don't reshape (it's English/literal)
    code_table = Table([[Paragraph(code_text.replace('\n', '<br/>'), ParagraphStyle(
        'CodeInner', parent=style_body,
        fontName='Courier', fontSize=8.5, leading=12,
        alignment=TA_LEFT, textColor=colors.HexColor('#E2E8F0'),
        backColor=colors.HexColor('#1E293B'),
    ))]], colWidths=[CONTENT_W])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1E293B')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#475569')),
    ]))
    story.append(code_table)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(fa("۵.۲ انواع Adapter مورد نیاز"), style_h2))
    story.append(P("بر اساس تنوع دیتابیس‌های شما، حداقل چهار نوع Adapter نیاز دارید. در ادامه هر یک به‌طور خلاصه توضیح داده می‌شود."))
    
    story.append(Paragraph(fa("Adapter ۱: SQL Server (همکاران سیستم)"), style_h3))
    story.append(P("نرم‌افزار همکاران سیستم از SQL Server استفاده می‌کند و دیتابیس آن ساختار شناخته‌شده‌ای دارد. این Adapter با استفاده از کتابخانه pyodbc یا SQLAlchemy به دیتابیس متصل می‌شود، جدول‌های اسناد (معمولاً با نام‌هایی مانند DocHeader و DocDetail) را کوئری می‌کند، و خروجی را به مدل استاندارد تبدیل می‌کند. یک چالش مهم این است که ساختار دقیق دیتابیس همکاران در نسخه‌های مختلف متفاوت است؛ بنابراین Adapter باید نسخه نرم‌افزار را تشخیص دهد و کوئری مناسب را اجرا کند. نکته امنیتی: اتصال باید فقط خواندنی (Read-Only) باشد. کاربر SQL که به Adapter داده می‌شود باید فقط دسترسی SELECT داشته باشد و دسترسی INSERT، UPDATE یا DELETE نداشته باشد."))
    
    story.append(Paragraph(fa("Adapter ۲: SQL Server (سپیدار)"), style_h3))
    story.append(P("نرم‌افزار سپیدار نیز از SQL Server استفاده می‌کند اما ساختار دیتابیس آن با همکاران متفاوت است. این Adapter مشابه Adapter همکاران پیاده‌سازی می‌شود، اما کوئری‌ها و نگاشت فیلدها متفاوت است. در عمل، کلاس پایه یکسانی دارند اما کوئری‌های SQL متفاوت اجرا می‌کنند. مهم: سپیدار در نسخه‌های اخیر از یک دیتابیس مرکزی برای چند شرکت استفاده می‌کند و شناسایی شرکت داخل کوئری باید با فیلتر روی فیلد CompanyID انجام شود."))
    
    story.append(Paragraph(fa("Adapter ۳: Excel/CSV Files"), style_h3))
    story.append(P("برای شرکت‌هایی که از نرم‌افزار حسابداری با خروجی Excel یا CSV استفاده می‌کنند، این Adapter فایل‌ها را از مسین تعیین‌شده (یا از طریق آپلود خودکار) می‌خواند. این Adapter با کتابخانه pandas یا openpyxl کار می‌کند و باید با چالش‌های فرمت تاریخ شمسی در اکسل، تنوع کدگذاری (UTF-8، Windows-1256)، و وجود ستون‌های اضافی کنار بیاید. مزیت این Adapter این است که فایل‌های اکسل اغلب در مسیرهای شبکه‌ای ذخیره می‌شوند و می‌توان با یک سرویس زمان‌بندی‌شده آن‌ها را به‌صورت خودکار خواند."))
    
    story.append(Paragraph(fa("Adapter ۴: REST API"), style_h3))
    story.append(P("برای نرم‌افزارهای حسابداری که API ارائه می‌دهند (مانند برخی نرم‌افزارهای ابری ایرانی)، این Adapter با درخواست‌های HTTP به API متصل می‌شود. این Adapter معمولاً احراز هویت با توکن (Bearer Token یا API Key) نیاز دارد. مزیت این روش این است که از تغییرات ساختار دیتابیس داخلی نرم‌افزار مستقل است؛ تا زمانی که API پایدار بماند، Adapter بدون تغییر کار می‌کند."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۵.۳ مدیریت تنظیمات اتصال"), style_h2))
    story.append(P("هر شرکت در دفتر شما نیاز به تنظیمات اتصال مستقل دارد. این تنظیمات شامل نوع Adapter، رشته اتصال (connection string)، نام دیتابیس، شناسه شرکت در نرم‌افزار مبدأ، و سایر پارامترها است. این تنظیمات در یک جدول پیکربندی در دیتابیس مرکزی سامانه ذخیره می‌شود و رمزگذاری می‌شود. وقتی کارمندی فایل اکسل شرکت A را بارگذاری می‌کند، سامانه به‌طور خودکار با استفاده از تنظیمات اتصال شرکت A، Adapter مناسب را فعال می‌کند، اسناد واقعی را می‌خواند، و با فایل اکسل مقایسه می‌کند."))
    
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
    col_w_set = [4*cm, 12.8*cm]
    factor = CONTENT_W / sum(col_w_set)
    col_w_set = [w * factor for w in col_w_set]
    story.append(make_table(settings_data, col_widths=col_w_set))
    story.append(Spacer(1, 8))
    
    story.append(callout("هشدار امنیتی: اتصال به دیتابیس‌های حسابداری باید صرفاً Read-Only باشد. هیچ شرایطی نباید به سامانه اجازه دهد داده‌های حسابداری شرکت‌ها را تغییر دهد. این اصل، حفاظت از اطلاعات مالی مشتریان شما را تضمین می‌کند.", 'danger'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 6 ============================
    story.append(Paragraph(fa("فصل ۶: الگوی اکسل اسناد حسابداری"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("فایل اکسلی که کارمندان بارگذاری می‌کنند، باید یک قالب استاندارد مشخص داشته باشد تا موتور کنترل بتواند به‌طور خودکار آن را پردازش کند. در این فصل، ساختار دقیق ستون‌ها، قواعد اعتبارسنجی هر ستون، و یک نمونه رکورد ارائه می‌شود. این قالب بر اساس استانداردهای رایج حسابداری ایران (ساختار کل/معین/تفصیل و تراز بدهکار/بستانکار) طراحی شده است."))
    
    story.append(Paragraph(fa("۶.۱ ساختار ستون‌ها"), style_h2))
    story.append(P("فایل اکسل باید شامل دقیقاً این ۹ ستون با این ترتیب باشد. ردیف اول فایل باید هدر (نام ستون‌ها) باشد و داده‌ها از ردیف دوم شروع شوند. سامانه در صورت مشاهده هرگونه انحراع از این قالب، فایل را رد می‌کند و دلیل را به کارمند گزارش می‌دهد."))
    
    columns_data = [
        ["شماره", "نام ستون", "نوع داده", "الزامی", "قواعد اعتبارسنجی"],
        ["۱", "ردیف", "عدد صحیح", "بله", "باید یکتا در داخل فایل باشد؛ از ۱ شروع و متوالی"],
        ["۲", "شماره سند", "متن/عدد", "بله", "می‌تواند تکراری باشد (چند ردیف یک سند)؛ ولی دو ردیف با شماره و تاریخ یکسان باید با ردیف متمایز شوند"],
        ["۳", "تاریخ سند", "تاریخ شمسی", "بله", "فرمت YYYY/MM/DD یا YY/MM/DD؛ معتبر و قابل تبدیل"],
        ["۴", "کد کل", "متن/عدد", "بله", "کد حساب کل؛ باید در طرح حساب شرکت وجود داشته باشد"],
        ["۵", "کد معین", "متن/عدد", "بله", "کد حساب معین؛ باید زیرمجموعه کد کل همان ردیف باشد"],
        ["۶", "کد تفصیل", "متن/عدد", "خیر", "کد تفصیل (در صورت پشتیبانی شرکت)"],
        ["۷", "شرح سند", "متن", "خیر", "توضیح ردیف سند؛ حداکثر ۵۰۰ کاراکتر"],
        ["۸", "بدهکار", "عدد اعشاری", "بله*", "مبلغ بدهکار؛ *دقیقاً یکی از بده یا بستان باید صفر باشد"],
        ["۹", "بستانکار", "عدد اعشاری", "بله*", "مبلغ بستانکار؛ *دقیقاً یکی از بده یا بستان باید صفر باشد"],
    ]
    col_w_cols = [1.2*cm, 2.8*cm, 2.4*cm, 1.6*cm, 8.8*cm]
    factor = CONTENT_W / sum(col_w_cols)
    col_w_cols = [w * factor for w in col_w_cols]
    story.append(make_table(columns_data, col_widths=col_w_cols))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۶.۲ قواعد اعتبارسنجی هوشمند"), style_h2))
    story.append(P("سیستم در زمان بارگذاری فایل، چندین لایه اعتبارسنجی را به‌ترتیب اجرا می‌کند. اگر هر لایه با شکست روبه‌رو شود، پردازش متوقف می‌شود و خطای مربوطه گزارش می‌شود. این طراحی چندلایه باعث می‌شود خطاهای ساختاری قبل از خطاهای منطقی شناسایی شوند و گزارش‌های مفیدتری به کارمند ارائه شود."))
    
    story.append(Paragraph(fa("لایه ۱: اعتبارسنجی قالب"), style_h3))
    story.append(P("فایل باید یک فایل اکسل معتبر با پسوند .xlsx یا .xls باشد. صرف تغییر پسوند یک فایل غیر اکسل به .xlsx قابل قبول نیست؛ سامانه با خواندن سرآیند فایل (magic bytes) نوع واقعی را تشخیص می‌دهد. سپس تعداد ستون‌ها و نام هدرها بررسی می‌شوند. اگر نام ستون‌ها با قالب استاندارد مطابقت نداشته باشد، سامانه سعی می‌کند با الگوریتم تطبیق فازی، نام‌های نزدیک را شناسایی و به کارمند پیشنهاد اصلاح دهد. این کار به کارمندان کمک می‌کند تا بدون نیاز به یادآوری دقیق نام ستون‌ها، با اشتباهات جزئی هم فایل را بارگذاری کنند."))
    
    story.append(Paragraph(fa("لایه ۲: اعتبارسنجی نوع داده"), style_h3))
    story.append(P("هر ستون باید نوع داده مشخصی داشته باشد. ستون «ردیف» باید عدد صحیح مثبت باشد. ستون «تاریخ سند» باید یک تاریخ معتبر شمسی باشد. سامانه فرمت‌های مختلف تاریخ شمسی (۱۴۰۵/۰۷/۲۰، ۱۴۰۵-۰۷-۲۰، ۲۰/۰۷/۱۴۰۵) را تشخیص می‌دهد و آن‌ها را به یک فرمت استاندارد داخلی (ISO) تبدیل می‌کند. ستون‌های «بدهکار» و «بستانکار» باید عدد اعشاری نامنفی باشند. ستون‌های غیر عددی اگر حاوی داده عددی نباشند، ردیف رد می‌شود."))
    
    story.append(Paragraph(fa("لایه ۳: اعتبارسنجی منطقی حسابداری"), style_h3))
    story.append(P("چند قاعده منطقی باید برقرار باشد. اول، در هر ردیف، دقیقاً یکی از بدهکار یا بستانکار باید صفر باشد (یک ردیف نمی‌تواند هم‌زمان بدهکار و بستانکار باشد). دوم، در هر سند (گروه ردیف‌های با شماره سند یکسان)، مجموع بدهکار باید با مجموع بستانکار برابر باشد (تراز سند). سوم، کد معین باید زیرمجموعه کد کل همان ردیف باشد. این قواعد منطقی باعث می‌شوند فایل‌های نادرست قبل از مقایسه با دیتابیس شناسایی شوند."))
    
    story.append(Paragraph(fa("لایه ۴: کنترل تکراری"), style_h3))
    story.append(P("این لایه تخصصی‌ترین بخش موتور کنترل است. تکراری بودن را در سه سطح بررسی می‌کند. سطح اول: ردیف‌های تکراری در داخل فایل - اگر دو ردیف با تمام فیلدهای یکسان وجود داشته باشد، این یک خطای واقعی است. سطح دوم: ردیف‌های تکراری میان فایل فعلی و فایل‌های قبلی همان شرکت - اگر کارمندی قبلاً سندی را در فایل قبلی بارگذاری کرده باشد و در فایل جدید نیز تکرار شود، این یک تکراری واقعی است مگر اینکه کارمند به‌صورت صریح اعلام کند که فایل جدید شامل اسناد قبلی + اسناد جدید است (مثلاً برای بازنشر فایل کامل دوره). سطح سوم: تشخیص اصلاح سند از تکراری واقعی - اگر سندی در فایل قبلی بارگذاری شده و در فایل جدید با همان شماره سند و تاریخ اما با مبالغ متفاوت ظاهر شود، این یک «اصلاح سند» است، نه تکراری. سامانه باید این دو حالت را از هم تشخیص دهد."))
    
    story.append(Paragraph(fa("لایه ۵: تطبیق با دیتابیس واقعی"), style_h3))
    story.append(P("پس از اعتبارسنجی داخلی فایل، سامانه با استفاده از Adapter مناسب، اسناد واقعی شرکت را در بازه تاریخی ادعایی کارمند از دیتابیس می‌خواند. سپس دو مجموعه اسناد را بر اساس یک کلید منطقی (ترکیب شماره سند + تاریخ + ردیف) مقایسه می‌کند. اسنادی که در فایل هستند اما در دیتابیس نیستند، به‌عنوان «اسناد ادعایی بدون پایه» شناسایی می‌شوند. اسنادی که در دیتابیس هستند اما در فایل نیستند، به‌عنوان «اسناد مفقود از فایل» شناسایی می‌شوند. اسنادی که در هر دو هستند اما با مبالغ متفاوت، به‌عنوان «مغایرت مقدار» شناسایی می‌شوند."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۶.۳ نمونه فایل اکسل استاندارد"), style_h2))
    story.append(P("نمونه زیر سه ردیف فرضی از فایل اکسل یک شرکت را نشان می‌دهد. این نمونه صرفاً برای نمایش قالب است و اعداد واقعی نیستند."))
    
    sample_data = [
        ["ردیف", "شماره سند", "تاریخ سند", "کد کل", "کد معین", "کد تفصیل", "شرح سند", "بدهکار", "بستانکار"],
        ["۱", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۱", "۱۰۱", "۱۰۱۰۱", "فروش نقدی به شرکت الف", "۵٬۰۰۰٬۰۰۰", "۰"],
        ["۲", "۱۰۰۱", "۱۴۰۵/۰۷/۰۱", "۵", "۵۰۱", "۵۰۱۰۱", "دریافت نقدی", "۰", "۵٬۰۰۰٬۰۰۰"],
        ["۳", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۲", "۲۰۱", "۲۰۱۰۱", "خرید کالا از شرکت ب", "۰", "۳٬۰۰۰٬۰۰۰"],
        ["۴", "۱۰۰۲", "۱۴۰۵/۰۷/۰۵", "۴", "۴۰۱", "۴۰۱۰۱", "پرداخت نقدی", "۳٬۰۰۰٬۰۰۰", "۰"],
    ]
    col_w_sample = [1.0*cm, 1.6*cm, 1.8*cm, 1.0*cm, 1.0*cm, 1.2*cm, 4.5*cm, 2.0*cm, 2.0*cm]
    factor = CONTENT_W / sum(col_w_sample)
    col_w_sample = [w * factor for w in col_w_sample]
    story.append(make_table(sample_data, col_widths=col_w_sample))
    story.append(Spacer(1, 8))
    
    story.append(callout("نکته: در سند ۱۰۰۱ و ۱۰۰۲، مجموع بدهکار (۵+۳=۸ میلیون) با مجموع بستانکار (۵+۳=۸ میلیون) برابر است؛ یعنی تراز سند برقرار است. این یک ویژگی منطقی است که موتور کنترل به‌صورت خودکار بررسی می‌کند.", 'info'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 7 ============================
    story.append(Paragraph(fa("فصل ۷: موتور کنترل هوشمند اسناد"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("موتور کنترل هوشمند اسناد، قلب متمایزکننده سامانه شماست. این موتور مسئولیت پردازش هر فایل اکسل بارگذاری‌شده را بر عهده دارد و خروجی آن یک گزارش کنترل ساختاریافته است که به مدیر نمایش داده می‌شود. در این فصل، ۹ مرحله کنترل، قواعد تشخیص اصلاح از تکرار، و نمونه گزارش مغایرت به‌طور کامل تشریح می‌شود."))
    
    story.append(Paragraph(fa("۷.۱ نه مرحله کنترل"), style_h2))
    story.append(P("هر بارگذاری فایل اکسل، موتور کنترل ۹ مرحله متوالی را روی آن اجرا می‌کند. این مراحل به‌صورت لایه‌ای طراحی شده‌اند: اگر یک مرحله با خطای مهره‌ای روبه‌رو شود، مراحل بعدی اجرا نمی‌شوند و خطا به کارمند گزارش می‌شود. اما اگر خطا قابل بازیابی باشد (مثلاً چند ردیف نامعتبر)، سامانه ادامه می‌دهد و در پایان تمام خطاها را در یک گزارش واحد ارائه می‌کند."))
    
    story.extend(numbered_list([
        "کنترل قالب و ساختار: بررسی نوع فایل، تعداد ستون‌ها، نام هدرها و تطبیق با الگو.",
        "شمارش ردیف‌ها: شمارش کل ردیف‌ها، ردیف‌های معتبر، ردیف‌های نامعتبر و ردیف‌های خالی.",
        "تشخیص بارگذاری مجدد: محاسبه هش فایل و مقایسه با فایل‌های قبلی همان شرکت؛ اگر یکسان باشد، به‌عنوان «تکرار فایل» گزارش می‌شود.",
        "تشخیص ردیف‌های تکراری در فایل: شناسایی ردیف‌هایی که تمام فیلدهای آن‌ها یکسان است.",
        "کنترل شماره سند تکراری: تفکیک ردیف‌های متعلق به یک سند (مجاز) از تکرار واقعی سند (خطا).",
        "تطبیق بازه تاریخی ادعا با فایل: محاسبه حداقل و حداکثر تاریخ در فایل و مقایسه با بازه ادعایی کارمند.",
        "مقایسه اسناد فایل با دیتابیس شرکت: خواندن اسناد واقعی از دیتابیس و مقایسه با فایل.",
        "شناسایی اسناد مفقود و اسناد خارج از بازه: اسنادی که در دیتابیس هستند اما در فایل نیستند (مفقود) یا برعکس.",
        "کنترل تراز بدهکار/بستانکار: محاسبه مجموع بدهکار و بستانکار هر سند و کنترل تراز.",
    ]))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("۷.۲ قواعد تشخیص اصلاح سند از تکرار"), style_h2))
    story.append(P("یکی از پیچیده‌ترین بخش‌های موتور کنترل، تشخیص اصلاح سند از تکرار واقعی است. این تشخیص بر اساس وضعیت سند در دیتابیس و فایل انجام می‌شود. در ادامه، پنج حالت اصلی و قاعده کنترل هر یک تشریح می‌شود."))
    
    rules_data = [
        ["حالت", "وضعیت در فایل قبلی", "وضعیت در فایل جدید", "وضعیت در دیتابیس", "تشخیص سامانه", "اقدام"],
        ["۱", "وجود ندارد", "وجود دارد", "وجود دارد", "سند جدید", "تأیید"],
        ["۲", "وجود دارد", "وجود ندارد", "وجود دارد", "حذف از گزارش", "اخطار به مدیر"],
        ["۳", "وجود دارد", "وجود دارد (یکسان)", "وجود دارد", "تکرار فایل", "خطا - رد فایل"],
        ["۴", "وجود دارد", "وجود دارد (مقادیر متفاوت)", "وجود دارد (با مقادیر جدید)", "اصلاح سند", "تأیید با ثبت نسخه قبلی"],
        ["۵", "وجود ندارد", "وجود دارد", "وجود ندارد", "سند بدون پایه", "خطا - ادعای بی‌اساس"],
    ]
    col_w_rules = [1.2*cm, 2.2*cm, 2.5*cm, 2.5*cm, 2.0*cm, 2.0*cm, 3.4*cm]
    factor = CONTENT_W / sum(col_w_rules)
    col_w_rules = [w * factor for w in col_w_rules]
    story.append(make_table(rules_data, col_widths=col_w_rules))
    story.append(Spacer(1, 8))
    
    story.append(callout("نکته فنی: تشخیص صحیح حالت ۴ (اصلاح سند) نیازمند آن است که نرم‌افزار حسابداری مبدأ شناسه پایدار برای سند داشته باشد. اگر نرم‌افزار این قابلیت را نداشته باشد، باید بر اساس ترکیب شماره سند + تاریخ سند شناسایی کرد که ممکن است در موارد نادر (تغییر تاریخ یک سند) منجر به تشخیص نادرست شود.", 'warn'))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("۷.۳ نمونه گزارش کنترل اسناد"), style_h2))
    story.append(P("نمونه زیر یک گزارش کنترل واقعی را برای یک فایل فرضی نشان می‌دهد. این گزارش به مدیر نمایش داده می‌شود و او می‌تواند آن را تأیید یا برای اصلاح به کارمند برگرداند. اعداد فرضی هستند."))
    
    report_data = [
        [Paragraph(fa("گزارش کنترل اسناد شرکت A - بازه ادعایی ۱۴۰۵/۰۷/۰۱ تا ۱۴۰۵/۰۷/۲۰"), style_table_header)],
    ]
    report_header = Table(report_data, colWidths=[CONTENT_W])
    report_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_ACCENT),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(report_header)
    story.append(Spacer(1, 4))
    
    summary_data = [
        ["شاخص", "مقدار", "وضعیت"],
        ["تعداد کل ردیف‌های فایل", "۱٬۲۵۲", "—"],
        ["تعداد ردیف‌های معتبر", "۱٬۲۴۰", "✓"],
        ["تعداد ردیف‌های نامعتبر", "۱۲", "✗"],
        ["تعداد اسناد یکتا", "۳۸۵", "✓"],
        ["تعداد ردیف‌های تکراری در فایل", "۰", "✓"],
        ["تعداد اسناد مفقود از دیتابیس در فایل", "۵", "✗"],
        ["تعداد اسناد ادعایی بدون پایه در دیتابیس", "۲", "✗"],
        ["مغایرت بازه تاریخی", "۲ روز", "✗"],
        ["تراز بدهکار کل", "۴۵٬۲۳۰٬۰۰۰ تومان", "✓"],
        ["تراز بستانکار کل", "۴۵٬۲۳۰٬۰۰۰ تومان", "✓"],
        ["مغایرت مقدار در ردیف‌ها", "۳ مورد", "✗"],
        ["وضعیت کلی", "نیازمند بررسی مدیر", "⚠"],
    ]
    col_w_rep = [6*cm, 4*cm, 3*cm]
    factor = CONTENT_W / sum(col_w_rep)
    col_w_rep = [w * factor for w in col_w_rep]
    story.append(make_table(summary_data, col_widths=col_w_rep))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("جزئیات مغایرت‌ها (نمونه)"), style_h3))
    detail_data = [
        ["نوع مغایرت", "شماره سند", "تاریخ", "شرح", "اقدام پیشنهادی"],
        ["سند مفقود از فایل", "۱۰۳۲", "۱۴۰۵/۰۷/۱۰", "سند در دیتابیس است اما در فایل اکسل نیست", "بررسی با کارمند"],
        ["سند مفقود از فایل", "۱۰۵۸", "۱۴۰۵/۰۷/۱۵", "سند در دیتابیس است اما در فایل اکسل نیست", "بررسی با کارمند"],
        ["مغایرت مقدار - بدهکار", "۱۰۴۲", "۱۴۰۵/۰۷/۱۲", "فایل: ۳٬۰۰۰٬۰۰۰ / دیتابیس: ۳٬۵۰۰٬۰۰۰", "اصلاح فایل یا بررسی دیتابیس"],
        ["سند خارج از بازه ادعا", "۱۰۷۰", "۱۴۰۵/۰۷/۲۵", "تاریخ خارج از بازه ادعایی (۰۱ تا ۲۰)", "اصلاح بازه ادعا"],
    ]
    col_w_det = [3.5*cm, 1.8*cm, 2.2*cm, 6*cm, 3.5*cm]
    factor = CONTENT_W / sum(col_w_det)
    col_w_det = [w * factor for w in col_w_det]
    story.append(make_table(detail_data, col_widths=col_w_det))
    story.append(Spacer(1, 10))
    
    story.append(callout("طراحی کلیدی: سامانه نباید صرفاً یک پیام «فایل صحیح است» یا «فایل دارای خطاست» نشان دهد. هر بارگذاری باید یک گزارش کنترل مستقل تولید کند که شامل تمام مغایرت‌ها، ریشه‌یابی و اقدام پیشنهادی باشد. این شفافیت به مدیر اجازه می‌دهد تصمیم آگاهانه بگیرد.", 'info'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 8 ============================
    story.append(Paragraph(fa("فصل ۸: چارچوب ارزیابی عملکرد پرسنل"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("ارزیابی عملکرد پنج کارمند شما نباید صرفاً بر اساس «تعداد تسک‌های بسته‌شده» باشد. این معیار ساده، انگیزه نادرستی ایجاد می‌کند: کارمند برای افزایش تعداد تسک‌ها، ممکن است کارهای کوچک و ساده را ترجیح دهد و از کارهای پیچیده و زمان‌بر شانه خالی کند. چارچوب پیشنهادی ما بر اساس پنج شاخص وزن‌دار است که کیفیت، تحویل به‌موقع، حجم/پیچیدگی، مستندات و همکاری را به‌صورت متوازن ارزیابی می‌کند."))
    
    story.append(Paragraph(fa("۸.۱ پنج شاخص کلیدی عملکرد (KPI)"), style_h2))
    
    kpi_data = [
        ["شاخص", "وزن", "تعریف", "روش اندازه‌گیری", "دامنه امتیاز"],
        ["کیفیت و صحت کار تأییدشده", "۳۵٪", "نسبت تسک‌های تأییدشده به کل تسک‌های ارسالی، با در نظر گرفتن شدت مغایرت", "اتوماتیک از موتور کنترل + بازبینی مدیر", "۰ تا ۱۰۰"],
        ["تحویل به‌موقع", "۲۵٪", "نسبت تسک‌های تحویلی در مهلت مقرر به کل تسک‌ها", "اتوماتیک از تاریخ تحویل در برابر مهلت", "۰ تا ۱۰۰"],
        ["حجم کار نسبت به پیچیدگی", "۲۰٪", "حجم کار استانداردشده بر اساس نوع فعالیت، تنظیم شده با ضریب پیچیدگی", "نیمه‌خودکار: فرمول پیچیدگی + تأیید مدیر", "۰ تا ۱۰۰"],
        ["کامل بودن مستندات", "۱۰٪", "کیفیت فایل اکسل، گزارش کار، شرح فعالیت و پیوست‌ها", "اتوماتیک (اعتبارسنجی) + بازبینی مدیر", "۰ تا ۱۰۰"],
        ["همکاری و ارجاع صحیح", "۱۰٪", "کیفیت ارجاع‌ها به همکاران، پیگیری و تحویل منظم", "ارزیابی کیفی ماهانه مدیر", "۰ تا ۱۰۰"],
    ]
    col_w_kpi = [3.2*cm, 1.2*cm, 4.5*cm, 4.2*cm, 2.0*cm]
    factor = CONTENT_W / sum(col_w_kpi)
    col_w_kpi = [w * factor for w in col_w_kpi]
    story.append(make_table(kpi_data, col_widths=col_w_kpi))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۸.2 دلیل وزن‌دهی به این شکل"), style_h2))
    story.append(P("وزن ۳۵٪ برای کیفیت بالاترین وزن را دارد زیرا در دفتر حسابداری، کیفیت کار با اعتبار دفتر و رضایت مشتریان رابطه مستقیم دارد. یک کار نادرست می‌تواند به زیان مالی شرکت و در نتیجه به دعوای حقوقی با دفتر منجر شود. وزن ۲۵٪ برای تحویل به‌موقع نشان‌دهنده اهمیت پایبندی به توافق با مشتری است. وزن ۲۰٪ برای حجم/پیچیدگی به این دلیل طراحی شده که کارمندی که کارهای پیچیده‌تر انجام می‌دهد، تشویق شود؛ اما بدون کیفیت، حجم به‌تنهایی کافی نیست. وزن ۱۰+۱۰٪ برای مستندات و همکاری نشان‌دهنده این است که این دو عامل اهمیت دارند اما نباید بر کیفیت غلبه کنند. این وزن‌دهی نقطه شروع است و باید پس از یک تا دو ماه داده واقعی، بر اساس مشاهدات شما بازتنظیم شود."))
    
    story.append(Paragraph(fa("۸.۳ نمونه کارت امتیاز ماهانه"), style_h2))
    story.append(P("نمونه زیر یک کارت امتیاز ماهانه فرضی برای یک کارمند را نشان می‌دهد. این کارت در پایان هر ماه به‌صورت اتوماتیک تولید و در داشبورد مدیر نمایش داده می‌شود."))
    
    scorecard_data = [
        ["شاخص", "امتیاز ماه", "وزن", "امتیاز وزن‌دار", "تغییر نسبت به ماه قبل"],
        ["کیفیت کار", "۸۸", "۳۵٪", "۳۰٫۸", "+۵"],
        ["تحویل به‌موقع", "۹۲", "۲۵٪", "۲۳٫۰", "+۲"],
        ["حجم/پیچیدگی", "۸۵", "۲۰٪", "۱۷٫۰", "-۳"],
        ["مستندات", "۹۰", "۱۰٪", "۹٫۰", "۰"],
        ["همکاری", "۸۷", "۱۰٪", "۸٫۷", "+۱"],
        ["امتیاز کل ماه", "—", "۱۰۰٪", "۸۸٫۵", "+۳٫۲"],
        ["رتبه در دفتر", "—", "—", "۲ از ۵", "—"],
    ]
    col_w_sc = [4.5*cm, 2.5*cm, 2.0*cm, 3.0*cm, 4.0*cm]
    factor = CONTENT_W / sum(col_w_sc)
    col_w_sc = [w * factor for w in col_w_sc]
    story.append(make_table(scorecard_data, col_widths=col_w_sc))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۸.۴ داشبورد روزانه مدیر"), style_h2))
    story.append(P("علاوه بر کارت امتیاز ماهانه، مدیر باید یک داشبورد روزانه داشته باشد که نگاهی فوری به وضعیت جاری دفتر ارائه دهد. این داشبورد باید در یک صفحه، مهم‌ترین اطلاعات را بدون نیاز به کلیک چندباره نمایش دهد."))
    
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
    story.extend(bullet_list(dashboard_items))
    
    story.append(Spacer(1, 6))
    story.append(callout("اصل طراحی داشبورد: کمتر، بهتر. مدیر نباید با اطلاعات جزئی غرق شود. داشبورد باید سؤال‌های اصلی را پاسخ دهد: «چه چیزی نیاز به توجه من دارد؟» و «وضعیت کلی چگونه است؟». جزئیات باید در گزارش‌های پایین‌دست قابل دسترسی باشند.", 'info'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 9 ============================
    story.append(Paragraph(fa("فصل ۹: گردش کار تسک و ارجاع به همکار"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("مدل داده تسک و گردش کار آن باید به‌گونه‌ای طراحی شود که ارجاع بخشی از یک تسک به همکار، تأیید چندمرحله‌ای مدیر، و پیگیری پیشرفت واقعی به‌صورت شفاف انجام شود. در این فصل، مدل کامل تسک، چرخه وضعیت‌ها، و قواعد ارجاع به همکار تشریح می‌شود."))
    
    story.append(Paragraph(fa("۹.۱ مدل داده تسک"), style_h2))
    story.append(P("هر تسک شامل مجموعه‌ای از فیلدها است که در جدول زیر نشان داده شده است. این فیلدها به‌گونه‌ای طراحی شده‌اند که تمام اطلاعات لازم برای کنترل، ارزیابی و گزارش‌گیری را در خود نگه دارند."))
    
    task_data = [
        ["فیلد", "نوع", "توضیح"],
        ["task_id", "UUID", "شناسه یکتای تسک"],
        ["company_id", "UUID", "شرکت مربوط به تسک"],
        ["activity_type", "Enum", "نوع فعالیت: ثبت اسناد / اصلاح / گزارش / مالیات / سایر"],
        ["title", "String", "عنوان کوتاه تسک"],
        ["description", "Text", "توضیح کامل"],
        ["assigned_to", "UUID", "کارمند مسئول اصلی"],
        ["collaborators", "Array<UUID>", "فهرست همکاران (در صورت ارجاع)"],
        ["date_start", "Date", "تاریخ شروع واقعی"],
        ["date_due", "Date", "مهلت انجام"],
        ["date_completed", "Date", "تاریخ تکمیل واقعی"],
        ["checklist", "Array<Item>", "چک‌لیست مراحل با وضعیت انجام/نادان"],
        ["progress_percent", "Integer 0-100", "درصد پیشرفت واقعی"],
        ["attached_files", "Array<File>", "فایل‌های پیوست (شامل فایل اکسل)"],
        ["control_status", "Enum", "وضعیت کنترل: در انتظار / تأیید / رد / نیازمند اصلاح"],
        ["control_report_id", "UUID", "شناسه گزارش کنترل مرتبط"],
        ["approved_by", "UUID", "کاربری که تأیید کرده"],
        ["approved_at", "Timestamp", "زمان تأیید"],
        ["change_history", "Array<Event>", "تاریخچه کامل تغییرات (immutable)"],
    ]
    col_w_task = [4.5*cm, 3.5*cm, 9*cm]
    factor = CONTENT_W / sum(col_w_task)
    col_w_task = [w * factor for w in col_w_task]
    story.append(make_table(task_data, col_widths=col_w_task))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۹.۲ چرخه وضعیت تسک"), style_h2))
    story.append(P("تسک از یک ماشین وضعیت (state machine) پیروی می‌کند. انتقال از یک وضعیت به وضعیت دیگر فقط از مسیرهای مجاز ممکن است. این کنترل از رفتارهای غیرمجاز (مثلاً تأیید یک تسک که هنوز کنترل نشده) جلوگیری می‌کند."))
    
    status_data = [
        ["وضعیت", "توضیح", "انتقال‌های مجاز بعدی"],
        ["تازه (Created)", "تسک ایجاد شده اما کارمند هنوز شروع نکرده", "در حال انجام، رد شده، کنسل"],
        ["در حال انجام (In Progress)", "کارمند اعلام شروع کرده است", "در انتظار کنترل، ارجاع به همکار، رد شده"],
        ["ارجاع به همکار (Delegated)", "بخشی از کار به همکار واگذار شده", "در حال انجام (پس از بازگشت)، در انتظار کنترل"],
        ["در انتظار کنترل (Pending Review)", "کارمند کار را تمام کرده و فایل آپلود کرده", "تأیید شده، رد شده، نیازمند اصلاح"],
        ["نیازمند اصلاح (Revision Needed)", "مدیر مغایرت‌هایی را یافته است", "در حال انجام (مجدد)، رد شده"],
        ["تأیید شده (Approved)", "مدیر کار را تأیید کرده", "بسته شده (terminal)"],
        ["رد شده (Rejected)", "کار قابل قبول نبوده", "بسته شده (terminal)"],
        ["کنسل (Cancelled)", "تسک قبل از شروع لغو شده", "بسته شده (terminal)"],
    ]
    col_w_st = [3.5*cm, 5.5*cm, 8*cm]
    factor = CONTENT_W / sum(col_w_st)
    col_w_st = [w * factor for w in col_w_st]
    story.append(make_table(status_data, col_widths=col_w_st))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۹.۳ ارجاع بخشی از تسک به همکار"), style_h2))
    story.append(P("یکی از ویژگی‌های کلیدی شما، امکان ارجاع بخشی از یک تسک به همکار است. به عنوان مثال، کارمند الف ممکن است بخش «ثبت اسناد خرید» از یک تسک بزرگ «بستن ماهانه شرکت A» را به کارمند ب ارجاع دهد. در این حالت، سامانه باید سهم هر فرد را به‌صورت شفاف پیگیری کند تا در ارزیابی عملکرد، یک کار دو بار به‌عنوان خروجی کامل دو کارمند حساب نشود."))
    
    story.append(P("راهکار ما این است: هر ارجاع به یک SubTask از تسک اصلی تبدیل می‌شود. SubTask مسئول، مهلت و وضعیت مستقل دارد، اما به تسک اصلی متصل است. در گزارش ارزیابی، تسک اصلی به نسبت کارمندی که بیشترین سهم را داشته اختصاص می‌یابد و سهم سایر کارمندان به‌صورت وزن‌دار محاسبه می‌شود. به‌عنوان مثال، اگر کارمند الف ۷۰٪ زمان را صرف کرده و کارمند ب ۳۰٪، امتیاز حجم کار به نسبت ۷۰/۳۰ تقسیم می‌شود."))
    
    story.append(callout("قاعده کلیدی: یک تسک نباید به‌عنوان خروجی کامل دو کارمند حساب شود. سامانه باید سهم هر فرد را به‌صورت عددی پیگیری کند و در محاسبه امتیاز حجم کار، این سهم را لحاظ نماید.", 'warn'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 10 ============================
    story.append(Paragraph(fa("فصل ۱۰: حضور و غیاب، مرخصی، درخواست‌ها و لاگ فعالیت"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این فصل، قابلیت‌های جانبی اما مهم سامانه بررسی می‌شود: ثبت مرخصی، ورود و خروج، درخواست‌ها به مدیر و مدیرعامل، و لاگ فعالیت غیرقابل ویرایش. این قابلیت‌ها در فاز اولیه به‌صورت ساده پیاده‌سازی می‌شوند و در فازهای بعدی به دستگاه حضور و غیاب متصل می‌شوند."))
    
    story.append(Paragraph(fa("۱۰.۱ ثبت مرخصی"), style_h2))
    story.append(P("کارمند می‌تواند درخواست مرخصی روزانه، ساعتی، استعلاگی یا استحقاقی ثبت کند. درخواست شامل نوع مرخصی، بازه زمانی، دلیل و وضعیت تأیید است. گردش تأیید بسته به نوع مرخصی متفاوت است: مرخصی استحقاقی فقط نیاز به تأیید مدیر مستقیم دارد. مرخصی استعلاگی نیاز به تأیید مدیر و مدیرعامل دارد. مرخصی بیش از ۳ روز نیاز به تأیید مدیرعامل دارد. در صورت عدم پاسخ مدیر در مدت مشخص (پیشنهاد: ۲۴ ساعت)، مرخصی به‌صورت خودکار به مدیرعامل ارجاع می‌شود."))
    
    story.append(Paragraph(fa("۱۰.۲ ثبت ورود و خروج"), style_h2))
    story.append(P("در فاز اول، ثبت ورود و خروج به‌صورت دستی از طریق پنل کارمند انجام می‌شود. کارمند در شروع روز کاری «ورود» و در پایان «خروج» را ثبت می‌کند. سامانه ساعت، تاریخ و کارمند را به‌صورت خودکار ثبت می‌کند. در فاز دوم، این قابلیت به دستگاه حضور و غیاب فیزیکی متصل می‌شود و ثبت به‌صورت خودکار انجام می‌شود. در هر دو حالت، گزارش ماهانه حضور و غیاب به‌صورت اتوماتیک تولید می‌شود."))
    
    story.append(Paragraph(fa("۱۰.۳ درخواست به مدیر و مدیرعامل"), style_h2))
    story.append(P("کارمند می‌تواند درخواست‌های مختلفی ثبت کند: درخواست مساعده، درخواست ارتقای شغلی، درخواست تجهیزات، درخواست تغییر شیفت، و درخواست‌های دلخواه. هر درخواست نوع، عنوان، توضیح، پیوست و وضعیت تأیید دارد. گردش تأیید بسته به نوع درخواست متفاوت است. تمام درخواست‌ها در کارتابل مدیر یا مدیرعامل نمایش داده می‌شوند و می‌توانند تأیید، رد یا برای اطلاعات بیشتر برگردانده شوند."))
    
    story.append(Paragraph(fa("۱۰.۴ لاگ فعالیت غیرقابل ویرایش (Immutable Audit Log)"), style_h2))
    story.append(P("یکی از مهم‌ترین ویژگی‌های امنیتی سامانه، لاگ فعالیت غیرقابل ویرایش است. این لاگ رویدادهای مهم را ثبت می‌کند: ورود/خروج کاربر، ایجاد/ویرایش/حذف تسک، بارگذاری فایل، تأیید یا رد گزارش، تغییر تنظیمات اتصال، و سایر رویدادهای حساس. هر رویداد شامل نوع، زمان، کاربر، آدرس IP، توضیح و داده‌های مرتبط است."))
    
    story.append(P("مهم‌ترین ویژگی این لاگ، غیرقابل ویرایش بودن آن است. این یعنی حتی مدیر هم نمی‌تواند رویدادهای ثبت‌شده را ویرایش یا حذف کند. این قابلیت با دو روش پیاده‌سازی می‌شود. روش اول: استفاده از یک جدول دیتابیس که فقط INSERT مجاز است و UPDATE/DELETE در سطح کاربر دیتابیس غیرفعال است. روش دوم (پیشنهادی برای حساس‌ترین داده‌ها): نوشتن لاگ به یک سیستم لاگ خارجی (مانند Elasticsearch یا یک سرور لاگ مستقل) که حتی اگر دیتابیس اصلی دفتر دستکاری شود، لاگ دست‌نخورده باقی بماند."))
    
    log_data = [
        ["نوع رویداد", "کاربر", "زمان", "توضیح نمونه", "اولویت"],
        ["AUTH_LOGIN", "کارمند", "۱۴۰۵/۰۷/۲۰ ۰۸:۳۲", "ورود موفق از IP 192.168.1.5", "متوسط"],
        ["TASK_CREATED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۰۹:۱۵", "ایجاد تسک ۱۲۳۴ برای شرکت A", "متوسط"],
        ["FILE_UPLOADED", "کارمند", "۱۴۰۵/۰۷/۲۰ ۱۰:۴۵", "آپلود فایل اسناد_شرکت_A.xlsx (۲.۳MB)", "بالا"],
        ["TASK_APPROVED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۱۱:۲۰", "تأیید تسک ۱۲۳۴ با امتیاز ۸۸", "بالا"],
        ["TASK_REJECTED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۱۱:۳۵", "رد تسک ۱۲۳۵ - مغایرت ۵ سند", "بالا"],
        ["CONN_CONFIG_CHANGED", "مدیر", "۱۴۰۵/۰۷/۲۰ ۱۴:۰۰", "تغییر تنظیمات اتصال شرکت B", "بحرانی"],
        ["LEAVE_REQUESTED", "کارمند", "۱۴۰۵/۰۷/۲۰ ۱۵:۲۰", "درخواست مرخصی ۱۴۰۵/۰۸/۰۱ تا ۰۸/۰۳", "متوسط"],
    ]
    col_w_log = [3.5*cm, 1.8*cm, 3.5*cm, 6*cm, 2.4*cm]
    factor = CONTENT_W / sum(col_w_log)
    col_w_log = [w * factor for w in col_w_log]
    story.append(make_table(log_data, col_widths=col_w_log))
    story.append(Spacer(1, 8))
    
    story.append(callout("اصل امنیتی: لاگ فعالیت نباید صرفاً یک متن قابل ویرایش باشد. رویدادهای مهم باید در یک سابقه محافظت‌شده ثبت شوند که حتی مدیر سیستم هم نتواند آن را تغییر دهد. این اصل، اعتماد به گزارش‌های ارزیابی پرسنل و رسیدگی به مغایرت‌ها را تضمین می‌کند.", 'danger'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 11 ============================
    story.append(Paragraph(fa("فصل ۱۱: نقشه راه پیاده‌سازی فازبندی شده"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("ساخت تمام قابلیت‌های سامانه به‌صورت یکجا، ریسک پروژه را به‌شدت افزایش می‌دهد. بهتر است سامانه در پنج فاز پیاده‌سازی شود، به‌گونه‌ای که هر فاز خروجی قابل استفاده و قابل آزمایش داشته باشد. این رویکرد Incremental به شما اجازه می‌دهد در هر فاز، ارزشی به دفتر ببخشید و بازخورد واقعی کاربران را برای فاز بعدی جمع‌آوری کنید."))
    
    story.append(Paragraph(fa("فاز ۱: شناخت دیتابیس نمونه (هفته ۱-۲)"), style_h2))
    story.append(P("در این فاز، هدف اصلی این است که قبل از هر گونه توسعه، یک شرکت نمونه و یک فایل اکسل واقعی انتخاب شود و ساختار دیتابیس آن به‌طور کامل شناخته شود. این فاز شامل: انتخاب یک شرکت با نرم‌افزار همکاران، یک شرکت با نرم‌افزار سپیدار، و یک شرکت با فایل اکسل، بررسی ساختار جداول اسناد در هر دیتابیس، شناسایی کلیدهای اصلی و فیلدهای مهم، تعیین روش اتصال (مستقیم یا API)، و نوشتن یک اسکریپت آزمایشی برای خواندن چند سند. خروجی این فاز یک سند فنی است که به‌عنوان ورودی فاز بعد استفاده می‌شود. مدت زمان: ۲ هفته. ریسک: اگر ساختار دیتابیس نرم‌افزارهای مختلف به‌طور قابل توجهی متفاوت باشد، ممکن است نیاز به Adapter‌های بیشتری باشد."))
    
    story.append(Paragraph(fa("فاز ۲: نسخه اولیه مدیریت کار (هفته ۳-۶)"), style_h2))
    story.append(P("در این فاز، هسته پنل وب و مدیریت تسک ساخته می‌شود. شامل: احراز هویت کاربران، تعریف نقش‌ها (مدیر، مدیرعامل، کارمند)، تعریف شرکت‌ها و کارمندان، تخصیص تسک، چک‌لیست مراحل، پیگیری پیشرفت، آپلود فایل اکسل (بدون کنترل هوشمند)، و اعلان‌های پایه. در این فاز، سامانه هنوز راستی‌آزمایی هوشمند انجام نمی‌دهد اما کارمندان می‌توانند تسک‌ها را مدیریت کنند. این نسخه به‌تنهایی ارزش دارد و می‌تواند جایگزین روش‌های دستی شود. مدت زمان: ۴ هفته. خروجی: نسخه قابل استفاده دفتر برای مدیریت تسک."))
    
    story.append(Paragraph(fa("فاز ۳: موتور کنترل هوشمند اکسل (هفته ۷-۱۰)"), style_h2))
    story.append(P("این فاز قلب متمایزکننده سامانه است. شامل: پیاده‌سازی ۹ مرحله کنترل، ساخت Adapter‌های SQL Server و Excel، پیاده‌سازی مدل داده استاندارد، تولید گزارش مغایرت، رابط کاربری مدیر برای مشاهده گزارش‌ها، تأیید یا رد گزارش. در پایان این فاز، سامانه می‌تواند فایل اکسل را راستی‌آزمایی کند. مدت زمان: ۴ هفته. خروجی: نسخه با کنترل کامل اسناد برای یک شرکت نمونه."))
    
    story.append(Paragraph(fa("فاز ۴: اجرای آزمایشی (هفته ۱۱-۱۳)"), style_h2))
    story.append(P("سامانه روی دو یا سه شرکت با کارمندان واقعی استفاده می‌شود. هدف: مقایسه نتایج کنترل با بررسی دستی، شناسایی خطاهای موتور کنترل، تنظیم قواعد تکراری، و جمع‌آوری بازخورد کاربران. این فاز نباید حذف شود؛ حتی اگر فاز قبلی موفق به نظر برسد، اجرای آزمایشی روی داده‌های واقعی معمولاً چندین مورد ناهماهنگی آشکار می‌کند. مدت زمان: ۳ هفته. خروجی: نسخه پایدار قابل اعتماد."))
    
    story.append(Paragraph(fa("فاز ۵: توسعه و خودکارسازی (هفته ۱۴+)"), style_h2))
    story.append(P("در این فاز، قابلیت‌های پیشرفته اضافه می‌شوند: سایر Adapter‌ها برای نرم‌افزارهای دیگر، اتصال به دستگاه حضور و غیاب، مرخصی و درخواست‌های پیشرفته، گزارش ارزیابی پرسنل، داشبورد مدیریتی کامل، دریافت خودکار ریز اسناد زمان‌بندی‌شده، و API برای اتصال ابزارهای خارجی. این فاز باز است و بر اساس نیازهای واقعی دفتر ادامه می‌یابد. مدت زمان: ادامه‌دار."))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(fa("۱۱.۱ جدول خلاصه فازها"), style_h2))
    
    phase_data = [
        ["فاز", "مدت", "خروجی اصلی", "ریسک"],
        ["۱. شناخت دیتابیس نمونه", "۲ هفته", "سند فنی ساختار دیتابیس", "تفاوت ساختار نرم‌افزارها"],
        ["۲. نسخه اولیه مدیریت کار", "۴ هفته", "پنل وب + مدیریت تسک", "پذیرش کاربران"],
        ["۳. موتور کنترل هوشمند", "۴ هفته", "کنترل کامل اسناد", "پیچیدگی منطق کنترل"],
        ["۴. اجرای آزمایشی", "۳ هفته", "نسخه پایدار", "خطاهای پنهان در داده واقعی"],
        ["۵. توسعه و خودکارسازی", "ادامه‌دار", "قابلیت‌های پیشرفته", "اولویت‌بندی"],
        ["مجموع تا MVP", "۱۳ هفته", "نسخه قابل استفاده", "—"],
    ]
    col_w_ph = [4.5*cm, 2*cm, 5.5*cm, 5*cm]
    factor = CONTENT_W / sum(col_w_ph)
    col_w_ph = [w * factor for w in col_w_ph]
    story.append(make_table(phase_data, col_widths=col_w_ph))
    story.append(Spacer(1, 10))
    
    story.append(callout("نکته مهم: فاز ۱ (شناخت دیتابیس) نباید حذف شود. حتی اگر تجربه شما با نرم‌افزارهای همکاران و سپیدار زیاد است، ساختار دیتابیس این نرم‌افزارها در نسخه‌های مختلف متفاوت است. بدون این شناخت دقیق، Adapter‌ها در فاز ۳ به خطاهای ساختاری روبه‌رو می‌شوند.", 'warn'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 12 ============================
    story.append(Paragraph(fa("فصل ۱۲: تحلیل هزینه، زمان و توصیه استقرار"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این فصل، تحلیل هزینه و زمان پیاده‌سازی سامانه، انتخاب پشته فنی، و گزینه‌های استقرار (On-Premise، Cloud خصوصی ایران، Cloud عمومی) بررسی می‌شود. هدف این است که شما بتوانید بر اساس بودجه و شرایط دفتر، تصمیم آگاهانه بگیرید."))
    
    story.append(Paragraph(fa("۱۲.۱ برآورد هزینه"), style_h2))
    story.append(P("هزینه کل پروژه شامل سه بخش است: هزینه توسعه اولیه، هزینه زیرساخت (سرور و دیتابیس)، و هزینه نگهداری و پشتیبانی ماهانه. جدول زیر برآوردی برای یک تیم توسعه ایرانی با نرخ ساعت ۲۵۰ هزار تومان است."))
    
    cost_data = [
        ["بخش", "توضیح", "هزینه برآوردی (تومان)"],
        ["تحلیل و طراحی", "۲ هفته، تحلیل‌گر + معمار", "۲۰-۳۰ میلیون"],
        ["توسعه فاز ۲ (پنل وب)", "۴ هفته، ۲ توسعه‌دهنده", "۵۰-۷۰ میلیون"],
        ["توسعه فاز ۳ (موتور کنترل)", "۴ هفته، ۲ توسعه‌دهنده + کارشناس حسابداری", "۶۰-۸۰ میلیون"],
        ["اجرای آزمایشی و رفع باگ", "۳ هفته", "۲۰-۳۰ میلیون"],
        ["زیرساخت سال اول (سرور VPS)", "VPS ۸GB RAM، ۲۰۰GB SSD", "۶-۱۰ میلیون"],
        ["نام دامنه و گواهی SSL", "سالانه", "۱-۲ میلیون"],
        ["پشتیبانی ماهانه (سال اول)", "۲۰٪ هزینه توسعه، گزینه‌ای", "۲۰-۳۰ میلیون در سال"],
        ["مجموع سال اول (بدون پشتیبانی)", "—", "۱۵۷-۲۱۲ میلیون"],
        ["مجموع سال اول (با پشتیبانی)", "—", "۱۷۷-۲۴۲ میلیون"],
    ]
    col_w_cost = [4.5*cm, 6.5*cm, 5*cm]
    factor = CONTENT_W / sum(col_w_cost)
    col_w_cost = [w * factor for w in col_w_cost]
    story.append(make_table(cost_data, col_widths=col_w_cost))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۱۲.۲ مقایسه با هزینه ابزار آماده"), style_h2))
    story.append(P("اگر بخواهید از یک ابزار آماده خارجی مانند Karbon استفاده کنید، هزینه ماهانه برای ۵ کاربر بین ۳۰۰ تا ۴۵۰ دلار است. در سه سال، این رقم به ۱۰٬۸۰۰ تا ۱۶٬۲۰۰ دلار می‌رسد (معادل ۶۰۰ تا ۹۰۰ میلیون تومان با نرخ فعلی). این رقم تقریباً سه برابر هزینه ساخت سامانه اختصاصی است، و این در حالی است که ابزار آماده نیازمندی‌های اصلی شما (کنترل هوشمند اسناد، اتصال به دیتابیس‌های ایرانی) را پوشش نمی‌دهد. به‌علاوه، ابزار آماده هرگز با نیازهای خاص شما رشد نمی‌کند و شما به‌صورت دائم به‌صلب یا محدودیت‌های آن روبه‌رو خواهید بود."))
    
    story.append(Paragraph(fa("۱۲.۳ پشته فنی پیشنهادی"), style_h2))
    story.append(P("پشته فنی پیشنهادی بر اساس سه معیار انتخاب شده: بلوغ و پشتیبانی گسترده جامعه، در دسترس بودن نیروی متخصص در ایران، و تناسب با نوع کارکرد. جدول زیر پشته پیشنهادی را نشان می‌دهد."))
    
    stack_data = [
        ["لایه", "فناوری", "دلیل انتخاب"],
        ["Frontend", "Next.js 14 + React + TypeScript + Tailwind", "محبوب، مستندات فراوان، سئو و SSR قوی، نیروی متخصص"],
        ["Backend API", "Python + FastAPI", "سریع، توسعه آسان، کتابخانه‌های فراوان داده"],
        ["دیتابیس اصلی", "PostgreSQL 15+", "قوی، Open Source، پشتیبانی JSON، فول‌تکست سرچ"],
        ["Adapter Layer", "Python + SQLAlchemy + pyodbc + openpyxl", "اتصال به SQL Server و اکسل"],
        ["Authentication", "JWT + NextAuth.js", "محبوب، امن، پشتیبانی OAuth"],
        ["Message Queue", "Redis + RQ (ساده) یا Celery (پیشرفته)", "پردازش غیرهمزمان فایل‌های اکسل"],
        ["File Storage", "محلی + S3-compatible (MinIO)", "ذخیره فایل‌های اکسل با نسخه‌بندی"],
        ["Monitoring", "Sentry + Prometheus + Grafana", "رصد خطاها و عملکرد"],
        ["Deployment", "Docker + Docker Compose (اولیه)، Kubernetes (پیشرفته)", "استقرار ساده و قابل تکرار"],
        ["CI/CD", "GitHub Actions یا GitLab CI", "خودکارسازی تست و استقرار"],
    ]
    col_w_stack = [3.5*cm, 5*cm, 7.5*cm]
    factor = CONTENT_W / sum(col_w_stack)
    col_w_stack = [w * factor for w in col_w_stack]
    story.append(make_table(stack_data, col_widths=col_w_stack))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph(fa("۱۲.۴ گزینه‌های استقرار"), style_h2))
    story.append(P("سه گزینه برای استقرار سامانه وجود دارد که هر کدام مزایا و معایب خود را دارند. انتخاب گزینه به شرایط فنی، بودجه و میزان حساسیت داده‌ها بستگی دارد."))
    
    deploy_data = [
        ["گزینه", "مزایا", "معایب", "هزینه ماهانه تقریبی"],
        ["On-Premise (سرور دفتر)", "کنترل کامل داده، عدم وابستگی به اینترنت، امنیت فیزیکی", "نیاز به نگهداری سخت‌افزاری، پشتیبان‌گیری دستی، عدم دسترسی راه‌دور", "هزینه اولیه سخت‌افزار + برق"],
        ["Cloud خصوصی ایران (مثل لیارا، پارس‌پک)", "دسترسی راه‌دور، پشتیبان‌گیری، مقرر بودن ایران", "وابستگی به ارائه‌دهنده، ممکن است گران باشد", "۵۰۰-۲۰۰۰ هزار تومان"],
        ["Cloud عمومی (AWS/Hetzner)", "ارزان، مقیاس‌پذیر، خدمات فراوان", "تحریم‌پذیر، نگرانی حریم خصوصی داده", "۲۰۰-۸۰۰ هزار تومان (با VPN)"],
    ]
    col_w_dep = [3.5*cm, 4.5*cm, 4.5*cm, 3.5*cm]
    factor = CONTENT_W / sum(col_w_dep)
    col_w_dep = [w * factor for w in col_w_dep]
    story.append(make_table(deploy_data, col_widths=col_w_dep))
    story.append(Spacer(1, 8))
    
    story.append(callout("توصیه: برای دفتر شما، گزینه Cloud خصوصی ایران (مثل لیارا یا پارس‌پک) بهترین تعادل بین هزینه، راحتی و مقررات ایران را ارائه می‌دهد. هزینه ماهانه ۵۰۰ تا ۲۰۰۰ هزار تومان برای VPS با ۸ گیگابایت RAM و ۲۰۰ گیگابایت SSD کافی است.", 'success'))
    
    story.append(PageBreak())
    
    # ============================ CHAPTER 13 ============================
    story.append(Paragraph(fa("فصل ۱۳: جمع‌بندی و توصیه‌های نهایی"), style_h1))
    story.append(hbar())
    story.append(Spacer(1, 8))
    
    story.append(P("در این گزارش، نیازهای دفتر حسابداری شما را به‌طور کامل بررسی کردیم: نرم‌افزارهای آماده موجود در بازار جهانی و ایرانی، چارچوب ارزیابی پرسنل، معماری چندپایگاه‌داده با Adapter Pattern، الگوی اکسل اسناد، موتور کنترل هوشمند، و نقشه راه پیاده‌سازی فازبندی شده. در این فصل پایانی، توصیه‌های نهایی و قدم‌های بعدی را به‌صورت عملی ارائه می‌دهیم."))
    
    story.append(Paragraph(fa("۱۳.۱ توصیه نهایی"), style_h2))
    story.append(P("توصیه نهایی ما ساخت یک سامانه اختصاصی با معماری ترکیبی است. این انتخاب بر اساس چهار دلیل اصلی است. اول، هیچ نرم‌افزار آماده‌ای در بازار جهانی یا ایرانی، تمام نیازهای شما را به‌صورت یکپارچه پوشش نمی‌دهد، به‌ویژه موتور کنترل هوشمند اسناد و اتصال به دیتابیس‌های متنوع نرم‌افزارهای ایرانی. دوم، هزینه ساخت اختصاصی در یک دوره سه‌ساله تقریباً یک‌سوم هزینه اشتراک ابزار آماده است. سوم، سامانه اختصاصی به‌صورت کامل با نیازهای شما رشد می‌کند و شما را به‌صلب یا محدودیت ابزار خارجی محدود نمی‌کند. چهارم، داده‌های حساس دفتر شما (اسناد ۵۰ شرکت) در ایران نگه‌داری می‌شود و از ریسک تحریم یا قطع دسترسی به ابر خارجی در امان است."))
    
    story.append(Paragraph(fa("۱۳.۲ قدم‌های بعدی فوری (هفته اول)"), style_h2))
    story.extend(numbered_list([
        "انتخاب یک شرکت نمونه با نرم‌افزار همکاران و یک شرکت با نرم‌افزار سپیدار برای فاز ۱.",
        "تهیه یک فایل اکسل واقعی از اسناد یکی از شرکت‌ها برای آزمون موتور کنترل.",
        "اخذ دسترسی Read-Only به دیتابیس SQL Server شرکت‌های نمونه (از نرم‌افزارکار یا مدیر IT شرکت).",
        "مشاوره با یک تیم توسعه ایرانی برای دریافت پیشنهاد قیمت و زمان دقیق (با این گزارش به‌عنوان RFP).",
        "تعیین بودجه نهایی و زمان‌بندی پروژه بر اساس پیشنهاد تیم توسعه.",
    ]))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("۱۳.۳ اقدامات میان‌مدت (۳ ماه)"), style_h2))
    story.extend(numbered_list([
        "تأیید تیم توسعه و امضای قرارداد شامل تعرفه‌های روشن برای فازهای ۲ تا ۵.",
        "شروع فاز ۱ (شناخت دیتابیس) و تولید سند فنی ساختار.",
        "طراحی دقیق مدل داده استاندارد و بررسی با تیم توسعه.",
        "آغاز فاز ۲ (پنل وب) و آموزش کارمندان به‌صورت موازی با توسعه.",
        "تعریف نقش‌ها و سطوح دسترسی به‌صورت رسمی قبل از راه‌اندازی.",
    ]))
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(fa("۱۳.۴ چک‌لیست آماده‌سازی برای شروع پروژه"), style_h2))
    story.extend(bullet_list([
        "فهرست کامل ۵۰ شرکت با نوع نرم‌افزار حسابداری و نسخه آن.",
        "اطلاعات تماس نرم‌افزارکار هر شرکت برای همکاری در دسترسی Read-Only.",
        "نمونه فایل اکسل از ۳ شرکت با ساختار متفاوت برای آزمون.",
        "فهرست انواع فعالیت‌های حسابداری که در دفتر انجام می‌شود (برای نوع فعالیت تسک).",
        "تعریف اولیه پنج شاخص KPI و وزن هر کدام (بر اساس این گزارش).",
        "تعیین نقش‌ها: مدیر، مدیرعامل، ۵ کارمند، مسئول کنترل.",
        "تصمیم در مورد گزینه استقرار (پیشنهاد: Cloud خصوصی ایران).",
        "بودجه اولیه و تعیین حداکثر هزینه قابل قبول.",
        "تیم‌سازی: انتخاب تیم توسعه یا برون‌سپاری به یک شرکت توسعه.",
        "زمان‌بندی: تعیین تاریخ شروع و تاریخ تحویل MVP.",
    ]))
    
    story.append(Spacer(1, 10))
    
    story.append(callout("پیام پایانی: این پروژه یک سرمایه‌گذاری راهبردی برای دفتر شماست. اگر به‌درستی پیاده‌سازی شود، علاوه بر کنترل کامل عملیات دفتر، مزیت رقابتی قابل توجهی به شما می‌دهد - توانایی پذیرش شرکت‌های بیشتر بدون افزایش متناسب کارکنان، کاهش خطاهای حسابداری، و اعتبار بالاتر در بازار. با این حال، موفقیت پروژه به‌شدت به انتخاب تیم توسعه مناسب و پایبندی به نقشه راه فازبندی شده وابسته است.", 'success'))
    
    story.append(Spacer(1, 20))
    
    # Final signature line
    final_para = ParagraphStyle(
        'Final', parent=style_body,
        fontName='Vazirmatn', fontSize=10, leading=16,
        alignment=TA_CENTER, textColor=C_TEXT_MUTED,
    )
    story.append(Paragraph(fa("پایان گزارش راهبردی"), final_para))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated: {output_path}")

if __name__ == '__main__':
    output = '/home/z/my-project/download/سامانه_مدیریت_دفتر_حسابداری_گزارش_راهبردی.pdf'
    build_pdf_v2(output)
    print("Build complete!")
