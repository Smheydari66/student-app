
import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import random

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
# Page Configuration & Full RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS Styling & Fixes
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea, label, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #ffffff !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    }
    
    /* Responsive Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white !important;
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
    
    /* Button Styles & Text Wrap Fixes */
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
    
    /* Text Inputs, Selectboxes, Dataframes */
    input, select, textarea, div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border-radius: 8px !important;
    }
    
    /* Radio Buttons Nav */
    div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    div[role="radiogroup"] label {
        background-color: rgba(30, 41, 59, 0.7) !important;
        padding: 10px 16px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s !important;
    }
    
    div[role="radiogroup"] label:hover {
        background-color: rgba(37, 99, 235, 0.4) !important;
        border-color: #3b82f6 !important;
    }
    
    /* Popover Fix */
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
        
        # Teacher Auth Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        # Migrations for existing databases
        columns_to_add = [
            ("students", "pin_code", "TEXT DEFAULT '1234'"),
            ("students", "student_group", "TEXT DEFAULT 'بدون گروه'"),
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

# Safe Read Helper
def safe_read_sql(query, conn, params=None):
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception:
        init_db()
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception:
            return pd.DataFrame()

# ---------------------------------------------------------
# Default Quiz Seeder
# ---------------------------------------------------------
def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if count == 0:
            shamsi_today = get_current_shamsi_date()
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                ("آزمونک جامع فصل اول ریاضی و علوم پنجم", "ریاضی", 60, shamsi_today)
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
import re

with open('/workspace/scratch/student_management_app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Let's inspect helper functions location
pdf_helpers = '''
# ---------------------------------------------------------
# PDF Generator Helpers (Official Letterheads & Reports)
# ---------------------------------------------------------
def generate_chart_b64(quiz_titles, quiz_pcts, eval_counts):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 2.8), dpi=150)
    fig.patch.set_facecolor('#ffffff')
    
    if quiz_pcts:
        ax1.bar(range(len(quiz_pcts)), quiz_pcts, color='#2563eb', width=0.4)
        ax1.set_ylim(0, 110)
        ax1.set_title('درصد آزمون‌های آنلاین (٪)', fontsize=9, fontname='DejaVu Sans')
        ax1.set_xticks(range(len(quiz_titles)))
        ax1.set_xticklabels([f'آزمون {i+1}' for i in range(len(quiz_titles))], fontsize=8, fontname='DejaVu Sans')
    else:
        ax1.text(0.5, 0.5, 'آزمونی ثبت نشده', ha='center', va='center', fontsize=9, fontname='DejaVu Sans')
        ax1.axis('off')
        
    labels = list(eval_counts.keys())
    values = list(eval_counts.values())
    colors = ['#16a34a', '#2563eb', '#eab308', '#dc2626']
    if sum(values) > 0:
        ax2.bar(labels, values, color=colors[:len(labels)], width=0.4)
        ax2.set_title('توزیع سطح ارزشیابی‌ها', fontsize=9, fontname='DejaVu Sans')
    else:
        ax2.text(0.5, 0.5, 'ارزشیابی ثبت نشده', ha='center', va='center', fontsize=9, fontname='DejaVu Sans')
        ax2.axis('off')
        
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return b64

def generate_behavior_report_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    is_positive = 'مثبت' in b_type or 'تشویق' in b_type
    theme_color = '#15803d' if is_positive else '#b91c1c'
    bg_color = '#f0fdf4' if is_positive else '#fef2f2'
    border_color = '#22c55e' if is_positive else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_positive else 'کارت اطلاع‌رسانی و هشدار انضباطی اولیا'
    
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 30px; color: #0f172a; line-height: 1.8; }}
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
    
    html_path = f"/workspace/scratch/b_report_{random.randint(1000, 9999)}.html"
    pdf_path = html_path.replace(".html", ".pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    try:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', html_path, '--outdir', '/workspace/scratch'], capture_output=True)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        if os.path.exists(html_path): os.remove(html_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        return pdf_bytes
    except Exception:
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
        
        df_evals = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ? ORDER BY id DESC", conn, params=(student_id,))
        df_beh = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ? ORDER BY id DESC", conn, params=(student_id,))
        df_quizzes = safe_read_sql("SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'تاریخ ثبت' FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC", conn, params=(student_id,))

    quiz_titles = df_quizzes['عنوان آزمون'].tolist() if not df_quizzes.empty else []
    quiz_pcts = df_quizzes['درصد ٪'].tolist() if not df_quizzes.empty else []
    
    eval_counts = {
        "خیلی خوب": len(df_evals[df_evals['سطح توصیفی'].str.contains('خیلی خوب')]) if not df_evals.empty else 0,
        "خوب": len(df_evals[df_evals['سطح توصیفی'].str.contains('خوب')]) if not df_evals.empty else 0,
        "قابل قبول": len(df_evals[df_evals['سطح توصیفی'].str.contains('قابل قبول')]) if not df_evals.empty else 0,
        "نیازمند تلاش": len(df_evals[df_evals['سطح توصیفی'].str.contains('تلاش')]) if not df_evals.empty else 0
    }
    
    chart_b64 = generate_chart_b64(quiz_titles[:5], quiz_pcts[:5], eval_counts)
    
    quiz_avg = sum(quiz_pcts)/len(quiz_pcts) if quiz_pcts else None
    beh_pos_count = len(df_beh[df_beh['نوع'].str.contains('مثبت|تشویق')]) if not df_beh.empty else 0
    beh_neg_count = len(df_beh[df_beh['نوع'].str.contains('پیگیری|توجه|منفی')]) if not df_beh.empty else 0
    
    strengths_list = []
    improvement_list = []
    
    if quiz_avg and quiz_avg >= 85:
        strengths_list.append(f"عملکرد عالی در آزمون‌های آنلاین با میانگین درصد {quiz_avg:.1f}٪")
    elif quiz_avg and quiz_avg < 70:
        improvement_list.append(f"نیاز به مرور و تمرین بیشتر در مفاهیم آزمون‌ها (میانگین درصد فعلی: {quiz_avg:.1f}٪)")
        
    if eval_counts["خیلی خوب"] > 0:
        strengths_list.append(f"احراز سطح «خیلی خوب» در {eval_counts['خیلی خوب']} مورد ارزشیابی توصیفی درسی")
        
    if beh_pos_count > 0:
        strengths_list.append(f"ثبت {beh_pos_count} مورد تشویق و رفتار مثبت انضباطی در کلاس درس")
    if beh_neg_count > 0:
        improvement_list.append(f"نیاز به توجه بیشتر به نظم و قانون‌مداری کلاسی ({beh_neg_count} مورد نیاز به پیگیری)")
        
    if not strengths_list:
        strengths_list.append("حضور منظم و فعال در برنامه‌های آموزشی کلاس درس")
    if not improvement_list:
        improvement_list.append("تثبیت مهارت‌های حل مسئله در دروس ریاضی و علوم")
        
    strengths_html = "".join([f"<li>{s}</li>" for s in strengths_list])
    improvement_html = "".join([f"<li>{i}</li>" for i in improvement_list])
    
    shamsi_today = get_current_shamsi_date()
    
    eval_table_html = df_evals.to_html(index=False, classes="data-table") if not df_evals.empty else "<p>ارزشیابی درسی ثبت نشده است.</p>"
    beh_table_html = df_beh.to_html(index=False, classes="data-table") if not df_beh.empty else "<p>مورد رفتاری ثبت نشده است.</p>"
    quiz_table_html = df_quizzes.to_html(index=False, classes="data-table") if not df_quizzes.empty else "<p>آزمون آنلاینی ثبت نشده است.</p>"
    
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; direction: rtl; text-align: right; padding: 25px; color: #0f172a; line-height: 1.6; font-size: 12px; }}
.letterhead {{ border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
.org-name {{ color: #1e3a8a; font-size: 13px; font-weight: bold; }}
.school-name {{ color: #0f172a; font-size: 17px; font-weight: bold; margin-top: 3px; }}
.sub-header {{ color: #475569; font-size: 11px; margin-top: 2px; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; background: #f8fafc; border-radius: 6px; overflow: hidden; }}
.meta-table td {{ padding: 6px 10px; border: 1px solid #cbd5e1; font-size: 12px; }}
.section-title {{ color: #1e3a8a; font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 8px; border-right: 4px solid #2563eb; padding-right: 8px; }}
.data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 11px; }}
.data-table th {{ background: #1e3a8a; color: #ffffff; padding: 6px; border: 1px solid #1e3a8a; text-align: center; }}
.data-table td {{ padding: 5px; border: 1px solid #cbd5e1; text-align: center; }}
.analysis-box {{ background: #f0f9ff; border: 1px solid #0284c7; border-radius: 8px; padding: 12px; margin-top: 15px; }}
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
    <div class="sub-header">گزارش جامع عملکرد تحصیلی و پوشه کار دیجیتال — سال تحصیلی ۱۴۰۴-۱۴۰۵</div>
</div>

<table class="meta-table">
    <tr>
        <td><b>نام دانش‌آموز:</b> {student_name}</td>
        <td><b>کد ملی:</b> {national_id}</td>
        <td><b>گروه کلاسی:</b> {student_group}</td>
        <td><b>شماره اولیا:</b> {parent_phone}</td>
        <td><b>تاریخ صدور:</b> {shamsi_today}</td>
    </tr>
</table>

<div class="section-title">📊 نمودار تحلیلی رشد تحصیلی و توزیع ارزشیابی‌ها</div>
<div style="text-align: center; margin: 10px 0;">
    <img src="data:image/png;base64,{chart_b64}" style="width: 85%; max-width: 650px;">
</div>

<div class="section-title">📝 ارزشیابی‌های کیفی-توصیفی ۷ عنوان درسی پایه پنجم</div>
{eval_table_html}

<div class="section-title">🌟 سوابق رفتاری و مشاهدات انضباطی</div>
{beh_table_html}

<div class="section-title">✏️ نتایج آزمون‌های آنلاین با تصحیح هوشمند</div>
{quiz_table_html}

<div class="analysis-box">
    <h4 style="color: #0369a1; margin-top: 0; margin-bottom: 8px;">💡 تحلیل جامع آموزشی و توصیه‌های تربیتی آموزگار:</h4>
    <p style="text-align: justify; margin-bottom: 8px;">
        دانش‌آموز عزیز <b>{student_name}</b> در ارزیابی‌های دوره جاری کلاس پنجم دبستان شهید مطهری، روندی فعال را طی نموده است. خلاصه‌ی تحلیل عملکرد وی به شرح زیر می‌باشد:
    </p>
    <b>🌟 نقاط قوت تحصیلی و انضباطی:</b>
    <ul style="margin-top: 4px; margin-bottom: 8px; padding-right: 20px;">
        {strengths_html}
    </ul>
    <b>🎯 زمینه‌های نیازمند تمرین و پیگیری اولیا در منزل:</b>
    <ul style="margin-top: 4px; margin-bottom: 4px; padding-right: 20px;">
        {improvement_html}
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
    
    html_path = f"/workspace/scratch/portfolio_{random.randint(1000, 9999)}.html"
    pdf_path = html_path.replace(".html", ".pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    try:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', html_path, '--outdir', '/workspace/scratch'], capture_output=True)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        if os.path.exists(html_path): os.remove(html_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        return pdf_bytes
    except Exception:
        return html.encode('utf-8')
'''

print('pdf_helpers defined successfully!')


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
        df = safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, pin_code, parent_phone, student_group, notes FROM students", conn)
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
    curr_shamsi = get_current_shamsi_date()
    st.markdown(f"""
    <div class="main-header">
        <h1>🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h1>
        <p style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">🏫 دبستان شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
        <p style="font-size: 1.1rem; opacity: 0.9;">طراح و آموزگار پایه پنجم: <b>سید موسی حیدری</b> | امروز: <b>{curr_shamsi}</b></p>
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
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت به‌ویژه ساحت علمی-فناوری و اخلاقی.</li>
                <li><b>ارزشیابی توصیفی کشوری:</b> رعایت دقیق بارم‌بندی و سطوح عملکردی (خیلی خوب، خوب، قابل قبول، نیاز به تلاش).</li>
                <li><b>توسعه عدالت آموزشی:</b> امکان دسترسی آسان تمامی دانش‌آموزان با گوشی، تبلت و کامپیوتر بدون نیاز به نصب.</li>
                <li><b>ارتباط مستمر خانه و مدرسه:</b> ارائه گزارش‌های دوره‌ای قابل چاپ جهت درج در پوشه کار فیزیکی.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس و آزمون آنلاین", use_container_width=True):
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
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری | تاریخ امروز: {curr_shamsi}</p>
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

with col_h3:
    if st.button("🏠 صفحه خوش‌آمدگویی"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# NAVIGATION MENU (RADIO BUTTONS - 100% READONLY & CLICKABLE)
# ---------------------------------------------------------
st.markdown("### 📌 منوی بخش‌های سامانه (انتخاب کنید):")

if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]

menu_choice = st.radio("منو:", menu_options, label_visibility="collapsed", key="main_nav_menu")

# Teacher Auth Guard Helper
def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING & OVERVIEW PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    curr_shamsi = get_current_shamsi_date()
    st.markdown(f"""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران | تاریخ امروز: <b>{curr_shamsi}</b></p>
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
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES & EXCEL BULK UPLOAD (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت پرونده دانش‌آموزان و گروه‌بندی (۲۹ نفر)")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 لیست دانش‌آموزان و گروه‌ها",
        "✏️ ویرایش کامل اطلاعات دانش‌آموز",
        "🗑️ حذف پرونده دانش‌آموز",
        "📊 ثبت دسته‌جمعی از اکسل",
        "➕ ثبت دانش‌آموز جدید (تکی)"
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
                'notes': 'ملاحظات پرونده'
            }), use_container_width=True, hide_index=True)
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("✏️ ویرایش کامل مشخصات دانش‌آموز")
        students_df = load_students()
        if not students_df.empty():
            sel_st_edit = st.selectbox("دانش‌آموز مورد نظر جهت ویرایش را انتخاب کنید:", students_df['full_name'].tolist(), key="tab_edit_sel")
            s_row = students_df[students_df['full_name'] == sel_st_edit].iloc[0]
            s_id = int(s_row['id'])

            with get_connection() as conn:
                full_rec = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()

            with st.form("edit_student_full_form"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_fn = st.text_input("نام:*", value=full_rec['first_name'])
                    e_nid = st.text_input("کد ملی:", value=full_rec['national_id'] or "")
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=CLASS_GROUPS.index(full_rec['student_group']) if full_rec['student_group'] in CLASS_GROUPS else 0)
                with col_e2:
                    e_ln = st.text_input("نام خانوادگی:*", value=full_rec['last_name'])
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=full_rec['pin_code'] or "1234")
                    e_ph = st.text_input("شماره همراه اولیا:", value=full_rec['parent_phone'] or "")

                e_notes = st.text_area("ملاحظات پرونده / آموزشی / پزشکی:", value=full_rec['notes'] or "")

                if st.form_submit_button("💾 ذخیره تغییرات ویرایش‌یافته"):
                    if e_fn.strip() and e_ln.strip():
                        with get_connection() as conn:
                            conn.execute("""
                                UPDATE students 
                                SET first_name = ?, last_name = ?, national_id = ?, pin_code = ?, parent_phone = ?, student_group = ?, notes = ?
                                WHERE id = ?
                            """, (e_fn.strip(), e_ln.strip(), e_nid.strip(), e_pin.strip(), e_ph.strip(), e_grp, e_notes.strip(), s_id))
                            conn.commit()
                        st.success(f"اطلاعات دانش‌آموز '{e_fn} {e_ln}' با موفقیت ویرایش شد.")
                        st.rerun()
                    else:
                        st.error("نام و نام خانوادگی نمی‌تواند خالی باشد.")
        else:
            st.info("دانش‌آموزی برای ویرایش وجود ندارد.")

    with tab3:
        st.subheader("🗑️ حذف کامل پرونده دانش‌آموز")
        students_df = load_students()
        if not students_df.empty():
            sel_st_del = st.selectbox("دانش‌آموز مورد نظر جهت حذف را انتخاب کنید:", students_df['full_name'].tolist(), key="tab_del_sel")
            s_id_del = int(students_df[students_df['full_name'] == sel_st_del]['id'].values[0])

            st.warning(f"⚠️ **هشدار:** آیا از حذف کامل پرونده **{sel_st_del}** اطمینان دارید؟ تمام سوابق تحصیلی، ارزشیابی‌ها، موارد رفتاری و نمرات آزمون‌های این دانش‌آموز نیز حذف خواهند شد.")

            if st.button("🗑️ حذف قطعی پرونده دانش‌آموز"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id_del,))
                    conn.commit()
                st.success(f"پرونده دانش‌آموز {sel_st_del} با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("دانش‌آموزی جهت حذف وجود ندارد.")

    with tab4:
        st.subheader("📊 بارگذاری دسته‌جمعی ۲۹ دانش‌آموز از فایل اکسل (در ۱ ثانیه)")
        st.info("فایل اکسل باید شامل ستون‌های 'نام'، 'نام خانوادگی'، 'کد ملی'، 'شماره همراه اولیا' و 'گروه کلاسی' باشد.")

        sample_df = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "احمدی", "کد ملی": "1001112233", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09181111111", "گروه کلاسی": "گروه ارمغان 🚀"},
            {"نام": "محمدیاسین", "نام خانوادگی": "حیدری", "کد ملی": "1002223344", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09182222222", "گروه کلاسی": "گروه دانا 💡"}
        ])

        st.download_button(
            "📥 دانلود فایل اکسل الگوی اسامی دانش‌آموزان",
            sample_df.to_csv(index=False).encode('utf-8-sig'),
            "students_template.csv",
            "text/csv"
        )

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

    with tab5:
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
                        st.success(f"دانش‌آموز {fn} {ln} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")
