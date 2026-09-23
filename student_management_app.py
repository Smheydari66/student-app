

import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import time

# ---------------------------------------------------------
# Page Configuration & RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS & Popover Overrides
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #0f172a !important;
    }
    
    .stApp {
        background-color: #f8fafc;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 14px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .main-header h2, .main-header p {
        color: #ffffff !important;
        word-break: keep-all;
    }

    .role-card {
        background-color: #ffffff;
        border: 2px solid #0284c7;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.06);
    }

    .timer-card {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff !important;
        padding: 14px 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
    }

    .feature-box {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 10px;
        border-right: 5px solid #0284c7;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    .feature-box h4, .feature-box p {
        color: #0f172a !important;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #0284c7;
        color: #ffffff !important;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #0369a1;
        color: #ffffff !important;
    }

    /* Force Dropdown Popover List Items to Pure White Text on Dark Background */
    div[data-baseweb="popover"] ul li, 
    div[data-baseweb="popover"] div[role="option"],
    div[data-baseweb="select"] ul li {
        color: #ffffff !important;
        background-color: #1e293b !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="popover"] ul li:hover,
    div[data-baseweb="popover"] div[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    label, div[data-testid="stMarkdownContainer"] p, .stRadio label {
        color: #0f172a !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'is_teacher' not in st.session_state:
    st.session_state['is_teacher'] = False

if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"

if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

if 'quiz_start_time' not in st.session_state:
    st.session_state['quiz_start_time'] = None

if 'active_quiz_id' not in st.session_state:
    st.session_state['active_quiz_id'] = None

# ---------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            student_group TEXT DEFAULT 'گروه اندیشه 📖',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 60,
            created_at DATE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_type TEXT DEFAULT 'تستی',
            question_text TEXT NOT NULL,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option INTEGER,
            model_answer TEXT,
            explanation TEXT DEFAULT '',
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            descriptive_answers TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        conn.commit()

init_db()

# Seed sample built-in exam if quizzes table is empty
def seed_default_quiz():
    with get_connection() as conn:
        q_count = conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if q_count == 0:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                ("آزمون جامع ریاضی و علوم فصل ۱ تا ۳", "ریاضی", 60, datetime.date.today())
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ("تستی", "حاصل ضرب کسر ۳/۴ در ۵/۶ کدام است؟", "۱۵/۲۴", "۸/۱۰", "۱۵/۱۰", "۱۲/۲۰", 1, "", "ضرب کسرها: صورت در صورت (۳×۵=۱۵) و مخرج در در مخرج (۴×۶=۲۴). پس ۱۵/۲۴ صحیح است."),
                ("تستی", "کدام یک از موارد زیر تغییر شیمیایی است؟", "ذوب شدن یخ", "سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "سوختن چوب تغییر شیمیایی است چون جنس ماده تغییر کرده و ماده جدید تولید می‌شود."),
                ("تستی", "محیط مربعی به ضلع ۲.۵ سانتی‌متر چقدر است؟", "۵ سانتی‌متر", "۷.۵ سانتی‌متر", "۱۰ سانتی‌متر", "۶.۲۵ سانتی‌متر", 3, "", "محیط مربع = ضلع × ۴. پس ۲.۵ × ۴ = ۱۰ سانتی‌متر."),
                ("تشریحی", "دو تفاوت مهم بین تغییر فیزیکی و تغییر شیمیایی را با ذکر مثال توضیح دهید.", "", "", "", "", None, "در تغییر فیزیکی جنس ماده تغییر نمی‌کند (مثل ذوب یخ)، اما در تغییر شیمیایی جنس ماده تغییر می‌کند (مثل سوختن چوب).", "پاسخ کامل باید شامل تعریف تغییر جنس ماده و مثال برای هرکدام باشد."),
                ("تشریحی", "مفهوم کسرهای مساوی را توضیح داده و بگویید چگونه می‌توان یک کسر مساوی با کسر دیگر ساخت؟", "", "", "", "", None, "با ضرب یا تقسیم صورت و مخرج کسر در یک عدد غیرصفر ثابت، کسر مساوی به دست می‌آید.", "ضرب یا تقسیم همزمان صورت و مخرج در یک عدد ثابت باعث ثابت ماندن مقدار کسر می‌شود.")
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
    "گروه ارمغان 🚀 (۶ نفر)",
    "گروه دانا 💡 (۶ نفر)",
    "گروه تلاش 🌟 (۶ نفر)",
    "گروه نخبگان 🏆 (۶ نفر)",
    "گروه اندیشه 📖 (۵ نفر)"
]

def load_students():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'parent_phone', 'student_group', 'notes'])

# ---------------------------------------------------------
# Header & Navigation
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>ارزشیابی کیفی-توصیفی، پایش رفتاری، بارگذاری دسته‌جمعی اکسل و آزمون‌ساز آنلاین با زمان‌بندی</p>
</div>
""", unsafe_allow_html=True)

# Top Bar Login & Role Selection
st.markdown('<div class="role-card">', unsafe_allow_html=True)
col_r1, col_r2 = st.columns([1, 2])

with col_r1:
    role_choice = st.radio(
        "👤 نوع کاربری خود را انتخاب کنید:",
        ["دانش‌آموز / اولیا 👨‍🎓", "آموزگار / مدیر 🔑"],
        index=1 if st.session_state['is_teacher'] else 0,
        horizontal=True
    )

with col_r2:
    if "آموزگار" in role_choice:
        if not st.session_state['is_teacher']:
            st.markdown("##### 🔑 ورود آموزگار")
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                input_pass = st.text_input("رمز عبور آموزگار را وارد کنید:", type="password", key="login_pass_input", help="رمز عبور پیش‌فرض: 1234 یا مطهری")
            with col_p2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("ورود به سامانه"):
                    if input_pass in [st.session_state['teacher_password'], "1234", "مطهری"]:
                        st.session_state['is_teacher'] = True
                        st.success("ورود آموزگار موفقیت‌آمیز بود.")
                        st.rerun()
                    else:
                        st.error("رمز عبور اشتباه است.")
        else:
            st.success("🟢 آموزگار محترم، شما با موفقیت وارد شده‌اید.")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("خروج از حالت معلم"):
                    st.session_state['is_teacher'] = False
                    st.rerun()
            with col_b2:
                with st.popover("🔐 تغییر رمز عبور آموزگار"):
                    curr_p = st.text_input("رمز فعلی:", type="password", key="cp_curr")
                    new_p = st.text_input("رمز جدید:", type="password", key="cp_new")
                    if st.button("ذخیره رمز جدید"):
                        if curr_p == st.session_state['teacher_password']:
                            st.session_state['teacher_password'] = new_p
                            st.success("رمز عبور جدید با موفقیت ذخیره شد.")
                        else:
                            st.error("رمز فعلی اشتباه است.")
    else:
        st.session_state['is_teacher'] = False
        st.info("👤 حالت دانش‌آموز فعال است (دسترسی به شرکت در آزمون آنلاین و کارنامه).")

st.markdown('</div>', unsafe_allow_html=True)

# Menu Options based on Role
if st.session_state['is_teacher']:
    menu_options = [
        "1. 🏠 صفحه اصلی و معرفی برنامه",
        "2. 👨‍🎓 مدیریت دانش‌آموزان و ثبت اکسل (۲۹ نفر)",
        "3. 📝 ارزشیابی کیفی-توصیفی (معلم)",
        "4. 🌟 ثبت رفتار و انضباط (معلم)",
        "5. ✏️ آزمون‌ساز و طراحی سوالات (معلم)",
        "6. 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7. 📊 داشبورد و کارنامه جامع"
    ]
else:
    menu_options = [
        "1. 🏠 صفحه اصلی و معرفی برنامه",
        "6. 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7. 📊 داشبورد و کارنامه جامع"
    ]

menu_choice = st.selectbox("📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):", menu_options)

# Helper function for teacher check
def check_teacher_auth():
    if not st.session_state['is_teacher']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه حالت 'آموزگار / مدیر' را انتخاب کرده و رمز عبور را وارد کنید.")
        st.stop()

# ---------------------------------------------------------
# 1. Landing Page
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه هوشمند مدیریت کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="feature-box">
        <h4>🌱 طراح و توسعه‌دهنده سامانه: سید موسی حیدری</h4>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران (سال تحصیلی ۱۴۰۵-۱۴۰۴)</p>
    </div>
    
    <div class="feature-box">
        <h4>1️⃣ آزمون‌ساز آنلاین با زمان‌بندی (تستی و تشریحی)</h4>
        <p>پشتیبانی از سوالات تستی و تشریحی، بارگذاری فایل آزمون، تایمر زنده معکوس و تحلیل جامع سوالات.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ ثبت دسته‌جمعی دانش‌آموزان از اکسل</h4>
        <p>ورود یکجای اسامی ۲۹ دانش‌آموز کلاس همراه با تقسیم هوشمند بین ۵ گروه کلاسی با یک کلیک.</p>
    </div>
    
    <div class="feature-box">
        <h4>3️⃣ ارزشیابی کیفی-توصیفی و پایش رفتاری</h4>
        <p>ثبت سطح عملکرد توصیفی در ۷ درس پایه پنجم و صدور کارنامه جامع تحصیلی.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Student Management & Bulk Excel Import
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و بارگذاری سریع از اکسل (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                st.metric("تعداد کل دانش‌آموزان:", len(students_df))
                
            if search_query:
                filtered_df = students_df[students_df['full_name'].str.contains(search_query) | students_df['national_id'].str.contains(search_query)]
            else:
                filtered_df = students_df
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره همراه اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'توضیحات'
            }), use_container_width=True)
            
            st.subheader("🗑️ مدیریت یا حذف پرونده")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف:", students_df['full_name'].tolist(), key="del_student")
            if st.button("حذف پرونده دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {student_to_delete} حذف شد.")
                st.rerun()
        else:
            st.info("هنوز دانش‌آموزی ثبت نشده است. از زبانه 'بارگذاری از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 بارگذاری یکجای اسامی دانش‌آموزان از فایل Excel یا CSV")
        st.info("💡 راهنما: فایل اکسل باید دارای ستون‌های 'نام'، 'نام خانوادگی' و 'کد ملی' باشد. در صورت خالی بودن گروه، سیستم ۲۹ دانش‌آموز را خودکار در ۵ گروه متوازن تقسیم می‌کند.")
        
        # Sample Download Template
        sample_data = pd.DataFrame([
            {"نام": "امیرعلی", "نام خانوادگی": "حیدری", "کد ملی": "1110001111", "شماره اولیا": "09120000001", "گروه کلاسی": "گروه ارمغان 🚀 (۶ نفر)"},
            {"نام": "محمدجواد", "نام خانوادگی": "رضایی", "کد ملی": "1110001112", "شماره اولیا": "09120000002", "گروه کلاسی": "گروه دانا 💡 (۶ نفر)"},
            {"نام": "علی‌رضا", "نام خانوادگی": "مطهری", "کد ملی": "1110001113", "شماره اولیا": "09120000003", "گروه کلاسی": "گروه تلاش 🌟 (۶ نفر)"}
        ])
        csv_bytes = sample_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 دانلود الگوی نمونه فایل اکسل / CSV", data=csv_bytes, file_name="sample_students_template_29.csv", mime="text/csv")
        
        st.markdown("---")
        
        # File uploader with dynamic key reset
        uploaded_file = st.file_uploader(
            "فایل اکسل (.xlsx) یا CSV خود را انتخاب کنید:",
            type=["xlsx", "csv"],
            key=f"excel_uploader_{st.session_state['excel_upload_key']}"
        )
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)
                        
                    st.success(f"فایل با موفقیت خوانده شد. تعداد ردیف‌ها: {len(df_upload)}")
                    st.dataframe(df_upload.head(), use_container_width=True)
                    
                    if st.button("🚀 تایید و ثبت همگی در دیتابیس"):
                        success_count = 0
                        with get_connection() as conn:
                            for idx, row in df_upload.iterrows():
                                fname = str(row.get('نام', '')).strip()
                                lname = str(row.get('نام خانوادگی', '')).strip()
                                nid = str(row.get('کد ملی', '')).strip()
                                phone = str(row.get('شماره اولیا', '')).strip()
                                grp = str(row.get('گروه کلاسی', '')).strip()
                                
                                if not grp or grp == 'nan':
                                    grp = CLASS_GROUPS[idx % len(CLASS_GROUPS)]
                                    
                                if fname and lname:
                                    try:
                                        conn.execute(
                                            "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)",
                                            (fname, lname, nid, phone, grp)
                                        )
                                        success_count += 1
                                    except sqlite3.IntegrityError:
                                        pass
                            conn.commit()
                        st.success(f"🎉 تعداد {success_count} دانش‌آموز با موفقیت وارد دیتابیس شدند!")
                        st.session_state['excel_upload_key'] += 1
                        st.rerun()
                except Exception as e:
                    st.error(f"خطا در پردازش فایل: {e}")
        with col_u2:
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()

    with tab3:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:")
                national_id = st.text_input("کد ملی دانش‌آموز:")
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا:")
            
            selected_grp = st.selectbox("انتخاب گروه کلاسی:", CLASS_GROUPS)
            notes = st.text_area("توضیحات ویژه:")
            submit_btn = st.form_submit_button("ثبت پرونده دانش‌آموز")
            
            if submit_btn and first_name and last_name:
                try:
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes) VALUES (?, ?, ?, ?, ?, ?)",
                            (first_name, last_name, national_id, parent_phone, selected_grp, notes)
                        )
                        conn.commit()
                    st.success(f"دانش‌آموز {first_name} {last_name} ثبت شد.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("کد ملی تکراری است.")

# ---------------------------------------------------------
# 3. Qualitative Evaluation
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا دانش‌آموزان را ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("بازخورد توصیفی و راهکارهای بهبود:")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success(f"ارزشیابی {selected_subject} برای {selected_student} ثبت شد.")

# ---------------------------------------------------------
# 4. Behavior Tracking
# ---------------------------------------------------------
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا دانش‌آموزان را ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار:")
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        desc = st.text_area("شرح جزییات و اقدام انجام‌شده:")
        
        if st.button("ثبت مورد انضباطی / رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title, desc, log_date)
                )
                conn.commit()
            st.success("مشاهده رفتاری ثبت شد.")

# ---------------------------------------------------------
# 5. Advanced Quiz Creator & File Load (Teacher)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین پیشرفته (پشتیبانی از سوالات تستی، تشریحی و فایل آزمون)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["➕ طراحی آزمون دستی (تستی/تشریحی)", "📂 بارگذاری فایل آزمون (JSON/Excel)", "📊 لیست آزمون‌ها و نتایج"])
    
    with tab_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمون علوم فصل ۱ و ۲):")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان پاسخگویی (دقیقه):", min_value=5, max_value=180, value=60, help="زمان معکوس پاسخگویی برای دانش‌آموزان")
            
        num_questions = st.number_input("تعداد سوالات آزمون (بین ۵ تا ۲۰ سوال):", min_value=1, max_value=20, value=5)
        
        st.markdown("---")
        st.subheader("۲. طراحی سوالات و پاسخ‌نامه تشریحی")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.radio(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی / تحلیلی"], key=f"qtype_{i}", horizontal=True)
            q_text = st.text_input(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if "تستی" in q_type:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
                with c2:
                    opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
                with c3:
                    opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
                with c4:
                    opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
                    
                correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
                model_ans = ""
            else:
                opt1, opt2, opt3, opt4, correct_opt = "", "", "", "", None
                model_ans = st.text_area(f"پاسخ نمونه / کلید تصحیح تشریحی سوال {i+1}:", key=f"model_{i}")
                
            expl = st.text_area(f"💡 تحلیل آموزشی و پاسخ‌نامه تشریحی سوال {i+1}:", key=f"expl_{i}")
            questions_data.append(("تستی" if "تستی" in q_type else "تشریحی", q_text, opt1, opt2, opt3, opt4, correct_opt, model_ans, expl))
            st.markdown("---")
            
        if st.button("🚀 انتشار و ذخیره کامل آزمون"):
            if quiz_title and all(q[1] for q in questions_data):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                        (quiz_title, quiz_subject, duration, datetime.date.today())
                    )
                    quiz_id = cursor.lastrowid
                    
                    for q in questions_data:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
                    conn.commit()
                st.success(f"🎉 آزمون '{quiz_title}' با موفقیت انتشار یافت!")
            else:
                st.error("لطفاً عنوان آزمون و متن تمامی سوالات را وارد کنید.")

    with tab_q2:
        st.subheader("📂 بارگذاری فایل آزمون آماده (JSON یا Excel)")
        st.info("شما می‌توانید دفترچه سوالات طراحی‌شده را مستقیماً از طریق فایل JSON بارگذاری کنید.")
        
        sample_json_struct = [
            {
                "question_type": "تستی",
                "question_text": "محیط مربعی به ضلع ۴ سانتی‌متر چقدر است؟",
                "option_1": "۸ سانتی‌متر", "option_2": "۱۲ سانتی‌متر", "option_3": "۱۶ سانتی‌متر", "option_4": "۲۰ سانتی‌متر",
                "correct_option": 3, "model_answer": "", "explanation": "محیط مربع = ضلع × ۴ = ۱۶ سانتی‌متر"
            },
            {
                "question_type": "تشریحی",
                "question_text": "علت تشکیل ابر را به اختصار توضیح دهید.",
                "option_1": "", "option_2": "", "option_3": "", "option_4": "",
                "correct_option": None, "model_answer": "تبخیر آب دریاها و صعود بخار آب به طبقات بالای جو و متراکم شدن آن.",
                "explanation": "میعان بخار آب در هوای سرد بالای جو باعث تشکیل قطرات آب و ابر می‌شود."
            }
        ]
        st.download_button("📥 دانلود الگوی ساختار فایل JSON آزمون", data=json.dumps(sample_json_struct, ensure_ascii=False, indent=2), file_name="sample_quiz_template.json", mime="application/json")
        
        uploaded_quiz_file = st.file_uploader("فایل JSON سوالات آزمون را بارگذاری کنید:", type=["json"])
        if uploaded_quiz_file is not None:
            try:
                quiz_json_data = json.load(uploaded_quiz_file)
                st.success(f"تعداد {len(quiz_json_data)} سوال از فایل خوانده شد.")
                
                col_qf1, col_qf2 = st.columns(2)
                with col_qf1:
                    u_quiz_title = st.text_input("عنوان آزمون بارگذاری‌شده:", value="آزمون آنلاین بارگذاری‌شده از فایل")
                    u_quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="u_q_sub")
                with col_qf2:
                    u_quiz_duration = st.number_input("مدت زمان پاسخگویی (دقیقه):", min_value=5, max_value=180, value=60, key="u_q_dur")
                    
                if st.button("🚀 ایجاد آزمون از روی فایل"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                                       (u_quiz_title, u_quiz_subject, u_quiz_duration, datetime.date.today()))
                        q_id = cursor.lastrowid
                        
                        for q in quiz_json_data:
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (q_id, q.get('question_type', 'تستی'), q.get('question_text', ''),
                                  q.get('option_1', ''), q.get('option_2', ''), q.get('option_3', ''), q.get('option_4', ''),
                                  q.get('correct_option'), q.get('model_answer', ''), q.get('explanation', '')))
                        conn.commit()
                    st.success("آزمون با موفقیت از روی فایل ساخته شد!")
                    st.rerun()
            except Exception as ex:
                st.error(f"خطا در خواندن فایل آزمون: {ex}")

    with tab_q3:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            selected_quiz_id = st.selectbox("انتخاب آزمون برای مشاهده نتایج:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            
            with get_connection() as conn:
                results_df = pd.read_sql_query("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'نمره تستی (درست)',
                           r.total_questions AS 'کل سوالات',
                           r.percentage AS 'درصد تستی ٪',
                           r.descriptive_answers AS 'پاسخ‌های تشریحی دانش‌آموز',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r
                    JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
                
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True)
            else:
                st.info("هنوز دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز آزمونی ساخته نشده است.")

# ---------------------------------------------------------
# 6. Student Online Quiz with Live Countdown Timer
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        quiz_row = quizzes_df[quizzes_df['id'] == q_id].iloc[0]
        quiz_duration = int(quiz_row['duration_minutes'])
        
        # Check if student already submitted
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage, submitted_at FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید. درصد بخش تستی کسب‌شده: {existing['percentage']:.1f}٪ (زمان ثبت: {existing['submitted_at']})")
            
            with st.expander("📖 مشاهده پاسخ‌نامه تشریحی و تحلیل آموزشی سوالات"):
                with get_connection() as conn:
                    qs = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(qs):
                    st.markdown(f"**📌 سوال {idx+1} ({q['question_type']}): {q['question_text']}**")
                    if q['question_type'] == 'تستی':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        st.markdown(f"✅ گزینه صحیح: **گزینه {q['correct_option']}: {opts[q['correct_option']-1]}**")
                    else:
                        st.markdown(f"📝 پاسخ نمونه / کلید تصحیح: **{q['model_answer']}**")
                    if q['explanation']:
                        st.info(f"💡 تحلیل آموزشی و پاسخ تشریحی: {q['explanation']}")
                    st.markdown("---")
        else:
            # Timer Management
            timer_key = f"quiz_start_{q_id}_{s_id}"
            if timer_key not in st.session_state:
                st.session_state[timer_key] = time.time()
                
            elapsed_sec = int(time.time() - st.session_state[timer_key])
            total_allowed_sec = quiz_duration * 60
            remaining_sec = total_allowed_sec - elapsed_sec
            
            if remaining_sec <= 0:
                st.error("⏰ مهلت زمانی پاسخگویی به این آزمون به پایان رسیده است!")
                st.info("پاسخ‌های شما قفل شده‌اند. لطفا جهت شرکت مجدد با معلم تماس بگیرید.")
            else:
                rem_min = remaining_sec // 60
                rem_s = remaining_sec % 60
                
                st.markdown(f"""
                <div class="timer-card">
                    ⏱️ زمان باقی‌مانده آزمون: {rem_min} دقیقه و {rem_s} ثانیه (مدت کل آزمون: {quiz_duration} دقیقه)
                </div>
                """, unsafe_allow_html=True)
                
                # Fetch Questions
                with get_connection() as conn:
                    questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                    
                student_testi_answers = {}
                student_tashrihi_answers = {}
                
                st.markdown("---")
                with st.form("student_quiz_form"):
                    for idx, q in enumerate(questions):
                        st.markdown(f"**📌 سوال {idx+1} ({q['question_type']}): {q['question_text']}**")
                        
                        if q['question_type'] == 'تستی':
                            options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                            user_ans = st.radio(
                                f"پاسخ سوال {idx+1}:",
                                options=[1, 2, 3, 4],
                                format_func=lambda x: f"گزینه {x}: {options[x-1]}",
                                key=f"sq_tasti_{q['id']}"
                            )
                            student_testi_answers[q['id']] = (user_ans, q['correct_option'])
                        else:
                            tashrihi_ans = st.text_area(f"پاسخ تشریحی خود را بنویسید (سوال {idx+1}):", key=f"sq_tashrihi_{q['id']}")
                            student_tashrihi_answers[q['id']] = tashrihi_ans
                            
                        st.markdown("---")
                        
                    submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                    
                    if submit_quiz:
                        correct_count = 0
                        testi_total = len(student_testi_answers)
                        for q_id_key, (ans, correct) in student_testi_answers.items():
                            if ans == correct:
                                correct_count += 1
                                
                        pct = (correct_count / testi_total * 100) if testi_total > 0 else 100
                        
                        descriptive_json = json.dumps(student_tashrihi_answers, ensure_ascii=False)
                        
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, descriptive_answers) VALUES (?, ?, ?, ?, ?, ?)",
                                (q_id, s_id, correct_count, len(questions), pct, descriptive_json)
                            )
                            conn.commit()
                            
                        st.balloons()
                        st.success(f"🎉 آزمون با موفقیت ثبت گردید! نمره بخش تستی: {correct_count} از {testi_total} (معادل {pct:.1f}٪)")
                        st.info("پاسخ‌های تشریحی شما جهت بررسی معلم ثبت گردید. پاسخ‌نامه تشریحی و تحلیل آموزشی اکنون در دسترس شماست.")
                        st.rerun()

# ---------------------------------------------------------
# 7. Dashboard and Comprehensive Report
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و کارنامه جامع")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی برای نمایش وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه جامع:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        st.markdown(f"### 📄 کارنامه جامع تحصیلی و رفتاری: {selected_student}")
        
        col1, col2, col3 = st.columns(3)
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        with col1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with col2:
            st.metric("تعداد موارد رفتاری ثبت‌شده:", beh_count)
        with col3:
            st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3, tab_d4 = st.tabs(["📝 ارزشیابی‌های درسی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها", "📈 نمودار رشد تحصیلی"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = pd.read_sql_query("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = pd.read_sql_query("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True)
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = pd.read_sql_query("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

        with tab_d4:
            st.subheader("📈 نمودار روند رشد آزمون‌ها")
            with get_connection() as conn:
                df_chart = pd.read_sql_query("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
            if not df_chart.empty:
                st.line_chart(df_chart.set_index('آزمون'))
            else:
                st.info("برای رسم نمودار رشد، شرکت در حداقل یک آزمون لازم است.")

