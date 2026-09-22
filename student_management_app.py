import streamlit as st
import sqlite3
import pandas as pd
import datetime

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'is_teacher' not in st.session_state:
    st.session_state['is_teacher'] = False

# ---------------------------------------------------------
# Universal High Contrast & Professional RTL Styling (CSS)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Universal Font and Direction */
    html, body, [class*="css"], div, span, button, input, select, textarea, p, h1, h2, h3, h4, h5, h6, label {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Overall Background */
    .stApp {
        background-color: #f8fafc !important;
    }
    
    /* Force High Contrast Text Color on All Standard Elements */
    p, span, label, div, .stMarkdown, .stText, .stSelectbox label, .stTextInput label, .stTextArea label, .stRadio label {
        color: #0f172a !important;
        font-weight: 500;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #0369a1 !important;
        font-weight: 800 !important;
    }

    /* Main Header Banner */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3c72 50%, #0369a1 100%);
        color: #ffffff !important;
        padding: 24px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        border: 2px solid #0284c7;
    }
    
    .main-header h2 {
        color: #ffffff !important;
        margin-bottom: 8px;
        font-size: 1.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    
    .main-header p {
        color: #e0f2fe !important;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Elegant Card Containers */
    .custom-card {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        margin-bottom: 20px;
        border-right: 6px solid #0284c7;
        border-left: 1px solid #e2e8f0;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }

    .author-card {
        background-color: #f0f9ff !important;
        border: 2px dashed #0284c7 !important;
        border-radius: 14px;
        padding: 18px;
        text-align: center !important;
        margin-bottom: 20px;
    }
    
    .author-card h3 {
        color: #0369a1 !important;
        margin: 0 0 6px 0;
    }

    .author-card p {
        color: #0f172a !important;
        font-size: 1.1rem;
        font-weight: bold;
        margin: 0;
    }

    /* Login Container Style */
    .login-box {
        background-color: #ffffff !important;
        border: 2px solid #0284c7 !important;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.15);
        margin-bottom: 25px;
    }

    /* Form Inputs and Selectboxes */
    .stTextInput input, .stSelectbox select, .stTextArea textarea, .stNumberInput input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }

    /* Custom Primary Buttons */
    .stButton>button {
        width: 100%;
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(2, 132, 199, 0.25);
        transition: all 0.2s ease-in-out;
    }
    
    .stButton>button:hover {
        background-color: #0369a1 !important;
        transform: translateY(-2px);
    }

    /* Alert / Info Boxes High Contrast */
    .stAlert {
        border-radius: 10px !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

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
        
        # Students Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT UNIQUE,
            parent_phone TEXT,
            student_group TEXT DEFAULT 'عمومی 📚',
            avatar TEXT DEFAULT '👨‍🎓',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Qualitative Evaluations Table
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
        
        # Behaviors Table
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
        
        # Quizzes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 15,
            created_at DATE
        )
        """)
        
        # Questions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_text TEXT NOT NULL,
            option_1 TEXT NOT NULL,
            option_2 TEXT NOT NULL,
            option_3 TEXT NOT NULL,
            option_4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL,
            explanation TEXT DEFAULT '',
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
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
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
        """)
        
        # Auto-migration checks
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN student_group TEXT DEFAULT 'عمومی 📚'")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN avatar TEXT DEFAULT '👨‍🎓'")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        conn.commit()

init_db()

# ---------------------------------------------------------
# Helper Constants & Functions
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

STUDENT_GROUPS = [
    "گروه نخبگان 🏆",
    "گروه تلاش 🌟",
    "گروه دانا 💡",
    "گروه ارمغان 🚀",
    "عمومی 📚"
]

