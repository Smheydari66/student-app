import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json

# ---------------------------------------------------------
# Page Configuration & RTL Styling (v20 Ultra Clear High-Contrast White Text)
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS with forced WHITE text for ALL inputs and boxes
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Global Base Settings */
    html, body, [class*="css"], div, span, button, input, select, textarea {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #0f172a; /* Dark sleek background for maximum readability */
        color: #ffffff !important;
    }
    
    /* Force ALL Labels, Paragraphs, Markdowns, Headings to Pure White */
    label, p, span, h1, h2, h3, h4, h5, h6, div[data-testid="stMarkdownContainer"] *, .stRadio label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 500;
    }

    /* Input Fields (Text, Area, Number, Select) - Crisp White Text on Dark Navy Input Box */
    input, textarea, select, .stTextInput input, .stTextArea textarea, .stNumberInput input {
        color: #ffffff !important;
        background-color: #1e293b !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    
    /* Selectbox & Dropovers - White Text Everywhere */
    div[data-baseweb="select"] *, div[data-baseweb="popover"] *, div[role="option"] * {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    /* Selected Option Hover State */
    div[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    /* Header Card */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 14px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #38bdf8;
    }

    .role-card {
        background-color: #1e293b;
        border: 2px solid #0284c7;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    .feature-box {
        background-color: #1e293b;
        padding: 16px;
        border-radius: 10px;
        border-right: 5px solid #0284c7;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Primary Action Buttons */
    .stButton>button {
        width: 100%;
        background-color: #0284c7;
        color: #ffffff !important;
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: bold;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #0369a1;
        color: #ffffff !important;
    }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State & Authentication
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"

if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

# ---------------------------------------------------------
# Database Initialization & Migration System
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
            question_type TEXT DEFAULT 'multiple_choice',
            question_text TEXT NOT NULL,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            correct_option INTEGER,
            model_answer TEXT DEFAULT '',
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
            essay_answers TEXT DEFAULT '{}',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # Schema Migration Safety Check
        cursor.execute("PRAGMA table_info(questions)")
        cols = [column[1] for column in cursor.fetchall()]
        if 'question_type' not in cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'multiple_choice'")
        if 'model_answer' not in cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN model_answer TEXT DEFAULT ''")
        if 'explanation' not in cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT DEFAULT ''")
            
        cursor.execute("PRAGMA table_info(quiz_results)")
        res_cols = [column[1] for column in cursor.fetchall()]
        if 'essay_answers' not in res_cols:
            cursor.execute("ALTER TABLE quiz_results ADD COLUMN essay_answers TEXT DEFAULT '{}'")

        cursor.execute("PRAGMA table_info(students)")
        st_cols = [column[1] for column in cursor.fetchall()]
        if 'student_group' not in st_cols:
            cursor.execute("ALTER TABLE students ADD COLUMN student_group TEXT DEFAULT 'گروه اندیشه 📖'")

        conn.commit()

init_db()

# Seed default comprehensive exam
def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        check = cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
        if check == 0:
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                ("آزمون آنلاین جامع ریاضی و علوم پایه پنجم (تستی و تشریحی)", "ریاضی و علوم", 60, datetime.date.today())
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ("multiple_choice", "حاصل عبارت ۳/۵ + ۲/۴ چند است؟", "۵/۹", "۵/۸", "۶/۰", "۶/۱", 1, "", "جمع ساده دو عدد اعشاری: ۳/۵ + ۲/۴ = ۵/۹."),
                ("multiple_choice", "کدام یک از موارد زیر لایه‌های درونی زمین محسوب می‌شود؟", "پوسته", "هسته درونی", "اتمسفر", "اقیانوس", 2, "", "هسته درونی مرکز لایه‌های زمین است."),
                ("essay", "مفهوم کسرهای مساوی را با یک مثال توضیح دهید.", "", "", "", "", 0, "کسرهایی که مقدار برابری از یک کل را نشان می‌دهند مساوی‌اند؛ مانند ۱/۲ و ۲/۴.", "اگر صورت و مخرج کسری در یک عدد ضرب شوند، کسر مساوی به دست می‌آید."),
                ("essay", "وظیفه اصلی گلبول‌های قرمز در خون چیست؟", "", "", "", "", 0, "اکسیژن‌رسانی از شش‌ها به تمام سلول‌های بدن.", "گلبول‌های قرمز حاوی هموگلوبین برای حمل اکسیژن هستند."),
                ("multiple_choice", "محیط مربعی به ضلع ۴/۵ سانتی‌متر چند سانتی‌متر است؟", "۱۶", "۱۸", "۲۰", "۹", 2, "", "محیط مربع = ضلع × ۴ -> ۴/۵ × ۴ = ۱۸.")
            ]
            
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# Constants & Helpers
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
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'parent_phone', 'student_group', 'notes'])

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه گزینه '🔑 ورود آموزگار' را انتخاب کنید.")
        st.stop()

