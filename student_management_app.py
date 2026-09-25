import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
import datetime
import json
import random
import re
import io
import os
import tempfile
import subprocess

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
# Page Configuration & RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Persian / RTL CSS (Targeted & Clean)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Global Typography & Font */
    html, body, [class*="st-"], .stMarkdown, p, span, button, input, select, textarea, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
        text-align: center !important;
        margin: 4px 0;
    }
    
    /* Card Boxes */
    .card-box {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .quote-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.7) 0%, rgba(30, 41, 59, 0.95) 100%);
        border-right: 6px solid #fbbf24;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    /* Fast & Stylish Sidebar Navigation */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-left: 2px solid #1e293b !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #ffffff !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #2563eb !important;
        border-color: #60a5fa !important;
        transform: translateX(-3px);
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: 2px solid #60a5fa !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
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
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
    }
    
    /* Inputs & Controls */
    input, select, textarea, div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border-radius: 8px !important;
    }
    
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
        
        # Students Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            pin_code TEXT DEFAULT '1234',
            parent_phone TEXT,
            student_group TEXT DEFAULT 'بدون گروه',
            notes TEXT,
            created_at TEXT
        )
        """)
        
        # Evaluations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            feedback TEXT,
            eval_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # Behaviors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            log_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        # Quizzes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 15,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)
        
        # Questions Table
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
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
        """)
        
        # Quiz Results Table
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
            submitted_at TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        conn.commit()

init_db()

def safe_read_sql(query, conn, params=None):
    try:
        if params:
            return pd.read_sql_query(query, conn, params=params)
        return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# Default Quiz Seeder
# ---------------------------------------------------------
def seed_default_quiz():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if count == 0:
            shamsi_today = get_current_shamsi_date()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 20, shamsi_today)
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ("mcq", "حاصل عبارت (۳/۵ + ۲/۴) کدام است؟", "۵/۹", "۶/۱", "۵/۷", "۶/۵", 1, "", ""),
                ("mcq", "کدام یک از موارد زیر جزء تغییرات شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "تبخیر آب", "زنگ زدن آهن", "خرد کردن چوب", 3, "", ""),
                ("essay", "علت اصلی ایجاد روز و شب چیست؟ (توضیح دهید)", "", "", "", "", 1, "چرخش زمین به دور محور خود در مدت ۲۴ ساعت.", "مفاهیم پایه جغرافیا و علوم")
            ]
            
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# PDF & HTML Report Generators
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_chart_b64(quiz_titles, quiz_pcts, eval_counts):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 2.8), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        
        if quiz_pcts:
            ax1.bar(range(len(quiz_pcts)), quiz_pcts, color='#2563eb', width=0.4)
            ax1.set_ylim(0, 110)
            ax1.set_title('درصد آزمون‌های آنلاین', fontsize=9)
            ax1.set_xticks(range(len(quiz_titles)))
            ax1.set_xticklabels([f'آزمون {i+1}' for i in range(len(quiz_titles))], fontsize=8)
        else:
            ax1.text(0.5, 0.5, 'آزمونی ثبت نشده', ha='center', va='center', fontsize=9)
            ax1.axis('off')
            
        labels = list(eval_counts.keys())
        values = list(eval_counts.values())
        colors = ['#16a34a', '#2563eb', '#eab308', '#dc2626']
        if sum(values) > 0:
            ax2.bar(labels, values, color=colors[:len(labels)], width=0.4)
            ax2.set_title('توزیع سطح ارزشیابی‌ها', fontsize=9)
        else:
            ax2.text(0.5, 0.5, 'ارزشیابی ثبت نشده', ha='center', va='center', fontsize=9)
            ax2.axis('off')
            
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return b64
    except Exception:
        return ""

def _get_fpdf():
    try:
        from fpdf import FPDF
        return True, FPDF
    except ImportError:
        return False, None

def _get_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.colors import HexColor
        return True, A4, canvas, pdfmetrics, TTFont, HexColor
    except ImportError:
        return False, None, None, None, None, None

def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date):
    is_positive = 'مثبت' in b_type or 'تشویق' in b_type
    theme_color = '#15803d' if is_positive else '#b91c1c'
    bg_color = '#f0fdf4' if is_positive else '#fef2f2'
    border_color = '#22c55e' if is_positive else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; background: #ffffff; line-height: 1.8; }}