def load_students():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT id, first_name || ' ' || last_name AS full_name, first_name, last_name, 
                       national_id, parent_phone, student_group, avatar, notes 
                FROM students ORDER BY last_name ASC
            """, conn)
        return df
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>دبستان شهید مطهری مهران - ارزشیابی کیفی-توصیفی، پایش رفتاری و برگزاری آزمون‌های آنلاین</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Teacher Login Bar & Status ( مرتب‌سازی کامل رمز ورود )
# ---------------------------------------------------------
with st.expander("🔑 **پنل مدیریت دسترسی آموزگار (ورود / خروج با رمز عبور)**", expanded=not st.session_state['is_teacher']):
    col_login1, col_login2 = st.columns([2, 1])
    
    with col_login1:
        if st.session_state['is_teacher']:
            st.success("🟢 **شما به عنوان آموزگار وارد شده‌اید.** (دسترسی کامل به ویرایش و طراحی فعال است)")
        else:
            st.info("👤 **حالت عمومی (دانش‌آموز / اولیا):** جهت دسترسی به منوهای مدیریتی آموزگار، رمز ورود را وارد نمایید.")
            
    with col_login2:
        if not st.session_state['is_teacher']:
            pass_input = st.text_input("رمز عبور آموزگار:", type="password", key="teacher_pwd", placeholder="رمز عبور را وارد کنید")
            if st.button("ورود به سامانه 🔓"):
                if pass_input.strip() in ["1234", "مطهری", "حیدری"]:
                    st.session_state['is_teacher'] = True
                    st.success("ورود با موفقیت انجام شد!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور نادرست است.")
        else:
            if st.button("خروج از حساب آموزگار 🔒"):
                st.session_state['is_teacher'] = False
                st.info("از حساب آموزگار خارج شدید.")
                st.rerun()

# ---------------------------------------------------------
# Top Collapsible Navigation Menu ( کشویی )
# ---------------------------------------------------------
st.markdown("### 📌 منوی اصلی سامانه (انتخاب بخش مورد نظر)")

menu_options = [
    "🏠 صفحه اصلی و معرفی برنامه",
    "👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویژه معلم)",
    "📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)",
    "🌟 ثبت رفتار و انضباط (ویژه معلم)",
    "✏️ آزمون‌ساز آنلاین (ویژه معلم)",
    "📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)",
    "📊 داشبورد و کارنامه جامع (عمومی / اولیا)"
]

selected_menu = st.selectbox(
    "جهت جابه‌جایی بین بخش‌های مختلف کلیک کنید:",
    options=menu_options,
    index=0
)

st.markdown("---")

# ---------------------------------------------------------
# Teacher Check Security Guard
# ---------------------------------------------------------
def check_teacher():
    if not st.session_state['is_teacher']:
        st.warning("🔒 **این بخش مخصوص آموزگار است.** لطفاً از کادر بالا روی 'پنل مدیریت دسترسی آموزگار' کلیک کرده و رمز عبور را وارد نمایید.")
        st.stop()

# =========================================================
# SECTION 0: Landing Page & App Info
# =========================================================
if selected_menu == "🏠 صفحه اصلی و معرفی برنامه":
    st.markdown("""
    <div class="author-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه</h3>
        <p>سید موسی حیدری — آموزگار کلاس پنجم ابتدایی دبستان شهید مطهری مهران</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 اهداف و ویژگی‌های برجسته سامانه:")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown("""
        <div class="custom-card">
            <h4 style="color: #0369a1;">1️⃣ ارزشیابی کیفی-توصیفی دقیق</h4>
            <p>ثبت و دسته‌بندی سطح عملکرد دانش‌آموزان در تمامی ۷ عنوان درسی پایه پنجم به همراه بازخوردهای توصیفی سازنده.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h4 style="color: #0369a1;">2️⃣ آزمون‌ساز آنلاین با تصحیح خودکار</h4>
            <p>طراحی آزمون‌های ۴ گزینه‌ای، تصحیح آنی، محاسبه درصد نمره و ارائه پاسخ‌نامه تشریحی بدون نیاز به تصحیح دستی.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_f2:
        st.markdown("""
        <div class="custom-card">
            <h4 style="color: #0369a1;">3️⃣ گروه‌بندی کلاسی و پایش رفتاری</h4>
            <p>دسته‌بندی دانش‌آموزان در گروه‌های آموزشی و ثبت مشاهدات انضباطی جهت ارتقای روحیه همکاری و تعامل با اولیا.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h4 style="color: #0369a1;">4️⃣ کارنامه جامع و نمودار رشد</h4>
            <p>مشاهده گزارش کامل تحصیلی، نشان‌های افتخار دیجیتال و نمودار خطی پیشرفت آزمون‌ها برای هر دانش‌آموز.</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# SECTION 1: Student Management & Grouping (Teacher)
# =========================================================
elif selected_menu == "👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (ویژه معلم)":
    check_teacher()
    st.header("👨‍🎓 مدیریت پرونده دانش‌آموزان و گروه‌بندی کلاسی")
    
    tab_s1, tab_s2 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "➕ ثبت دانش‌آموز جدید"])
    
    with tab_s1:
        df_students = load_students()
        if not df_students.empty:
            search_q = st.text_input("🔍 جستجوی زنده دانش‌آموز (بر اساس نام یا کد ملی):")
            if search_q:
                df_students = df_students[
                    df_students['full_name'].str.contains(search_q) | 
                    df_students['national_id'].astype(str).str.contains(search_q)
                ]
                
            st.dataframe(
                df_students[['avatar', 'full_name', 'national_id', 'parent_phone', 'student_group', 'notes']].rename(columns={
                    'avatar': 'نماد',
                    'full_name': 'نام و نام خانوادگی',
                    'national_id': 'کد ملی',
                    'parent_phone': 'شماره همراه اولیا',
                    'student_group': 'گروه کلاسی',
                    'notes': 'توضیحات'
                }),
                use_container_width=True
            )
            
            st.markdown("---")
            st.subheader("🗑️ حذف یا ویرایش پرونده دانش‌آموز")
            del_student_name = st.selectbox("انتخاب دانش‌آموز جهت حذف:", df_students['full_name'].tolist())
            if st.button("حذف کامل پرونده دانش‌آموز ❌"):
                s_id = int(df_students[df_students['full_name'] == del_student_name]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {del_student_name} با موفقیت حذف شد.")
                st.rerun()
        else:
            st.info("هنوز دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دانش‌آموز جدید' استفاده کنید.")

    with tab_s2:
        with st.form("add_student_form_v9"):
            c1, c2 = st.columns(2)
            with c1:
                f_name = st.text_input("نام دانش‌آموز:")
                nat_id = st.text_input("کد ملی (۱۰ رقم):")
                st_group = st.selectbox("گروه کلاسی:", STUDENT_GROUPS)
            with c2:
                l_name = st.text_input("نام خانوادگی:")
                phone_no = st.text_input("شماره همراه اولیا:")
                st_avatar = st.selectbox("انتخاب آیکون/نماد:", ["👨‍🎓", "👦", "👧", "🚀", "🌟", "🏆"])
                
            st_notes = st.text_area("توضیحات یا ملاحظات ویژه آموزگار:")
            
            submit_student = st.form_submit_button("ثبت پرونده دانش‌آموز")
            
            if submit_student:
                if f_name and l_name:
                    try:
                        with get_connection() as conn:
                            conn.execute("""
                                INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, avatar, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (f_name.strip(), l_name.strip(), nat_id.strip(), phone_no.strip(), st_group, st_avatar, st_notes))
                            conn.commit()
                        st.success(f"دانش‌آموز {f_name} {l_name} با موفقیت ثبت شد!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# =========================================================
# SECTION 2: Qualitative Evaluation (Teacher)
# =========================================================
elif selected_menu == "📝 ثبت ارزشیابی کیفی-توصیفی (ویژه معلم)":
    check_teacher()
    st.header("📝 ثبت ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    df_students = load_students()
    if df_students.empty:
        st.warning("لطفاً ابتدا دانش‌آموزان را در سیستم ثبت کنید.")
    else:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            sel_student = st.selectbox("انتخاب دانش‌آموز:", df_students['full_name'].tolist())
            sel_subject = st.selectbox("انتخاب درس:", FIFTH_GRADE_SUBJECTS)
        with col_e2:
            sel_level = st.selectbox("سطح عملکرد توصیفی:", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area("بازخورد توصیفی و راهکارهای بهبود (توصیف عملکرد):", 
                                     placeholder="مثلاً: در محاسبات کسرها عملکردی عالی دارد، اما نیاز به تمرین بیشتر در ضرب اعشاری دارد.")
        
        if st.button("ثبت ارزشیابی توصیفی ✅"):
            s_id = int(df_students[df_students['full_name'] == sel_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO evaluations (student_id, subject, level, feedback, eval_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (s_id, sel_subject, sel_level, feedback_text, eval_date))
                conn.commit()
            st.success(f"ارزشیابی {sel_subject} برای {sel_student} با موفقیت ثبت شد.")

        st.markdown("---")
        st.subheader(f"🔍 سوابق ارزشیابی توصیفی: {sel_student}")
        s_id = int(df_students[df_students['full_name'] == sel_student]['id'].values[0])
        with get_connection() as conn:
            df_eval_hist = pd.read_sql_query("""
                SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد آموزگار', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, conn, params=(s_id,))
            
        if not df_eval_hist.empty:
            st.dataframe(df_eval_hist, use_container_width=True)
        else:
            st.info("هنوز سابقه ارزشیابی برای این دانش‌آموز ثبت نشده است.")

# =========================================================
# SECTION 3: Behavioral Tracking (Teacher)
# =========================================================
elif selected_menu == "🌟 ثبت رفتار و انضباط (ویژه معلم)":
    check_teacher()
    st.header("🌟 مدیریت مشاهدات رفتاری و انضباطی")
    
    df_students = load_students()
    if df_students.empty:
        st.warning("لطفاً ابتدا دانش‌آموزان را در سیستم ثبت کنید.")
    else:
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            sel_student_b = st.selectbox("انتخاب دانش‌آموز:", df_students['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with c_b2:
            b_title = st.text_input("عنوان مشاهده (مثلاً: همکاری گروهی، انجام به‌موقع تکالیف، تاخیر ورود):")
            b_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        b_desc = st.text_area("شرح جزییات و اقدام انجام‌شده:")
        
        if st.button("ثبت مورد رفتاری ✅"):
            s_id = int(df_students[df_students['full_name'] == sel_student_b]['id'].values[0])
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO behaviors (student_id, behavior_type, title, description, log_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (s_id, b_type, b_title, b_desc, b_date))
                conn.commit()
            st.success(f"مشاهده رفتاری برای {sel_student_b} ثبت شد.")

        st.markdown("---")
        st.subheader(f"📋 سوابق رفتاری: {sel_student_b}")
        s_id = int(df_students[df_students['full_name'] == sel_student_b]['id'].values[0])
        with get_connection() as conn:
            df_b_hist = pd.read_sql_query("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
            """, conn, params=(s_id,))
            
        if not df_b_hist.empty:
            st.dataframe(df_b_hist, use_container_width=True)
        else:
            st.info("هیچ مورد رفتاری ثبت نشده است.")

# =========================================================
# SECTION 4: Quiz Builder (Teacher)
# =========================================================
elif selected_menu == "✏️ آزمون‌ساز آنلاین (ویژه معلم)":
    check_teacher()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی سوالات و مشاهده نتایج)")
    
    t_q1, t_q2 = st.tabs(["➕ ساخت آزمون جدید و طراحی سوالات", "📊 نتایج و کارنامه آزمون‌ها"])
    
    with t_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            q_title = st.text_input("عنوان آزمون (مثلاً: آزمونک کسرها و اعداد اعشاری):")
        with col_q2:
            q_subj = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col_q3:
            q_duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
            
        n_questions = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=20, value=2)
        
        st.markdown("---")
        st.subheader("۲. طراحی سوالات، گزینه‌ها و پاسخ‌نامه تشریحی")
        
        q_list_data = []
        for i in range(int(n_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_txt = st.text_input(f"متن سوال {i+1}:", key=f"q_txt_{i}")
            
            c_opt1, c_opt2, c_opt3, c_opt4 = st.columns(4)
            with c_opt1:
                o1 = st.text_input(f"گزینه ۱:", key=f"o1_{i}")
            with c_opt2:
                o2 = st.text_input(f"گزینه ۲:", key=f"o2_{i}")
            with c_opt3:
                o3 = st.text_input(f"گزینه ۳:", key=f"o3_{i}")
            with c_opt4:
                o4 = st.text_input(f"گزینه ۴:", key=f"o4_{i}")
                
            corr_o = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
            q_expl = st.text_input(f"پاسخ‌نامه تشریحی / نکته آموزشی سوال {i+1}:", key=f"expl_{i}", placeholder="توضیح کوتاه دلیل صحّت این گزینه...")
            
            q_list_data.append((q_txt, o1, o2, o3, o4, corr_o, q_expl))
            st.markdown("---")
            
        if st.button("انتشار آزمون در سامانه 🚀"):
            if q_title and all(q[0] for q in q_list_data):
                with get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO quizzes (title, subject, duration_minutes, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (q_title, q_subj, q_duration, datetime.date.today()))
                    quiz_id = cur.lastrowid
                    
                    for q in q_list_data:
                        cur.execute("""
                            INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6]))
                    conn.commit()
                st.success(f"آزمون '{q_title}' با موفقیت ساخته شد و برای دانش‌آموزان فعال گردید!")
            else:
                st.error("لطفاً عنوان آزمون و متن تمام سوالات را تکمیل کنید.")

    with t_q2:
        with get_connection() as conn:
            df_quizzes = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
            
        if not df_quizzes.empty:
            st.dataframe(df_quizzes, use_container_width=True)
            
            st.subheader("📈 جدول نتایج دانش‌آموزان در آزمون")
            sel_q_id = st.selectbox("انتخاب آزمون جهت مشاهده نتایج:", df_quizzes['id'].tolist(), format_func=lambda x: df_quizzes[df_quizzes['id'] == x]['عنوان'].values[0])
            
            with get_connection() as conn:
                df_res = pd.read_sql_query("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'پاسخ صحیح',
                           r.total_questions AS 'کل سوالات',
                           r.percentage AS 'درصد ٪',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(sel_q_id,))
                
            if not df_res.empty:
                st.dataframe(df_res, use_container_width=True)
            else:
                st.info("هنوز دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز هیچ آزمونی طراحی نشده است.")

# =========================================================
# SECTION 5: Student Online Quiz Interface (Public)
# =========================================================
elif selected_menu == "📱 شرکت در آزمون آنلاین (عمومی / دانش‌آموز)":
    st.header("📱 شرکت در آزمون آنلاین دانش‌آموزان")
    
    df_students = load_students()
    with get_connection() as conn:
        df_quizzes = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
        
    if df_students.empty or df_quizzes.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم ثبت نشده است.")
    else:
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", df_students['full_name'].tolist())
        with col_st2:
            qz_name = st.selectbox("انتخاب عنوان آزمون:", df_quizzes['title'].tolist())
            
        s_id = int(df_students[df_students['full_name'] == st_name]['id'].values[0])
        q_id = int(df_quizzes[df_quizzes['title'] == qz_name]['id'].values[0])
        
        with get_connection() as conn:
            existing_res = conn.execute("SELECT id, percentage, score, total_questions FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing_res:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید. نمره کسب‌شده: {existing_res['score']} از {existing_res['total_questions']} (درصد: {existing_res['percentage']:.1f}٪)")
            
            # Display Explanations / Answer Key
            with st.expander("📖 مشاهده پاسخ‌نامه تشریحی و راهنمای سوالات"):
                with get_connection() as conn:
                    q_list = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q_item in enumerate(q_list):
                    st.markdown(f"**سوال {idx+1}: {q_item['question_text']}**")
                    st.write(f"✅ گزینه صحیح: گزینه {q_item['correct_option']}")
                    if q_item['explanation']:
                        st.info(f"💡 نکته آموزشی: {q_item['explanation']}")
                    st.markdown("---")
        else:
            duration_val = int(df_quizzes[df_quizzes['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ **زمان پیشنهادی آزمون:** {duration_val} دقیقه")
            
            with get_connection() as conn:
                questions_list = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_ans_dict = {}
            st.markdown("---")
            with st.form("quiz_student_form_v9"):
                for idx, q in enumerate(questions_list):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    
                    ans = st.radio(
                        f"انتخاب پاسخ سوال {idx+1}:",
                        options=[1, 2, 3, 4],
                        format_func=lambda x: f"گزینه {x}: {opts[x-1]}",
                        key=f"q_radio_{q['id']}"
                    )
                    student_ans_dict[q['id']] = (ans, q['correct_option'])
                    st.markdown("---")
                    
                submit_q_btn = st.form_submit_button("پایان آزمون و مشاهده نتیجه آنی 🏁")
                
                if submit_q_btn:
                    correct_cnt = 0
                    total_cnt = len(questions_list)
                    for qk, (u_ans, c_ans) in student_ans_dict.items():
                        if u_ans == c_ans:
                            correct_cnt += 1
                            
                    pct = (correct_cnt / total_cnt) * 100 if total_cnt > 0 else 0
                    
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage)
                            VALUES (?, ?, ?, ?, ?)
                        """, (q_id, s_id, correct_cnt, total_cnt, pct))
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 آزمون با موفقیت به پایان رسید! نمره شما: {correct_cnt} از {total_cnt} (معادل {pct:.1f} درصد)")
                    st.rerun()

# =========================================================
# SECTION 6: Dashboard & Student Report Card (Public)
# =========================================================
elif selected_menu == "📊 داشبورد و کارنامه جامع (عمومی / اولیا)":
    st.header("📊 داشبورد تحلیلی و کارنامه جامع دانش‌آموز")
    
    df_students = load_students()
    if df_students.empty:
        st.warning("اطلاعاتی برای نمایش کارنامه وجود ندارد.")
    else:
        sel_rep_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه جامع:", df_students['full_name'].tolist())
        s_row = df_students[df_students['full_name'] == sel_rep_student].iloc[0]
        s_id = int(s_row['id'])
        
        st.markdown(f"### 📄 کارنامه جامع تحصیلی و توصیفی: {s_row['avatar']} {sel_rep_student}")
        st.write(f"**گروه کلاسی:** {s_row['student_group']} | **کد ملی:** {s_row['national_id']}")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with get_connection() as conn:
            eval_cnt = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_cnt = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg_val = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        with col_m1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_cnt)
        with col_m2:
            st.metric("تعداد ثبت‌های رفتاری:", beh_cnt)
        with col_m3:
            st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg_val:.1f}٪" if quiz_avg_val else "بدون آزمون")
            
        # Digital Badges Gamification
        st.markdown("#### 🏆 مدال‌ها و نشان‌های افتخار دیجیتال دانش‌آموز:")
        badge_cols = st.columns(4)
        with badge_cols[0]:
            if quiz_avg_val and quiz_avg_val >= 90:
                st.success("🏆 **مدال نخبگان** (درصد بالای ۹۰)")
            else:
                st.caption("🔒 مدال نخبگان (نیاز به میانگین بالای ۹۰)")
        with badge_cols[1]:
            if quiz_avg_val and quiz_avg_val >= 75:
                st.info("🌟 **نشان تلاش ممتاز** (درصد بالای ۷۵)")
            else:
                st.caption("🔒 نشان تلاش ممتاز")
        with badge_cols[2]:
            if beh_cnt >= 2:
                st.success("🏆 **الگوی انضباط** (ثبت مثبت)")
            else:
                st.caption("🔒 الگوی انضباط")
        with badge_cols[3]:
            st.info(f"🚀 **عضو {s_row['student_group']}**")
            
        st.markdown("---")
        
        tab_r1, tab_r2, tab_r3, tab_r4 = st.tabs(["📝 ارزشیابی‌های درسی", "🌟 سوابق رفتاری", "📊 نمرات آزمون‌ها", "📈 نمودار رشد تحصیلی"])
        
        with tab_r1:
            with get_connection() as conn:
                df_e_rep = pd.read_sql_query("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e_rep.empty:
                st.dataframe(df_e_rep, use_container_width=True)
                csv_data_e = df_e_rep.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 دانلود فایل کارنامه توصیفی (CSV)", csv_data_e, f"evaluations_{s_id}.csv", "text/csv")
            else:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_r2:
            with get_connection() as conn:
                df_b_rep = pd.read_sql_query("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", conn, params=(s_id,))
            if not df_b_rep.empty:
                st.dataframe(df_b_rep, use_container_width=True)
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_r3:
            with get_connection() as conn:
                df_q_rep = pd.read_sql_query("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q_rep.empty:
                st.dataframe(df_q_rep, use_container_width=True)
            else:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")

        with tab_r4:
            with get_connection() as conn:
                df_chart_rep = pd.read_sql_query("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد ٪'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
            if not df_chart_rep.empty:
                st.line_chart(df_chart_rep.set_index('آزمون'))
            else:
                st.info("جهت رسم نمودار رشد، شرکت در حداقل یک آزمون لازم است.")