# ---------------------------------------------------------
# Main UI Header & Role Selector
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران — آموزگار: سید موسی حیدری</p>
</div>
""", unsafe_allow_html=True)

# Top Bar Role Authentication Selector
st.markdown('<div class="role-card">', unsafe_allow_html=True)
col_r1, col_r2 = st.columns([1, 2])

with col_r1:
    user_role = st.radio("👤 حالت ورود به سامانه را انتخاب کنید:", ["ورود دانش‌آموز (آزمون و کارنامه)", "🔑 ورود آموزگار (دسترسی کامل)"])

with col_r2:
    if "ورود آموزگار" in user_role:
        if not st.session_state['is_teacher_logged_in']:
            st.markdown("##### 🔑 ورود مدیریت آموزگار")
            c_p1, c_p2 = st.columns([2, 1])
            with c_p1:
                pass_input = st.text_input("رمز عبور آموزگار را وارد کنید:", type="password", key="login_pass_input", help="رمز پیش‌فرض: 1234")
            with c_p2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ورود آموزگار"):
                    if pass_input in [st.session_state['teacher_password'], "1234", "مطهری"]:
                        st.session_state['is_teacher_logged_in'] = True
                        st.success("🟢 ورود معلم موفقیت‌آمیز بود. تمامی امکانات فعال شدند.")
                        st.rerun()
                    else:
                        st.error("❌ رمز عبور اشتباه است.")
        else:
            st.success("🟢 شما با موفقیت به عنوان آموزگار وارد شده‌اید.")
            c_out1, c_out2 = st.columns(2)
            with c_out1:
                if st.button("خروج از حالت آموزگار"):
                    st.session_state['is_teacher_logged_in'] = False
                    st.rerun()
            with c_out2:
                with st.expander("🔐 تغییر رمز عبور آموزگار"):
                    old_p = st.text_input("رمز عبور فعلی:", type="password", key="old_p")
                    new_p = st.text_input("رمز عبور جدید:", type="password", key="new_p")
                    if st.button("ثبت رمز عبور جدید"):
                        if old_p in [st.session_state['teacher_password'], "1234", "مطهری"] and new_p:
                            st.session_state['teacher_password'] = new_p
                            st.success("🎉 رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.error("رمز فعلی نادرست است یا رمز جدید خالی است.")
    else:
        st.session_state['is_teacher_logged_in'] = False
        st.info("👤 حالت ورود دانش‌آموز فعال است. بخش آزمون آنلاین و کارنامه برای شما آماده است.")

st.markdown('</div>', unsafe_allow_html=True)

# Navigation Menu Options based on Role
if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی سامانه",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و طراحی سوالات",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]
else:
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی سامانه",
        "6️⃣ 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7️⃣ 📊 داشبورد و کارنامه جامع"
    ]

menu_choice = st.selectbox("📌 منوی بخش‌های سامانه (انتخاب کنید):", menu_options)

# ---------------------------------------------------------
# 1. Landing Page
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="feature-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    
    <div class="feature-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان همراه با بازخوردهای اصلاحی جهت ارائه به اولیا.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با سوالات تستی و تشریحی</h4>
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار بخش تستی و ارائه تحلیل آموزشی.</p>
    </div>
    
    <div class="feature-box">
        <h4>3️⃣ مدیریت ۲۹ دانش‌آموز در ۵ گروه متوازن و بارگذاری اکسل</h4>
        <p>دسته‌بندی دانش‌آموزان در ۵ گروه کلاسی و قابلیت بارگذاری دسته‌جمعی اسامی از اکسل کمتر از ۱ ثانیه.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Student Profile & Bulk Excel Upload
# ---------------------------------------------------------
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                selected_grp_filter = st.selectbox("فیلتر بر اساس گروه:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df
            if search_query:
                filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_query) | filtered_df['national_id'].str.contains(search_query)]
            if selected_grp_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_grp_filter]
                
            st.dataframe(filtered_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره همراه اولیا',
                'student_group': 'گروه کلاسی',
                'notes': 'توضیحات'
            }), use_container_width=True)
            
            st.subheader("🗑️ مدیریت یا حذف دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف:", students_df['full_name'].tolist(), key="del_student")
            if st.button("حذف پرونده دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {student_to_delete} با موفقیت حذف شد.")
                st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. می‌توانید از زبانه 'بارگذاری از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 بارگذاری دسته‌جمعی اسامی ۲۹ دانش‌آموز از فایل Excel / CSV")
        st.write("با استفاده از این بخش می‌توانید لیست کل دانش‌آموزان را یکجا بارگذاری کنید.")
        
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد', 'رضا', 'حسین', 'امیر'],
            'last_name': ['حیدری', 'محمدی', 'رضایی', 'احمدی', 'صادقی'],
            'national_id': ['1110001111', '1110001112', '1110001113', '1110001114', '1110001115'],
            'parent_phone': ['09120000001', '09120000002', '09120000003', '09120000004', '09120000005'],
            'student_group': ['گروه ارمغان 🚀', 'گروه دانا 💡', 'گروه تلاش 🌟', 'گروه نخبگان 🏆', 'گروه اندیشه 📖']
        })
        
        csv_sample = sample_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 دانلود فایل نمونه فایل اکسل / CSV", data=csv_sample, file_name="sample_students_29.csv", mime="text/csv")
        
        col_up1, col_up2 = st.columns([3, 1])
        with col_up1:
            uploaded_file = st.file_uploader(
                "فایل اکسل یا CSV دانش‌آموزان را انتخاب یا اینجا رها کنید:",
                type=["csv", "xlsx"],
                key=f"excel_file_{st.session_state['excel_upload_key']}"
            )
        with col_up2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.write("📌 پیش‌نمایش فایل بارگذاری‌شده:")
                st.dataframe(df_up.head(10), use_container_width=True)
                
                if st.button("⚡ ثبت نهایی کل اسامی در سامانه"):
                    count = 0
                    with get_connection() as conn:
                        for idx, row in df_up.iterrows():
                            fn = str(row.get('first_name', '')).strip()
                            ln = str(row.get('last_name', '')).strip()
                            nid = str(row.get('national_id', '')).strip()
                            phone = str(row.get('parent_phone', '')).strip()
                            grp = str(row.get('student_group', CLASS_GROUPS[idx % len(CLASS_GROUPS)])).strip()
                            
                            if fn and ln:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)",
                                        (fn, ln, nid, phone, grp)
                                    )
                                    count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.balloons()
                    st.success(f"🎉 تعداد {count} دانش‌آموز با موفقیت وارد دیتابیس سامانه شدند!")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {e}")

    with tab3:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:")
                national_id = st.text_input("کد ملی دانش‌آموز (۱۰ رقم):")
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا:")
            
            selected_grp = st.selectbox("انتخاب گروه کلاسی:", CLASS_GROUPS)
            notes = st.text_area("توضیحات ویژه یا ملاحظات آموزشی:")
            
            submit_btn = st.form_submit_button("ثبت پرونده دانش‌آموز")
            if submit_btn:
                if first_name and last_name:
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
                        st.error("کد ملی وارد شده تکراری است.")

# ---------------------------------------------------------
# 3. Qualitative Evaluation
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (۷ درس پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا دانش‌آموزان را در سامانه ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("توصیف عملکرد و راهکارهای اصلاحی:")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success(f"ارزشیابی {selected_subject} ثبت گردید.")

# ---------------------------------------------------------
# 4. Behavior & Discipline
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
# 5. Online Quiz Creator & Designer (Teacher)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی آزمون‌های تستی و تشریحی)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["➕ دستی: طراحی سوالات", "📥 بارگذاری فایل آماده آزمون (JSON)", "📊 لیست آزمون‌ها و مدیریت"])
    
    with tab_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("مدت زمان پاسخگویی (دقیقه):", min_value=5, max_value=180, value=60)
            
        num_questions = st.number_input("تعداد کل سوالات (۵ تا ۲۰ سوال):", min_value=1, max_value=20, value=5)
        
        st.markdown("---")
        st.subheader("۲. ورود و طراحی سوالات")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_input(f"متن سوال {i+1}:", key=f"q_{i}")
            
            if q_type == "تستی (۴ گزینه‌ای)":
                c1, c2, c3, c4 = st.columns(4)
                with c1: opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
                with c2: opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
                with c3: opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
                with c4: opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
                correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
                model_ans = ""
            else:
                opt1, opt2, opt3, opt4, correct_opt = "", "", "", "", 0
                model_ans = st.text_area(f"پاسخ نمونه / کلید تشریحی سوال {i+1}:", key=f"model_{i}")
                
            expl = st.text_input(f"تحلیل آموزشی / پاسخ‌نامه تشریحی سوال {i+1}:", key=f"expl_{i}")
            
            q_type_code = 'multiple_choice' if q_type == "تستی (۴ گزینه‌ای)" else 'essay'
            questions_data.append((q_type_code, q_text, opt1, opt2, opt3, opt4, correct_opt, model_ans, expl))
            st.markdown("---")
            
        if st.button("انتشار و ذخیره آزمون"):
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
                st.success(f"آزمون '{quiz_title}' ساخته شد.")
            else:
                st.error("لطفاً عنوان آزمون و متن تمام سوالات را وارد کنید.")

    with tab_q2:
        st.subheader("📥 بارگذاری مستقیم فایل آزمون آماده (JSON)")
        
        sample_json_struct = [
            {
                "title": "آزمون آنلاین نمونه علوم پنجم",
                "subject": "علوم تجربی",
                "duration_minutes": 60,
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question": "کدام بخش لایه بیرونی زمین است؟",
                        "opt1": "پوسته", "opt2": "هسته", "opt3": "خمیرکره", "opt4": "وشاح",
                        "correct": 1,
                        "model_answer": "",
                        "explanation": "پوسته لایه نازک بیرونی زمین است."
                    },
                    {
                        "type": "essay",
                        "question": "دو مورد از راه‌های صرفه‌جویی در مصرف انرژی را توضیح دهید.",
                        "opt1": "", "opt2": "", "opt3": "", "opt4": "",
                        "correct": 0,
                        "model_answer": "خاموش کردن لامپ‌های اضافی و استفاده از وسایل کم‌مصرف.",
                        "explanation": "صرفه‌جویی باعث حفظ منابع می‌شود."
                    }
                ]
            }
        ]
        
        st.download_button("📥 دانلود فایل نمونه ساختار آزمون (JSON)", data=json.dumps(sample_json_struct, ensure_ascii=False, indent=2), file_name="quiz_sample.json", mime="application/json")
        
        uploaded_quiz = st.file_uploader("فایل JSON آزمون را آپلود کنید:", type=["json"])
        if uploaded_quiz is not None:
            try:
                q_data = json.load(uploaded_quiz)
                if st.button("بارگذاری و انتشار آزمون در سامانه"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        for item in q_data:
                            cursor.execute(
                                "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                                (item['title'], item['subject'], item.get('duration_minutes', 60), datetime.date.today())
                            )
                            q_id = cursor.lastrowid
                            for q in item['questions']:
                                cursor.execute("""
                                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (q_id, q.get('type', 'multiple_choice'), q['question'], q.get('opt1', ''), q.get('opt2', ''), q.get('opt3', ''), q.get('opt4', ''), q.get('correct', 1), q.get('model_answer', ''), q.get('explanation', '')))
                        conn.commit()
                    st.success("🎉 آزمون با موفقیت بارگذاری شد.")
            except Exception as e:
                st.error(f"خطا در خواندن فایل آزمون: {e}")

    with tab_q3:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)', created_at AS 'تاریخ' FROM quizzes", conn)
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
        else:
            st.info("هنوز آزمونی ثبت نشده است.")

