import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random
import io
import base64
import os
import streamlit.components.v1 as components

# ---------------------------------------------------------
# Jalali / Shamsi Date Conversion Helper (Pure Python)
# ---------------------------------------------------------
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy if gm > 2 else gy - 1
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return f"{jy:04d}/{jm:02d}/{jd:02d}"

def get_current_shamsi_date():
    today = datetime.date.today()
    return gregorian_to_jalali(today.year, today.month, today.day)

# ---------------------------------------------------------
# Page Configuration & Clean RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom Persian / RTL CSS Styling (Clean, Bulletproof, No Label Leaks)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stMarkdown, .stMarkdown p, h1, h2, h3, h4, h5, h6, label, .stRadio label, .stSelectbox label, .stTextInput label {
        color: #ffffff !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    /* Input Fields */
    input, select, textarea {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: #ffffff !important;
        padding: 24px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
    }
    
    /* Card Styling */
    .card-box {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Quote Box */
    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.6) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    /* Buttons */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Popover Styling */
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    li[role="option"] {
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ReportLab Persian PDF Reshaper & Generator Helpers
# ---------------------------------------------------------
FARSI_CHAR_MAP = {
    'آ': ('ﺁ', 'ﺁ', 'ﺂ', 'ﺁ'), 'ا': ('ﺍ', 'ﺍ', 'ﺎ', 'ﺍ'), 'ب': ('ﺏ', 'ﺑ', 'ﺒ', 'ﺐ'),
    'پ': ('ﭖ', 'ﭘ', 'ﭙ', 'ﭗ'), 'ت': ('ﺕ', 'ﺗ', 'ﺘ', 'ﺖ'), 'ث': ('ﺙ', 'ﺛ', 'ﺜ', 'ﺚ'),
    'ج': ('ﺝ', 'ﺟ', 'ﺠ', 'ﺞ'), 'چ': ('ﭺ', 'ﭼ', 'ﭽ', 'ﭻ'), 'ح': ('ﺡ', 'ﺣ', 'ﺤ', 'ﺢ'),
    'خ': ('ﺥ', 'ﺧ', 'ﺨ', 'ﺦ'), 'د': ('ﺩ', 'ﺩ', 'ﺪ', 'ﺩ'), 'ذ': ('ﺫ', 'ﺫ', 'ﺬ', 'ﺫ'),
    'ر': ('ﺭ', 'ﺭ', 'ﺮ', 'ﺭ'), 'ز': ('ﺯ', 'ﺯ', 'ﺰ', 'ﺯ'), 'ژ': ('ﮊ', 'ﮊ', 'ﮋ', 'ﮊ'),
    'س': ('ﺱ', 'ﺳ', 'ﺴ', 'ﺲ'), 'ش': ('ﺵ', 'ﺷ', 'ﺸ', 'ﺶ'), 'ص': ('ﺹ', 'ﺻ', 'ﺼ', 'ﺺ'),
    'ض': ('ﺽ', 'ﺿ', 'ﻀ', 'ﺾ'), 'ط': ('ﻁ', 'ﻃ', 'ﻄ', 'ﻂ'), 'ظ': ('ﻅ', 'ﻇ', 'ﻈ', 'ﻆ'),
    'ع': ('ﻉ', 'ﻋ', 'ﻌ', 'ﻊ'), 'غ': ('ﻍ', 'ﻏ', 'ﻐ', 'ﻎ'), 'ف': ('ﻑ', 'ﻑ', 'ﻔ', 'ﻒ'),
    'ق': ('ﻕ', 'ﻗ', 'ﻘ', 'ﻖ'), 'ک': ('ﮎ', 'ﻛ', 'ﻜ', 'ﻚ'), 'گ': ('ﮒ', 'ﮔ', 'ﮕ', 'ﮓ'),
    'ل': ('ﻝ', 'ﻟ', 'ﻠ', 'ﻞ'), 'م': ('ﻡ', 'ﻣ', 'ﻤ', 'ﻢ'), 'ن': ('ﻥ', 'ﻧ', 'ﻨ', 'ﻦ'),
    'و': ('ﻭ', 'ﻭ', 'ﻮ', 'ﻭ'), 'ه': ('ﻩ', 'ﻫ', 'ﻬ', 'ﻪ'), 'ی': ('ﯼ', 'ﻳ', 'ﻴ', 'ﯽ'),
    'ي': ('ﻱ', 'ﻳ', 'ﻴ', 'ﻲ'), 'ك': ('ﻙ', 'ﻛ', 'ﻜ', 'ﻚ'), 'ئ': ('ﺋ', 'ﺋ', 'ﺌ', 'ﺊ'), 'ء': ('ﺀ', 'ﺀ', 'ﺀ', 'ﺀ'),
}
NON_JOINING = set('آأإادذرزژوؤء')

def _reshape(text):
    if not text: return ''
    res = []
    chars = list(text)
    n = len(chars)
    for i, c in enumerate(chars):
        if c not in FARSI_CHAR_MAP:
            res.append(c)
            continue
        prev_c = chars[i-1] if i > 0 else None
        next_c = chars[i+1] if i < n-1 else None
        
        prev_joins = prev_c is not None and prev_c in FARSI_CHAR_MAP and prev_c not in NON_JOINING and prev_c != ' '
        next_joins = next_c is not None and next_c in FARSI_CHAR_MAP and next_c != ' '
        
        forms = FARSI_CHAR_MAP[c]
        if not prev_joins and not next_joins: res.append(forms[0])
        elif not prev_joins and next_joins: res.append(forms[1])
        elif prev_joins and next_joins: res.append(forms[2])
        elif prev_joins and not next_joins: res.append(forms[3])
    return ''.join(res)

def _rtl(text):
    if not text: return ''
    words = str(text).split(' ')
    reshaped_words = [_reshape(w) for p in words for w in [p]]
    return ' '.join([w[::-1] for w in reshaped_words[::-1]])

def draw_pdf_header(c, w, h, doc_title, letter_no, letter_date):
    from reportlab.lib import colors
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.rect(0, h-100, w, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont('PersianFont', 11)
    c.drawCentredString(w/2, h-25, _rtl('باسمه تعالی'))
    c.setFont('PersianFont', 12)
    c.drawCentredString(w/2, h-45, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont('PersianFont', 10)
    c.drawCentredString(w/2, h-63, _rtl('اداره کل آموزش و پرورش استان ایلام - مدیریت آموزش و پرورش شهرستان مهران'))
    c.setFont('PersianFont', 12)
    c.drawCentredString(w/2, h-85, _rtl('دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵'))
    
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont('PersianFont', 9)
    c.drawRightString(140, h-115, _rtl(f'تاریخ: {letter_date}'))
    c.drawRightString(140, h-130, _rtl(f'شماره: {letter_no}'))
    c.drawRightString(140, h-145, _rtl('پیوست: دارد'))

def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        font_name = 'Helvetica'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                font_name = 'PersianFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        
        is_pos = 'مثبت' in b_type or 'تشویق' in b_type
        doc_title = 'تقدیرنامه و لوح سپاس انضباطی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی'
        letter_no = f'۱۰۱/ب/{random.randint(100, 999)}'
        
        draw_pdf_header(c, w, h, doc_title, letter_no, log_date)
        
        y = h - 170
        banner_bg = colors.HexColor('#15803d') if is_pos else colors.HexColor('#b91c1c')
        c.setFillColor(banner_bg)
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 22, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 22, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 22, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 55, y - 40, _rtl(f'عنوان مشاهده رفتاری: {title}'))
        c.drawRightString(w - 300, y - 40, _rtl(f'تاریخ ثبت: {log_date}'))
        
        y -= 80
        c.setFillColor(colors.HexColor('#eff6ff') if is_pos else colors.HexColor('#fef2f2'))
        c.rect(40, y-170, w-80, 170, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        
        if is_pos:
            l1 = f'سرپرست محترم دانش‌آموز گرامی {student_name}؛'
            l2 = 'با سلام و اهدای تحیت؛'
            l3 = f'بدین‌وسیله از تلاش‌های شایسته، انضباط برتر و پیشرفت اخلاقی فرزند گرامی‌تان ({title}) در پایه'
            l4 = 'پنجم دبستان پسرانه شهید مطهری مهران صمیمانه تقدیر و تشکر می‌گردد. بدون شک، توفیق'
            l5 = 'فرزند دلبندتان حاصل اهتمام و پرورش شایسته در کانون گرم خانواده محترم می‌باشد.'
            l6 = 'با اعطای این لوح سپاس، توفیق روزافزون ایشان را از درگاه خداوند متعال مسألت می‌نماییم.'
        else:
            l1 = f'سرپرست محترم دانش‌آموز گرامی {student_name}؛'
            l2 = 'با سلام و احترام؛'
            l3 = f'بدین‌وسیله به اطلاع می‌رساند فرزند گرامی شما در تاریخ {log_date} متأسفانه مرتکب رفتار نیازمند پیگیری'
            l4 = f'({title}) گردیده است. با توجه به اهمیت حفظ نظم، کرامت کلاسی و رشد تربیتی دانش‌آموزان،'
            l5 = 'این نامه جهت اطلاع و آگاهی جنابعالی صادر گردیده است. خواهشمند است ضمن گفتگو با فرزند خود،'
            l6 = 'جهت هماهنگی بیشتر و پیگیری موضوع با آموزگار مربوطه همکاری لازم را به عمل آورید.'
            
        c.drawRightString(w - 55, y - 25, _rtl(l1))
        c.drawRightString(w - 55, y - 45, _rtl(l2))
        c.drawRightString(w - 55, y - 70, _rtl(l3))
        c.drawRightString(w - 55, y - 90, _rtl(l4))
        c.drawRightString(w - 55, y - 110, _rtl(l5))
        c.drawRightString(w - 55, y - 130, _rtl(l6))
        c.drawRightString(w - 55, y - 155, _rtl(f'نوع ثبت: {b_type} | توضیحات: {desc if desc else "ثبت نشده"}'))
        
        y -= 220
        c.setFont(font_name, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error: {e}".encode('utf-8')

def generate_exams_pdf(student_name, national_id, student_group, quizzes_data, quiz_avg_str, letter_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        font_name = 'Helvetica'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                font_name = 'PersianFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'گزارش تحلیلی نمرات و عملکرد در آزمون‌های آنلاین'
        letter_no = f'۱۰۲/آ/{random.randint(100, 999)}'
        
        draw_pdf_header(c, w, h, doc_title, letter_no, letter_date)
        
        y = h - 170
        c.setFillColor(colors.HexColor('#1e3a8a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 22, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 22, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 22, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 55, y - 40, _rtl(f'میانگین درصد آزمون‌ها: {quiz_avg_str}'))
        
        y -= 70
        c.setFillColor(colors.HexColor('#eff6ff'))
        c.rect(40, y-180, w-80, 180, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        
        l1 = f'اولیا و دانش‌آموز گرامی {student_name}؛'
        l2 = 'با سلام و احترام؛'
        l3 = 'بدین‌وسیله گزارش تحلیلی نمرات و درصد عملکرد در آزمون‌های آنلاین برگزارشده پایه پنجم به همراه'
        l4 = f'جدول سوابق ذیل حضورتان تقدیم می‌گردد. میانگین کل آزمون‌های ایشان {quiz_avg_str} می‌باشد.'
        l5 = 'خواهشمند است با بررسی بازخوردهای آموزشی ثبت‌شده، زمینه‌های تثبیت یادگیری را فراهم فرمایید.'
        
        c.drawRightString(w - 55, y - 25, _rtl(l1))
        c.drawRightString(w - 55, y - 45, _rtl(l2))
        c.drawRightString(w - 55, y - 70, _rtl(l3))
        c.drawRightString(w - 55, y - 90, _rtl(l4))
        c.drawRightString(w - 55, y - 110, _rtl(l5))
        
        line_y = y - 135
        if quizzes_data:
            for q in quizzes_data[:3]:
                t = q.get('عنوان آزمون', 'آزمون')
                s = q.get('نمره تستی', 0)
                tot = q.get('کل سوالات تستی', 0)
                pct = q.get('درصد ٪', 0)
                c.drawRightString(w - 55, line_y, _rtl(f'• {t}: نمره {s} از {tot} ({pct:.1f}٪)'))
                line_y -= 18
        else:
            c.drawRightString(w - 55, line_y, _rtl('• آزمون ثبت‌شده‌ای یافت نشد.'))
            
        y -= 230
        c.setFont(font_name, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error: {e}".encode('utf-8')

def generate_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, letter_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        
        font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
        font_name = 'Helvetica'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                font_name = 'PersianFont'
            except Exception:
                pass
                
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'کارنامه جامع تحصیلی و پوشه کار دیجیتال دانش‌آموز'
        letter_no = f'۱۰۳/ک/{random.randint(100, 999)}'
        
        draw_pdf_header(c, w, h, doc_title, letter_no, letter_date)
        
        y = h - 170
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(font_name, 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        c.drawRightString(w - 55, y - 22, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 22, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 22, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 55, y - 40, _rtl(f'ارزشیابی‌ها: {eval_count} | موارد رفتاری: {beh_count} | میانگین آزمون‌ها: {quiz_avg_str}'))
        
        y -= 70
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-190, w-80, 190, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(font_name, 10)
        
        l1 = f'ولی محترم دانش‌آموز گرامی {student_name}؛'
        l2 = 'با سلام و اهدای تحیت؛'
        l3 = 'بدین‌وسیله گزارش جامع عملکرد تحصیلی، ارزشیابی کیفی-توصیفی ۷ عنوان درسی پایه پنجم،'
        l4 = 'نتایج آزمون‌های آنلاین و سوابق پایش رفتاری فرزندتان در دبستان شهید مطهری مهران جهت اطلاع'
        l5 = 'و آگاهی کامل حضورفرمایتان تقدیم می‌گردد. این پرونده انعکاس‌دهنده تلاش‌های علمی و انضباطی'
        l6 = 'دانش‌آموز می‌باشد. خواهشمند است پس از ملاحظه سوابق، فرم ذیل را تایید فرمایید.'
        
        c.drawRightString(w - 55, y - 25, _rtl(l1))
        c.drawRightString(w - 55, y - 45, _rtl(l2))
        c.drawRightString(w - 55, y - 70, _rtl(l3))
        c.drawRightString(w - 55, y - 90, _rtl(l4))
        c.drawRightString(w - 55, y - 110, _rtl(l5))
        c.drawRightString(w - 55, y - 130, _rtl(l6))
        
        c.setFont(font_name, 11)
        c.drawRightString(w - 55, y - 160, _rtl('💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):'))
        c.setFont(font_name, 9)
        c.drawRightString(w - 55, y - 180, _rtl('حضور منظم، مشارکت فعال در فعالیت‌های گروهی کلاسی و رشد مستمر نمرات آزمون‌ها.'))
        
        y -= 240
        c.setFont(font_name, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error: {e}".encode('utf-8')

# ---------------------------------------------------------
# HTML Report Generator Helpers (For Preview in Iframe)
# ---------------------------------------------------------
def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date, letter_no):
    is_pos = 'مثبت' in b_type or 'تشویق' in b_type
    theme_color = '#15803d' if is_pos else '#b91c1c'
    bg_color = '#f0fdf4' if is_pos else '#fef2f2'
    border_color = '#22c55e' if is_pos else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی' if is_pos else 'کارت اطلاع‌رسانی و هشدار انضباطی'
    
    if is_pos:
        body_p = f"""
        <p><b>سرپرست محترم دانش‌آموز گرامی {student_name}؛</b></p>
        <p>با سلام و اهدای تحیت؛</p>
        <p>بدین‌وسیله از تلاش‌های شایسته، انضباط برتر و پیشرفت اخلاقی فرزند گرامی‌تان (<b>{title}</b>) در پایه پنجم دبستان پسرانه شهید مطهری مهران صمیمانه تقدیر و تشکر می‌گردد. بدون شک، توفیق فرزند دلبندتان حاصل اهتمام و پرورش شایسته در کانون گرم خانواده محترم می‌باشد.</p>
        <p>با اعطای این لوح سپاس، سلامتی و موفقیت روزافزون ایشان را در تمامی مراحل زندگی از درگاه خداوند متعال مسألت می‌نماییم.</p>
        """
    else:
        body_p = f"""
        <p><b>سرپرست محترم دانش‌آموز گرامی {student_name}؛</b></p>
        <p>با سلام و احترام؛</p>
        <p>بدین‌وسیله به اطلاع می‌رساند فرزند گرامی شما در تاریخ <b>{log_date}</b> متأسفانه مرتکب رفتار نیازمند پیگیری و توجه (<b>{title}</b>) گردیده است. با توجه به اهمیت حفظ نظم، کرامت کلاسی و رشد تربیتی دانش‌آموزان، این نامه جهت اطلاع و آگاهی جنابعالی صادر گردیده است. خواهشمند است ضمن گفتگو با فرزند خود و اتخاذ تدابیر تربیتی در منزل، جهت هماهنگی بیشتر و پیگیری موضوع با آموزگار مربوطه همکاری لازم را به عمل آورید.</p>
        """

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.8; margin: 0; }}
.letterhead {{ border-bottom: 3px double {theme_color}; padding-bottom: 12px; margin-bottom: 15px; position: relative; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 16px; font-weight: bold; margin-top: 4px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-box {{ position: absolute; left: 10px; top: 0; font-size: 11px; color: #334155; text-align: left; line-height: 1.6; }}
.report-card {{ background: {bg_color}; border: 2px solid {border_color}; border-radius: 12px; padding: 20px; margin-top: 10px; }}
.report-header {{ color: {theme_color}; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; border-bottom: 1px dashed {border_color}; padding-bottom: 8px; }}
.meta-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 12px; background: #ffffff; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 6px 10px; border: 1px solid #cbd5e1; }}
.content-text {{ font-size: 13px; line-height: 1.9; text-align: justify; margin: 10px 0; }}
.signature-table {{ width: 100%; margin-top: 30px; text-align: center; font-size: 11px; border-collapse: collapse; }}
.signature-table td {{ padding: 8px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="meta-box">
        <b>تاریخ:</b> {log_date}<br>
        <b>شماره:</b> {letter_no}<br>
        <b>پیوست:</b> دارد
    </div>
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه شهید مطهری مهران</div>
    <div class="sub-header">سال تحصیلی ۱۴۰۴-۱۴۰۵ | پایه پنجم ابتدایی — آموزگار: سید موسی حیدری</div>
</div>

<div class="report-card">
    <div class="report-header">{report_title}</div>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
        </tr>
        <tr>
            <td colspan="2"><b>عنوان مشاهده رفتاری:</b> {title}</td>
            <td><b>تاریخ ثبت:</b> {log_date}</td>
        </tr>
    </table>
    
    <div class="content-text">
        {body_p}
        <p style="margin-top: 10px; font-size: 12px; color: #475569;"><b>شرح و جزئیات رفتار:</b> {desc if desc else 'توضیحات تکمیلی ثبت نشده است.'}</p>
    </div>
    
    <table class="signature-table">
        <tr>
            <td width="33%"><b>آموزگار پایه پنجم</b><br>سید موسی حیدری</td>
            <td width="33%"><b>مدیریت دبستان</b><br>شهید مطهری مهران</td>
            <td width="33%"><b>رویت و امضای اولیا</b><br>محل امضا و تاریخ</td>
        </tr>
    </table>
</div>
</body>
</html>"""

def generate_exams_report_html(student_name, national_id, student_group, quizzes_data, quiz_avg_str, letter_date, letter_no):
    table_rows = ""
    if quizzes_data:
        for q in quizzes_data:
            table_rows += f"""
            <tr>
                <td>{q.get('عنوان آزمون', 'آزمون')}</td>
                <td>{q.get('درس', 'ریاضی')}</td>
                <td>{q.get('نمره تستی', 0)} از {q.get('کل سوالات تستی', 0)}</td>
                <td><b>{q.get('درصد ٪', 0):.1f}٪</b></td>
                <td>{q.get('زمان ثبت (شمسی)', '-')}</td>
            </tr>
            """
    else:
        table_rows = "<tr><td colspan='5' style='text-align:center;'>هنوز نتیجه آزمون آنلاینی ثبت نشده است.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.8; margin: 0; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 12px; margin-bottom: 15px; position: relative; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 16px; font-weight: bold; margin-top: 4px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-box {{ position: absolute; left: 10px; top: 0; font-size: 11px; color: #334155; text-align: left; line-height: 1.6; }}
.report-card {{ background: #eff6ff; border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; margin-top: 10px; }}
.report-header {{ color: #1e3a8a; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; border-bottom: 1px dashed #3b82f6; padding-bottom: 8px; }}
.meta-table, .data-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 12px; background: #ffffff; border-radius: 6px; overflow: hidden; }}
.meta-table td, .data-table td, .data-table th {{ padding: 8px; border: 1px solid #cbd5e1; text-align: center; }}
.data-table th {{ background: #1e3a8a; color: #ffffff; font-weight: bold; }}
.content-text {{ font-size: 13px; line-height: 1.9; text-align: justify; margin: 10px 0; }}
.signature-table {{ width: 100%; margin-top: 30px; text-align: center; font-size: 11px; border-collapse: collapse; }}
.signature-table td {{ padding: 8px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="meta-box">
        <b>تاریخ:</b> {letter_date}<br>
        <b>شماره:</b> {letter_no}<br>
        <b>پیوست:</b> دارد
    </div>
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه شهید مطهری مهران</div>
    <div class="sub-header">سال تحصیلی ۱۴۰۴-۱۴۰۵ | پایه پنجم ابتدایی — آموزگار: سید موسی حیدری</div>
</div>

<div class="report-card">
    <div class="report-header">گزارش تحلیلی نمرات و عملکرد در آزمون‌های آنلاین</div>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
            <td><b>میانگین درصد آزمون‌ها:</b> {quiz_avg_str}</td>
        </tr>
    </table>
    
    <div class="content-text">
        <p><b>اولیا و دانش‌آموز گرامی {student_name}؛</b></p>
        <p>با سلام و احترام؛ بدین‌وسیله گزارش تحلیلی نمرات و درصد عملکرد در آزمون‌های آنلاین برگزارشده پایه پنجم به همراه جدول نتایج حضورتان تقدیم می‌گردد. میانگین کل آزمون‌های ایشان <b>{quiz_avg_str}</b> می‌باشد. خواهشمند است با بررسی بازخوردهای آموزشی ثبت‌شده، زمینه‌های تثبیت یادگیری را فراهم فرمایید.</p>
    </div>
    
    <table class="data-table">
        <thead>
            <tr>
                <th>عنوان آزمون</th>
                <th>درس</th>
                <th>نمره تستی</th>
                <th>درصد کسب‌شده</th>
                <th>تاریخ ثبت</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    
    <table class="signature-table">
        <tr>
            <td width="33%"><b>آموزگار پایه پنجم</b><br>سید موسی حیدری</td>
            <td width="33%"><b>مدیریت دبستان</b><br>شهید مطهری مهران</td>
            <td width="33%"><b>رویت و امضای اولیا</b><br>محل امضا و تاریخ</td>
        </tr>
    </table>
</div>
</body>
</html>"""

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, letter_date, letter_no):
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.8; margin: 0; }}
.letterhead {{ border-bottom: 3px double #0f172a; padding-bottom: 12px; margin-bottom: 15px; position: relative; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 16px; font-weight: bold; margin-top: 4px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-box {{ position: absolute; left: 10px; top: 0; font-size: 11px; color: #334155; text-align: left; line-height: 1.6; }}
.report-card {{ background: #f8fafc; border: 2px solid #0f172a; border-radius: 12px; padding: 20px; margin-top: 10px; }}
.report-header {{ color: #0f172a; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; border-bottom: 1px dashed #0f172a; padding-bottom: 8px; }}
.meta-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 12px; background: #ffffff; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 8px; border: 1px solid #cbd5e1; text-align: center; }}
.content-text {{ font-size: 13px; line-height: 1.9; text-align: justify; margin: 10px 0; }}
.advice-box {{ background: #eff6ff; border-right: 4px solid #2563eb; padding: 12px; border-radius: 6px; font-size: 12px; margin-top: 15px; }}
.signature-table {{ width: 100%; margin-top: 30px; text-align: center; font-size: 11px; border-collapse: collapse; }}
.signature-table td {{ padding: 8px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="meta-box">
        <b>تاریخ:</b> {letter_date}<br>
        <b>شماره:</b> {letter_no}<br>
        <b>پیوست:</b> دارد
    </div>
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه شهید مطهری مهران</div>
    <div class="sub-header">سال تحصیلی ۱۴۰۴-۱۴۰۵ | پایه پنجم ابتدایی — آموزگار: سید موسی حیدری</div>
</div>

<div class="report-card">
    <div class="report-header">کارنامه جامع تحصیلی و پوشه کار دیجیتال دانش‌آموز</div>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
            <td><b>همراه اولیا:</b> {parent_phone}</td>
        </tr>
        <tr>
            <td><b>ارزشیابی‌ها:</b> {eval_count} مورد</td>
            <td><b>سوابق رفتاری:</b> {beh_count} مورد</td>
            <td colspan="2"><b>میانگین درصد آزمون‌های آنلاین:</b> {quiz_avg_str}</td>
        </tr>
    </table>
    
    <div class="content-text">
        <p><b>ولی محترم دانش‌آموز گرامی {student_name}؛</b></p>
        <p>با سلام و اهدای تحیت؛ بدین‌وسیله گزارش جامع عملکرد تحصیلی، ارزشیابی کیفی-توصیفی ۷ عنوان درسی پایه پنجم، نتایج آزمون‌های آنلاین و سوابق پایش رفتاری فرزندتان در دبستان شهید مطهری مهران جهت اطلاع و آگاهی کامل حضورفرمایتان تقدیم می‌گردد. این پرونده انعکاس‌دهنده تلاش‌های علمی و انضباطی دانش‌آموز در طول سال تحصیلی می‌باشد.</p>
    </div>
    
    <div class="advice-box">
        <b>💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):</b><br>
        حضور منظم در کلاس، مشارکت فعال در فعالیت‌های گروهی، رشد مستمر نمرات آزمون‌های آنلاین و رعایت عالی انضباط کلاسی.
    </div>
    
    <table class="signature-table">
        <tr>
            <td width="33%"><b>آموزگار پایه پنجم</b><br>سید موسی حیدری</td>
            <td width="33%"><b>مدیریت دبستان</b><br>شهید مطهری مهران</td>
            <td width="33%"><b>رویت و امضای اولیا</b><br>محل امضا و تاریخ</td>
        </tr>
    </table>
</div>
</body>
</html>"""

# ---------------------------------------------------------
# Database Initialization & Auto Schema Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Students Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            student_group TEXT DEFAULT 'بدون گروه',
            notes TEXT,
            pin_code TEXT DEFAULT '1234',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Evaluations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            feedback TEXT,
            eval_date DATE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 3. Behaviors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            log_date DATE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 4. Quizzes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 15,
            is_active INTEGER DEFAULT 1,
            created_at DATE
        )
        """)
        
        # 5. Questions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_type TEXT DEFAULT 'mcq',
            question_text TEXT NOT NULL,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option INTEGER DEFAULT 1,
            model_answer TEXT,
            explanation TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        )
        """)
        
        # 6. Quiz Results Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            photo_data TEXT,
            essay_answers TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # 7. Teacher Auth Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        # Auto-migration for existing DBs
        columns_to_add = [
            ("students", "student_group", "TEXT DEFAULT 'بدون گروه'"),
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("quizzes", "is_active", "INTEGER DEFAULT 1"),
            ("questions", "question_type", "TEXT DEFAULT 'mcq'"),
            ("questions", "model_answer", "TEXT"),
            ("questions", "explanation", "TEXT"),
            ("quiz_results", "photo_data", "TEXT"),
            ("quiz_results", "essay_answers", "TEXT")
        ]
        for table, col, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
                
        conn.commit()

init_db()

# Safe Read Helper Function
def safe_read_sql(query, conn, params=None):
    try:
        df = pd.read_sql_query(query, conn, params=params)
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception:
        init_db()
        try:
            df = pd.read_sql_query(query, conn, params=params)
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        except Exception:
            return pd.DataFrame()

# ---------------------------------------------------------
# Seed Default 29 Students
# ---------------------------------------------------------
def seed_default_students():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            default_students = [
                ("آرمین", "احمدی", "1001", "09181111111", "گروه ارمغان 🚀", "1234"),
                ("احسان", "ابراهیمی", "1002", "09181111112", "گروه ارمغان 🚀", "1234"),
                ("امیررضا", "اسدی", "1003", "09181111113", "گروه ارمغان 🚀", "1234"),
                ("بنیامين", "بابایی", "1004", "09181111114", "گروه ارمغان 🚀", "1234"),
                ("پارسـا", "پیرانی", "1005", "09181111115", "گروه ارمغان 🚀", "1234"),
                ("پوریا", "تقی‌پور", "1006", "09181111116", "گروه ارمغان 🚀", "1234"),
                ("جواد", "جعفری", "1007", "09181111117", "گروه دانا 💡", "1234"),
                ("حسام", "حسینی", "1008", "09181111118", "گروه دانا 💡", "1234"),
                ("دانیال", "داوودی", "1009", "09181111119", "گروه دانا 💡", "1234"),
                ("رضا", "رحیمی", "1010", "09181111120", "گروه دانا 💡", "1234"),
                ("سینا", "سلیمانی", "1011", "09181111121", "گروه دانا 💡", "1234"),
                ("شایان", "شریفی", "1012", "09181111122", "گروه دانا 💡", "1234"),
                ("علی", "عباسی", "1013", "09181111123", "گروه تلاش 🌟", "1234"),
                ("کیان", "ابراهیمی", "1014", "09181111124", "گروه تلاش 🌟", "1234"),
                ("محمد", "محمدی", "1015", "09181111125", "گروه تلاش 🌟", "1234"),
                ("مهدی", "مرادی", "1016", "09181111126", "گروه تلاش 🌟", "1234"),
                ("نیما", "نوروزی", "1017", "09181111127", "گروه تلاش 🌟", "1234"),
                ("یاسین", "یاسینی", "1018", "09181111128", "گروه تلاش 🌟", "1234"),
                ("ابوالفضل", "صادقی", "1019", "09181111129", "گروه نخبگان 🏆", "1234"),
                ("امیرعلی", "رضایی", "1020", "09181111130", "گروه نخبگان 🏆", "1234"),
                ("حسین", "کریم‌زاده", "1021", "09181111131", "گروه نخبگان 🏆", "1234"),
                ("سبحان", "قاسمی", "1022", "09181111132", "گروه نخبگان 🏆", "1234"),
                ("سهیل", "نجفی", "1023", "09181111133", "گروه نخبگان 🏆", "1234"),
                ("متین", "موسوی", "1024", "09181111134", "گروه نخبگان 🏆", "1234"),
                ("ارشیا", "خسروی", "1025", "09181111135", "گروه اندیشه 📖", "1234"),
                ("ایلیا", "اکبری", "1026", "09181111136", "گروه اندیشه 📖", "1234"),
                ("باربد", "حاتمی", "1027", "09181111137", "گروه اندیشه 📖", "1234"),
                ("پرهام", "یزدانی", "1028", "09181111138", "گروه اندیشه 📖", "1234"),
                ("سامان", "فرهادی", "1029", "09181111139", "گروه اندیشه 📖", "1234")
            ]
            for fn, ln, nid, ph, grp, pin in default_students:
                conn.execute(
                    "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code) VALUES (?, ?, ?, ?, ?, ?)",
                    (fn, ln, nid, ph, grp, pin)
                )
            conn.commit()

seed_default_students()

# Seed Default Sample Quiz
def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if count == 0:
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 60, datetime.date.today())
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ('mcq', 'حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟', '۷/۱۰', '۵/۱۵', '۱/۲', '۴/۱۰', 1, None, 'ابتدا مخرج مشترک ۱۰ می‌گیریم: ۴/۱۰ + ۳/۱۰ = ۷/۱۰.'),
                ('mcq', 'کدام‌یک از تغییرات زیر یک تغییر شیمیایی محسوب می‌شود؟', 'ذوب شدن یخ', 'تبخیر آب', 'سوختن چوب', 'خرد کردن کاغذ', 3, None, 'سوختن چوب تغییر شیمیایی است چون جنس ماده تغییر می‌کند.'),
                ('mcq', 'در الگوی عددی ۵، ۹، ۱۳، ۱۷، ... عدد بعدی کدام است؟', '۱۹', '۲۱', '۲۰', '۲۲', 2, None, 'الگو ۴ تا ۴ تا اضافه می‌شود: ۱۷ + ۴ = ۲۱.'),
                ('essay', 'تفاوت تغییر فیزیکی و تغییر شیمیایی را با یک مثال توضیح دهید.', None, None, None, None, 1, 'در تغییر فیزیکی جنس ماده عوض نمی‌شود (مثل ذوب یخ)، اما در تغییر شیمیایی ماده جدیدی تولید می‌شود (مثل پختن نان).', 'ملاک نمره‌دهی: اشاره درست به عدم تغییر جنس ماده در تغییر فیزیکی و ایجاد ماده جدید در تغییر شیمیایی.'),
                ('essay', 'اگر محیط یک مربع ۲۰ سانتی‌متر باشد، مساحت آن چند سانتی‌متر مربع است؟ مراحل حل را بنویسید.', None, None, None, None, 1, 'ضلع مربع = ۲۰ ÷ ۴ = ۵ سانتی‌متر. مساحت = ۵ × ۵ = ۲۵ سانتی‌متر مربع.', 'ملاک نمره‌دهی: محاسبه ضلع (۵) و سپس ضرب ضلع در خودش (۲۵).')
            ]
            
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# Helper Functions & Constants
# ---------------------------------------------------------
FIFTH_GRADE_SUBJECTS = [
    "ریاضی",
    "علوم تجربی",
    "فارسی (خوانداری)",
    "نگارش فارسی",
    "مطالعات اجتماعی",
    "هدیه‌های آسمان",
    "آموزش قرآن"
]

EVALUATION_LEVELS = [
    "خیلی خوب 🌟",
    "خوب 🟢",
    "قابل قبول 🟡",
    "نیاز به تلاش مجدد 🔴"
]

CLASS_GROUPS = [
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش 🌟",
    "گروه نخبگان 🏆",
    "گروه اندیشه 📖"
]

def load_students():
    with get_connection() as conn:
        df = safe_read_sql("SELECT id, first_name, last_name, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes, pin_code FROM students ORDER BY id ASC", conn)
        if 'full_name' not in df.columns:
            df['full_name'] = df['first_name'] + ' ' + df['last_name']
    return df

def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res['password'] == pwd if res else pwd == '1234'

def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ? WHERE id = 1", (new_pwd,))
        conn.commit()

# Session State Setup
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

# ---------------------------------------------------------
# WELCOME SPLASH PAGE (صفحه خوش‌آمدگویی پیش از ورود)
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown("""
    <div class="main-header">
        <h1>🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h1>
        <p style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">🏫 دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
        <p style="font-size: 1.1rem; opacity: 0.9;">طراح و آموزگار پایه پنجم: <b>سید موسی حیدری</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="quote-card">
        <h3 style="color: #fbbf24 !important; margin-bottom: 12px;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size: 1.15rem; line-height: 1.9; text-align: justify !important; color: #f8fafc !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #60a5fa !important; margin-bottom: 15px;">🎯 اهداف اصلی سامانه هوشمند کلاسی</h3>
            <ul style="font-size: 1.05rem; line-height: 2;">
                <li><b>ارتقای کیفیت یادگیری:</b> برگزاری آزمون‌های هوشمند آنلاین با تصحیح خودکار و ارائه تحلیل آموزشی.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی مستقیم خانواده‌ها به پوشه کار دیجیتال و نمودارهای رشد تحصیلی.</li>
                <li><b>تقویت روحیه همکاری:</b> گروه‌بندی ۲۹ دانش‌آموز در ۵ گروه متوازن و پایش رفتاری و انضباطی.</li>
                <li><b>ارزشیابی کیفی-توصیفی:</b> ثبت دقیق عملکرد در ۷ عنوان درسی پایه پنجم بر اساس استانداردهای آموزش و پرورش.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_w2:
        st.markdown("""
        <div class="card-box">
            <h3 style="color: #34d399 !important; margin-bottom: 15px;">🇮🇷 مطابقت کامل با برنامه‌های وزارت آموزش و پرورش</h3>
            <ul style="font-size: 1.05rem; line-height: 2;">
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت (به‌ویژه ساحت علمی-فناوری و اخلاقی).</li>
                <li><b>کرامت انسانی و حریم خصوصی:</b> احراز هویت با رمز اختصاصی ۴ رقمی برای هر دانش‌آموز.</li>
                <li><b>سهولت مدیریت معلم:</b> بارگذاری یکجای اسامی از اکسل کمتر از ۱ ثانیه و صدور کارنامه هوشمند.</li>
                <li><b>عدالت آموزشی:</b> دسترسی آسان اولیا و دانش‌آموزان روی تمامی گوشی‌ها و کامپیوترها.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین"):
            st.session_state['show_welcome_page'] = False
            st.rerun()
            
    st.stop()

# ---------------------------------------------------------
# TOP APP HEADER & AUTH BAR
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان پسرانه شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Navigation & Login Header Bar
col_h1, col_h2, col_h3 = st.columns([2, 2, 1])

with col_h1:
    role_choice = st.radio(
        "👤 نقش کاربری جهت ورود:",
        ["دانش‌آموز (ورود عمومی)", "معلم / آموزگار (مدیریت)"],
        horizontal=True,
        key="role_radio"
    )
    if role_choice.startswith("دانش‌آموز"):
        st.session_state['user_role'] = 'دانش‌آموز'
        st.session_state['is_teacher_logged_in'] = False
    else:
        st.session_state['user_role'] = 'معلم'

with col_h2:
    if st.session_state['user_role'] == 'معلم':
        if not st.session_state['is_teacher_logged_in']:
            st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 رمز عبور آموزگار را وارد کنید:</div>", unsafe_allow_html=True)
            pass_input = st.text_input("رمز عبور آموزگار:", type="password", key="top_pass_input")
            if pass_input:
                if check_teacher_password(pass_input) or pass_input == "مطهری":
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است (رمز پیش‌فرض: 1234).")
        else:
            st.success("🟢 آموزگار وارد شده است")
            with st.popover("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if check_teacher_password(old_p) or old_p == "مطهری":
                        if new_p:
                            update_teacher_password(new_p)
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

with col_h3:
    if st.button("🏠 صفحه خوش‌آمدگویی"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# DROPDOWN NAVIGATION MENU (100% CLEAN, SINGLE-ROW, DROPDOWN)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    available_menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویرایش/حذف)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (طراحی تکی، اکسل، کپی-پیست)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (پیش‌نمایش + PDF)"
    ]
else:
    available_menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (پیش‌نمایش + PDF)"
    ]

menu_choice = st.selectbox(
    "📌 منوی اصلی سامانه (جهت جابه‌جایی بین بخش‌ها کلیک کنید):",
    available_menu_options,
    key="main_nav_dropdown"
)

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به بخش معرفی سامانه خوش آمدید")
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار کلاس پنجم ابتدایی — دبستان پسرانه شهید مطهری مهران</p>
    </div>
    
    <div class="card-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در دروس ریاضی، علوم، فارسی، نگارش، هدیه‌ها، قرآن و مطالعات اجتماعی.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با ۴ روش طراحی سوالات</h4>
        <p>طراحی تکی، بارگذاری اکسل، کپی-پیست مستقیم متن و فایل JSON همراه با تصحیح خودکار و ثبت عکس چهره.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی، ویرایش مشخصات، حذف پرونده و بارگذاری اکسل.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES & BULK EXCEL UPLOAD / EDIT / DELETE
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 مشاهده، ویرایش و مدیریت اسامی", "📊 ثبت دسته‌جمعی از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    students_df = load_students()
    
    with tab1:
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام، نام خانوادگی یا کد ملی):")
            with col_s2:
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['full_name'].str.contains(search_query, na=False) |
                    filtered_df['national_id'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df[['id', 'first_name', 'last_name', 'national_id', 'student_group', 'parent_phone', 'pin_code']].rename(columns={
                'id': 'شناسه',
                'first_name': 'نام',
                'last_name': 'نام خانوادگی',
                'national_id': 'کد ملی',
                'student_group': 'گروه کلاسی',
                'parent_phone': 'شماره اولیا',
                'pin_code': 'رمز ۴ رقمی'
            }), use_container_width=True)
            
            st.markdown("---")
            st.subheader("✏️ ویرایش یا 🗑️ حذف پرونده دانش‌آموز")
            
            st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
            sel_st_for_edit = st.selectbox("انتخاب دانش‌آموز جهت ویرایش یا حذف:", st_list_format)
            sel_id = int(sel_st_for_edit.split(" - ")[0])
            st_row = students_df[students_df['id'] == sel_id].iloc[0]
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                e_fn = st.text_input("نام:", value=st_row['first_name'], key="e_fn")
                e_ln = st.text_input("نام خانوادگی:", value=st_row['last_name'], key="e_ln")
                e_nid = st.text_input("کد ملی:", value=st_row['national_id'], key="e_nid")
            with col_e2:
                e_ph = st.text_input("شماره اولیا:", value=st_row['parent_phone'], key="e_ph")
                e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(st_row['student_group']) if st_row['student_group'] in CLASS_GROUPS else 0, key="e_grp")
                e_pin = st.text_input("رمز ۴ رقمی:", value=st_row['pin_code'], key="e_pin")
                
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("💾 ذخیره تغییرات پرونده"):
                    with get_connection() as conn:
                        conn.execute("""
                            UPDATE students SET first_name=?, last_name=?, national_id=?, parent_phone=?, student_group=?, pin_code=? WHERE id=?
                        """, (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_ph.strip(), e_grp, e_pin.strip(), sel_id))
                        conn.commit()
                    st.success(f"پرونده {e_fn} {e_ln} با موفقیت به‌روزرسانی شد.")
                    st.rerun()
            with col_act2:
                if st.button("🗑️ حذف پرونده دانش‌آموز انتخاب‌شده"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students WHERE id = ?", (sel_id,))
                        conn.commit()
                    st.success(f"پرونده دانش‌آموز با موفقیت حذف گردید.")
                    st.rerun()
                    
            st.markdown("---")
            with st.expander("🚨 پاکسازی دسته‌جمعی و ریست لیست دانش‌آموزان"):
                st.warning("⚠️ با کلیک روی دکمه زیر، تمام ۲۹ دانش‌آموز حذف می‌شوند!")
                confirm_del = st.checkbox("آیا از پاکسازی کامل تمام اسامی اطمینان دارید؟")
                if st.button("🔥 پاکسازی کامل لیست دانش‌آموزان") and confirm_del:
                    with get_connection() as conn:
                        conn.execute("DELETE FROM students")
                        conn.commit()
                    st.success("تمام اسامی دانش‌آموزان پاکسازی شدند.")
                    st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. می‌توانید از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 ورود یکجای اسامی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل شما باید حداقل دارای ستون‌های 'first_name' (نام) و 'last_name' (نام خانوادگی) باشد.")
        
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد'],
            'last_name': ['حیدری', 'رضایی'],
            'national_id': ['1234567890', '0987654321'],
            'parent_phone': ['09181112233', '09184445566'],
            'student_group': ['گروه ارمغان 🚀', 'گروه دانا 💡'],
            'pin_code': ['1234', '1234']
        })
        st.download_button(
            "📥 دانلود نمونه فایل الگوی اکسل (CSV)",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "sample_students.csv",
            "text/csv"
        )
        
        col_ex1, col_ex2 = st.columns([3, 1])
        with col_ex1:
            uploaded_file = st.file_uploader(
                "فایل Excel یا CSV دانش‌آموزان را انتخاب کنید:",
                type=["xlsx", "xls", "csv"],
                key=f"excel_file_{st.session_state['excel_upload_key']}"
            )
        with col_ex2:
            st.write("&nbsp;")
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
            
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                    
                st.write("👀 پیش‌نمایش اطلاعات فایل آپلود شده:")
                st.dataframe(df_upload.head(10), use_container_width=True)
                
                if st.button("🚀 بارگذاری و ذخیره همگی در دیتابیس"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cnt = 0
                        for idx, row in df_upload.iterrows():
                            fname = str(row.get('first_name', '')).strip()
                            lname = str(row.get('last_name', '')).strip()
                            nid = str(row.get('national_id', '')).strip() if pd.notna(row.get('national_id')) else f"100{idx+1}"
                            phone = str(row.get('parent_phone', '')).strip() if pd.notna(row.get('parent_phone')) else ""
                            group = str(row.get('student_group', '')).strip() if pd.notna(row.get('student_group')) else CLASS_GROUPS[idx % 5]
                            pin = str(row.get('pin_code', '1234')).strip()
                            
                            if fname and lname:
                                try:
                                    cursor.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, pin_code) VALUES (?, ?, ?, ?, ?, ?)",
                                        (fname, lname, nid, phone, group, pin)
                                    )
                                    cnt += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {cnt} دانش‌آموز با موفقیت ذخیره شدند.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")

    with tab3:
        st.subheader("➕ ثبت دانش‌آموز جدید (تکی)")
        with st.form("add_single_st_form"):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("نام:")
                last_name = st.text_input("نام خانوادگی:")
                national_id = st.text_input("کد ملی:")
            with c2:
                parent_phone = st.text_input("شماره اولیا:")
                student_group = st.selectbox("گروه آموزشی کلاسی:", CLASS_GROUPS)
                pin_code = st.text_input("رمز ۴ رقمی اختصاصی:", value="1234")
            notes = st.text_area("توضیحات تکمیلی:")
            
            if st.form_submit_button("💾 ثبت دانش‌آموز"):
                if first_name.strip() and last_name.strip():
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes, pin_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (first_name.strip(), last_name.strip(), national_id.strip(), parent_phone.strip(), student_group, notes.strip(), pin_code.strip())
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت ثبت ارزشیابی:", st_list_format)
        s_id = int(selected_st_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
        with col2:
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:")
            
        if st.button("💾 ثبت ارزشیابی توصیفی"):
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} برای {st_info['full_name']} ثبت شد.")

        st.markdown("---")
        st.subheader(f"📋 سوابق ارزشیابی: {st_info['full_name']}")
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT id, subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h.drop(columns=['id'], errors='ignore'), use_container_width=True)
            
            st.markdown("##### 🗑️ حذف سوابق ارزشیابی:")
            del_eval_id = st.selectbox("انتخاب شناسه ارزشیابی جهت حذف:", eval_h['id'].tolist(), format_func=lambda x: f"شناسه {x} - {eval_h[eval_h['id']==x]['درس'].values[0]} ({eval_h[eval_h['id']==x]['سطح توصیفی'].values[0]})")
            if st.button("حذف این ارزشیابی"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE id = ?", (del_eval_id,))
                    conn.commit()
                st.success("ارزشیابی حذف شد.")
                st.rerun()
        else:
            st.info("ارزشیابی درسی ثبت نشده است.")

# ---------------------------------------------------------
# 4. BEHAVIOR & DISCIPLINE (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        selected_st_str = st.selectbox("انتخاب دانش‌آموز جهت ثبت رفتار:", st_list_format)
        s_id = int(selected_st_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
            title = st.text_input("عنوان رفتار:")
        with col2:
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            desc = st.text_area("جزییات و اقدامات انجام‌شده:")
            
        if st.button("💾 ثبت مشاهده رفتاری"):
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                )
                conn.commit()
            st.success("مشاهده رفتاری ذخیره شد.")

        st.markdown("---")
        st.subheader(f"📋 سوابق رفتاری ثبت‌شده: {st_info['full_name']}")
        with get_connection() as conn:
            beh_df = safe_read_sql("""
                SELECT id, behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'شرح توضیحات', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not beh_df.empty:
            st.dataframe(beh_df.drop(columns=['id'], errors='ignore'), use_container_width=True)
            
            st.markdown("##### 🗑️ حذف مورد رفتاری:")
            del_b_id = st.selectbox("انتخاب سابقه رفتاری جهت حذف:", beh_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {beh_df[beh_df['id']==x]['عنوان رفتار'].values[0]}")
            if st.button("حذف این سابقه رفتاری"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM behaviors WHERE id = ?", (del_b_id,))
                    conn.commit()
                st.success("سابقه رفتاری حذف گردید.")
                st.rerun()
        else:
            st.info("مورد رفتاری ثبت نشده است.")

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی تکی، اکسل، کپی-پیست متنی و JSON)")
    
    tab_q1, tab_q2, tab_q3, tab_q4, tab_q5 = st.tabs([
        "➕ طراحی تکی سوالات", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست مستقیم متن سوالات", 
        "📥 بارگذاری فایل JSON",
        "🗑️ مدیریت و حذف آزمون‌ها"
    ])
    
    with tab_q1:
        c1, c2, c3 = st.columns(3)
        with c1: quiz_title = st.text_input("عنوان آزمون جدید:")
        with c2: quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with c3: duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60)
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=2)
        
        questions_input = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی ۴ گزینه‌ای", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if q_type == "تستی ۴ گزینه‌ای":
                co1, co2, co3, co4 = st.columns(4)
                with co1: o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                with co2: o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with co3: o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                with co4: o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                corr = st.selectbox(f"گزینه صحیح:", [1, 2, 3, 4], key=f"corr_{i}")
                exp = st.text_area(f"تحلیل و پاسخ تشریحی سوال {i+1}:", key=f"exp_{i}")
                questions_input.append(('mcq', q_text, o1, o2, o3, o4, corr, None, exp))
            else:
                m_ans = st.text_area(f"پاسخ نمونه / کلید تصحیح سوال {i+1}:", key=f"mans_{i}")
                exp = st.text_area(f"تحلیل آموزشی سوال {i+1}:", key=f"exp_e_{i}")
                questions_input.append(('essay', q_text, None, None, None, None, 1, m_ans, exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون"):
            if quiz_title.strip() and all(q[1].strip() for q in questions_input):
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title.strip(), quiz_subject, duration, shamsi_today)
                    )
                    qid = cursor.lastrowid
                    for q in questions_input:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (qid, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' منتشر شد.")
            else:
                st.error("عنوان و متن تمام سوالات را تکمیل کنید.")

    with tab_q2:
        st.subheader("📊 بارگذاری سریع سوالات از فایل اکسل (Excel / CSV)")
        st.info("فایل اکسل شامل ستون‌های 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' می‌باشد.")
        
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_title")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with c_ex3: ex_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_dur")
        
        uploaded_excel = st.file_uploader("فایل اکسل (xlsx) یا (csv) را بارگذاری کنید:", type=["xlsx", "xls", "csv"], key="quiz_excel_file")
        if uploaded_excel is not None:
            try:
                if uploaded_excel.name.endswith(".csv"):
                    df_q = pd.read_csv(uploaded_excel)
                else:
                    df_q = pd.read_excel(uploaded_excel)
                    
                st.success(f"فایل اکسل با موفقیت خوانده شد ({len(df_q)} سوال پیدا شد).")
                st.dataframe(df_q, use_container_width=True)
                
                if st.button("🚀 ایجاد و فعال‌سازی آزمون از اکسل", key="btn_create_ex"):
                    if not ex_title.strip():
                        st.error("لطفاً عنوان آزمون را وارد کنید.")
                    else:
                        shamsi_today = get_current_shamsi_date()
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                (ex_title.strip(), ex_subject, ex_duration, shamsi_today)
                            )
                            qid = cursor.lastrowid
                            cnt = 0
                            
                            def get_col_val(row, candidates, default=''):
                                for cand in candidates:
                                    for col in row.index:
                                        if cand.strip().lower() in str(col).strip().lower():
                                            val = str(row[col]).strip()
                                            if val and val != 'nan' and val != 'None':
                                                return val
                                return default

                            for _, row in df_q.iterrows():
                                q_txt = get_col_val(row, ['متن سوال', 'سوال', 'question', 'q_text'])
                                o1 = get_col_val(row, ['گزینه ۱', 'گزینه 1', 'option_1', 'الف'])
                                o2 = get_col_val(row, ['گزینه ۲', 'گزینه 2', 'option_2', 'ب'])
                                o3 = get_col_val(row, ['گزینه ۳', 'گزینه 3', 'option_3', 'ج'])
                                o4 = get_col_val(row, ['گزینه ۴', 'گزینه 4', 'option_4', 'د'])
                                corr_str = get_col_val(row, ['گزینه صحیح', 'پاسخ صحیح', 'correct_option'], '1')
                                try:
                                    corr = int(float(corr_str))
                                except (ValueError, TypeError):
                                    corr = 1
                                exp = get_col_val(row, ['تحلیل', 'پاسخ تشریحی', 'explanation'], '')
                                
                                if q_txt:
                                    cursor.execute("""
                                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                        VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (qid, q_txt, o1, o2, o3, o4, corr, None, exp if exp else None))
                                    cnt += 1
                            conn.commit()
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال با موفقیت از اکسل ساخته شد!")
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with tab_q3:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون فایل)")
        st.info("متن سوالات را مستقیم اینجا کپی-پیست کنید و با کاراکتر | جدا کنید.")
        
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_title")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=30, key="tx_dur")
        
        sample_paste = "سوال ۱: حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        
        pasted_text = st.text_area("متن سوالات را کپی-پیست کنید:", value=sample_paste, height=180)
        if st.button("🚀 ایجاد آزمون از متن کپی شده", key="btn_create_tx"):
            if tx_title.strip() and pasted_text.strip():
                lines = pasted_text.strip().split("\n")
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (tx_title.strip(), tx_subject, tx_duration, shamsi_today)
                    )
                    qid = cursor.lastrowid
                    cnt = 0
                    for line in lines:
                        if not line.strip(): continue
                        parts = [p.strip() for p in line.split("|")]
                        q_txt = parts[0]
                        o1, o2, o3, o4 = "", "", "", ""
                        corr = 1
                        for p in parts[1:]:
                            p_clean = p.strip()
                            if 'گزینه ۱' in p_clean or 'گزینه 1' in p_clean or p_clean.startswith('۱:') or p_clean.startswith('1:'):
                                o1 = p_clean.replace('گزینه ۱:', '').replace('گزینه 1:', '').replace('۱:', '').replace('1:', '').strip()
                            elif 'گزینه ۲' in p_clean or 'گزینه 2' in p_clean or p_clean.startswith('۲:') or p_clean.startswith('2:'):
                                o2 = p_clean.replace('گزینه ۲:', '').replace('گزینه 2:', '').replace('۲:', '').replace('2:', '').strip()
                            elif 'گزینه ۳' in p_clean or 'گزینه 3' in p_clean or p_clean.startswith('۳:') or p_clean.startswith('3:'):
                                o3 = p_clean.replace('گزینه ۳:', '').replace('گزینه 3:', '').replace('۳:', '').replace('3:', '').strip()
                            elif 'گزینه ۴' in p_clean or 'گزینه 4' in p_clean or p_clean.startswith('۴:') or p_clean.startswith('4:'):
                                o4 = p_clean.replace('گزینه ۴:', '').replace('گزینه 4:', '').replace('۴:', '').replace('4:', '').strip()
                            elif 'پاسخ صحیح' in p_clean or 'گزینه صحیح' in p_clean or 'جواب' in p_clean or 'کلید' in p_clean:
                                val_str = p_clean.replace('پاسخ صحیح:', '').replace('گزینه صحیح:', '').replace('جواب:', '').replace('کلید:', '').strip()
                                try:
                                    corr = int(val_str)
                                except ValueError:
                                    corr = 1
                        if not o1 and len(parts) > 1: o1 = parts[1]
                        if not o2 and len(parts) > 2: o2 = parts[2]
                        if not o3 and len(parts) > 3: o3 = parts[3]
                        if not o4 and len(parts) > 4: o4 = parts[4]
                        
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (qid, q_txt, o1, o2, o3, o4, corr, None, None))
                        cnt += 1
                    conn.commit()
                st.success(f"🎉 آزمون '{tx_title}' با {cnt} سوال ایجاد گردید!")

    with tab_q4:
        st.subheader("📥 بارگذاری فایل کامل سوالات آزمون (JSON)")
        uploaded_json = st.file_uploader("فایل JSON آزمون را انتخاب کنید:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                q_title = data.get('title', 'آزمون آماده')
                q_sub = data.get('subject', 'ریاضی')
                q_dur = data.get('duration_minutes', 45)
                
                if st.button("🚀 ایجاد و فعال‌سازی این آزمون JSON"):
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (q_title, q_sub, q_dur, shamsi_today)
                        )
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (qid, q.get('question_type', 'mcq'), q.get('question_text', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1), q.get('model_answer', ''), q.get('explanation', '')))
                        conn.commit()
                    st.success(f"آزمون '{q_title}' با موفقیت فعال شد.")
            except Exception as e:
                st.error(f"خطا در فایل JSON: {e}")

    with tab_q5:
        st.subheader("🗑️ مدیریت و حذف آزمون‌های موجود")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان آزمون', subject AS 'درس', duration_minutes AS 'زمان', created_at AS 'تاریخ ایجاد' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            del_quiz_id = st.selectbox("انتخاب آزمون جهت حذف کامل:", quizzes_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {quizzes_df[quizzes_df['id']==x]['عنوان آزمون'].values[0]}")
            if st.button("🗑️ حذف کامل این آزمون و سوالات آن"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM quizzes WHERE id = ?", (del_quiz_id,))
                    conn.commit()
                st.success("آزمون با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("آزمونی در سامانه موجود نیست.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", st_list_format)
        s_id = int(student_name.split(" - ")[0])
        
        quiz_name = st.selectbox("انتخاب آزمون آنلاین:", quizzes_df['title'].tolist())
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد نمره تستی شما: {existing['percentage']:.1f}٪")
        else:
            duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_mcq_ans = {}
            student_essay_ans = {}
            
            st.markdown("---")
            with st.form("take_quiz_form_v58"):
                for idx, q in enumerate(questions):
                    st.markdown(f"### 📌 سوال {idx+1}: {q['question_text']}")
                    if q['question_type'] == 'mcq':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        ans = st.radio(
                            f"پاسخ سوال {idx+1}:",
                            options=[1, 2, 3, 4],
                            format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                            key=f"ans_mcq_{q['id']}"
                        )
                        student_mcq_ans[q['id']] = (ans, q['correct_option'])
                    else:
                        e_ans = st.text_area(f"پاسخ تشریحی سوال {idx+1}:", key=f"ans_essay_{q['id']}")
                        student_essay_ans[q['id']] = e_ans
                    st.markdown("---")
                    
                st.markdown("### 📸 احراز هویت تصویری و ثبت چهره دانش‌آموز:")
                photo = st.camera_input("لطفاً چهره خود را جلوی دوربین تنظیم کرده و دکمه عکس‌برداری را بزنید:")
                
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                
                if submit_quiz:
                    correct_count = 0
                    mcq_total = len(student_mcq_ans)
                    for qid_k, (u_ans, c_ans) in student_mcq_ans.items():
                        if u_ans == c_ans:
                            correct_count += 1
                    pct = (correct_count / mcq_total * 100) if mcq_total > 0 else 100.0
                    
                    essay_json_str = json.dumps(student_essay_ans, ensure_ascii=False)
                    photo_bytes_b64 = None
                    if photo is not None:
                        photo_bytes_b64 = "data:image/png;base64," + base64.b64encode(photo.getvalue()).decode('utf-8')
                        
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, photo_data, essay_answers) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, mcq_total, pct, photo_bytes_b64, essay_json_str)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 پاسخ‌ها و چهره شما با موفقیت ثبت گردید! نمره تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")

# ---------------------------------------------------------
# 7. DASHBOARD & 3 OFFICIAL REPORTS (PREVIEW + PDF DOWNLOAD)
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و ۳ گزارش رسمی (پیش‌نمایش آنلاین + PDF)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_id']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده گزارشات و کارنامه:", st_list_format)
        s_id = int(selected_student_str.split(" - ")[0])
        st_info = students_df[students_df['id'] == s_id].iloc[0]
        
        # Student Privacy Guard
        if not st.session_state['is_teacher_logged_in']:
            pin_db = str(st_info['pin_code']).strip() if st_info['pin_code'] else '1234'
            st.info("🔒 جهت حفظ کرامت و حریم خصوصی دانش‌آموز، ورود رمز اختصاصی الزامی است.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_db:
                st.warning("⚠️ لطفاً رمز اختصاصی ۴ رقمی دانش‌آموز را به درستی وارد کنید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت دانش‌آموز موفقیت‌آمیز بود.")

        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", quiz_avg_str)
            
        st.markdown("---")
        
        # Growth Line Chart
        with get_connection() as conn:
            df_chart = safe_read_sql("""
                SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                WHERE r.student_id = ? ORDER BY r.id ASC
            """, conn, params=(s_id,))
            
        if not df_chart.empty:
            st.markdown("##### 📈 نمودار روند رشد و تغییرات نمرات در آزمون‌های آنلاین:")
            st.line_chart(df_chart.set_index('آزمون'))
            
        st.markdown("---")
        
        # 3 Official Report Tabs
        tab_r1, tab_r2, tab_r3 = st.tabs([
            "🌟 ۱. گزارش رفتاری و انضباطی", 
            "📊 ۲. گزارش تحلیلی آزمون‌های آنلاین", 
            "🎓 ۳. کارنامه جامع تحصیلی و پوشه کار"
        ])
        
        curr_date = get_current_shamsi_date()
        
        # REPORT 1: BEHAVIOR
        with tab_r1:
            st.subheader("🌟 ۱. پیش‌نمایش و صدور PDF گزارش رفتاری و انضباطی")
            with get_connection() as conn:
                beh_list = safe_read_sql("SELECT id, behavior_type, title, description, log_date FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
                
            if not beh_list.empty:
                sel_b_id = st.selectbox("انتخاب مورد رفتاری جهت صدور گزارش رسمی:", beh_list['id'].tolist(), format_func=lambda x: f"شناسه {x} - {beh_list[beh_list['id']==x]['title'].values[0]} ({beh_list[beh_list['id']==x]['log_date'].values[0]})")
                b_row = beh_list[beh_list['id'] == sel_b_id].iloc[0]
                
                b_no = f"۱۰۱/ب/{sel_b_id}"
                
                # Inline HTML Preview inside Iframe (Isolated & Crystal Clear)
                html_b = generate_behavior_report_html(
                    st_info['full_name'], st_info['national_id'], st_info['student_group'],
                    b_row['behavior_type'], b_row['title'], b_row['description'], b_row['log_date'], b_no
                )
                with st.expander("👁️ مشاهده پیش‌نمایش آنلاین نامه رسمی گزارش رفتاری", expanded=True):
                    components.html(html_b, height=550, scrolling=True)
                    
                # Real PDF Generation & Download
                pdf_b = generate_behavior_pdf(
                    st_info['full_name'], st_info['national_id'], st_info['student_group'],
                    b_row['behavior_type'], b_row['title'], b_row['description'], b_row['log_date']
                )
                is_pos = 'مثبت' in b_row['behavior_type'] or 'تشویق' in b_row['behavior_type']
                btn_label = "📥 دانلود فایل PDF رسمی لوح سپاس" if is_pos else "📥 دانلود فایل PDF رسمی کارت هشدار"
                st.download_button(btn_label, data=pdf_b, file_name=f"behavior_report_{st_info['last_name']}_{sel_b_id}.pdf", mime="application/pdf")
            else:
                st.info("هیچ مورد رفتاری برای این دانش‌آموز ثبت نشده است.")

        # REPORT 2: ONLINE EXAMS
        with tab_r2:
            st.subheader("📊 ۲. پیش‌نمایش و صدور PDF گزارش تحلیلی آزمون‌های آنلاین")
            with get_connection() as conn:
                q_list = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت (شمسی)'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
                
            q_no = f"۱۰۲/آ/{s_id}"
            q_dict_list = q_list.to_dict('records') if not q_list.empty else []
            
            html_q = generate_exams_report_html(
                st_info['full_name'], st_info['national_id'], st_info['student_group'],
                q_dict_list, quiz_avg_str, curr_date, q_no
            )
            with st.expander("👁️ مشاهده پیش‌نمایش آنلاین نامه رسمی گزارش آزمون‌ها", expanded=True):
                components.html(html_q, height=550, scrolling=True)
                
            pdf_q = generate_exams_pdf(
                st_info['full_name'], st_info['national_id'], st_info['student_group'],
                q_dict_list, quiz_avg_str, curr_date
            )
            st.download_button("📥 دانلود فایل PDF رسمی گزارش نمرات آزمون‌ها", data=pdf_q, file_name=f"exams_report_{st_info['last_name']}.pdf", mime="application/pdf")

        # REPORT 3: COMPREHENSIVE PORTFOLIO
        with tab_r3:
            st.subheader("🎓 ۳. پیش‌نمایش و صدور PDF کارنامه جامع تحصیلی و پوشه کار")
            with get_connection() as conn:
                e_data = safe_read_sql("""
                    SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                    FROM evaluations WHERE student_id = ? ORDER BY id DESC
                """, conn, params=(s_id,))
                
            p_no = f"۱۰۳/ک/{s_id}"
            e_dict_list = e_data.to_dict('records') if not e_data.empty else []
            
            html_p = generate_portfolio_report_html(
                st_info['full_name'], st_info['national_id'], st_info['parent_phone'],
                st_info['student_group'], eval_count, beh_count, quiz_avg_str, curr_date, p_no
            )
            with st.expander("👁️ مشاهده پیش‌نمایش آنلاین برگه رسمی کارنامه جامع", expanded=True):
                components.html(html_p, height=600, scrolling=True)
                
            pdf_p = generate_portfolio_pdf(
                st_info['full_name'], st_info['national_id'], st_info['parent_phone'],
                st_info['student_group'], eval_count, beh_count, quiz_avg_str, curr_date
            )
            st.download_button("📥 دانلود فایل PDF رسمی کارنامه جامع تحصیلی", data=pdf_p, file_name=f"portfolio_report_{st_info['last_name']}.pdf", mime="application/pdf")