.letterhead {{ border-bottom: 3px double {theme_color}; padding-bottom: 12px; margin-bottom: 20px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 14px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 18px; font-weight: bold; margin-top: 5px; }}
.sub-header {{ color: #475569; font-size: 12px; margin-top: 4px; }}
.report-card {{ background: {bg_color}; border: 2px solid {border_color}; border-radius: 12px; padding: 25px; margin-top: 15px; }}
.report-header {{ color: {theme_color}; font-size: 20px; font-weight: bold; text-align: center; margin-bottom: 15px; border-bottom: 1px dashed {border_color}; padding-bottom: 10px; }}
.meta-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 15px; background: #ffffff; border-radius: 8px; overflow: hidden; }}
.meta-table td {{ padding: 8px 12px; border: 1px solid #e2e8f0; }}
.content-text {{ font-size: 14px; line-height: 2; text-align: justify; margin: 15px 0; }}
.signature-table {{ width: 100%; margin-top: 40px; text-align: center; font-size: 13px; border-collapse: collapse; }}
.signature-table td {{ padding: 10px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران</div>
    <div class="sub-header">سال تحصیلی ۱۴۰۴-۱۴۰۵ | پایه پنجم ابتدایی — آموزگار: سید موسی حیدری</div>
</div>

<div class="report-card">
    <div class="report-header">{report_title}</div>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
            <td><b>تاریخ ثبت:</b> {log_date}</td>
        </tr>
    </table>
    <div class="content-text">
        {'فرزند عزیز و دانش‌آموز گرامی:' if is_positive else 'اولیاء محترم دانش‌آموز گرامی:'} <b>{student_name}</b><br>
        {'بدین‌وسیله از تلاش، انضباط شایسته و رفتار نمونه شما در کلاس درس قدردانی می‌گردد.' if is_positive else 'با سلام و احترام، به استلزام اهداف پرورشی و تربیتی مدرسه، بدین‌وسیله گزارش زیر جهت اطلاع و پیگیری به حضورتان ارسال می‌گردد:'}<br><br>
        <div style="background: #ffffff; padding: 12px; border-radius: 8px; border-right: 4px solid {theme_color}; margin: 10px 0;">
            <b>📌 عنوان مشاهده رفتاری:</b> {title}<br>
            <b>📝 توضیحات تکمیلی آموزگار:</b> {desc}
        </div>
        <br>
        {'توفیق روزافزون شما را در مسیر اخلاق، دانایی و بالندگی از درگاه خداوند متعال خواستاریم.' if is_positive else 'خواهشمند است ضمن گفتگوی تربیتی و صمیمانه با فرزندتان، جهت پیگیری و بهبود این رفتار همکاری و هماهنگی لازم را با آموزگار مربوطه مبذول فرمایید.'}
    </div>
</div>

<table class="signature-table">
    <tr>
        <td style="width: 50%;">
            <b>آموزگار پایه پنجم ابتدایی</b><br>
            سید موسی حیدری<br><br>
            امضا و تاریخ
        </td>
        <td style="width: 50%;">
            {'<b>مدیریت دبستان شهید مطهری مهران</b><br><br>مهر و امضا' if is_positive else '<b>رویت و امضای اولیای محترم دانش‌آموز</b><br><br>تاریخ و امضا'}
        </td>
    </tr>
</table>
</body>
</html>"""

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str):
    shamsi_today = get_current_shamsi_date()
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 20px; color: #0f172a; background: #ffffff; line-height: 1.7; font-size: 13px; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 17px; font-weight: bold; margin-top: 3px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 6px 10px; border: 1px solid #cbd5e1; font-size: 12px; }}
.summary-box {{ background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 12px; margin-bottom: 15px; }}
.signature-table {{ width: 100%; margin-top: 30px; text-align: center; font-size: 12px; border-collapse: collapse; }}
.signature-table td {{ padding: 10px; vertical-align: top; }}
</style>
</head>
<body>
<div class="letterhead">
    <div class="org-name">باسمه تعالی</div>
    <div class="org-name">جمهوری اسلامی ایران - وزارت آموزش و پرورش</div>
    <div class="sub-header">اداره کل آموزش و پرورش استان ایلام | مدیریت آموزش و پرورش شهرستان مهران</div>
    <div class="school-name">دبستان پسرانه هیئت امنایی شهید مطهری مهران</div>
    <div class="sub-header">کارنامه جامع تحصیلی و پوشه کار دیجیتال — پایه پنجم ابتدایی | سال تحصیلی ۱۴۰۴-۱۴۰۵</div>
</div>

<table class="meta-table">
    <tr>
        <td><b>نام دانش‌آموز:</b> {student_name}</td>
        <td><b>کد ملی:</b> {national_id}</td>
        <td><b>گروه کلاسی:</b> {student_group}</td>
        <td><b>شماره همراه اولیا:</b> {parent_phone}</td>
        <td><b>تاریخ صدور:</b> {shamsi_today}</td>
    </tr>
</table>

<div class="summary-box">
    <h4 style="color: #1e3a8a; margin-top: 0; margin-bottom: 8px;">📊 خلاصه وضعیت پوشه کار دانش‌آموز:</h4>
    <ul>
        <li><b>تعداد ارزشیابی‌های کیفی-توصیفی ثبت‌شده:</b> {eval_count} مورد</li>
        <li><b>تعداد مشاهدات رفتاری و انضباطی:</b> {beh_count} مورد</li>
        <li><b>میانگین درصد عملکرد در آزمون‌های آنلاین:</b> {quiz_avg_str}</li>
        <li><b>آموزگار پایه پنجم:</b> سید موسی حیدری</li>
    </ul>
</div>

<table class="signature-table">
    <tr>
        <td style="width: 33%;">
            <b>آموزگار پایه پنجم ابتدایی</b><br>
            سید موسی حیدری<br><br>
            امضا و تاریخ
        </td>
        <td style="width: 33%;">
            <b>مدیریت دبستان شهید مطهری مهران</b><br><br>
            مهر و امضا
        </td>
        <td style="width: 33%;">
            <b>رویت و امضای اولیای محترم</b><br><br>
            تاریخ و امضا
        </td>
    </tr>
</table>
</body>
</html>"""

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    has_fpdf, FPDF = _get_fpdf()
    if has_fpdf:
        try:
            pdf = FPDF()
            pdf.add_page()
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            if os.path.exists(font_path):
                pdf.add_font('DejaVu', '', font_path)
                pdf.set_font('DejaVu', '', 12)
            else:
                pdf.set_font('Arial', '', 12)
            
            pdf.cell(0, 10, f"Report: {student_name} - {title}", ln=True, align='C')
            pdf.cell(0, 10, f"Date: {log_date} | Group: {student_group}", ln=True, align='C')
            pdf.multi_cell(0, 10, f"Description: {desc}")
            buf = io.BytesIO()
            pdf.output(buf)
            return buf.getvalue()
        except Exception:
            pass
            
    html = generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date)
    return html.encode('utf-8')

def generate_comprehensive_portfolio_pdf(student_id):
    with get_connection() as conn:
        st_row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not st_row:
            return b""
        student_name = f"{st_row['first_name']} {st_row['last_name']}"
        national_id = st_row['national_id'] or "ثبت نشده"
        parent_phone = st_row['parent_phone'] or "ثبت نشده"
        student_group = st_row['student_group'] or "بدون گروه"
        
        eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (student_id,)).fetchone()[0]
        beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (student_id,)).fetchone()[0]
        quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"

    has_fpdf, FPDF = _get_fpdf()
    if has_fpdf:
        try:
            pdf = FPDF()
            pdf.add_page()
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            if os.path.exists(font_path):
                pdf.add_font('DejaVu', '', font_path)
                pdf.set_font('DejaVu', '', 12)
            else:
                pdf.set_font('Arial', '', 12)
            
            pdf.cell(0, 10, f"Portfolio Report Card: {student_name}", ln=True, align='C')
            pdf.cell(0, 10, f"National ID: {national_id} | Group: {student_group}", ln=True, align='C')
            pdf.cell(0, 10, f"Evaluations: {eval_count} | Behaviors: {beh_count} | Quiz Avg: {quiz_avg_str}", ln=True, align='C')
            buf = io.BytesIO()
            pdf.output(buf)
            return buf.getvalue()
        except Exception:
            pass
            
    html = generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str)
    return html.encode('utf-8')

# Helper Constants
FIFTH_GRADE_SUBJECTS = [
    "ریاضی", "علوم تجربی", "فارسی (خوانداری)", "نگارش فارسی", "مطالعات اجتماعی", "هدیه‌های آسمان", "آموزش قرآن"
]

EVALUATION_LEVELS = [
    "خیلی خوب 🌟", "خوب 🟢", "قابل قبول 🟡", "نیاز به تلاش مجدد 🔴"
]

CLASS_GROUPS = [
    "گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟", "گروه کاوشگر 🔍", "گروه اندیشه 🧠"
]

def load_students():
    try:
        with get_connection() as conn:
            df = safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, pin_code, parent_phone, student_group, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'pin_code', 'parent_phone', 'student_group', 'notes'])

