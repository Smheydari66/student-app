import streamlit as st
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
# Database Initialization & Migration Helpers
# ---------------------------------------------------------
DB_PATH = "student_management.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=OFF;")
    return conn

def safe_str(val, default=""):
    if val is None or pd.isna(val):
        return default
    s = str(val).strip()
    return s if s else default

def safe_read_sql(query, conn, params=None):
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception:
        return pd.DataFrame()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_code TEXT UNIQUE,
            national_id TEXT,
            first_name TEXT NOT NULL,
            last_family_name TEXT NOT NULL,
            last_name TEXT,
            parent_phone TEXT,
            notes TEXT,
            student_group TEXT DEFAULT 'گروه ارمغان 🚀',
            pin_code TEXT DEFAULT '1234',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Auto-migration for missing columns
    cursor.execute("PRAGMA table_info(students)")
    cols = [r[1] for r in cursor.fetchall()]
    for c_name, c_type in [
        ('national_code', 'TEXT'),
        ('national_id', 'TEXT'),
        ('last_family_name', 'TEXT'),
        ('last_name', 'TEXT'),
        ('parent_phone', 'TEXT'),
        ('notes', 'TEXT'),
        ('student_group', 'TEXT DEFAULT "گروه ارمغان 🚀"'),
        ('pin_code', 'TEXT DEFAULT "1234"')
    ]:
        if c_name not in cols:
            try:
                cursor.execute(f"ALTER TABLE students ADD COLUMN {c_name} {c_type}")
            except Exception:
                pass

    # 2. Evaluations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT NOT NULL,
            eval_date TEXT,
            grade_level TEXT,
            level TEXT,
            feedback TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    # 3. Behavior Logs / Behaviors Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            behavior_type TEXT NOT NULL,
            title TEXT,
            description TEXT,
            log_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            log_date TEXT,
            behavior_type TEXT NOT NULL,
            score INTEGER DEFAULT 5,
            description TEXT,
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

    # 6. Quiz Results / Submissions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            submitted_at TEXT,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    
    conn.commit()
    conn.close()

def load_students():
    init_db()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students)")
        cols = [r[1] for r in cursor.fetchall()]
        
        ln_col = "last_family_name" if "last_family_name" in cols else ("last_name" if "last_name" in cols else "last_family_name")
        nc_col = "national_code" if "national_code" in cols else ("national_id" if "national_id" in cols else "national_code")
        
        df = pd.read_sql_query(f"SELECT *, {ln_col} AS last_family_name, {nc_col} AS national_code FROM students ORDER BY id ASC", conn)
        df = df.loc[:, ~df.columns.duplicated()]
        
        if not df.empty:
            df['first_name'] = df['first_name'].apply(lambda x: safe_str(x, 'دانش‌آموز'))
            df['last_family_name'] = df['last_family_name'].apply(lambda x: safe_str(x, ''))
            df['last_name'] = df['last_family_name']
            df['full_name'] = df.apply(lambda r: f"{r['first_name']} {r['last_family_name']}".strip(), axis=1)
            df['national_code'] = df['national_code'].apply(lambda x: safe_str(x, 'ثبت نشده'))
            df['national_id'] = df['national_code']
            df['parent_phone'] = df['parent_phone'].apply(lambda x: safe_str(x, 'ثبت نشده'))
            df['student_group'] = df['student_group'].apply(lambda x: safe_str(x, 'گروه ارمغان 🚀'))
            df['pin_code'] = df['pin_code'].apply(lambda x: safe_str(x, '1234'))
            df['notes'] = df['notes'].apply(lambda x: safe_str(x, ''))
        else:
            df = pd.DataFrame(columns=['id', 'first_name', 'last_family_name', 'last_name', 'full_name', 'national_code', 'national_id', 'parent_phone', 'notes', 'student_group', 'pin_code'])
        return df
    except Exception:
        return pd.DataFrame(columns=['id', 'first_name', 'last_family_name', 'last_name', 'full_name', 'national_code', 'national_id', 'parent_phone', 'notes', 'student_group', 'pin_code'])
    finally:
        conn.close()

def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res[0] == pwd if res else pwd == '1234'

def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ? WHERE id = 1", (new_pwd,))
        conn.commit()

def delete_single_student(student_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("DELETE FROM evaluations WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM behaviors WHERE student_id = ?", (student_id,))
        try: cursor.execute("DELETE FROM behavior_logs WHERE student_id = ?", (student_id,))
        except Exception: pass
        cursor.execute("DELETE FROM quiz_results WHERE student_id = ?", (student_id,))
        try: cursor.execute("DELETE FROM quiz_submissions WHERE student_id = ?", (student_id,))
        except Exception: pass
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()

def delete_all_students():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("DELETE FROM evaluations;")
        cursor.execute("DELETE FROM behaviors;")
        try: cursor.execute("DELETE FROM behavior_logs;")
        except Exception: pass
        cursor.execute("DELETE FROM quiz_results;")
        try: cursor.execute("DELETE FROM quiz_submissions;")
        except Exception: pass
        cursor.execute("DELETE FROM students;")
        conn.commit()

# ---------------------------------------------------------
# ReportLab PDF Helper Functions (100% Robust & Font-Safe)
# ---------------------------------------------------------
GLOBAL_FONT = 'Helvetica'
font_path = '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'
if os.path.exists(font_path):
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont('PersianFont', font_path))
        GLOBAL_FONT = 'PersianFont'
    except Exception:
        pass

def _rtl(text):
    if not text:
        return ''
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)[::-1]