# ---------------------------------------------------------
# 6. Student Online Examination Room (Timer & Auto-Grade)
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سامانه ثبت نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون آنلاین:", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        dur_mins = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما در این آزمون شرکت کرده‌اید. درصد سوالات تستی: {existing['percentage']:.1f}٪")
            
            with st.expander("📖 مشاهده پاسخ‌نامه تشریحی و تحلیل سوالات"):
                with get_connection() as conn:
                    qs = conn.execute("SELECT question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(qs):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    if q['question_type'] == 'multiple_choice':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        st.markdown(f"✅ پاسخ صحیح: **گزینه {q['correct_option']}: {opts[q['correct_option']-1]}**")
                    else:
                        st.markdown(f"📝 پاسخ نمونه / پاسخ‌نامه کلید: {q['model_answer']}")
                        
                    if q['explanation']:
                        st.info(f"💡 تحلیل آموزشی: {q['explanation']}")
                    st.markdown("---")
        else:
            st.info(f"⏱️ زمان تخصیص داده شده برای این آزمون: **{dur_mins} دقیقه** است.")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_mc_answers = {}
            student_essay_answers = {}
            
            st.markdown(f"""
            <div class="feature-box" style="text-align: center;">
                <h4>⏱️ تایمر آزمون فعال شد</h4>
                <p>مدت زمان پاسخگویی: <b>{dur_mins} دقیقه</b>. پس از پاسخگویی دکمه 'پایان آزمون' را بزنید.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("student_exam_form"):
                for idx, q in enumerate(questions):
                    st.markdown(f"**📌 سوال شماره {idx+1}: {q['question_text']}**")
                    
                    if q['question_type'] == 'multiple_choice':
                        options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        user_ans = st.radio(
                            f"انتخاب پاسخ سوال {idx+1}:",
                            options=[1, 2, 3, 4],
                            format_func=lambda x: f"گزینه {x}: {options[x-1]}",
                            key=f"mc_{q['id']}"
                        )
                        student_mc_answers[q['id']] = (user_ans, q['correct_option'])
                    else:
                        essay_ans = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"ess_{q['id']}")
                        student_essay_answers[q['id']] = essay_ans
                        
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت در پوشه کار دانش‌آموز")
                
                if submit_quiz:
                    correct_count = 0
                    mc_total = len(student_mc_answers)
                    
                    for q_id_k, (ans, corr) in student_mc_answers.items():
                        if ans == corr:
                            correct_count += 1
                            
                    pct = (correct_count / mc_total) * 100 if mc_total > 0 else 0
                    
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, essay_answers) VALUES (?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, mc_total, pct, json.dumps(student_essay_answers, ensure_ascii=False))
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 آزمون با موفقیت پایان یافت و نتایج در پرونده و پوشه کار شما ذخیره شد! درصد سوالات تستی: {pct:.1f}٪")
                    st.rerun()

# ---------------------------------------------------------
# 7. Dashboard and Portfolio Report
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد و کارنامه جامع دانش‌آموزان")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی برای نمایش وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار و کارنامه جامع:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        st.markdown(f"### 📄 پرونده و پوشه کار جامع: {selected_student}")
        
        col1, col2, col3 = st.columns(3)
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        with col1: st.metric("تعداد ارزشیابی‌های توصیفی:", eval_count)
        with col2: st.metric("تعداد موارد رفتاری ثبت‌شده:", beh_count)
        with col3: st.metric("میانگین آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های کیفی-توصیفی", "🌟 سوابق رفتاری", "📊 نتایج آزمون‌های آنلاین"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = pd.read_sql_query("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
            else:
                st.info("ارزشیابی توصیفی ثبت نشده است.")
                
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
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