def check_teacher_password(pwd):
    if 'teacher_password' not in st.session_state:
        st.session_state['teacher_password'] = '1234'
    return pwd.strip() == st.session_state['teacher_password']

def update_teacher_password(new_pwd):
    st.session_state['teacher_password'] = new_pwd.strip()

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

# ---------------------------------------------------------
# TOP APP HEADER & AUTH BAR
# ---------------------------------------------------------
curr_shamsi = get_current_shamsi_date()
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 تاریخ امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Navigation & Login Header Bar
col_h1, col_h2 = st.columns([2, 2])

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
            pass_input = st.text_input("رمز:", type="password", key="top_pass_input", label_visibility="collapsed")
            if pass_input:
                if check_teacher_password(pass_input):
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🔓 ورود موفقیت‌آمیز آموزگار!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است.")
        else:
            st.success("🟢 آموزگار وارد شده است")
            with st.popover("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if check_teacher_password(old_p):
                        if new_p:
                            update_teacher_password(new_p)
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

st.markdown("---")

# ---------------------------------------------------------
# SINGLE, RELIABLE SIDEBAR NAVIGATION MENU
# ---------------------------------------------------------
MENU_OPTIONS = [
    "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
    "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (معلم)",
    "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی (معلم)",
    "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی (معلم)",
    "5️⃣ ✏️ آزمون‌ساز آنلاین (معلم)",
    "6️⃣ 📱 شرکت در آزمون (دانش‌آموز)",
    "7️⃣ 📊 داشبورد و کارنامه جامع"
]

st.sidebar.markdown("### 📌 منوی مدیریت سامانه")
menu_choice = st.sidebar.radio(
    "انتخاب بخش منو:",
    MENU_OPTIONS,
    index=0,
    key="single_fast_nav_radio"
)

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING & OVERVIEW PAGE (FULL RICHEST INTRO)
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    
    <div class="quote-card">
        <h3 style="color: #fbbf24 !important; margin-bottom: 12px;">📜 رهنمودهای مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h3>
        <p style="font-size: 1.15rem; line-height: 1.9; text-align: justify !important; color: #f8fafc !important;">
        «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    
    <div class="card-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان همراه با بازخوردهای اصلاحی جهت ارائه به اولیا.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با امنیت ۴ لایه (رمز، سوالات تصادفی، قفل ارسال و ثبت چهره)</h4>
        <p>طراحی آزمون از طریق فایل اکسل، کپی-پیست متن یا تکی، تعیین زمان معکوس، تصحیح خودکار و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن و بارگذاری اکسل</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت بارگذاری دسته‌جمعی اسامی از اکسل کمتر از ۱ ثانیه.</p>
    </div>
    
    <div class="card-box">
        <h4>4️⃣ کارنامه جامع و پوشه کار دیجیتال قابل چاپ (PDF)</h4>
        <p>صدور لوح‌های تقدیر/هشدار انضباطی و کارنامه تحصیلی کامل به همراه نمودار رشد و تحلیل تربیتی معلم.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES & EXCEL BULK UPLOAD (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها",
        "✏️ ویرایش اطلاعات دانش‌آموز",
        "📊 ثبت دسته‌جمعی از اکسل",
        "➕ ثبت دانش‌آموز جدید",
        "🗑️ حذف پرونده دانش‌آموز"
    ])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
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
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'pin_code': 'رمز ۴ رقمی',
                'parent_phone': 'شماره همراه اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'ملاحظات'
            }), use_container_width=True, hide_index=True)
        else:
            st.info("هنوز دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        students_df = load_students()
        if not students_df.empty:
            st.subheader("✏️ ویرایش کامل اطلاعات پرونده دانش‌آموز")
            st_to_edit = st.selectbox("انتخاب دانش‌آموز جهت ویرایش:", students_df['full_name'].tolist(), key="edit_student_dropdown")
            st_info = students_df[students_df['full_name'] == st_to_edit].iloc[0]
            
            with st.form("edit_student_form"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_fn = st.text_input("نام:", value=st_info['full_name'].split()[0] if st_info['full_name'] else "")
                    e_nid = st.text_input("کد ملی:", value=str(st_info['national_id'] or ""))
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(st_info['student_group']) if st_info['student_group'] in CLASS_GROUPS else 0)
                with col_e2:
                    e_ln = st.text_input("نام خانوادگی:", value=" ".join(st_info['full_name'].split()[1:]) if len(st_info['full_name'].split()) > 1 else "")
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=str(st_info['pin_code'] or "1234"))
                    e_ph = st.text_input("شماره همراه اولیا:", value=str(st_info['parent_phone'] or ""))
                e_notes = st.text_area("ملاحظات ویژه پرونده:", value=str(st_info['notes'] or ""))
                
                if st.form_submit_button("💾 ذخیره تغییرات ویرایش‌یافته"):
                    s_id = int(st_info['id'])
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE students SET first_name=?, last_name=?, national_id=?, pin_code=?, parent_phone=?, student_group=?, notes=? WHERE id=?",
                            (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_pin.strip(), e_ph.strip(), e_grp, e_notes.strip(), s_id)
                        )
                        conn.commit()
                    st.success(f"اطلاعات پرونده دانش‌آموز {e_fn} {e_ln} با موفقیت به‌روزرسانی شد.")
                    st.rerun()
        else:
            st.info("دانش‌آموزی جهت ویرایش وجود ندارد.")

    with tab3:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی دانش‌آموزان از فایل اکسل (در ۱ ثانیه)")
        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا (csv) اسامی را انتخاب کنید:", type=["xlsx", "csv"], key=f"excel_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} دانش‌آموز پیدا شد.")
                st.dataframe(df_up, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره تمام اسامی در دیتابیس"):
                    with get_connection() as conn:
                        added_count = 0
                        shamsi_today = get_current_shamsi_date()
                        for _, row in df_up.iterrows():
                            fn = str(row.get('نام', '')).strip()
                            ln = str(row.get('نام خانوادگی', '')).strip()
                            nid = str(row.get('کد ملی', '')).strip()
                            pin = str(row.get('رمز اختصاصی', '1234')).strip()
                            ph = str(row.get('شماره همراه اولیا', '')).strip()
                            grp = str(row.get('گروه کلاسی', 'گروه ارمغان 🚀')).strip()
                            
                            if fn and ln:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                        (fn, ln, nid, pin, ph, grp, shamsi_today)
                                    )
                                    added_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab4:
        with st.form("add_single_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                fn = st.text_input("نام:*")
                nid = st.text_input("کد ملی دانش‌آموز:")
                grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS)
            with col2:
                ln = st.text_input("نام خانوادگی:*")
                pin = st.text_input("رمز ۴ رقمی اختصاصی:", value="1234")
                ph = st.text_input("شماره همراه اولیا:")
            notes = st.text_area("توضیحات تکمیلی:")
            
            if st.form_submit_button("ثبت دانش‌آموز"):
                if fn.strip() and ln.strip():
                    try:
                        shamsi_today = get_current_shamsi_date()
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, pin_code, parent_phone, student_group, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (fn.strip(), ln.strip(), nid.strip(), pin.strip(), ph.strip(), grp, notes.strip(), shamsi_today)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت گردید.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

    with tab5:
        students_df = load_students()
        if not students_df.empty:
            st.subheader("🗑️ حذف کامل پرونده دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", students_df['full_name'].tolist(), key="del_student_sel")
            if st.button("🗑️ حذف قطعی پرونده دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {student_to_delete} با موفقیت حذف گردید.")
                st.rerun()

# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATIONS (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:", placeholder="مثلاً: در مفاهیم کسرها و مخرج مشترک مهارتی عالی دارد...")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} برای {selected_student} ثبت شد.")
            
        st.markdown("---")
        st.subheader(f"🔍 سوابق ارزشیابی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            e_history = safe_read_sql("""
                SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not e_history.empty:
            st.dataframe(e_history, use_container_width=True, hide_index=True)
        else:
            st.info("ارزشیابی درسی برای این دانش‌آموز ثبت نشده است.")

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
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار (مثلاً: مسئولیت‌پذیری در گروه):")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            
        desc = st.text_area("شرح جزییات و اقدامات تربیتی آموزگار:")
        
        if st.button("ثبت مشاهده رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            st_info = students_df[students_df['full_name'] == selected_student].iloc[0]
            nat_id = st_info['national_id'] or 'ثبت نشده'
            st_grp = st_info['student_group'] or 'بدون گروه'
            
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title.strip(), desc.strip(), log_date.strip())
                )
                conn.commit()
            st.success("✅ مشاهده رفتاری با موفقیت در سیستم ذخیره شد.")
            
            # Render Online Card inside App safely
            html_card = generate_behavior_report_html(selected_student, nat_id, st_grp, b_type, title.strip(), desc.strip(), log_date.strip())
            with st.expander("👁️ مشاهده برگه رسمی لوح انضباطی (نمایش درون سامانه)", expanded=True):
                components.html(html_card, height=480, scrolling=True)
                
            beh_pdf = generate_behavior_report_pdf(selected_student, nat_id, st_grp, b_type, title.strip(), desc.strip(), log_date.strip())
            is_pos = 'مثبت' in b_type or 'تشویق' in b_type
            btn_label = "📥 دانلود تقدیرنامه و لوح سپاس رسمی (PDF)" if is_pos else "📥 دانلود برگه هشدار و اطلاع‌رسانی اولیا (PDF)"
            st.download_button(btn_label, data=beh_pdf, file_name=f"behavior_report_{s_id}_{random.randint(100,999)}.pdf", mime="application/pdf")

        st.markdown("---")
        st.subheader(f"📋 گزارش انضباطی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            b_h = safe_read_sql("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not b_h.empty:
            st.dataframe(b_h, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 5. ONLINE QUIZ CREATOR (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و مدیریت آزمون)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs([
        "➕ طراحی دستی سوالات",
        "📄 ورودی سریع از متن (کپی-پیست)",
        "📊 نتایج و کارنامه آزمون‌ها"
    ])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1: quiz_title = st.text_input("عنوان آزمون:")
        with col2: quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="man_q_sub")
        with col3: duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
        num_q = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=20, value=2)
        
        st.markdown("---")
        q_data = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            qt = st.text_input(f"متن سوال {i+1}:", key=f"mqt_{i}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: o1 = st.text_input(f"گزینه ۱:", key=f"mo1_{i}")
            with c2: o2 = st.text_input(f"گزینه ۲:", key=f"mo2_{i}")
            with c3: o3 = st.text_input(f"گزینه ۳:", key=f"mo3_{i}")
            with c4: o4 = st.text_input(f"گزینه ۴:", key=f"mo4_{i}")
            corr = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"mcorr_{i}")
            q_data.append((qt, o1, o2, o3, o4, corr))
            st.markdown("---")
            
        if st.button("انتشار آزمون دستی"):
            if quiz_title and all(q[0] for q in q_data):
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (quiz_title, quiz_subject, duration, shamsi_today))
                    qid = cursor.lastrowid
                    for q in q_data:
                        cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?)", (qid, q[0], q[1], q[2], q[3], q[4], q[5]))
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' منتشر گردید!")
            else:
                st.warning("لطفاً عنوان و متن تمامی سوالات را وارد کنید.")

    with tab_q2:
        st.subheader("📄 ورودی سریع سوالات با کپی-پیست")
        col_tx1, col_tx2, col_tx3 = st.columns(3)
        with col_tx1: tx_title = st.text_input("عنوان آزمون:", key="tx_q_title")
        with col_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with col_tx3: tx_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15, key="tx_dur")
        
        pasted_text = st.text_area("متن سوالات را کپی کرده و اینجا پیست کنید:")
        if st.button("ثبت آزمون از متن کپی شده"):
            if tx_title and pasted_text:
                lines = pasted_text.strip().split("\n")
                shamsi_today = get_current_shamsi_date()
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (tx_title, tx_subject, tx_duration, shamsi_today))
                    qid = cursor.lastrowid
                    for line in lines:
                        if line.strip():
                            cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (?, 'mcq', ?, 'گزینه ۱', 'گزینه ۲', 'گزینه ۳', 'گزینه ۴', 1)", (qid, line.strip()))
                    conn.commit()
                st.success(f"آزمون '{tx_title}' با موفقیت از متن ثبت شد.")
            else:
                st.warning("لطفاً عنوان و متن سوالات را وارد کنید.")

    with tab_q3:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان آزمون', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            st.subheader("📈 مشاهده کارنامه شرکت‌کنندگان")
            selected_quiz_id = st.selectbox("انتخاب آزمون:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان آزمون'].values[0])
            with get_connection() as conn:
                results_df = safe_read_sql("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات',
                           r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True, hide_index=True)
            else:
                st.info("هنوز دانش‌آموزی در این آزمون شرکت نکرده است.")

# ---------------------------------------------------------
# 6. STUDENT QUIZ TAKING INTERFACE
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم ثبت نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1: student_name = st.selectbox("نام و نام خانوادگی خود را انتخاب کنید:*", students_df['full_name'].tolist())
        with col2: quiz_name = st.selectbox("آزمون مورد نظر را انتخاب کنید:*", quizzes_df['title'].tolist())
        
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید. درصد نهایی کسب‌شده: {existing['percentage']:.1f}٪")
        else:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
                
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز:", type="password", key=f"q_pin_{s_id}_{q_id}")
            if input_pin.strip() != pin_db:
                st.info("💡 جهت شروع آزمون، رمز ۴ رقمی اختصاصی خود را وارد نمایید (رمز پیش‌فرض: 1234).")
            else:
                st.success("🔓 رمز عبور تایید شد. سوالات آزمون آماده می‌باشد:")
                with get_connection() as conn:
                    questions_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                    
                questions = [dict(q) for q in questions_rows]
                
                if f"shuffled_q_{q_id}_{s_id}" not in st.session_state:
                    shuffled = list(questions)
                    random.seed(s_id + q_id)
                    random.shuffle(shuffled)
                    st.session_state[f"shuffled_q_{q_id}_{s_id}"] = shuffled
                    
                shuffled_questions = st.session_state[f"shuffled_q_{q_id}_{s_id}"]
                student_mcq_ans = {}
                student_essay_ans = {}
                
                st.markdown("---")
                with st.form(f"take_quiz_form_{s_id}_{q_id}"):
                    for idx, q in enumerate(shuffled_questions):
                        st.markdown(f"### 📌 سوال {idx+1}: {q['question_text']}")
                        if q['question_type'] == 'mcq':
                            opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                            ans = st.radio(
                                f"پاسخ سوال {idx+1}:",
                                options=[1, 2, 3, 4],
                                format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                                key=f"ans_mcq_{q['id']}_{s_id}"
                            )
                            student_mcq_ans[q['id']] = (ans, q['correct_option'])
                        else:
                            e_ans = st.text_area(f"پاسخ تشریحی شما:", key=f"ans_essay_{q['id']}_{s_id}")
                            student_essay_ans[q['id']] = e_ans
                        st.markdown("---")
                        
                    st.markdown("##### 📸 ثبت تصویر چهره جهت احراز هویت آزمون")
                    photo = st.camera_input("ثبت تصویر چهره دانش‌آموز", key=f"cam_{s_id}_{q_id}")
                    
                    if st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها"):
                        photo_data_str = ""
                        if photo is not None:
                            import base64
                            bytes_data = photo.getvalue()
                            photo_data_str = "data:image/png;base64," + base64.b64encode(bytes_data).decode('utf-8')
                            
                        correct_count = 0
                        mcq_total = len(student_mcq_ans)
                        for qid, (u_ans, c_ans) in student_mcq_ans.items():
                            if u_ans == c_ans:
                                correct_count += 1
                        pct = (correct_count / mcq_total * 100) if mcq_total > 0 else 100.0
                        
                        essay_json_str = json.dumps(student_essay_ans, ensure_ascii=False)
                        shamsi_submitted = f"{get_current_shamsi_date()} - {datetime.datetime.now().strftime('%H:%M')}"
                        
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, photo_data, essay_answers, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (q_id, s_id, correct_count, mcq_total, pct, photo_data_str, essay_json_str, shamsi_submitted)
                            )
                            conn.commit()
                            
                        st.balloons()
                        st.success(f"🎉 پاسخ‌های شما با موفقیت ثبت شد! نمره‌ی بخش تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")
                        st.rerun()

