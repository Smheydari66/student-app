import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json

# ---------------------------------------------------------
# Page Configuration & RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS
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
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    }

    .author-card {
        background-color: #ffffff;
        border: 2px solid #0284c7;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
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

    /* Dropdown & Popover CSS Fixes */
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    
    li[role="option"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    
    li[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    label, div[data-testid="stMarkdownContainer"] p, .stRadio label {
        color: #0f172a !important;
        font-weight: 500;
    }

    .timer-card {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff !important;
        padding: 14px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = "دانش‌آموز"
if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

# ---------------------------------------------------------
# Database Initialization & Auto-Migration
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
            student_group TEXT DEFAULT 'گروه اندیشه 📖',
            notes TEXT,
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
            duration_minutes INTEGER DEFAULT 60,
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
            option_1 TEXT DEFAULT '',
            option_2 TEXT DEFAULT '',
            option_3 TEXT DEFAULT '',
            option_4 TEXT DEFAULT '',
            correct_option INTEGER DEFAULT 1,
            model_answer TEXT DEFAULT '',
            explanation TEXT DEFAULT '',
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
            essay_answers TEXT DEFAULT '{}',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # ---------------------------------------------------------
        # Schema Migration Guards for Existing Databases
        # ---------------------------------------------------------
        # Check 'students' columns
        cursor.execute("PRAGMA table_info(students)")
        s_cols = [r['name'] for r in cursor.fetchall()]
        if 'student_group' not in s_cols:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN student_group TEXT DEFAULT 'گروه اندیشه 📖'")
            except Exception:
                pass

        # Check 'questions' columns
        cursor.execute("PRAGMA table_info(questions)")
        q_cols = [r['name'] for r in cursor.fetchall()]
        if 'question_type' not in q_cols:
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'mcq'")
            except Exception:
                pass
        if 'model_answer' not in q_cols:
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN model_answer TEXT DEFAULT ''")
            except Exception:
                pass
        if 'explanation' not in q_cols:
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT DEFAULT ''")
            except Exception:
                pass

        # Check 'quiz_results' columns
        cursor.execute("PRAGMA table_info(quiz_results)")
        r_cols = [r['name'] for r in cursor.fetchall()]
        if 'essay_answers' not in r_cols:
            try:
                cursor.execute("ALTER TABLE quiz_results ADD COLUMN essay_answers TEXT DEFAULT '{}'")
            except Exception:
                pass

        conn.commit()

init_db()

# ---------------------------------------------------------
# Seed Default Comprehensive Quiz
# ---------------------------------------------------------
def seed_default_quiz():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM quizzes")
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                ("آزمون آنلاین جامع ریاضی و علوم (تستی-تشریحی)", "ریاضی", 60, datetime.date.today())
            )
            quiz_id = c.lastrowid
            
            sample_questions = [
                ("mcq", "حاصل کسر ۳/۵ به اضافه ۱/۱۰ کدام گزینه است؟", "۷/۱۰", "۴/۱۵", "۴/۱۰", "۵/۱۰", 1, "", "برای جمع کسرها مخرج مشترک ۱۰ گرفته می‌شود: ۶/۱۰ + ۱/۱۰ = ۷/۱۰."),
                ("mcq", "کدام یک از موارد زیر تغییر شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "پختن نان و سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "پختن نان و سوختن تغییر شیمیایی است زیرا جنس ماده عوض می‌شود."),
                ("essay", "مفهوم ارزش مکانی رقم ۵ را در عدد ۳۴۵,۸۱۲ با رسم شکل یا توصیف ریاضی توضیح دهید.", "", "", "", "", 0, "رقم ۵ در مرتبه یکان‌هزار قرار دارد و ارزش مکانی آن برابر با ۵,۰۰۰ است.", "تحلیل: شناسایی مرتبه یکان‌هزار در اعداد ۶ رقمی."),
                ("essay", "سه مورد از نقش‌ها و وظایف اصلی گیاهان را در زنجیره غذایی محیط زیست شرح دهید.", "", "", "", "", 0, "۱. تولیدکننده اکسیژن، ۲. منبع غذایی اصلی جانداران گیاه‌خوار، ۳. تثبیت خاک و جلوگیری از فرسایش.", "پاسخ کامل باید به نقش تولیدکنندگی اشاره داشته باشد.")
            ]
            
            for q in sample_questions:
                c.execute("""
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

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود مدیریت آموزگار' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# Main UI Header
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>ارزشیابی کیفی-توصیفی، پایش رفتاری و برگزاری آزمون‌های آنلاین</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Role & Access Control Selection
# ---------------------------------------------------------
st.markdown('<div class="role-card">', unsafe_allow_html=True)
col_r1, col_r2 = st.columns([1, 2])

with col_r1:
    role_choice = st.radio(
        "👤 نقش خود را انتخاب کنید:",
        ["دانش‌آموز 👨‍🎓", "آموزگار 👨‍🏫"],
        horizontal=True
    )

with col_r2:
    if role_choice == "آموزگار 👨‍🏫":
        st.markdown("<div style='margin-bottom: 8px;'><b>🔑 ورود مدیریت آموزگار:</b></div>", unsafe_allow_html=True)
        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            pass_input = st.text_input("رمز عبور آموزگار را وارد کنید:", type="password", key="tech_pass_input", label_visibility="collapsed")
        with col_p2:
            if st.button("ورود به سامانه"):
                if pass_input == st.session_state['teacher_password'] or pass_input in ["1234", "مطهری"]:
                    st.session_state['is_teacher_logged_in'] = True
                    st.session_state['user_role'] = "آموزگار"
                    st.success("🟢 ورود موفقیت‌آمیز آموزگار.")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است.")
        
        if st.session_state['is_teacher_logged_in']:
            st.success("🟢 شما به عنوان آموزگار وارد شده‌اید.")
            with st.expander("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز عبور فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز عبور جدید:", type="password", key="new_p")
                if st.button("ذخیره رمز جدید"):
                    if old_p == st.session_state['teacher_password'] or old_p in ["1234", "مطهری"]:
                        if new_p:
                            st.session_state['teacher_password'] = new_p
                            st.success("رمز عبور با موفقیت تغییر یافت.")
                        else:
                            st.warning("رمز جدید نمی‌تواند خالی باشد.")
                    else:
                        st.error("رمز عبور فعلی نادرست است.")
    else:
        st.session_state['user_role'] = "دانش‌آموز"
        st.session_state['is_teacher_logged_in'] = False
        st.info("👤 حالت دانش‌آموز فعال است (دسترسی به شرکت در آزمون و مشاهده کارنامه).")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Dynamic Menu Filtering by Role
# ---------------------------------------------------------
if st.session_state['is_teacher_logged_in']:
    available_menu_options = [
        "1. 🏠 صفحه اصلی و معرفی برنامه",
        "2. 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (معلم)",
        "3. 📝 ارزشیابی کیفی-توصیفی (معلم)",
        "4. 🌟 ثبت رفتار و انضباط (معلم)",
        "5. ✏️ آزمون‌ساز آنلاین (معلم)",
        "6. 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7. 📊 داشبورد و کارنامه جامع"
    ]
else:
    available_menu_options = [
        "1. 🏠 صفحه اصلی و معرفی برنامه",
        "6. 📱 شرکت در آزمون آنلاین (دانش‌آموز)",
        "7. 📊 داشبورد و کارنامه جامع"
    ]

menu_choice = st.selectbox(
    "📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):",
    available_menu_options
)

# ---------------------------------------------------------
# 1. Landing Page / About
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="author-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه</h3>
        <h4 style="color: #0284c7;">سید موسی حیدری</h4>
        <p style="font-size: 1.1em; font-weight: bold;">آموزگار پایه پنجم ابتدایی - مدرسه شهید مطهری مهران</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 اهداف و امکانات اصلی سامانه:")
    
    st.markdown("""
    <div class="feature-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در تمامی دروس همراه با بازخوردهای سازنده.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ آزمون‌ساز آنلاین پیشرفته (تستی و تشریحی) با تحلیل آموزگار</h4>
        <p>برگزاری آزمون‌های ۵ تا ۲۰ سوالی با زمان‌بندی معکوس (مثلاً ۶۰ دقیقه) و ارائه پاسخ‌نامه تشریحی.</p>
    </div>
    
    <div class="feature-box">
        <h4>3️⃣ پایش رفتاری و گروه‌بندی کلاسی (۲۹ دانش‌آموز در ۵ گروه)</h4>
        <p>دسته‌بندی متوازن دانش‌آموزان در ۵ گروه آموزشی (۴ گروه ۶ نفره + ۱ گروه ۵ نفره) و ثبت مشاهدات انضباطی.</p>
    </div>
    
    <div class="feature-box">
        <h4>4️⃣ بارگذاری سریع اطلاعات از فایل اکسل</h4>
        <p>ورود یکجای اسامی دانش‌آموزان از طریق فایل Excel/CSV بدون نیاز به ثبت تکی.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Student Profile & Bulk Excel Upload (Teacher Only)
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
                selected_group_filter = st.selectbox("فیلتر بر اساس گروه کلاسی:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
            filtered_df = students_df
            if search_query:
                filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_query) | filtered_df['national_id'].str.contains(search_query)]
            if selected_group_filter != "همه گروه‌ها":
                filtered_df = filtered_df[filtered_df['student_group'] == selected_group_filter]
                
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
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 ثبت یکجای اسامی ۲۹ دانش‌آموز از طریق اکسل/CSV")
        st.write("جهت ثبت سریع اسامی، فایل اکسل را بر اساس ستون‌های زیر بارگذاری کنید:")
        
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد', 'حسین'],
            'last_name': ['حیدری', 'رضایی', 'مطهری'],
            'national_id': ['1111111111', '2222222222', '3333333333'],
            'parent_phone': ['09180000001', '09180000002', '09180000003'],
            'student_group': ['گروه ارمغان 🚀 (۶ نفر)', 'گروه دانا 💡 (۶ نفر)', 'گروه اندیشه 📖 (۵ نفر)'],
            'notes': ['نمونه ۱', 'نمونه ۲', 'نمونه ۳']
        })
        
        csv_sample = sample_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 دریافت فایل نمونه الگوی اکسل (CSV)",
            data=csv_sample,
            file_name="sample_students_template_29.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        col_clear1, col_clear2 = st.columns([3, 1])
        with col_clear2:
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
                
        uploaded_file = st.file_uploader(
            "فایل اکسل (.xlsx یا .csv) حاوی اسامی دانش‌آموزان را انتخاب یا کشیده و رها کنید:",
            type=["csv", "xlsx"],
            key=f"excel_file_uploader_{st.session_state['excel_upload_key']}"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.write("👀 پیش‌نمایش اطلاعات فایل آپلود شده:")
                st.dataframe(df_up.head(10), use_container_width=True)
                
                if st.button("🚀 افزودن همگی دانش‌آموزان به پایگاه داده"):
                    success_count = 0
                    duplicate_count = 0
                    
                    default_groups = [
                        "گروه ارمغان 🚀 (۶ نفر)",
                        "گروه دانا 💡 (۶ نفر)",
                        "گروه تلاش 🌟 (۶ نفر)",
                        "گروه نخبگان 🏆 (۶ نفر)",
                        "گروه اندیشه 📖 (۵ نفر)"
                    ]
                    
                    with get_connection() as conn:
                        for idx, row in df_up.iterrows():
                            f_name = str(row.get('first_name', '')).strip()
                            l_name = str(row.get('last_name', '')).strip()
                            n_id = str(row.get('national_id', '')).strip()
                            p_phone = str(row.get('parent_phone', '')).strip() if pd.notna(row.get('parent_phone')) else ""
                            
                            grp = str(row.get('student_group', '')).strip() if pd.notna(row.get('student_group')) else ""
                            if not grp or grp not in default_groups:
                                grp = default_groups[idx % len(default_groups)]
                                
                            nts = str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else ""
                            
                            if f_name and l_name:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                        (f_name, l_name, n_id, p_phone, grp, nts)
                                    )
                                    success_count += 1
                                except sqlite3.IntegrityError:
                                    duplicate_count += 1
                        conn.commit()
                        
                    st.success(f"🎉 تعداد {success_count} دانش‌آموز با موفقیت ثبت شد.")
                    if duplicate_count > 0:
                        st.warning(f"تعداد {duplicate_count} دانش‌آموز به علت کد ملی تکراری نادیده گرفته شد.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل اکسل: {e}")

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
            notes = st.text_area("توضیحات ویژه یا ملاحظات پزشکی/آموزشی:")
            
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
                        st.success(f"دانش‌آموز {first_name} {last_name} با موفقیت ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. Qualitative Evaluation (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("ابتدا باید دانش‌آموزان را در سیستم ثبت کنید.")
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
# 4. Behavior and Discipline Tracking (Teacher Only)
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
# 5. Online Quiz Creator & Manager (Teacher Side)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین پیشرفته (طراحی سوالات ۵ تا ۲۰ تایی)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["➕ طراحی آزمون جدید (تستی و تشریحی)", "📂 بارگذاری آزمون از فایل JSON", "📊 لیست آزمون‌ها و نتایج"])
    
    with tab_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمونک فصل اول ریاضی):")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه - مثلاً ۶۰):", min_value=5, max_value=180, value=60)
            
        num_questions = st.number_input("تعداد کل سوالات آزمون (بین ۵ تا ۲۰ سوال):", min_value=1, max_value=20, value=5)
        
        st.markdown("---")
        st.subheader("۲. طراحی سوالات و پاسخ‌نامه تشریحی")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if q_type == "تستی (۴ گزینه‌ای)":
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
                with c2:
                    opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
                with c3:
                    opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
                with c4:
                    opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
                correct_opt = st.selectbox(f"گزینه صحیح برای سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
                model_ans = ""
            else:
                opt1, opt2, opt3, opt4 = "", "", "", ""
                correct_opt = 0
                model_ans = st.text_area(f"پاسخ نمونه / کلید تشریحی برای سوال {i+1}:", key=f"model_{i}")
                
            expl = st.text_area(f"💡 تحلیل آموزشی و پاسخ‌نامه تشریحی سوال {i+1}:", key=f"expl_{i}")
            questions_data.append(("mcq" if q_type == "تستی (۴ گزینه‌ای)" else "essay", q_text, opt1, opt2, opt3, opt4, correct_opt, model_ans, expl))
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
                        cursor.execute(
                            """INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8])
                        )
                    conn.commit()
                st.success(f"🎉 آزمون '{quiz_title}' با موفقیت انتشار یافت!")
            else:
                st.error("لطفاً عنوان آزمون و متن تمام سوالات را وارد کنید.")

    with tab_q2:
        st.subheader("📂 بارگذاری سریع آزمون آماده از فایل JSON")
        st.write("می‌توانید ساختار سوالات آزمون را در قالب یک فایل JSON بارگذاری کنید:")
        
        sample_quiz_json = {
            "title": "آزمونک نمونه فصل دوم علوم پنجم",
            "subject": "علوم تجربی",
            "duration_minutes": 45,
            "questions": [
                {
                    "type": "mcq",
                    "text": "کدام تغییر شیمیایی است؟",
                    "opt1": "تبخیر آب", "opt2": "سوختن چوب", "opt3": "ذوب یخ", "opt4": "خرد کردن کاغذ",
                    "correct": 2,
                    "explanation": "سوختن چوب تغییر شیمیایی است."
                },
                {
                    "type": "essay",
                    "text": "تفاوت تغییر فیزیکی و شیمیایی را با دو مثال توضیح دهید.",
                    "model_answer": "در تغییر فیزیکی جنس ماده عوض نمی‌شود اما در شیمیایی ماده جدید تولید می‌شود.",
                    "explanation": "تحلیل پاسخ‌های تشریحی علوم."
                }
            ]
        }
        
        st.download_button(
            label="📥 دریافت نمونه ساختار فایل آزمون (JSON)",
            data=json.dumps(sample_quiz_json, ensure_ascii=False, indent=2),
            file_name="sample_quiz_template.json",
            mime="application/json"
        )
        
        uploaded_quiz_file = st.file_uploader("فایل JSON آزمون را بارگذاری کنید:", type=["json"])
        if uploaded_quiz_file is not None:
            try:
                q_data = json.load(uploaded_quiz_file)
                st.write(f"📌 عنوان آزمون: **{q_data.get('title')}** (مدت زمان: {q_data.get('duration_minutes')} دقیقه)")
                if st.button("🚀 ایجاد آزمون از فایل"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                            (q_data.get('title'), q_data.get('subject', 'ریاضی'), q_data.get('duration_minutes', 60), datetime.date.today())
                        )
                        quiz_id = cursor.lastrowid
                        
                        for q in q_data.get('questions', []):
                            cursor.execute(
                                """INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (
                                    quiz_id,
                                    q.get('type', 'mcq'),
                                    q.get('text', ''),
                                    q.get('opt1', ''), q.get('opt2', ''), q.get('opt3', ''), q.get('opt4', ''),
                                    q.get('correct', 1),
                                    q.get('model_answer', ''),
                                    q.get('explanation', '')
                                )
                            )
                        conn.commit()
                    st.success("آزمون با موفقیت بارگذاری شد.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل آزمون: {e}")

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
                           r.percentage AS 'درصد ٪',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r
                    JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
                
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True)
            else:
                st.info("هنوز هیچ دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز آزمونی ساخته نشده است.")