# ---------------------------------------------------------
# 3. QUALITATIVE EVALUATION (TEACHER ONLY)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا اسامی دانش‌آموزان را ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("عنوان درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            
        feedback_text = st.text_area("بازخورد توصیفی و توصیه‌های آموزگار:", placeholder="مثلاً: در محاسبات کسرها عملکرد عالی دارد، نیاز به تمرین در ضرب اعشاری دارد.")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text.strip(), eval_date.strip())
                )
                conn.commit()
            st.success(f"ارزشیابی {selected_subject} برای {selected_student} با موفقیت ثبت شد.")

        st.markdown("---")
        st.subheader(f"📋 سوابق ارزشیابی: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY id DESC
            """, conn, params=(s_id,))
        if not eval_h.empty:
            st.dataframe(eval_h, use_container_width=True, hide_index=True)

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
            title = st.text_input("عنوان رفتار:")
            log_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date())
            
        desc = st.text_area("جزییات و اقدامات انجام‌شده:")
        
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
            
            # Generate instant PDF Report
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
    st.header("✏️ آزمون‌ساز آنلاین (بارگذاری آسان از اکسل، متن یا دستی)")
    
    tab_q1, tab_q_excel, tab_q_text, tab_q_json, tab_q_results = st.tabs([
        "➕ طراحی دستی سوالات", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "📋 کپی-پیست متن یکجا (بدون فایل)", 
        "📥 فایل JSON", 
        "📊 نتایج و نمرات"
    ])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:", key="m_q_title")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="m_q_sub")
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60, key="m_q_dur")
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=2, key="m_q_num")
        
        questions_input = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی ۴ گزینه‌ای", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if q_type == "تستی ۴ گزینه‌ای":
                c1, c2, c3, c4 = st.columns(4)
                with c1: o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
                with c2: o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
                with c3: o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
                with c4: o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                corr = st.selectbox(f"گزینه صحیح:", [1, 2, 3, 4], key=f"corr_{i}")
                exp = st.text_area(f"تحلیل و پاسخ تشریحی سوال {i+1}:", key=f"exp_{i}")
                questions_input.append(('mcq', q_text, o1, o2, o3, o4, corr, None, exp))
            else:
                m_ans = st.text_area(f"پاسخ نمونه / کلید تصحیح سوال {i+1}:", key=f"mans_{i}")
                exp = st.text_area(f"تحلیل آموزشی سوال {i+1}:", key=f"exp_e_{i}")
                questions_input.append(('essay', q_text, None, None, None, None, 1, m_ans, exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون دستی"):
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

    with tab_q_excel:
        st.subheader("🌸 بارگذاری سریع سوالات از فایل اکسل (Excel / CSV)")
        st.info("💡 ستون‌های اکسل شامل 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱ تا ۴)' می‌باشد.")
        
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
                                o1 = get_col_val(row, ['گزینه ۱', 'گزینه 1', 'گزینه1', 'گزینه۱', 'option_1', 'option1', 'الف'])
                                o2 = get_col_val(row, ['گزینه ۲', 'گزینه 2', 'گزینه2', 'گزینه۲', 'option_2', 'option2', 'ب'])
                                o3 = get_col_val(row, ['گزینه ۳', 'گزینه 3', 'گزینه3', 'گزینه۳', 'option_3', 'option3', 'ج'])
                                o4 = get_col_val(row, ['گزینه ۴', 'گزینه 4', 'گزینه4', 'گزینه۴', 'option_4', 'option4', 'د'])
                                corr_str = get_col_val(row, ['گزینه صحیح', 'پاسخ صحیح', 'کلید', 'correct_option', 'correct'], '1')
                                try:
                                    corr = int(float(corr_str))
                                except (ValueError, TypeError):
                                    corr = 1
                                exp = get_col_val(row, ['تحلیل', 'پاسخ تشریحی', 'توضیحات', 'explanation'], '')
                                
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

    with tab_q_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون فایل)")
        st.info("💡 اگر فایلی ندارید، متن سوالات را مستقیم اینجا کپی-پیست کنید.")
        
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_title")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=30, key="tx_dur")
        
        sample_paste = "سوال ۱: حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱\nسوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"
        
        pasted_text = st.text_area("متن سوالات را کپی-پیست کنید (با کاراکتر | جدا کنید):", value=sample_paste, height=180)
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
                        if len(parts) > 5 and corr == 1:
                            try:
                                corr = int(parts[5].replace('پاسخ صحیح:', '').strip())
                            except ValueError:
                                corr = 1
                                
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (qid, q_txt, o1, o2, o3, o4, corr, None, 'ورود متنی'))
                        cnt += 1
                    conn.commit()
                st.success(f"🎉 آزمون '{tx_title}' شامل {cnt} سوال با موفقیت ساخته شد!")

    with tab_q_json:
        st.subheader("📥 بارگذاری فایل JSON (روش برنامه‌نویسی)")
        sample_json = {"title": "نمونه آزمون", "subject": "ریاضی", "duration_minutes": 30, "questions": [{"question_type": "mcq", "question_text": "نمونه سوال؟", "option_1": "الف", "option_2": "ب", "option_3": "ج", "option_4": "د", "correct_option": 1}]}
        st.download_button("📥 دانلود الگوی JSON", json.dumps(sample_json, ensure_ascii=False, indent=2), "template.json", "application/json")
        uploaded_json = st.file_uploader("فایل JSON را انتخاب کنید:", type=["json"], key="quiz_json_file")
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                st.success(f"فایل آزمون '{data.get('title')}' شناسایی شد شامل {len(data.get('questions', []))} سوال.")
                if st.button("⚡ بارگذاری و فعال‌سازی این آزمون", key="btn_create_js"):
                    shamsi_today = get_current_shamsi_date()
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                            (data.get('title'), data.get('subject', 'ریاضی'), data.get('duration_minutes', 60), shamsi_today)
                        )
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                qid, q.get('question_type', 'mcq'), q.get('question_text'),
                                q.get('option_1'), q.get('option_2'), q.get('option_3'), q.get('option_4'),
                                q.get('correct_option', 1), q.get('model_answer'), q.get('explanation')
                            ))
                        conn.commit()
                    st.success("آزمون با موفقیت بارگذاری و فعال شد!")
            except Exception as e:
                st.error(f"خطا در خواندن فایل JSON: {e}")

    with tab_q_results:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت (شمسی)' FROM quizzes", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 6. STUDENT QUIZ TAKING INTERFACE (WITH 4 SECURITY LAYERS)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
            
        s_row = students_df[students_df['full_name'] == student_name].iloc[0]
        s_id = int(s_row['id'])
        correct_pin = str(s_row.get('pin_code', '1234')).strip()
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        # 🔑 LAYER 1: PIN AUTHENTICATION
        st.markdown("##### 🔑 لایه ۱ امنیت: ورود رمز اختصاصی دانش‌آموز")
        user_pin = st.text_input("رمز ۴ رقمی اختصاصی خود را وارد کنید:*", type="password", key=f"st_pin_{s_id}_{q_id}")
        
        if not user_pin:
            st.info("💡 جهت دسترسی به سوالات آزمون، رمز ۴ رقمی اختصاصی خود را وارد کنید (رمز پیش‌فرض: 1234).")
        elif user_pin.strip() != correct_pin:
            st.error("❌ رمز ۴ رقمی اختصاصی اشتباه است. لطفاً رمز درست خود را وارد کنید.")
        else:
            st.success("✅ رمز اختصاصی تایید شد. خوش آمدید!")
            
            # 🔒 LAYER 3: CHECK IF ALREADY SUBMITTED
            with get_connection() as conn:
                existing = conn.execute("SELECT id, percentage, photo_data, submitted_at FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
                
            if existing:
                st.warning(f"🔒 این آزمون قبلاً توسط شما در تاریخ {existing['submitted_at']} تحویل داده شده و قفل گردیده است.")
                st.info(f"درصد بخش تستی کسب‌شده: {existing['percentage']:.1f}٪")
                if existing['photo_data']:
                    st.image(existing['photo_data'], caption="عکس ثبت‌شده چهره شما در زمان تحویل آزمون", width=220)
            else:
                duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
                st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه")
                
                # Fetch Questions
                with get_connection() as conn:
                    questions_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                    
                questions = [dict(q) for q in questions_rows]
                
                # 🔀 LAYER 2: SHUFFLE QUESTIONS FOR THIS STUDENT
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
                            e_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ans_essay_{q['id']}_{s_id}")
                            student_essay_ans[q['id']] = e_ans
                        st.markdown("---")
                        
                    # 📸 LAYER 4: CAMERA PHOTO CAPTURE
                    st.markdown("##### 📸 لایه ۴ امنیت: ثبت تصویر چهره جهت احراز هویت آزمون")
                    st.info("لطفاً دوربین گوشی/سیستم خود را روشن کرده و یک عکس واضح از چهره خود بگیرید:")
                    photo = st.camera_input("ثبت تصویر چهره دانش‌آموز", key=f"cam_{s_id}_{q_id}")
                    
                    submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                    
                    if submit_quiz:
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
        
        # Privacy & Security Guard for Portfolio
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
                
        # Export Comprehensive PDF Report
        col_pdf1, col_pdf2 = st.columns([3, 1])
        with col_pdf1:
            st.markdown(f"### 📄 پوشه کار و کارنامه تحصیلی: **{selected_student}**")
        with col_pdf2:
            portfolio_pdf = generate_comprehensive_portfolio_pdf(s_id)
            st.download_button("📥 دانلود کارنامه جامع (PDF رسمی با سربرگ و نمودار)", data=portfolio_pdf, file_name=f"report_card_{selected_student}.pdf", mime="application/pdf")
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
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
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

