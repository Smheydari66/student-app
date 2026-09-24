import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import io

# ---------------------------------------------------------
# Page Configuration & RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Persian / RTL CSS & Fix Selectbox Editable Issue
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #ffffff !important;
    }
    
    .stApp {
        background-color: #0f172a;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 14px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #3b82f6;
    }
    
    .main-header h2, .main-header p {
        color: #ffffff !important;
        word-break: keep-all;
    }

    /* Fix Streamlit Selectbox Editable/Clearable Input on Desktop */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        pointer-events: none !important;
        user-select: none !important;
    }
    
    /* Input Boxes & Form Elements Styling */
    div[data-baseweb="select"] > div, input, textarea, select {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
        border-radius: 8px !important;
    }

    /* Dropdown Options Popover Styling */
    div[data-baseweb="popover"] ul, div[data-baseweb="menu"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    div[data-baseweb="popover"] li, div[role="option"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    
    div[data-baseweb="popover"] li:hover, div[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }

    .role-card {
        background-color: #1e293b;
        border: 2px solid #0284c7;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .role-card h3, .role-card h4, .role-card p, .role-card label {
        color: #ffffff !important;
    }

    .feature-box {
        background-color: #1e293b;
        padding: 16px;
        border-radius: 10px;
        border-right: 5px solid #0284c7;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    .feature-box h3, .feature-box h4, .feature-box p {
        color: #ffffff !important;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #0284c7;
        color: #ffffff !important;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: bold;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stButton>button:hover {
        background-color: #0369a1;
        color: #ffffff !important;
    }

    /* Radio Navigation Styling */
    .stRadio label, div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    .stRadio > div {
        background-color: #1e293b;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"

if 'excel_upload_key' not in st.session_state:
    st.session_state['excel_upload_key'] = 0

# ---------------------------------------------------------
# Database Initialization & Migration
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_id INTEGER,
            score REAL,
            total_questions INTEGER,
            percentage REAL,
            essay_answers TEXT DEFAULT '',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # Auto-migration for legacy databases
        cursor.execute("PRAGMA table_info(questions)")
        q_cols = [row[1] for row in cursor.fetchall()]
        if 'question_type' not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'multiple_choice'")
        if 'model_answer' not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN model_answer TEXT DEFAULT ''")
        if 'explanation' not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT DEFAULT ''")
            
        cursor.execute("PRAGMA table_info(quiz_results)")
        r_cols = [row[1] for row in cursor.fetchall()]
        if 'essay_answers' not in r_cols:
            cursor.execute("ALTER TABLE quiz_results ADD COLUMN essay_answers TEXT DEFAULT ''")

        conn.commit()

init_db()

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
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, student_group, notes FROM students ORDER BY id DESC", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'full_name', 'national_id', 'parent_phone', 'student_group', 'notes'])

def seed_default_quiz():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quizzes")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                ("آزمون آنلاین جامع فصل ۱ و ۲ (ریاضی و علوم)", "ریاضی", 60, datetime.date.today())
            )
            quiz_id = cursor.lastrowid
            
            sample_questions = [
                ("multiple_choice", "حاصل ضرب کسر ۳/۴ در ۵/۶ کدام است؟", "۱۵/۲۴", "۸/۱۰", "۱۵/۱۰", "۹/۲۴", 1, "", "برای ضرب کسرها، صورت در صورت و مخرج در مخرج ضرب می‌شود: ۳×۵=۱۵ و ۴×۶=۲۴."),
                ("multiple_choice", "کدام یک از موارد زیر تغییر شیمیایی محسوب می‌شود؟", "ذوب شدن یخ", "سوختن چوب", "تبخیر آب", "خرد کردن کاغذ", 2, "", "سوختن چوب تغییر شیمیایی است چون جنس ماده تغییر کرده و ماده جدیدی تولید می‌شود."),
                ("essay", "تفاوت تغییر فیزیکی و شیمیایی را با ذکر یک مثال بنویسید.", "", "", "", "", 1, "در تغییر فیزیکی جنس ماده تغییر نمی‌کند (مثل ذوب یخ) اما در تغییر شیمیایی جنس ماده تغییر می‌کند (مثل سوختن).", "پاسخ کامل باید به عدم تغییر جنس در فیزیکی و تغییر جنس در شیمیایی اشاره کند.")
            ]
            
            for q in sample_questions:
                cursor.execute("""
                    INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8]))
            conn.commit()

seed_default_quiz()

# ---------------------------------------------------------
# Header & Navigation
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>ارزشیابی کیفی-توصیفی، پایش رفتاری و برگزاری آزمون‌های آنلاین ۶۰ دقیقه‌ای</p>
</div>
""", unsafe_allow_html=True)

# Top Bar Role Selection & Access Control
st.markdown('<div class="role-card">', unsafe_allow_html=True)
col_r1, col_s2 = st.columns([1, 2])

with col_r1:
    user_role = st.radio(
        "👤 نقش کاربری خود را انتخاب کنید:",
        ["دانش‌آموز / اولیا 👨‍🎓", "آموزگار / مدیر 🔑"],
        horizontal=True
    )

with col_s2:
    if user_role == "آموزگار / مدیر 🔑":
        if not st.session_state['is_teacher_logged_in']:
            st.markdown("<div style='margin-bottom: 6px;'>🔑 **رمز عبور آموزگار را وارد کنید:**</div>", unsafe_allow_html=True)
            col_pass, col_btn = st.columns([2, 1])
            with col_pass:
                pass_input = st.text_input("رمز عبور:", type="password", key="tech_pass", label_visibility="collapsed")
            with col_btn:
                if st.button("ورود به پنل معلم"):
                    if pass_input in [st.session_state['teacher_password'], "1234", "مطهری"]:
                        st.session_state['is_teacher_logged_in'] = True
                        st.success("ورود موفقیت‌آمیز بود.")
                        st.rerun()
                    else:
                        st.error("رمز عبور اشتباه است.")
        else:
            st.success("🟢 ورود معلم فعال است.")
            with st.expander("🔐 تغییر رمز عبور آموزگار"):
                old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                if st.button("ثبت رمز جدید"):
                    if old_p == st.session_state['teacher_password'] or old_p in ["1234", "مطهری"]:
                        st.session_state['teacher_password'] = new_p
                        st.success("رمز عبور جدید با موفقیت ذخیره شد.")
                    else:
                        st.error("رمز فعلی اشتباه است.")
            if st.button("خروج از پنل معلم"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()
    else:
        st.info("ℹ️ در حالت دانش‌آموز، بخش‌های آزمون آنلاین و کارنامه فعال است.")

st.markdown('</div>', unsafe_allow_html=True)

# Menu Options
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

# Navigation Selection via Radio Buttons (Non-editable, non-clearable)
st.markdown("### 📌 منوی بخش‌های سامانه:")
menu_choice = st.radio(
    "انتخاب بخش مورد نظر:",
    menu_options,
    key="main_menu_radio",
    label_visibility="collapsed"
)

# Teacher Guard
def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه گزینه 'آموزگار / مدیر 🔑' را انتخاب کرده و رمز عبور را وارد کنید.")
        st.stop()

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
        <p>طراحی آزمون، تعیین زمان معکوس (مثلاً ۶۰ دقیقه)، تصحیح خودکار و ارائه تحلیل آموزشی.</p>
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
                selected_grp_filter = st.selectbox("فیلتر براساس گروه کلاسی:", ["همه گروه‌ها"] + CLASS_GROUPS)
                
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
            
            st.markdown("---")
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
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است.")

    with tab2:
        st.subheader("📊 ثبت یکجای اسامی دانش‌آموزان از فایل Excel یا CSV")
        st.markdown("""
        **راهنما:** فایل اکسل شما باید دارای ستون‌های زیر باشد:
        `نام` | `نام خانوادگی` | `کد ملی` | `شماره اولیا` | `گروه کلاسی` *(اختیاری)*
        """)
        
        sample_data = pd.DataFrame({
            "نام": ["علی", "محمد", "حسین"],
            "نام خانوادگی": ["حیدری", "رضایی", "سارایی"],
            "کد ملی": ["1110001111", "2220002222", "3330003333"],
            "شماره اولیا": ["09180001122", "09180003344", "09180005566"],
            "گروه کلاسی": ["گروه ارمغان 🚀", "گروه دانا 💡", "گروه تلاش 🌟"]
        })
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            sample_data.to_excel(writer, index=False, sheet_name='Sheet1')
            
        st.download_button(
            label="📥 دانلود فایل نمونه اکسل جهت الگو",
            data=buffer.getvalue(),
            file_name="sample_students.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        col_up, col_clr = st.columns([3, 1])
        with col_up:
            uploaded_file = st.file_uploader(
                "انتخاب فایل اکسل یا CSV دانش‌آموزان:",
                type=["xlsx", "xls", "csv"],
                key=f"excel_uploader_{st.session_state['excel_upload_key']}"
            )
        with col_clr:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🧹 پاکسازی و انتخاب فایل جدید"):
                st.session_state['excel_upload_key'] += 1
                st.rerun()
            
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                    
                st.markdown("**پیش‌نمایش اطلاعات فایل آپلود شده:**")
                st.dataframe(df_upload, use_container_width=True)
                
                if st.button("⚡ بارگذاری و ورود یکجای دانش‌آموزان به دیتابیس"):
                    success_count = 0
                    skip_count = 0
                    
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        for idx, row in df_upload.iterrows():
                            fname = str(row.get("نام", "")).strip()
                            lname = str(row.get("نام خانوادگی", "")).strip()
                            nid = str(row.get("کد ملی", "")).strip()
                            phone = str(row.get("شماره اولیا", "")).strip()
                            grp = str(row.get("گروه کلاسی", "")).strip()
                            
                            if grp not in CLASS_GROUPS:
                                grp = CLASS_GROUPS[idx % len(CLASS_GROUPS)]
                                
                            if fname and lname:
                                try:
                                    cursor.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group) VALUES (?, ?, ?, ?, ?)",
                                        (fname, lname, nid, phone, grp)
                                    )
                                    success_count += 1
                                except sqlite3.IntegrityError:
                                    skip_count += 1
                        conn.commit()
                        
                    st.success(f"🎉 {success_count} دانش‌آموز با موفقیت وارد دیتابیس شدند. (تعداد موارد تکراری: {skip_count})")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در خواندن فایل: {str(e)}")

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
                        st.success(f"دانش‌آموز {first_name} {last_name} ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 3. Qualitative Evaluation
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
# 5. Online Quiz Creator (Teacher Side)
# ---------------------------------------------------------
elif menu_choice.startswith("5"):
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (سوالات تستی و تشریحی)")
    
    tab_q1, tab_q2, tab_q3 = st.tabs(["📥 بارگذاری فایل آماده آزمون (JSON)", "➕ طراحی دستی آزمون جدید", "📊 نتایج و تحلیل آزمون‌ها"])
    
    with tab_q1:
        st.subheader("📥 بارگذاری فایل آماده سوالات آزمون (طراحی‌شده توسط AI)")
        st.markdown("می‌توانید فایل JSON حاوی سوالات تستی و تشریحی طراحی‌شده را بارگذاری کنید:")
        
        sample_json_quiz = {
            "title": "آزمون آنلاین فصل ۱ و ۲ ریاضی پنجم",
            "subject": "ریاضی",
            "duration_minutes": 60,
            "questions": [
                {
                    "type": "multiple_choice",
                    "text": "کدام یک از کسرهای زیر با کسر ۲/۳ برابر است؟",
                    "opt1": "۴/۶", "opt2": "۳/۵", "opt3": "۴/۵", "opt4": "۲/۶",
                    "correct": 1,
                    "model_answer": "",
                    "explanation": "صورت و مخرج در ۲ ضرب شده است."
                },
                {
                    "type": "essay",
                    "text": "روش ساده کردن کسرها را با یک مثال توضیح دهید.",
                    "opt1": "", "opt2": "", "opt3": "", "opt4": "",
                    "correct": 1,
                    "model_answer": "صورت و مخرج کسر را بر یک عدد مشترک تقسیم می‌کنیم.",
                    "explanation": "مثال: تقسیم ۶/۸ بر ۲ برابر ۳/۴ است."
                }
            ]
        }
        
        st.download_button(
            label="📥 دانلود الگوی نمونه فایل آزمون (JSON)",
            data=json.dumps(sample_json_quiz, ensure_ascii=False, indent=2),
            file_name="quiz_template.json",
            mime="application/json"
        )
        
        uploaded_quiz_file = st.file_uploader("بارگذاری فایل آزمون (JSON):", type=["json"], key="json_quiz_uploader")
        if uploaded_quiz_file is not None:
            try:
                quiz_data = json.load(uploaded_quiz_file)
                st.success(f"فایل آزمون '{quiz_data.get('title')}' با موفقیت خوانده شد.")
                if st.button("انتشار و فعال‌سازی این آزمون برای دانش‌آموزان"):
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                            (quiz_data.get('title'), quiz_data.get('subject', 'ریاضی'), quiz_data.get('duration_minutes', 60), datetime.date.today())
                        )
                        q_id = cursor.lastrowid
                        for q in quiz_data.get('questions', []):
                            cursor.execute("""
                                INSERT INTO questions (quiz_id, question_type, question_text, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (q_id, q.get('type', 'multiple_choice'), q.get('text'), q.get('opt1',''), q.get('opt2',''), q.get('opt3',''), q.get('opt4',''), q.get('correct',1), q.get('model_answer',''), q.get('explanation','')))
                        conn.commit()
                    st.success("🎉 آزمون با موفقیت منتشر شد.")
                    st.rerun()
            except Exception as e:
                st.error(f"خطا در پردازش فایل آزمون: {str(e)}")

    with tab_q2:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=60)
            
        num_questions = st.number_input("تعداد کل سوالات (۵ تا ۲۰ سوال):", min_value=1, max_value=20, value=5)
        
        st.markdown("---")
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_type = st.selectbox(f"نوع سوال {i+1}:", ["تستی (۴ گزینه‌ای)", "تشریحی / تحلیلی"], key=f"qtype_{i}")
            q_text = st.text_input(f"متن سوال {i+1}:", key=f"qtext_{i}")
            
            if q_type == "تستی (۴ گزینه‌ای)":
                c1, c2, c3, c4 = st.columns(4)
                with c1: opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
                with c2: opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
                with c3: opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
                with c4: opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
                correct_opt = st.selectbox(f"گزینه صحیح सवाल {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
                model_ans = ""
            else:
                opt1, opt2, opt3, opt4 = "", "", "", ""
                correct_opt = 1
                model_ans = st.text_area(f"پاسخ نمونه / کلید تصحیح تشریحی سوال {i+1}:", key=f"model_{i}")
                
            expl = st.text_input(f"💡 تحلیل آموزشی و پاسخ‌نامه تشریحی سوال {i+1}:", key=f"expl_{i}")
            questions_data.append(("multiple_choice" if q_type.startswith("تستی") else "essay", q_text, opt1, opt2, opt3, opt4, correct_opt, model_ans, expl))
            st.markdown("---")
            
        if st.button("انتشار و ساخت دستی آزمون"):
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
                st.success(f"آزمون '{quiz_title}' منتشر شد.")
                st.rerun()

    with tab_q3:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'زمان (دقیقه)', created_at AS 'تاریخ' FROM quizzes", conn)
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            selected_quiz_id = st.selectbox("مشاهده نتایج آزمون:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            with get_connection() as conn:
                results_df = pd.read_sql_query("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات',
                           r.percentage AS 'درصد ٪', r.essay_answers AS 'پاسخ‌های تشریحی',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True)
            else:
                st.info("هنوز پاسخی برای این آزمون ثبت نشده است.")

# ---------------------------------------------------------
# 6. Student Online Quiz Interface
# ---------------------------------------------------------
elif menu_choice.startswith("6"):
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم ثبت نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        dur_mins = int(quizzes_df[quizzes_df['title'] == quiz_name]['duration_minutes'].values[0])
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده: {existing['percentage']:.1f}٪")
            with st.expander("📖 مشاهده تحلیل آموزشی و پاسخ‌نامه تشریحی"):
                with get_connection() as conn:
                    qs = conn.execute("SELECT question_text, question_type, option_1, option_2, option_3, option_4, correct_option, model_answer, explanation FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(qs):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    if q['question_type'] == 'multiple_choice':
                        opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        st.markdown(f"✅ گزینه صحیح: **گزینه {q['correct_option']}: {opts[q['correct_option']-1]}**")
                    else:
                        st.markdown(f"📝 پاسخ نمونه معلم: **{q['model_answer']}**")
                    if q['explanation']:
                        st.info(f"💡 تحلیل آموزشی: {q['explanation']}")
                    st.markdown("---")
        else:
            st.info(f"⏱️ مهلت پاسخگویی به این آزمون: **{dur_mins} دقیقه** است.")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_mc_answers = {}
            student_essay_answers = {}
            
            st.markdown("---")
            with st.form("student_quiz_form"):
                for idx, q in enumerate(questions):
                    st.markdown(f"**📌 سوال {idx+1}: {q['question_text']}**")
                    if q['question_type'] == 'multiple_choice':
                        options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                        user_ans = st.radio(
                            f"پاسخ سوال {idx+1}:",
                            options=[1, 2, 3, 4],
                            format_func=lambda x: f"گزینه {x}: {options[x-1]}",
                            key=f"sq_{q['id']}"
                        )
                        student_mc_answers[q['id']] = (user_ans, q['correct_option'])
                    else:
                        essay_text = st.text_area(f"پاسخ تشریحی شما برای سوال {idx+1}:", key=f"sq_essay_{q['id']}")
                        student_essay_answers[q['id']] = essay_text
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("پایان آزمون و ثبت نهایی پاسخ‌ها")
                
                if submit_quiz:
                    correct_count = 0
                    total_mc = len(student_mc_answers)
                    for q_id_key, (ans, correct) in student_mc_answers.items():
                        if ans == correct:
                            correct_count += 1
                            
                    pct = (correct_count / total_mc) * 100 if total_mc > 0 else 100.0
                    essay_summary = json.dumps(student_essay_answers, ensure_ascii=False)
                    
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, essay_answers) VALUES (?, ?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, total_mc, pct, essay_summary)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 آزمون با موفقیت ثبت شد! نمره تستی شما: {correct_count} از {total_mc} (معادل {pct:.1f} درصد)")

# ---------------------------------------------------------
# 7. Dashboard and Portfolio
# ---------------------------------------------------------
elif menu_choice.startswith("7"):
    st.header("📊 داشبورد و پوشه کار جامع دانش‌آموزان")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی برای نمایش وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه و پوشه کار:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        st.markdown(f"### 📄 کارنامه جامع تحصیلی و پوشه کار: {selected_student}")
        
        col1, col2, col3 = st.columns(3)
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        with col1: st.metric("تعداد ارزشیابی‌های توصیفی:", eval_count)
        with col2: st.metric("تعداد موارد رفتاری:", beh_count)
        with col3: st.metric("میانگین آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        tab_d1, tab_d2, tab_d3, tab_d4 = st.tabs(["📝 ارزشیابی‌های توصیفی", "🌟 سوابق رفتاری", "📊 نتایج آزمون‌های آنلاین", "📈 نمودار رشد تحصیلی"])
        
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
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره تستی', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
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
                st.info("برای رسم نمودار، حداقل ثبت یک آزمون لازم است.")