# ---------------------------------------------------------
# 7. DASHBOARD & STUDENT PORTFOLIO
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        # Privacy Guard for Portfolio
        if not st.session_state['is_teacher_logged_in']:
            with get_connection() as conn:
                real_pin = conn.execute("SELECT pin_code FROM students WHERE id = ?", (s_id,)).fetchone()
                pin_code_db = str(real_pin['pin_code']).strip() if real_pin and real_pin['pin_code'] else '1234'
            
            st.info("🔒 جهت حفظ حریم خصوصی و کرامت دانش‌آموزان، کارنامه و پوشه کار محرمانه می‌باشد.")
            input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:", type="password", key="portfolio_pin_guard")
            if input_pin.strip() != pin_code_db:
                st.warning("⚠️ برای مشاهده کارنامه، لطفاً رمز ۴ رقمی اختصاصی دانش‌آموز را به درستی وارد کنید.")
                st.stop()
            else:
                st.success("🔓 احراز هویت موفقیت‌آمیز دانش‌آموز!")
                
        # Export & Display Comprehensive Report Card
        st.markdown(f"### 📄 پوشه کار و کارنامه تحصیلی: **{selected_student}**")
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_str = f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون"
            st_row = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
            nat_id_str = st_row['national_id'] if st_row and st_row['national_id'] else 'ثبت نشده'
            phone_str = st_row['parent_phone'] if st_row and st_row['parent_phone'] else 'ثبت نشده'
            grp_str = st_row['student_group'] if st_row and st_row['student_group'] else 'بدون گروه'

        # Render HTML Report Card safely INSIDE an Iframe using components.html
        portfolio_html = generate_portfolio_report_html(selected_student, nat_id_str, phone_str, grp_str, eval_count, beh_count, quiz_avg_str)
        with st.expander("👁️ مشاهده برگه رسمی کارنامه (نمایش آنلاین درون سامانه)", expanded=True):
            components.html(portfolio_html, height=520, scrolling=True)

        portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
        st.download_button("📥 دانلود فایل پی دی اف کارنامه (PDF معتبر قابل پرینت)", data=portfolio_pdf, file_name=f"report_card_{selected_student}.pdf", mime="application/pdf")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2:
            st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3:
            st.metric("میانگین درصد آزمون آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = safe_read_sql("SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ (شمسی)' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = safe_read_sql("SELECT id, behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ (شمسی)' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)
                
                st.markdown("##### 📥 صدور گزارش PDF رسمی برای موارد رفتاری فوق:")
                st_info = students_df[students_df['full_name'] == selected_student].iloc[0]
                nat_id = st_info['national_id'] or 'ثبت نشده'
                st_grp = st_info['student_group'] or 'بدون گروه'
                
                for _, b_row in df_b.iterrows():
                    col_b1, col_b2 = st.columns([3, 1])
                    with col_b1:
                        st.markdown(f"🔹 **{b_row['نوع']}** — {b_row['عنوان رفتار']} ({b_row['تاریخ (شمسی)']})")
                    with col_b2:
                        single_pdf = generate_behavior_report_pdf(
                            selected_student, nat_id, st_grp,
                            b_row['نوع'], b_row['عنوان رفتار'], b_row['توضیحات تکمیلی'], b_row['تاریخ (شمسی)']
                        )
                        is_pos = 'مثبت' in b_row['نوع'] or 'تشویق' in b_row['نوع']
                        btn_txt = "📥 PDF تقدیرنامه" if is_pos else "📥 PDF هشدار"
                        st.download_button(btn_txt, data=single_pdf, file_name=f"behavior_{b_row['id']}.pdf", mime="application/pdf", key=f"dl_b_{b_row['id']}")
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت (شمسی)', r.photo_data
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                show_df = df_q.drop(columns=['photo_data'], errors='ignore')
                st.dataframe(show_df, use_container_width=True, hide_index=True)
                
                st.markdown("##### 📸 تصاویر ثبت‌شده چهره در زمان تحویل آزمون‌ها:")
                for _, r_row in df_q.iterrows():
                    if r_row['photo_data']:
                        st.image(r_row['photo_data'], caption=f"آزمون: {r_row['عنوان آزمون']} | درصد: {r_row['درصد ٪']:.1f}٪ | زمان: {r_row['زمان ثبت (شمسی)']}", width=180)
                
                st.markdown("##### 📈 نمودار رشد نمرات آزمون‌ها:")
                df_chart = safe_read_sql("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
                if not df_chart.empty:
                    st.line_chart(df_chart.set_index('آزمون'))
            else:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")