def draw_pdf_header(c, w, h, doc_title, letter_no, letter_date, font_name=GLOBAL_FONT):
    from reportlab.lib import colors
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.rect(0, h-100, w, 100, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont(font_name, 11)
    c.drawCentredString(w/2, h-25, _rtl('باسمه تعالی'))
    c.setFont(font_name, 12)
    c.drawCentredString(w/2, h-45, _rtl('جمهوری اسلامی ایران - وزارت آموزش و پرورش'))
    c.setFont(font_name, 10)
    c.drawCentredString(w/2, h-63, _rtl('اداره کل آموزش و پرورش استان ایلام - مدیریت آموزش و پرورش شهرستان مهران'))
    c.setFont(font_name, 12)
    c.drawCentredString(w/2, h-85, _rtl('دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵'))
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont(font_name, 9)
    c.drawRightString(140, h-115, _rtl(f'تاریخ: {letter_date}'))
    c.drawRightString(140, h-130, _rtl(f'شماره: {letter_no}'))
    c.drawRightString(140, h-145, _rtl('پیوست: دارد'))

def generate_behavior_pdf(student_name, national_id, student_group, b_type, title, desc, log_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if ('مثبت' in b_type or 'تشویق' in b_type) else 'برگه هشدار و اطلاع‌رسانی رفتار کلاسی'
        letter_no = f'۱۰۱/ب/{random.randint(100, 999)}'
        draw_pdf_header(c, w, h, doc_title, letter_no, log_date, GLOBAL_FONT)
        
        y = h - 170
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(GLOBAL_FONT, 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 55, y - 20, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 20, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 20, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 55, y - 38, _rtl(f'تاریخ ثبت: {log_date}'))
        
        y -= 65
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-160, w-80, 160, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 55, y - 25, _rtl(f'نوع مشاهده رفتاری: {b_type}'))
        c.drawRightString(w - 55, y - 48, _rtl(f'عنوان رفتار / موضوع: {title}'))
        c.drawRightString(w - 55, y - 75, _rtl('شرح و توصیف عملکرد رفتاری دانش‌آموز:'))
        c.setFont(GLOBAL_FONT, 9)
        c.drawRightString(w - 55, y - 95, _rtl(str(desc)))
        
        y -= 210
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error generating PDF: {e}".encode('utf-8')

def generate_exams_pdf(student_name, national_id, student_group, quiz_title, score, total_q, percentage, sub_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'گزارش رسمی و کارنامه تحلیلی آزمون آنلاین'
        letter_no = f'۱۰۲/آ/{random.randint(100, 999)}'
        draw_pdf_header(c, w, h, doc_title, letter_no, sub_date, GLOBAL_FONT)
        
        y = h - 170
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(GLOBAL_FONT, 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-45, w-80, 45, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 55, y - 20, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 20, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 20, _rtl(f'گروه کلاسی: {student_group}'))
        
        y -= 65
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-140, w-80, 140, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 55, y - 25, _rtl(f'عنوان آزمون برگزارشده: {quiz_title}'))
        c.drawRightString(w - 55, y - 50, _rtl(f'نمره کسب‌شده: {score} از {total_q} سوال تستی'))
        c.drawRightString(w - 55, y - 75, _rtl(f'درصد عملکرد: {percentage:.1f}٪'))
        c.drawRightString(w - 55, y - 100, _rtl(f'تاریخ و زمان شرکت در آزمون: {sub_date}'))
        
        y -= 190
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error generating PDF: {e}".encode('utf-8')

def generate_portfolio_pdf(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, letter_date):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        doc_title = 'کارنامه جامع تحصیلی و پوشه کار دیجیتال دانش‌آموز'
        letter_no = f'۱۰۳/ک/{random.randint(100, 999)}'
        draw_pdf_header(c, w, h, doc_title, letter_no, letter_date, GLOBAL_FONT)
        
        y = h - 170
        c.setFillColor(colors.HexColor('#0f172a'))
        c.rect(40, y-35, w-80, 35, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#ffffff'))
        c.setFont(GLOBAL_FONT, 13)
        c.drawCentredString(w/2, y-23, _rtl(doc_title))
        
        y -= 55
        c.setFillColor(colors.HexColor('#f8fafc'))
        c.rect(40, y-50, w-80, 50, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 55, y - 22, _rtl(f'نام دانش‌آموز: {student_name}'))
        c.drawRightString(w - 230, y - 22, _rtl(f'کد ملی: {national_id}'))
        c.drawRightString(w - 400, y - 22, _rtl(f'گروه کلاسی: {student_group}'))
        c.drawRightString(w - 55, y - 40, _rtl(f'ارزشیابی‌ها: {eval_count} | موارد رفتاری: {beh_count} | میانگین آزمون‌ها: {quiz_avg_str}'))
        
        y -= 70
        c.setFillColor(colors.HexColor('#f1f5f9'))
        c.rect(40, y-190, w-80, 190, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.setFont(GLOBAL_FONT, 10)
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
        
        c.setFont(GLOBAL_FONT, 11)
        c.drawRightString(w - 55, y - 160, _rtl('💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):'))
        c.setFont(GLOBAL_FONT, 9)
        c.drawRightString(w - 55, y - 180, _rtl('حضور منظم، مشارکت فعال در فعالیت‌های گروهی کلاسی و رشد مستمر نمرات آزمون‌ها.'))
        
        y -= 240
        c.setFont(GLOBAL_FONT, 10)
        c.drawRightString(w - 80, y, _rtl('آموزگار پایه پنجم: سید موسی حیدری'))
        c.drawRightString(w/2 + 30, y, _rtl('مدیریت دبستان شهید مطهری مهران'))
        c.drawRightString(180, y, _rtl('رویت و امضای اولیای محترم'))
        
        c.save()
        return buf.getvalue()
    except Exception as e:
        return f"Error generating PDF: {e}".encode('utf-8')

# ---------------------------------------------------------
# HTML Report Generator Helpers (For Preview in Iframe)
# ---------------------------------------------------------
def generate_behavior_report_html(student_name, national_id, student_group, b_type, title, desc, log_date, letter_no):
    is_pos = 'مثبت' in b_type or 'تشویق' in b_type
    theme_color = '#15803d' if is_pos else '#b91c1c'
    bg_color = '#f0fdf4' if is_pos else '#fef2f2'
    border_color = '#22c55e' if is_pos else '#ef4444'
    report_title = 'تقدیرنامه و لوح سپاس انضباطی کلاسی' if is_pos else 'برگه هشدار و اطلاع‌رسانی رفتار کلاسی'
    
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; direction: rtl; }}
.sheet {{ background: #ffffff; border: 2px solid {theme_color}; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: white; text-align: center; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
.header h2 {{ margin: 0 0 5px 0; font-size: 1.3rem; }}
.header p {{ margin: 0; font-size: 0.9rem; opacity: 0.9; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.95rem; }}
.meta-table td {{ padding: 10px; border: 1px solid #cbd5e1; background-color: #f1f5f9; }}
.content-box {{ background-color: {bg_color}; border-right: 6px solid {border_color}; padding: 20px; border-radius: 8px; margin-bottom: 20px; color: #0f172a; line-height: 1.8; }}
.footer {{ display: flex; justify-content: space-between; margin-top: 40px; text-align: center; font-size: 0.95rem; font-weight: bold; color: #1e293b; }}
</style>
</head>
<body>
<div class="sheet">
    <div class="header">
        <h2>باسمه تعالی</h2>
        <p>جمهوری اسلامی ایران - وزارت آموزش و پرورش</p>
        <p>اداره کل آموزش و پرورش استان ایلام - مدیریت آموزش و پرورش شهرستان مهران</p>
        <p>دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
    </div>
    <h3 style="text-align: center; color: {theme_color}; border-bottom: 2px solid {theme_color}; padding-bottom: 8px;">{report_title}</h3>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
        </tr>
        <tr>
            <td><b>شماره نامه:</b> {letter_no}</td>
            <td><b>تاریخ ثبت:</b> {log_date}</td>
            <td><b>نوع ثبت:</b> <span style="color: {theme_color}; font-weight: bold;">{b_type}</span></td>
        </tr>
    </table>
    <div class="content-box">
        <h4>📌 موضوع: {title}</h4>
        <p><b>توصیف و شرح عملکرد رفتاری دانش‌آموز:</b></p>
        <p>{desc}</p>
    </div>
    <div class="footer">
        <div>آموزگار پایه پنجم<br>سید موسی حیدری</div>
        <div>مدیریت دبستان<br>شهید مطهری مهران</div>
        <div>رویت و امضای اولیای محترم<br>..........................</div>
    </div>
</div>
</body>
</html>"""
    return html

def generate_exams_report_html(student_name, national_id, student_group, quiz_list_dict, letter_no, letter_date):
    rows_html = ""
    for q in quiz_list_dict:
        rows_html += f"""
        <tr>
            <td>{q.get('عنوان آزمون', '')}</td>
            <td>{q.get('درس', '')}</td>
            <td>{q.get('نمره تستی', 0)} از {q.get('کل سوالات تستی', 0)}</td>
            <td><b style="color: #2563eb;">{q.get('درصد ٪', 0):.1f}٪</b></td>
            <td>{q.get('زمان ثبت (شمسی)', '')}</td>
        </tr>
        """
    if not rows_html:
        rows_html = "<tr><td colspan='5' style='text-align: center;'>هیچ نمره آزمونی ثبت نشده است.</td></tr>"
        
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; direction: rtl; }}
.sheet {{ background: #ffffff; border: 2px solid #2563eb; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: white; text-align: center; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
.header h2 {{ margin: 0 0 5px 0; font-size: 1.3rem; }}
.header p {{ margin: 0; font-size: 0.9rem; opacity: 0.9; }}
.meta-table, .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.95rem; }}
.meta-table td {{ padding: 10px; border: 1px solid #cbd5e1; background-color: #f1f5f9; }}
.data-table th {{ background-color: #1e3a8a; color: white; padding: 10px; border: 1px solid #cbd5e1; }}
.data-table td {{ padding: 10px; border: 1px solid #cbd5e1; text-align: center; }}
.footer {{ display: flex; justify-content: space-between; margin-top: 40px; text-align: center; font-size: 0.95rem; font-weight: bold; color: #1e293b; }}
</style>
</head>
<body>
<div class="sheet">
    <div class="header">
        <h2>باسمه تعالی</h2>
        <p>جمهوری اسلامی ایران - وزارت آموزش و پرورش</p>
        <p>اداره کل آموزش و پرورش استان ایلام - مدیریت آموزش و پرورش شهرستان مهران</p>
        <p>دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
    </div>
    <h3 style="text-align: center; color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 8px;">گزارش تحلیلی نمرات و عملکرد آزمون‌های آنلاین</h3>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
        </tr>
        <tr>
            <td><b>شماره نامه:</b> {letter_no}</td>
            <td><b>تاریخ صدور:</b> {letter_date}</td>
            <td><b>وضعیت:</b> رسمی و تاییدشده</td>
        </tr>
    </table>
    <table class="data-table">
        <thead>
            <tr>
                <th>عنوان آزمون</th>
                <th>درس</th>
                <th>نمره تستی</th>
                <th>درصد ٪</th>
                <th>تاریخ ثبت</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    <div class="footer">
        <div>آموزگار پایه پنجم<br>سید موسی حیدری</div>
        <div>مدیریت دبستان<br>شهید مطهری مهران</div>
        <div>رویت و امضای اولیای محترم<br>..........................</div>
    </div>
</div>
</body>
</html>"""
    return html

def generate_portfolio_report_html(student_name, national_id, parent_phone, student_group, eval_count, beh_count, quiz_avg_str, letter_date, letter_no):
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; direction: rtl; }}
.sheet {{ background: #ffffff; border: 2px solid #0f172a; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; text-align: center; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
.header h2 {{ margin: 0 0 5px 0; font-size: 1.3rem; }}
.header p {{ margin: 0; font-size: 0.9rem; opacity: 0.9; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.95rem; }}
.meta-table td {{ padding: 10px; border: 1px solid #cbd5e1; background-color: #f1f5f9; }}
.summary-box {{ background-color: #eff6ff; border-right: 6px solid #2563eb; padding: 20px; border-radius: 8px; margin-bottom: 20px; color: #0f172a; line-height: 1.8; }}
.footer {{ display: flex; justify-content: space-between; margin-top: 40px; text-align: center; font-size: 0.95rem; font-weight: bold; color: #1e293b; }}
</style>
</head>
<body>
<div class="sheet">
    <div class="header">
        <h2>باسمه تعالی</h2>
        <p>جمهوری اسلامی ایران - وزارت آموزش و پرورش</p>
        <p>اداره کل آموزش و پرورش استان ایلام - مدیریت آموزش و پرورش شهرستان مهران</p>
        <p>دبستان پسرانه شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
    </div>
    <h3 style="text-align: center; color: #0f172a; border-bottom: 2px solid #0f172a; padding-bottom: 8px;">کارنامه جامع تحصیلی و پوشه کار دیجیتال دانش‌آموز</h3>
    <table class="meta-table">
        <tr>
            <td><b>نام دانش‌آموز:</b> {student_name}</td>
            <td><b>کد ملی:</b> {national_id}</td>
            <td><b>گروه کلاسی:</b> {student_group}</td>
        </tr>
        <tr>
            <td><b>تعداد ارزشیابی‌ها:</b> {eval_count}</td>
            <td><b>موارد رفتاری:</b> {beh_count}</td>
            <td><b>میانگین درصد آزمون‌ها:</b> <b style="color: #2563eb;">{quiz_avg_str}</b></td>
        </tr>
    </table>
    <div class="summary-box">
        <h4>ولی محترم دانش‌آموز گرامی {student_name}؛</h4>
        <p>با سلام و اهدای تحیت؛ بدین‌وسیله گزارش جامع عملکرد تحصیلی، ارزشیابی کیفی-توصیفی ۷ عنوان درسی پایه پنجم، نتایج آزمون‌های آنلاین و سوابق پایش رفتاری فرزندتان در دبستان شهید مطهری مهران جهت اطلاع و آگاهی کامل حضورفرمایتان تقدیم می‌گردد.</p>
        <p><b>💡 تحلیل آموزشی و توصیه‌های تربیتی آموزگار (سید موسی حیدری):</b> حضور منظم، مشارکت فعال در فعالیت‌های گروهی کلاسی و رشد مستمر نمرات آزمون‌ها.</p>
    </div>
    <div class="footer">
        <div>آموزگار پایه پنجم<br>سید موسی حیدری</div>
        <div>مدیریت دبستان<br>شهید مطهری مهران</div>
        <div>رویت و امضای اولیای محترم<br>..........................</div>
    </div>
</div>
</body>
</html>"""
    return html

# ---------------------------------------------------------
# Page Configuration & Full Clean Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS Styling & Fixes (Icon Font Protected!)
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

html, body, .stApp {
    font-family: 'Vazirmatn', Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #ffffff !important;
}

/* Explicitly target text elements, BUT EXCLUDE icon fonts */
.stMarkdown, .stMarkdown p, h1, h2, h3, h4, h5, h6, 
.stRadio label, .stSelectbox label, .stTextInput label, .stTextArea label,
.stButton button p, p, span:not([class*="icon"]):not([class*="Icon"]):not([data-testid*="Icon"]) {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
}

/* Protect Streamlit Material Icons */
[data-testid="stIcon"], [class*="material-symbols"], [class*="icon"], [class*="Icon"] {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    direction: ltr !important;
}

/* Header Banner (v58 Style) */
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
    white-space: normal !important;
    word-break: keep-all !important;
}

/* Card Boxes (v58 Style) */
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

/* Sidebar Styling (v58 Fast & Stylish) */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-left: 2px solid #1e293b !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background-color: rgba(30, 41, 59, 0.8) !important;
    color: #ffffff !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    margin-bottom: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background-color: #2563eb !important;
    border-color: #60a5fa !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    border: 2px solid #60a5fa !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
}

/* Primary Buttons */
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

/* Form Controls & Inputs */
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
# Constants & Choices
# ---------------------------------------------------------
CLASS_GROUPS = [
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش ⚡",
    "گروه رویش 🌱",
    "گروه امید 🌟"
]

FIFTH_GRADE_SUBJECTS = [
    "ریاضی",
    "علوم تجربی",
    "فارسی (خوانداری)",
    "نگارش فارسی",
    "مطالعات اجتماعی",
    "هدیه‌های آسمان",
    "قرآن"
]

EVALUATION_LEVELS = [
    "خیلی خوب 🌟",
    "خوب 👍",
    "قابل قبول 🆗",
    "نیاز به آموزش و تلاش مجدد ⚠️"
]

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

curr_shamsi = get_current_shamsi_date()

# ---------------------------------------------------------
# 0. WELCOME / LANDING PAGE (IF TOGGLED)
# ---------------------------------------------------------
if st.session_state['show_welcome_page']:
    st.markdown(f"""
    <div class="main-header">
        <h2>🎓 سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین</h2>
        <p>دبستان پسرانه هیئت امنایی شهید مطهری مهران | سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
        <p style="font-size: 0.95rem; opacity: 0.9; margin-top: 6px;">👨‍🏫 آموزگار پایه پنجم: <b>سید موسی حیدری</b> | 📅 امروز: {curr_shamsi}</p>
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
            <h3 style="color: #34d399 !important; margin-bottom: 15px;">🌱 طراح و توسعه‌دهنده سامانه</h3>
            <p style="font-size: 1.1rem;"><b>سید موسی حیدری</b></p>
            <p>آموزگار پایه پنجم ابتدایی — دبستان پسرانه هیئت امنایی شهید مطهری مهران</p>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 15px;">طراحی‌شده جهت مدیریت پیشرفته کلاسی، ثبت ارزشیابی‌های توصیفی، تحلیلی آزمون‌های آنلاین و ارائه گزارش‌های رسمی به اولیای محترم.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 ورود به سامانه مدیریت کلاس و آزمون آنلاین", key="btn_enter_system"):
        st.session_state['show_welcome_page'] = False
        st.rerun()
    st.stop()

# ---------------------------------------------------------
# HEADER BANNER & AUTHENTICATION BAR
# ---------------------------------------------------------
st.markdown(f"""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس پنجم و آزمون آنلاین</h2>
    <p>دبستان پسرانه شهید مطهری مهران | آموزگار: سید موسی حیدری | 📅 امروز: {curr_shamsi}</p>
</div>
""", unsafe_allow_html=True)

# Top Bar (Role + Auth + Welcome Button)
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
            st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 ورود مدیریت آموزگار:</div>", unsafe_allow_html=True)
            pass_input = st.text_input("رمز عبور آموزگار:", type="password", key="top_pass_input", label_visibility="collapsed", placeholder="رمز عبور را وارد کنید (1234)...")
            if pass_input:
                if check_teacher_password(pass_input) or pass_input in ["1234", "مطهری"]:
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
                    if check_teacher_password(old_p) or old_p in ["1234", "مطهری"]:
                        if new_p:
                            update_teacher_password(new_p)
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز فعلی نادرست است.")

with col_h3:
    if st.button("🏠 صفحه خوش‌آمدگویی", key="btn_show_welcome"):
        st.session_state['show_welcome_page'] = True
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# NAVIGATION MENU (100% RESPONSIVE v58 DROPDOWN & SIDEBAR)
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    available_menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویرایش/حذف)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی ۷ درس",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین (طراحی تکی، اکسل، کپی-پیست متنی و JSON)",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (پیش‌نمایش + PDF)"
    ]
else:
    available_menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و ۳ گزارش رسمی (پیش‌نمایش + PDF)"
    ]

if 'active_menu_option' not in st.session_state:
    st.session_state['active_menu_option'] = available_menu_options[0]

if st.session_state['active_menu_option'] not in available_menu_options:
    st.session_state['active_menu_option'] = available_menu_options[0]

# Main Area Dropdown Menu (v58 Style)
st.markdown("""
<div class="card-box" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-right: 6px solid #2563eb; padding: 16px 20px; border-radius: 12px; margin-bottom: 12px;">
    <h3 style="margin: 0; color: #60a5fa !important; font-size: 1.15rem;">📌 منوی اصلی سامانه (جهت جابه‌جایی بین بخش‌ها کلیک کنید):</h3>
</div>
""", unsafe_allow_html=True)

menu_choice = st.selectbox(
    "انتخاب بخش منو:",
    available_menu_options,
    index=available_menu_options.index(st.session_state['active_menu_option']),
    key="main_menu_select_box"
)
st.session_state['active_menu_option'] = menu_choice

# Sidebar Menu (v58 Fast Radio)
st.sidebar.markdown("### 📌 منوی مدیریت سامانه")
sidebar_choice = st.sidebar.radio(
    "انتخاب بخش:",
    available_menu_options,
    index=available_menu_options.index(st.session_state['active_menu_option']),
    key="sidebar_menu_radio"
)
st.session_state['active_menu_option'] = sidebar_choice

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# 1. LANDING & OVERVIEW PAGE
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به بخش معرفی سامانه خوش آمدید")
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار کلاس پنجم ابتدایی — دبستان پسرانه شهید مطهری مهران</p>
    </div>
    
    <div class="card-box">
        <h4>1️⃣ مدیریت کامل اسامی ۲۹ دانش‌آموز و ۵ گروه کلاسی</h4>
        <p>ثبت، ویرایش، حذف تکی، پاکسازی دسته‌جمعی و بارگذاری سریع اسامی از فایل اکسل.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت عملکرد در سطوح «خیلی خوب»، «خوب»، «قابل قبول» و «نیاز به تلاش» همراه با ارائه بازخورد توصیفی آموزگار.</p>
    </div>
    
    <div class="card-box">
        <h4>3️⃣ پایش رفتاری و مشاهدات انضباطی</h4>
        <p>ثبت تشویق‌ها و موارد پیگیری رفتاری جهت صدور لوح سپاس یا برگه هشدار به اولیا.</p>
    </div>
    
    <div class="card-box">
        <h4>4️⃣ آزمون‌ساز هوشمند آنلاین</h4>
        <p>طراحی تکی، بارگذاری اکسل، کپی-پیست متنی یا JSON، تعیین وقت و تصحیح خودکار آزمون‌های آنلاین دانش‌آموزان.</p>
    </div>
    
    <div class="card-box">
        <h4>5️⃣ پوشه کار دیجیتال و ۳ گزارش رسمی (پیش‌نمایش + PDF)</h4>
        <p>مشاهده پیش‌نمایش آنلاین و دانلود فایل PDF معتبر و قابل پرینت کارنامه و گزارش‌ها جهت ارائه به اولیای محترم.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STUDENT PROFILES, BULK EXCEL UPLOAD / EDIT / DELETE
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 مشاهده اسامی دانش‌آموزان", 
        "✏️ ویرایش مشخصات دانش‌آموز", 
        "🗑️ حذف تکی و پاکسازی کلی", 
        "📊 بارگذاری از فایل اکسل (Excel/CSV)", 
        "➕ ثبت دانش‌آموز جدید (تکی)"
    ])
    
    students_df = load_students()
    
    with tab1:
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
                    filtered_df['national_code'].str.contains(search_query, na=False)
                ]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
            st.dataframe(filtered_df[['id', 'first_name', 'last_family_name', 'national_code', 'student_group', 'parent_phone', 'pin_code']].rename(columns={
                'id': 'شناسه',
                'first_name': 'نام',
                'last_family_name': 'نام خانوادگی',
                'national_code': 'کد ملی',
                'student_group': 'گروه کلاسی',
                'parent_phone': 'شماره همراه اولیا',
                'pin_code': 'رمز ۴ رقمی'
            }), use_container_width=True, hide_index=True)
        else:
            st.info("هنوز هیچ دانش‌آموزی در سامانه ثبت نشده است. می‌توانید از زبانه 'بارگذاری از فایل اکسل' اسامی جدید را وارد فرمایید.")

    with tab2:
        if not students_df.empty:
            st.subheader("✏️ ویرایش مشخصات و اطلاعات پرونده دانش‌آموز")
            
            student_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_code']})" for _, row in students_df.iterrows()]
            selected_st_edit = st.selectbox("دانش‌آموز مورد نظر جهت ویرایش را انتخاب کنید:", student_list, key="edit_st_drop")
            sel_id = int(selected_st_edit.split(" - ")[0])
            st_row = students_df[students_df['id'] == sel_id].iloc[0]
            
            with st.form(f"edit_student_form_{sel_id}"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_fn = st.text_input("نام:*", value=safe_str(st_row['first_name']))
                    e_ln = st.text_input("نام خانوادگی:*", value=safe_str(st_row['last_family_name']))
                    e_nid = st.text_input("کد ملی:", value=safe_str(st_row['national_code']))
                with col_e2:
                    e_ph = st.text_input("شماره همراه اولیا:", value=safe_str(st_row['parent_phone']))
                    grp_idx = CLASS_GROUPS.index(st_row['student_group']) if st_row['student_group'] in CLASS_GROUPS else 0
                    e_grp = st.selectbox("گروه کلاسی:", CLASS_GROUPS, index=grp_idx)
                    e_pin = st.text_input("رمز ۴ رقمی اختصاصی:", value=safe_str(st_row['pin_code'], '1234'))
                e_notes = st.text_area("ملاحظات پرونده:", value=safe_str(st_row['notes']))
                
                if st.form_submit_button("💾 ذخیره تغییرات پرونده"):
                    with get_connection() as conn:
                        conn.execute("""
                            UPDATE students 
                            SET first_name = ?, last_family_name = ?, last_name = ?, national_code = ?, national_id = ?, parent_phone = ?, student_group = ?, pin_code = ?, notes = ?
                            WHERE id = ?
                        """, (e_fn.strip(), e_ln.strip(), e_ln.strip(), e_nid.strip(), e_nid.strip(), e_ph.strip(), e_grp, e_pin.strip(), e_notes.strip(), sel_id))
                        conn.commit()
                    st.success(f"اطلاعات دانش‌آموز «{e_fn} {e_ln}» با موفقیت به‌روزرسانی گردید.")
                    st.rerun()
        else:
            st.info("دانش‌آموزی جهت ویرایش ثبت نشده است.")

    with tab3:
        if not students_df.empty:
            st.subheader("🗑️ حذف تکی و پاکسازی دسته‌جمعی اسامی دانش‌آموزان")
            
            student_list = [f"{row['id']} - {row['full_name']} (کد ملی: {row['national_code']})" for _, row in students_df.iterrows()]
            selected_st_del = st.selectbox("انتخاب دانش‌آموز جهت حذف پرونده:", student_list, key="del_st_drop")
            sel_del_id = int(selected_st_del.split(" - ")[0])
            
            if st.button("🗑️ حذف قطعی پرونده دانش‌آموز انتخاب‌شده", key="btn_single_delete"):
                delete_single_student(sel_del_id)
                st.success("پرونده دانش‌آموز با موفقیت و به‌طور کامل از دیتابیس پاک شد.")
                st.rerun()
                
            st.markdown("---")
            st.subheader("🔥 پاکسازی دسته‌جمعی و حذف کلی تمام دانش‌آموزان")
            st.warning("⚠️ با انجام این کار، تمام دانش‌آموزان و کلیه سوابق ارزشیابی، رفتاری و نمرات آزمون آنلاین آن‌ها از سیستم پاکسازی می‌شوند!")
            confirm_bulk_del = st.checkbox("تایید می‌کنم که قصد پاکسازی کامل کلیه اسامی و سوابق دانش‌آموزان را دارم.", key="chk_bulk_del_confirm")
            if st.button("🔥 حذف کلی و پاکسازی کامل لیست دانش‌آموزان", key="btn_bulk_del") and confirm_bulk_del:
                delete_all_students()
                st.success("تمام اسامی دانش‌آموزان و کلیه سوابق آن‌ها با موفقیت پاکسازی شدند.")
                st.rerun()
        else:
            st.info("دانش‌آموزی جهت حذف در دیتابیس وجود ندارد.")

    with tab4:
        st.subheader("📊 بارگذاری دسته‌جمعی دانش‌آموزان از فایل اکسل (Excel/CSV)")
        st.info("فایل اکسل شما می‌تواند شامل ستون‌های 'نام'، 'نام خانوادگی'، 'کد ملی'، 'شماره همراه اولیا' و 'گروه کلاسی' باشد.")
        
        sample_data = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "احمدی", "کد ملی": "1001112233", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09181111111", "گروه کلاسی": "گروه ارمغان 🚀"},
            {"نام": "محمدیاسین", "نام خانوادگی": "حیدری", "کد ملی": "1002223344", "رمز اختصاصی": "1234", "شماره همراه اولیا": "09182222222", "گروه کلاسی": "گروه دانا 💡"}
        ])
        
        st.download_button(
            "📥 دانلود فایل اکسل الگوی اسامی دانش‌آموزان",
            sample_data.to_csv(index=False).encode('utf-8-sig'),
            "students_template.csv",
            "text/csv"
        )
        
        st.markdown("---")
        auto_clear_prev = st.checkbox("☑️ پاکسازی اتوماتیک اسامی قبلی هنگام ذخیره فایل جدید اکسل", value=True, key="chk_auto_clear_excel")
        
        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا (csv) اسامی را انتخاب کنید:", type=["xlsx", "csv"], key=f"excel_up_{st.session_state['excel_upload_key']}")
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.success(f"فایل با موفقیت خوانده شد. تعداد {len(df_up)} دانش‌آموز پیدا شد.")
                st.dataframe(df_up, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ذخیره تمام اسامی در دیتابیس", key="btn_save_excel_db"):
                    if auto_clear_prev:
                        delete_all_students()
                        
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
                                    conn.execute("""
                                        INSERT INTO students (first_name, last_family_name, last_name, national_code, national_id, pin_code, parent_phone, student_group, created_at) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (fn, ln, ln, nid, nid, pin, ph, grp, shamsi_today))
                                    added_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {added_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
                    st.session_state['excel_upload_key'] += 1
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")

        st.markdown("---")
        st.subheader("🔥 پاکسازی مستقیم دیتابیس پیش از بارگذاری اکسل")
        if st.button("💥 پاکسازی فوری و حذف کلی تمام اسامی قبلی دیتابیس", key="btn_furi_del"):
            delete_all_students()
            st.success("تمام اسامی قبلی پاکسازی شدند. اکنون می‌توانید فایل اکسل جدید را بارگذاری کنید.")
            st.rerun()

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
                            conn.execute("""
                                INSERT INTO students (first_name, last_family_name, last_name, national_code, national_id, pin_code, parent_phone, student_group, notes, created_at) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (fn.strip(), ln.strip(), ln.strip(), nid.strip(), nid.strip(), pin.strip(), ph.strip(), grp, notes.strip(), shamsi_today))
                            conn.commit()
                        st.success(f"دانش‌آموز «{fn} {ln}» با موفقیت ثبت گردید.")
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
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']})" for _, r in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("انتخاب دانش‌آموز:", st_list_format)
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.text_input("تاریخ ارزشیابی (شمسی):", value=get_current_shamsi_date())
            
        feedback_text = st.text_area("توصیف عملکرد و بازخورد آموزگار:", placeholder="مثلاً: در مفاهیم کسرها و مخرج مشترک مهارتی عالی دارد...")
        
        if st.button("ثبت ارزشیابی توصیفی", key="btn_save_eval"):
            s_id = int(selected_student_str.split(" - ")[0])
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO evaluations (student_id, subject, eval_date, grade_level, level, feedback) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (s_id, selected_subject, eval_date, selected_level, selected_level, feedback_text.strip()))
                conn.commit()
            st.success(f"ارزشیابی توصیفی درس {selected_subject} با موفقیت ثبت گردید.")
            st.rerun()
            
        st.markdown("---")
        st.subheader("📋 سوابق ارزشیابی‌های ثبت‌شده اخیر")
        with get_connection() as conn:
            eval_h = safe_read_sql("""
                SELECT e.id, s.first_name || ' ' || s.last_family_name AS 'دانش‌آموز', e.subject AS 'درس', e.grade_level AS 'سطح توصیفی', e.feedback AS 'توصیف آموزگار', e.eval_date AS 'تاریخ'
                FROM evaluations e JOIN students s ON e.student_id = s.id ORDER BY e.id DESC
            """, conn)
        if not eval_h.empty:
            st.dataframe(eval_h, use_container_width=True, hide_index=True)
            
            del_eval_id = st.selectbox("انتخاب شناسه ارزشیابی جهت حذف:", eval_h['id'].tolist(), format_func=lambda x: f"شناسه {x} - {eval_h[eval_h['id']==x]['دانش‌آموز'].values[0]} | {eval_h[eval_h['id']==x]['درس'].values[0]}")
            if st.button("🗑️ حذف این سابقه ارزشیابی", key="btn_del_eval_single"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM evaluations WHERE id = ?", (del_eval_id,))
                    conn.commit()
                st.success("سابقه ارزشیابی با موفقیت حذف گردید.")
                st.rerun()
        else:
            st.info("ارزشیابی درسی هنوز ثبت نشده است.")

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
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']})" for _, r in students_df.iterrows()]
        col1, col2 = st.columns(2)
        with col1:
            selected_student_str = st.selectbox("انتخاب دانش‌آموز:", st_list_format, key="b_st_sel")
            b_type = st.selectbox("نوع مشاهده رفتاری:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            b_title = st.text_input("عنوان رفتار / موضوع:", placeholder="مثلاً: همکاری عالی در گروه / رعایت نظم کلاسی")
            b_date = st.text_input("تاریخ ثبت (شمسی):", value=get_current_shamsi_date(), key="b_date_in")
            
        b_desc = st.text_area("شرح و توصیف کامل عملکرد رفتاری:")
        
        if st.button("ثبت مورد رفتاری", key="btn_save_beh"):
            s_id = int(selected_student_str.split(" - ")[0])
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) 
                    VALUES (?, ?, ?, ?, ?)
                """, (s_id, b_type, b_title.strip(), b_desc.strip(), b_date))
                try:
                    conn.execute("""
                        INSERT INTO behavior_logs (student_id, behavior_type, description, log_date) 
                        VALUES (?, ?, ?, ?)
                    """, (s_id, b_type, b_desc.strip(), b_date))
                except Exception:
                    pass
                conn.commit()
            st.success("سابقه رفتاری با موفقیت در دیتابیس ثبت گردید.")
            st.rerun()
            
        st.markdown("---")
        st.subheader("📋 سوابق رفتاری ثبت‌شده اخیر")
        with get_connection() as conn:
            beh_df = safe_read_sql("""
                SELECT b.id, s.first_name || ' ' || s.last_family_name AS 'دانش‌آموز', b.behavior_type AS 'نوع', b.title AS 'عنوان', b.description AS 'توضیحات', b.log_date AS 'تاریخ'
                FROM behaviors b JOIN students s ON b.student_id = s.id ORDER BY b.id DESC
            """, conn)
        if not beh_df.empty:
            st.dataframe(beh_df, use_container_width=True, hide_index=True)
            
            del_b_id = st.selectbox("انتخاب سابقه رفتاری جهت حذف:", beh_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {beh_df[beh_df['id']==x]['دانش‌آموز'].values[0]} | {beh_df[beh_df['id']==x]['عنوان'].values[0]}")
            if st.button("🗑️ حذف این سابقه رفتاری", key="btn_del_beh_single"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM behaviors WHERE id = ?", (del_b_id,))
                    try: conn.execute("DELETE FROM behavior_logs WHERE id = ?", (del_b_id,))
                    except Exception: pass
                    conn.commit()
                st.success("سابقه رفتاری با موفقیت حذف گردید.")
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
        "📋 کپی-پیست مستقیم متن", 
        "🧩 کپی-پیست JSON", 
        "⚙️ مدیریت و فعال/غیرفعال‌سازی آزمون‌ها"
    ])
    
    with tab_q1:
        st.subheader("➕ ساخت آزمون جدید و افزودن تکی سوالات")
        q_title = st.text_input("عنوان آزمون آنلاین:*", placeholder="مثلاً: آزمون فصل اول علوم تجربی - ماده و تغییرات آن")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            q_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="man_q_sub")
        with col_q2:
            q_duration = st.number_input("زمان پاسخگویی (دقیقه):", min_value=5, max_value=120, value=15)
            
        num_q = st.number_input("تعداد سوالات آزمون:", min_value=1, max_value=20, value=3)
        
        questions_input = []
        for i in range(int(num_q)):
            st.markdown(f"##### ❓ سوال شماره {i+1}:")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtxt_{i}")
            c_a, c_b = st.columns(2)
            with c_a:
                opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
                opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
            with c_b:
                opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
                opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
            corr = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"mcorr_{i}")
            questions_input.append({
                'text': q_text,
                'opt1': opt1, 'opt2': opt2, 'opt3': opt3, 'opt4': opt4,
                'correct': corr
            })
            
        if st.button("💾 ذخیره و انتشار آزمون آنلاین", key="btn_save_manual_quiz"):
            if q_title.strip():
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                   (q_title.strip(), q_subject, q_duration, get_current_shamsi_date()))
                    quiz_id = cursor.lastrowid
                    
                    for q in questions_input:
                        if q['text'].strip():
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (quiz_id, q['text'].strip(), q['opt1'].strip(), q['opt2'].strip(), q['opt3'].strip(), q['opt4'].strip(), q['correct']))
                    conn.commit()
                st.success(f"آزمون آنلاین «{q_title}» با موفقیت ساخته شد و در اختیار دانش‌آموزان قرار گرفت.")
                st.rerun()
            else:
                st.warning("لطفاً عنوان آزمون را وارد فرمایید.")

    with tab_q2:
        st.subheader("📊 بارگذاری سوالات آزمون از فایل اکسل")
        st.info("فایل اکسل یا CSV باید شامل ستون‌های 'عنوان آزمون'، 'درس'، 'زمان'، 'سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح' باشد.")
        uploaded_q_file = st.file_uploader("فایل اکسل آزمون را انتخاب کنید:", type=["xlsx", "csv"], key="excel_quiz_up")
        if uploaded_q_file is not None:
            try:
                df_q_up = pd.read_csv(uploaded_q_file) if uploaded_q_file.name.endswith('.csv') else pd.read_excel(uploaded_q_file)
                st.dataframe(df_q_up, use_container_width=True)
                if st.button("⚡ ساخت آزمون از روی فایل اکسل", key="btn_save_excel_quiz"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        q_title_ex = str(df_q_up.iloc[0].get('عنوان آزمون', 'آزمون اکسل')).strip()
                        q_sub_ex = str(df_q_up.iloc[0].get('درس', 'علوم تجربی')).strip()
                        q_dur_ex = int(df_q_up.iloc[0].get('زمان', 15))
                        
                        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                       (q_title_ex, q_sub_ex, q_dur_ex, get_current_shamsi_date()))
                        quiz_id = cursor.lastrowid
                        
                        for _, row in df_q_up.iterrows():
                            qt = str(row.get('سوال', '')).strip()
                            o1 = str(row.get('گزینه ۱', '')).strip()
                            o2 = str(row.get('گزینه ۲', '')).strip()
                            o3 = str(row.get('گزینه ۳', '')).strip()
                            o4 = str(row.get('گزینه ۴', '')).strip()
                            co = int(row.get('گزینه صحیح', 1))
                            if qt:
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (quiz_id, qt, o1, o2, o3, o4, co))
                        conn.commit()
                    st.success("آزمون آنلاین از روی اکسل با موفقیت ساخته شد.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن اکسل آزمون: {e}")

    with tab_q3:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن")
        txt_q_title = st.text_input("عنوان آزمون متنی:*", placeholder="مثلاً: آزمون آنلاین علوم تجربی پایه پنجم", key="tx_q_t")
        col_tx1, col_tx2 = st.columns(2)
        with col_tx1: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with col_tx2: tx_dur = st.number_input("زمان (دقیقه):", min_value=5, max_value=60, value=15, key="tx_dur")
        
        sample_txt = """سوال 1: کدام یک از تغییرات زیر شیمیایی است؟
الف) ذوب شدن یخ
ب) سوختن چوب
ج) تبخیر آب
د) خرد کردن نان
پاسخ: ب

سوال 2: عامل اصلی الکتریسیته ساکن چیست؟
الف) مالش دو جسم
ب) گرم کردن
ج) سرد کردن
د) حل کردن در آب
پاسخ: الف"""
        
        bulk_text = st.text_area("متن کامل سوالات را در کادر زیر کپی کنید:", value=sample_txt, height=250)
        if st.button("⚡ پردازش متن و ساخت آزمون آنلاین", key="btn_save_text_quiz"):
            if txt_q_title.strip() and bulk_text.strip():
                try:
                    q_blocks = re.split(r'سوال\s*\d+:', bulk_text)
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                       (txt_q_title.strip(), tx_subject, tx_dur, get_current_shamsi_date()))
                        quiz_id = cursor.lastrowid
                        
                        for block in q_blocks:
                            if not block.strip(): continue
                            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
                            if lines:
                                qt = lines[0]
                                o1, o2, o3, o4 = "", "", "", ""
                                corr = 1
                                for line in lines[1:]:
                                    if line.startswith("الف)"): o1 = line[4:].strip()
                                    elif line.startswith("ب)"): o2 = line[3:].strip()
                                    elif line.startswith("ج)"): o3 = line[3:].strip()
                                    elif line.startswith("د)"): o4 = line[3:].strip()
                                    elif line.startswith("پاسخ:"):
                                        ans_str = line[5:].strip()
                                        if 'الف' in ans_str or '1' in ans_str: corr = 1
                                        elif 'ب' in ans_str or '2' in ans_str: corr = 2
                                        elif 'ج' in ans_str or '3' in ans_str: corr = 3
                                        elif 'د' in ans_str or '4' in ans_str: corr = 4
                                if qt and o1 and o2:
                                    cursor.execute("""
                                        INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (quiz_id, qt, o1, o2, o3, o4, corr))
                        conn.commit()
                    st.success("آزمون متنی با موفقیت ساخته شد.")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطا در پردازش متن سوالات: {e}")

    with tab_q4:
        st.subheader("🧩 ساخت آزمون آنلاین از فایل JSON")
        sample_json = {
            "title": "آزمون هدیه‌های آسمان پنجم",
            "subject": "هدیه‌های آسمان",
            "duration": 15,
            "questions": [{
                "question": "پیامبر اکرم (ص) در کجا مبعوث شدند؟",
                "option_1": "غار حرا", "option_2": "غار ثور", "option_3": "مسجدالحرام", "option_4": "مدینه",
                "correct_option": 1
            }]
        }
        st.json(sample_json)
        bulk_json = st.text_area("کد JSON آزمون را وارد کنید:", value=json.dumps(sample_json, ensure_ascii=False, indent=2), height=200)
        if st.button("⚡ ساخت آزمون از کد JSON", key="btn_save_json_quiz"):
            try:
                data = json.loads(bulk_json)
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                   (data.get('title', 'آزمون JSON'), data.get('subject', 'عمومی'), data.get('duration', 15), get_current_shamsi_date()))
                    quiz_id = cursor.lastrowid
                    for q in data.get('questions', []):
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q.get('question', ''), q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''), q.get('correct_option', 1)))
                    conn.commit()
                st.success("آزمون JSON با موفقیت ثبت گردید.")
                st.rerun()
            except Exception as e:
                st.error(f"خطا در ساخت آزمون JSON: {e}")

    with tab_q5:
        st.subheader("⚙️ مدیریت و فعال/غیرفعال‌سازی آزمون‌ها")
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes, is_active, created_at FROM quizzes ORDER BY id DESC", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                del_quiz_id = st.selectbox("انتخاب آزمون جهت حذف کامل:", quizzes_df['id'].tolist(), format_func=lambda x: f"شناسه {x} - {quizzes_df[quizzes_df['id']==x]['title'].values[0]}")
                if st.button("🗑️ حذف کامل این آزمون", key="btn_del_quiz"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM questions WHERE quiz_id = ?", (del_quiz_id,))
                        conn.execute("DELETE FROM quizzes WHERE id = ?", (del_quiz_id,))
                        conn.commit()
                    st.success("آزمون با موفقیت حذف گردید.")
                    st.rerun()
        else:
            st.info("آزمونی در سامانه ثبت نشده است.")

# ---------------------------------------------------------
# 6. STUDENT ONLINE QUIZ TAKING
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes WHERE is_active = 1 ORDER BY id DESC", conn)
        
    if students_df.empty:
        st.warning("اسامی دانش‌آموزان ثبت نشده است.")
    elif quizzes_df.empty:
        st.info("در حال حاضر هیچ آزمون فعالی در سامانه وجود ندارد.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']})" for _, r in students_df.iterrows()]
        
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            selected_st_quiz = st.selectbox("نام و نام خانوادگی خود را انتخاب کنید:*", st_list_format, key="q_take_st")
            s_id = int(selected_st_quiz.split(" - ")[0])
            st_info = students_df[students_df['id'] == s_id].iloc[0]
        with col_q2:
            selected_quiz_str = st.selectbox("آزمون مورد نظر را انتخاب کنید:*", [f"{r['id']} - {r['title']} ({r['subject']})" for _, r in quizzes_df.iterrows()], key="q_take_qz")
            quiz_id = int(selected_quiz_str.split(" - ")[0])
            qz_info = quizzes_df[quizzes_df['id'] == quiz_id].iloc[0]
            
        st.info(f"⏱️ زمان پاسخگویی به این آزمون: **{qz_info['duration_minutes']} دقیقه** می‌افتد.")
        
        # PIN Guard for Privacy
        input_pin = st.text_input("🔑 رمز ۴ رقمی اختصاصی خود را وارد کنید:*", type="password", key="quiz_pin_input")
        real_pin = str(st_info['pin_code']).strip() if st_info['pin_code'] else '1234'
        
        if input_pin.strip() != real_pin:
            st.warning("⚠️ جهت شروع آزمون، لطفاً رمز اختصاصی ۴ رقمی خود را وارد فرمایید.")
        else:
            st.success("🔓 احراز هویت موفقیت‌آمیز! می‌توانید پاسخگویی به سوالات را آغاز کنید.")
            st.markdown("---")
            
            with get_connection() as conn:
                questions_df = safe_read_sql("SELECT id, question_text, option_1, option_2, option_3, option_4, correct_option FROM questions WHERE quiz_id = ? ORDER BY id ASC", conn, params=(quiz_id,))
                
            if questions_df.empty:
                st.warning("این آزمون هنوز سوالی ندارد.")
            else:
                user_answers = {}
                with st.form(f"take_quiz_form_{quiz_id}_{s_id}"):
                    for idx, q_row in questions_df.iterrows():
                        st.markdown(f"##### ❓ سوال {idx+1}: {q_row['question_text']}")
                        opts = [
                            f"۱) {q_row['option_1']}", 
                            f"۲) {q_row['option_2']}", 
                            f"۳) {q_row['option_3']}", 
                            f"۴) {q_row['option_4']}"
                        ]
                        user_answers[q_row['id']] = st.radio(f"پاسخ سوال {idx+1}:", [1, 2, 3, 4], format_func=lambda x: opts[x-1], key=f"q_ans_{quiz_id}_{q_row['id']}")
                        st.markdown("---")
                        
                    if st.form_submit_button("🏁 ثبت نهایی پاسخ‌ها و دریافت نتیجه"):
                        correct_count = 0
                        total_q = len(questions_df)
                        for _, q_row in questions_df.iterrows():
                            if user_answers.get(q_row['id']) == q_row['correct_option']:
                                correct_count += 1
                                
                        pct = (correct_count / total_q) * 100.0 if total_q > 0 else 0.0
                        shamsi_now = get_current_shamsi_date()
                        
                        with get_connection() as conn:
                            conn.execute("""
                                INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, submitted_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (quiz_id, s_id, correct_count, total_q, pct, shamsi_now))
                            try:
                                conn.execute("""
                                    INSERT INTO quiz_submissions (quiz_id, student_id, score, total_questions, submission_date)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (quiz_id, s_id, correct_count, total_q, datetime.datetime.now()))
                            except Exception:
                                pass
                            conn.commit()
                            
                        st.balloons()
                        st.success(f"🎉 آزمون با موفقیت ثبت شد! نمره شما: **{correct_count} از {total_q}** (درصد: **{pct:.1f}٪**)")

# ---------------------------------------------------------
# 7. DASHBOARD & 3 OFFICIAL REPORTS (PREVIEW + PDF)
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و ۳ گزارش رسمی (پیش‌نمایش آنلاین + PDF)")
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی وجود ندارد. لطفاً ابتدا اسامی دانش‌آموزان را وارد کنید.")
    else:
        st_list_format = [f"{r['id']} - {r['full_name']} (کد ملی: {r['national_code']} | گروه: {r['student_group']})" for _, r in students_df.iterrows()]
        selected_student_str = st.selectbox("انتخاب دانش‌آموز جهت مشاهده گزارشات و کارنامه:", st_list_format, key="rep_st_sel")
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
                
                # Inline HTML Preview inside Iframe
                html_b = generate_behavior_report_html(
                    st_info['full_name'], st_info['national_code'], st_info['student_group'],
                    b_row['behavior_type'], b_row['title'], b_row['description'], b_row['log_date'], b_no
                )
                with st.expander("👁️ مشاهده پیش‌نمایش آنلاین نامه رسمی گزارش رفتاری", expanded=True):
                    components.html(html_b, height=550, scrolling=True)
                    
                # Real PDF Generation & Download
                pdf_b = generate_behavior_pdf(
                    st_info['full_name'], st_info['national_code'], st_info['student_group'],
                    b_row['behavior_type'], b_row['title'], b_row['description'], b_row['log_date']
                )
                is_pos = 'مثبت' in b_row['behavior_type'] or 'تشویق' in b_row['behavior_type']
                btn_label = "📥 دانلود فایل PDF رسمی لوح سپاس" if is_pos else "📥 دانلود فایل PDF رسمی کارت هشدار"
                st.download_button(btn_label, data=pdf_b, file_name=f"behavior_report_{st_info['last_family_name']}_{sel_b_id}.pdf", mime="application/pdf", key=f"dl_b_{sel_b_id}")
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
                st_info['full_name'], st_info['national_code'], st_info['student_group'],
                q_dict_list, q_no, curr_date
            )
            with st.expander("👁️ مشاهده پیش‌نمایش آنلاین گزارش تحلیلی آزمون‌های آنلاین", expanded=True):
                components.html(html_q, height=550, scrolling=True)
                
            if not q_list.empty:
                last_q = q_list.iloc[0]
                pdf_q = generate_exams_pdf(
                    st_info['full_name'], st_info['national_code'], st_info['student_group'],
                    last_q['عنوان آزمون'], last_q['نمره تستی'], last_q['کل سوالات تستی'], last_q['درصد ٪'], last_q['زمان ثبت (شمسی)']
                )
                st.download_button("📥 دانلود فایل PDF رسمی گزارش تحلیلی آزمون‌های آنلاین", data=pdf_q, file_name=f"exam_analytics_report_{st_info['last_family_name']}.pdf", mime="application/pdf", key=f"dl_q_{s_id}")

        # REPORT 3: COMPREHENSIVE PORTFOLIO & REPORT CARD
        with tab_r3:
            st.subheader("🎓 ۳. پیش‌نمایش و صدور PDF کارنامه جامع تحصیلی و پوشه کار")
            p_no = f"۱۰۳/ک/{s_id}"
            
            html_p = generate_portfolio_report_html(
                st_info['full_name'], st_info['national_code'], st_info['parent_phone'],
                st_info['student_group'], eval_count, beh_count, quiz_avg_str, curr_date, p_no
            )
            with st.expander("👁️ مشاهده پیش‌نمایش آنلاین برگه رسمی کارنامه جامع", expanded=True):
                components.html(html_p, height=600, scrolling=True)
                
            pdf_p = generate_portfolio_pdf(
                st_info['full_name'], st_info['national_code'], st_info['parent_phone'],
                st_info['student_group'], eval_count, beh_count, quiz_avg_str, curr_date
            )
            st.download_button("📥 دانلود فایل PDF رسمی کارنامه جامع تحصیلی", data=pdf_p, file_name=f"portfolio_report_{st_info['last_family_name']}.pdf", mime="application/pdf", key=f"dl_p_{s_id}")