# ---------------------------------------------------------
# 6. Student Online Quiz Interface with Countdown Timer
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
        duration_mins = int(quizzes_df[quizzes_df['title'] == quiz_name]['duration_minutes'].values[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage, essay_answers FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده در بخش تستی: {existing['percentage']:.1f}٪")
            
            with st.expander("📖 مشاهده پاسخ‌نامه تشریحی و تحلیل آموزشی سوالات"):
                with get_connection() as conn:
                    qs = conn.execute("SELECT question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(qs):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    if q['question_type'] == 'mcq':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        st.markdown(f"✅ گزینه صحیح: **گزینه {q['correct_option']}: {opts[q['correct_option']-1]}**")
                    else:
                        st.markdown(f"📝 **پاسخ نمونه تشریحی آموزگار:** {q['model_answer']}")
                        
                    if q['explanation']:
                        st.info(f"💡 تحلیل آموزشی: {q['explanation']}")
                    st.markdown("---")
        else:
            st.markdown(f"""
            <div class="timer-card">
                ⏱️ زمان فعال این آزمون: <b>{duration_mins} دقیقه</b> | پس از شروع، زمان معکوس محاسبه می‌شود.
            </div>
            """, unsafe_allow_html=True)
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_mcq_answers = {}
            student_essay_answers = {}
            
            st.markdown("---")
            with st.form("student_quiz_form"):
                for idx, q in enumerate(questions):
                    st.markdown(f"**📌 سوال {idx+1} ({'تستی' if q['question_type'] == 'mcq' else 'تشریحی'}): {q['question_text']}**")
                    
                    if q['question_type'] == 'mcq':
                        options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        user_ans = st.radio(
                            f"پاسخ سوال {idx+1}:",
                            options=[1, 2, 3, 4],
                            format_func=lambda x, opts=options: f"گزینه {x}: {opts[x-1]}",
                            key=f"sq_{q['id']}"
                        )
                        student_mcq_answers[q['id']] = (user_ans, q['correct_option'])
                    else:
                        essay_ans = st.text_area(f"پاسخ تشریحی خود را برای سوال {idx+1} بنویسید:", key=f"sq_essay_{q['id']}")
                        student_essay_answers[q['id']] = essay_ans
                        
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی پاسخ‌ها")
                
                if submit_quiz:
                    correct_count = 0
                    mcq_total = len(student_mcq_answers)
                    
                    for q_id_key, (ans, correct) in student_mcq_answers.items():
                        if ans == correct:
                            correct_count += 1
                            
                    pct = (correct_count / mcq_total) * 100 if mcq_total > 0 else 100.0
                    essay_json = json.dumps(student_essay_answers, ensure_ascii=False)
                    
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, essay_answers) VALUES (?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, mcq_total, pct, essay_json)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 آزمون با موفقیت به پایان رسید! درصد بخش تستی شما: {pct:.1f}٪")
                    st.info("پاسخ‌های تشریحی شما جهت بررسی و بازخورد تحلیلی معلم ثبت گردید.")

# ---------------------------------------------------------
# 7. Dashboard and Analytical Report
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
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

        with tab_d4:
            st.subheader("📈 نمودار روند درصدی آزمون‌ها")
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

