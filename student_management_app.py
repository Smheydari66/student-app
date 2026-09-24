import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json

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
    
    .card-box {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
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
    
    input, select, textarea, div[data-baseweb="select"] {
        color: #ffffff !important;
        background-color: #0f172a !important;
        border-radius: 8px !important;
    }
    
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
    
    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            student_pin TEXT DEFAULT '1234',
            student_group TEXT DEFAULT 'بدون گروه',
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
            FOREIGN KEY (student_id) REFERENCES students (id)
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
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
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
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password TEXT NOT NULL
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO teacher_auth (id, password) VALUES (1, '1234')")
        
        columns_to_add = [
            ("students", "student_pin", "TEXT DEFAULT '1234'"),
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

def safe_read_sql(query, conn, params=None):
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception:
        init_db()
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception:
            return pd.DataFrame()

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
        df = safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_pin, student_group, notes FROM students", conn)
    return df

def check_teacher_password(pwd):
    with get_connection() as conn:
        res = conn.execute("SELECT password FROM teacher_auth WHERE id = 1").fetchone()
        return res['password'] == pwd if res else pwd == '1234'

def update_teacher_password(new_pwd):
    with get_connection() as conn:
        conn.execute("UPDATE teacher_auth SET password = ?", (new_pwd,))
        conn.commit()

if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'دانش‌آموز'
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False
if 'show_welcome_page' not in st.session_state:
    st.session_state['show_welcome_page'] = True

# WELCOME PAGE
if st.session_state['show_welcome_page']:
    st.markdown("""
    <div class="main-header">
        <h1>🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی خوش آمدید 🌸</h1>
        <p style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">🏫 دبستان شهید مطهری مهران — سال تحصیلی ۱۴۰۴-۱۴۰۵</p>
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

# MAIN HEADER
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین — پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران | آموزگار: سید موسی حیدری</p>
</div>
""", unsafe_allow_html=True)

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

st.markdown("### 📌 منوی بخش‌های سامانه (انتخاب کنید):")

if st.session_state['is_teacher_logged_in']:
    menu_options = [
        "1️⃣ 🏠 معرفی سامانه و اهداف آموزشی",
        "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی (۲۹ نفر)",
        "3️⃣ 📝 ثبت ارزشیابی کیفی-توصیفی",
        "4️⃣ 🌟 مدیریت رفتار و مشاهدات انضباطی",
        "5️⃣ ✏️ آزمون‌ساز آنلاین و بارگذاری سریع",
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

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه در کادر '🔑 ورود معلم' رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# 1. LANDING
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    st.markdown("""
    <div class="card-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه: <b>سید موسی حیدری</b></h3>
        <p>آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    
    <div class="card-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان همراه با بازخوردهای اصلاحی جهت ارائه به اولیا.</p>
    </div>
    
    <div class="card-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با قابلیت بارگذاری اکسل، متن یا JSON</h4>
        <p>طراحی سریع آزمون، تعیین زمان معکوس، تصحیح خودکار بخش تستی و ۴ لایه امنیتی هوشمند.</p>
    </div>
    """, unsafe_allow_html=True)

# 2. STUDENT PROFILES
elif menu_choice.startswith("2"):
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    students_df = load_students()
    if not students_df.empty:
        st.dataframe(students_df.rename(columns={
            'id': 'شناسه',
            'full_name': 'نام و نام خانوادگی',
            'national_id': 'کد ملی',
            'parent_phone': 'شماره اولیا',
            'student_pin': 'رمز ۴ رقمی اختصاصی',
            'student_group': 'گروه کلاسی',
            'notes': 'توضیحات'
        }), use_container_width=True)

# 3. EVALUATIONS
elif menu_choice.startswith("3"):
    check_teacher_auth()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    students_df = load_students()
    if not students_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col2:
            selected_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("بازخورد توصیفی معلم:")
        if st.button("ثبت ارزشیابی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success("ارزشیابی با موفقیت ثبت شد.")

# 4. BEHAVIORS
elif menu_choice.startswith("4"):
    check_teacher_auth()
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
    students_df = load_students()
    if not students_df.empty:
        selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
        b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        title = st.text_input("عنوان رفتار:")
        desc = st.text_area("جزییات:")
        if st.button("ثبت مشاهده رفتاری"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, b_type, title, desc, datetime.date.today())
                )
                conn.commit()
            st.success("مشاهده رفتاری ثبت شد.")

# 5. QUIZ CREATOR (ENHANCED BULK UPLOAD)
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (بارگذاری آسان از اکسل، متن کپی شده یا دستی)")
    
    tab_q1, tab_q_excel, tab_q_text, tab_q_json, tab_q_results = st.tabs([
        "➕ طراحی دستی سوالات",
        "📊 بارگذاری از فایل اکسل (Excel)",
        "📋 کپی-پیست متن یکجا",
        "📥 بارگذاری فایل JSON",
        "📈 لیست آزمون‌ها و نتایج"
    ])
    
    with tab_q1:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=60)
            
        num_q = st.number_input("تعداد سوالات:", min_value=1, max_value=30, value=2)
        questions_input = []
        for i in range(int(num_q)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_text = st.text_area(f"متن سوال {i+1}:", key=f"qtext_{i}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
            with c2: o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
            with c3: o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
            with c4: o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
            corr = st.selectbox(f"گزینه صحیح:", [1, 2, 3, 4], key=f"corr_{i}")
            exp = st.text_area(f"تحلیل و پاسخ تشریحی {i+1}:", key=f"exp_{i}")
            questions_input.append(('mcq', q_text, o1, o2, o3, o4, corr, None, exp))
            st.markdown("---")
            
        if st.button("🚀 انتشار آزمون دستی"):
            if quiz_title and all(q[1] for q in questions_input):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (quiz_title, quiz_subject, duration, datetime.date.today())
                    )
                    qid = cursor.lastrowid
                    for q in questions_input:
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (qid, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' منتشر شد.")

    with tab_q_excel:
        st.subheader("📊 بارگذاری سریع سوالات از فایل اکسل (Excel / CSV)")
        st.info("💡 راحت‌ترین روش: ستون‌های فایل اکسل شامل 'متن سوال'، 'گزینه ۱'، 'گزینه ۲'، 'گزینه ۳'، 'گزینه ۴' و 'گزینه صحیح (۱-۴)' است.")
        
        c_ex1, c_ex2, c_ex3 = st.columns(3)
        with c_ex1: ex_title = st.text_input("عنوان آزمون جدید (از اکسل):", key="ex_q_title")
        with c_ex2: ex_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="ex_q_sub")
        with c_ex3: ex_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=180, value=45, key="ex_q_dur")
        
        uploaded_excel = st.file_uploader("فایل اکسل (.xlsx) یا (.csv) را بارگذاری کنید:", type=["xlsx", "xls", "csv"], key="quiz_excel_file")
        if uploaded_excel is not None:
            try:
                if uploaded_excel.name.endswith(".csv"):
                    df_q = pd.read_csv(uploaded_excel)
                else:
                    df_q = pd.read_excel(uploaded_excel)
                    
                st.success(f"فایل اکسل با موفقیت خوانده شد ({len(df_q)} سوال پیدا شد).")
                st.dataframe(df_q, use_container_width=True)
                
                if st.button("🚀 ایجاد و فعال‌سازی آزمون از اکسل", key="btn_create_ex"):
                    if not ex_title:
                        st.error("لطفاً عنوان آزمون را وارد کنید.")
                    else:
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                                (ex_title, ex_subject, ex_duration, datetime.date.today())
                            )
                            qid = cursor.lastrowid
                            cnt = 0
                            for _, row in df_q.iterrows():
                                q_text = str(row.get('متن سوال', '')).strip()
                                o1 = str(row.get('گزینه ۱', row.get('گزینه 1', ''))).strip()
                                o2 = str(row.get('گزینه ۲', row.get('گزینه 2', ''))).strip()
                                o3 = str(row.get('گزینه ۳', row.get('گزینه 3', ''))).strip()
                                o4 = str(row.get('گزینه ۴', row.get('گزینه 4', ''))).strip()
                                try:
                                    corr = int(row.get('گزینه صحیح (1 تا 4)', row.get('گزینه صحیح', 1)))
                                except (ValueError, TypeError):
                                    corr = 1
                                exp = str(row.get('پاسخ نمونه / تحلیل آموزشی', '')).strip()
                                
                                if q_text:
                                    cursor.execute("""
                                        INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                        VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, None, ?)
                                    """, (qid, q_text, o1, o2, o3, o4, corr, exp))
                                    cnt += 1
                            conn.commit()
                        st.success(f"🎉 آزمون '{ex_title}' با {cnt} سوال از اکسل ساخته شد!")
            except Exception as e:
                st.error(f"خطا در بارگذاری اکسل: {e}")

    with tab_q_text:
        st.subheader("📋 ورود یکجای سوالات با کپی-پیست متن (بدون فایل)")
        st.info("💡 اگر فایلی ندارید، متن سوالات را مستقیم اینجا کپی-پیست کنید.")
        
        c_tx1, c_tx2, c_tx3 = st.columns(3)
        with c_tx1: tx_title = st.text_input("عنوان آزمون متنی:", key="tx_title")
        with c_tx2: tx_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS, key="tx_sub")
        with c_tx3: tx_duration = st.number_input("زمان (دقیقه):", min_value=5, max_value=180, value=30, key="tx_dur")
        
        sample_paste = """سوال ۱: حاصل کسر ۲/۵ + ۳/۱۰ کدام است؟ | گزینه ۱: ۷/۱۰ | گزینه ۲: ۵/۱۵ | گزینه ۳: ۱/۲ | گزینه ۴: ۴/۱۰ | پاسخ صحیح: ۱
سوال ۲: کدام‌یک تغییر شیمیایی است؟ | گزینه ۱: ذوب یخ | گزینه ۲: تبخیر آب | گزینه ۳: سوختن چوب | گزینه ۴: خرد کردن کاغذ | پاسخ صحیح: ۳"""
        
        pasted_text = st.text_area("متن سوالات را کپی-پیست کنید (با کاراکتر | جدا کنید):", value=sample_paste, height=180)
        if st.button("🚀 ایجاد آزمون از متن کپی شده", key="btn_create_tx"):
            if tx_title and pasted_text.strip():
                lines = pasted_text.strip().split("\n")
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (tx_title, tx_subject, tx_duration, datetime.date.today())
                    )
                    qid = cursor.lastrowid
                    cnt = 0
                    for line in lines:
                        if not line.strip(): continue
                        parts = [p.strip() for p in line.split("|")]
                        q_txt = parts[0]
                        o1 = parts[1].replace("گزینه ۱:", "").replace("گزینه 1:", "").strip() if len(parts) > 1 else "گزینه ۱"
                        o2 = parts[2].replace("گزینه ۲:", "").replace("گزینه 2:", "").strip() if len(parts) > 2 else "گزینه ۲"
                        o3 = parts[3].replace("گزینه ۳:", "").replace("گزینه 3:", "").strip() if len(parts) > 3 else "گزینه ۳"
                        o4 = parts[4].replace("گزینه ۴:", "").replace("گزینه 4:", "").strip() if len(parts) > 4 else "گزینه ۴"
                        try:
                            corr = int(parts[5].replace("پاسخ صحیح:", "").replace("جواب:", "").strip()) if len(parts) > 5 else 1
                        except (ValueError, IndexError):
                            corr = 1
                        cursor.execute("""
                            INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                            VALUES (?, 'mcq', ?, ?, ?, ?, ?, ?, None, 'ورود متنی')
                        """, (qid, q_txt, o1, o2, o3, o4, corr))
                        cnt += 1
                    conn.commit()
                st.success(f"🎉 آزمون '{tx_title}' شامل {cnt} سوال با موفقیت ساخته شد!")

    with tab_q_json:
        st.subheader("📥 بارگذاری فایل JSON (روش برنامه‌نویسی)")
        sample_json = {"title": "نمونه آزمون", "subject": "ریاضی", "duration_minutes": 30, "questions": [{"question_type": "mcq", "question_text": "نمونه سوال؟", "option_1": "الف", "option_2": "ب", "option_3": "ج", "option_4": "د", "correct_option": 1}]}
        st.download_button("📥 دانلود الگوی JSON", json.dumps(sample_json, ensure_ascii=False, indent=2), "quiz_template.json", "application/json")
        uploaded_json = st.file_uploader("فایل JSON را انتخاب کنید:", type=["json"])
        if uploaded_json is not None:
            try:
                data = json.load(uploaded_json)
                if st.button("⚡ فعال‌سازی آزمون JSON"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO quizzes (title, subject, duration_minutes, is_active, created_at) VALUES (?, ?, ?, 1, ?)", (data.get('title'), data.get('subject', 'ریاضی'), data.get('duration_minutes', 30), datetime.date.today()))
                        qid = cursor.lastrowid
                        for q in data.get('questions', []):
                            cursor.execute("INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (qid, q.get('question_type', 'mcq'), q.get('question_text'), q.get('option_1'), q.get('option_2'), q.get('option_3'), q.get('option_4'), q.get('correct_option', 1), q.get('model_answer'), q.get('explanation')))
                        conn.commit()
                    st.success("آزمون JSON فعال شد!")
            except Exception as e: st.error(f"خطا: {e}")

    with tab_q_results:
        with get_connection() as conn:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)

# 6. STUDENT QUIZ TAKING
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
        correct_pin = str(s_row.get('student_pin', '1234'))
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        st.markdown("<div style='margin-bottom: 4px; font-weight: bold;'>🔑 رمز ۴ رقمی اختصاصی دانش‌آموز را وارد کنید:</div>", unsafe_allow_html=True)
        entered_pin = st.text_input("رمز اختصاصی:", type="password", key="student_quiz_pin_input", label_visibility="collapsed")
        
        if entered_pin:
            if entered_pin.strip() != correct_pin.strip():
                st.error("❌ رمز ۴ رقمی اختصاصی اشتباه است. لطفاً رمز صحیح خود را وارد کنید.")
            else:
                st.success("🔓 رمز تایید شد. خوش آمدید!")
                with get_connection() as conn:
                    existing = conn.execute("SELECT id, percentage, photo_data FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
                    
                if existing:
                    st.warning("⚠️ این آزمون قبلاً توسط شما تحویل داده شده و قفل گردیده است.")
                    st.info(f"درصد تستی شما: {existing['percentage']:.1f}٪")
                    if existing['photo_data']:
                        st.image(existing['photo_data'], caption="تصویر چهره ثبت‌شده در زمان آزمون", width=180)
                else:
                    duration_min = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
                    st.info(f"⏱️ زمان پاسخگویی: {duration_min} دقیقه")
                    
                    with get_connection() as conn:
                        questions_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                        
                    questions = [dict(q) for q in questions_rows]
                    if f"shuffled_q_{q_id}_{s_id}" not in st.session_state:
                        import random
                        shuffled = list(questions)
                        random.shuffle(shuffled)
                        st.session_state[f"shuffled_q_{q_id}_{s_id}"] = shuffled
                        
                    shuffled_questions = st.session_state[f"shuffled_q_{q_id}_{s_id}"]
                    student_mcq_ans = {}
                    student_essay_ans = {}
                    
                    st.markdown("---")
                    with st.form("take_quiz_form_v28"):
                        for idx, q in enumerate(shuffled_questions):
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
                                import base64
                                photo_bytes_b64 = "data:image/png;base64," + base64.b64encode(photo.getvalue()).decode('utf-8')
                                
                            with get_connection() as conn:
                                conn.execute(
                                    "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, photo_data, essay_answers) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (q_id, s_id, correct_count, mcq_total, pct, photo_bytes_b64, essay_json_str)
                                )
                                conn.commit()
                                
                            st.balloons()
                            st.success(f"🎉 پاسخ‌ها و چهره شما با موفقیت ثبت گردید! نمره تستی: {correct_count} از {mcq_total} ({pct:.1f}٪)")

# 7. DASHBOARD
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
    students_df = load_students()
    if not students_df.empty:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده پوشه کار:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2: st.metric("موارد رفتاری ثبت‌شده:", beh_count)
        with c3: st.metric("میانگین درصد آزمون آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 کارنامه و چهره آزمون‌ها"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e.empty: st.dataframe(df_e, use_container_width=True)
            else: st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", conn, params=(s_id,))
            if not df_b.empty: st.dataframe(df_b, use_container_width=True)
            else: st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات تستی', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
            else:
                st.info("نتیجه آزمونی ثبت نشده است.")

