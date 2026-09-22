import streamlit as st
import sqlite3
import pandas as pd
import datetime

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم ابتدایی",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast, Persian RTL CSS Styling
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, p, label, input, select, textarea, button {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Main Header Styling */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: #ffffff !important;
        padding: 22px 18px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(30, 60, 114, 0.25);
        word-break: keep-all !important;
        overflow-wrap: break-word !important;
    }
    .main-header h2 {
        color: #ffffff !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        line-height: 1.6 !important;
        margin: 0 0 8px 0 !important;
    }
    .main-header p {
        color: #e2e8f0 !important;
        font-size: 0.92rem !important;
        line-height: 1.5 !important;
        margin: 0 !important;
    }

    /* Author Card Styling (Fixed Invisible Text Issue) */
    .author-card {
        background-color: #ffffff !important;
        border: 2px solid #2a5298 !important;
        border-radius: 14px !important;
        padding: 20px !important;
        text-align: center !important;
        margin: 15px 0 25px 0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
    }
    .author-card h3 {
        color: #1e3c72 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin: 0 0 6px 0 !important;
    }
    .author-card h4 {
        color: #2a5298 !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        margin: 0 0 6px 0 !important;
    }
    .author-card p {
        color: #1e293b !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }

    /* Feature Box Styling (Fixed Invisible Text Issue) */
    .feature-box {
        background-color: #ffffff !important;
        padding: 18px 20px !important;
        border-radius: 12px !important;
        border-right: 6px solid #2a5298 !important;
        margin-bottom: 14px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    .feature-box h4 {
        color: #0f172a !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        margin: 0 0 6px 0 !important;
    }
    .feature-box p {
        color: #334155 !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }

    /* Top Navigation Dropdown Styling */
    .nav-container {
        background-color: #ffffff !important;
        padding: 15px 20px !important;
        border-radius: 14px !important;
        border: 1px solid #cbd5e1 !important;
        margin-bottom: 25px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        background-color: #2a5298 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(42, 82, 152, 0.2) !important;
    }
    .stButton>button:hover {
        background-color: #1e3c72 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Resilience
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
        conn.commit()

# Always initialize DB on startup
init_db()

# Safe Database Fetch Helpers with Auto-Healing
def load_students():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT id, avatar, first_name || ' ' || last_name AS full_name, first_name, last_name, national_id, parent_phone, notes FROM students ORDER BY last_name ASC", conn)
            return df
    except Exception:
        init_db()
        return pd.DataFrame(columns=['id', 'avatar', 'full_name', 'first_name', 'last_name', 'national_id', 'parent_phone', 'notes'])

# ---------------------------------------------------------
# Helper Constants
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

MENU_OPTIONS = [
    "🏠 صفحه اصلی و معرفی برنامه",
    "👨‍🎓 پرونده و ثبت‌نام دانش‌آموزان",
    "📝 ارزشیابی کیفی-توصیفی",
    "🌟 ثبت رفتار و انضباط",
    "✏️ آزمون‌ساز آنلاین (معلم)",
    "📱 شرکت در آزمون (دانش‌آموز)",
    "📊 داشبورد و کارنامه جامع"
]

# ---------------------------------------------------------
# App Header
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>ابزار جامع آموزگار جهت ارزشیابی کیفی-توصیفی، مدیریت انضباطی و برگزاری آزمون‌های آنلاین</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Top Navigation Menu Bar
# ---------------------------------------------------------
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
menu_choice = st.selectbox(
    "📌 انتخاب بخش مورد نظر سامانه:",
    MENU_OPTIONS,
    index=0
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 0. Landing Page / About
# ---------------------------------------------------------
if menu_choice == "🏠 صفحه اصلی و معرفی برنامه":
    st.subheader("👋 به سامانه هوشمند مدیریت کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="author-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه</h3>
        <h4>سید موسی حیدری</h4>
        <p>آموزگار کلاس پنجم ابتدایی دبستان شهید مطهری مهران</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 اهداف و امکانات کلیدی برنامه:")
    
    st.markdown("""
    <div class="feature-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی پیشرفته</h4>
        <p>ثبت و دسته‌بندی سطح عملکرد دانش‌آموزان در تمامی ۷ عنوان درسی پایه پنجم (ریاضی، علوم، فارسی، نگارش، مطالعات، هدیه‌ها و قرآن) همراه با بازخوردهای توصیفی دقیق.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ آزمون‌ساز هوشمند و تصحیح آنلاین</h4>
        <p>طراحی آزمون‌های ۴ گزینه‌ای آنلاین با زمان‌بندی مشخص، تصحیح آنی پاسخ‌ها و محاسبه نمره و درصد عملکرد دانش‌آموزان بدون نیاز به تصحیح دستی.</p>
    </div>
    
    <div class="feature-box">
        <h4>3️⃣ پایش رفتاری و انضباطی کلاس</h4>
        <p>ثبت و پیگیری مشاهدات رفتاری، تشویق‌ها و موارد انضباطی جهت ارتقای تعامل با اولیا و رشد اجتماعی دانش‌آموزان.</p>
    </div>
    
    <div class="feature-box">
        <h4>4️⃣ کارنامه جامع و تحلیل عملکرد</h4>
        <p>ارائه داشبورد تحلیلی یکپارچه برای هر دانش‌آموز شامل سوابق درسی، رفتاری و نمرات آزمون‌های آنلاین جهت ارائه به اولیا و مدیر مدرسه.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 جهت شروع کار، منوی بالای صفحه را باز کرده و بخش مورد نظر خود را انتخاب نمایید.")

# ---------------------------------------------------------
# 1. Student Profile Management
# ---------------------------------------------------------
elif menu_choice == "👨‍🎓 پرونده و ثبت‌نام دانش‌آموزان":
    st.header("👨‍🎓 مدیریت پرونده و ثبت‌نام دانش‌آموزان")
    
    tab1, tab2 = st.tabs(["📋 لیست و جستجوی دانش‌آموزان", "➕ فرم ثبت‌نام دانش‌آموز جدید"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (بر اساس نام یا کد ملی):", "")
            
            filtered_df = students_df
            if search_query:
                filtered_df = students_df[
                    students_df['full_name'].str.contains(search_query, na=False) |
                    students_df['national_id'].str.contains(search_query, na=False)
                ]
            
            st.dataframe(filtered_df[['avatar', 'full_name', 'national_id', 'parent_phone', 'notes']].rename(columns={
                'avatar': 'نماد',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره همراه اولیا',
                'notes': 'توضیحات'
            }), use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ حذف پرونده دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف کامل از سامانه:", students_df['full_name'].tolist(), key="del_student")
            if st.button("حذف پرونده دانش‌آموز"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده دانش‌آموز {student_to_delete} با موفقیت حذف شد.")
                st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی در سامانه ثبت نشده است. از زبانه 'فرم ثبت‌نام دانش‌آموز جدید' استفاده کنید.")

    with tab2:
        st.subheader("📝 مشخصات فردی دانش‌آموز")
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:")
                national_id = st.text_input("کد ملی دانش‌آموز (۱۰ رقم):")
                avatar = st.selectbox("آیکون اختصاصی دانش‌آموز:", ["👨‍🎓", "👦", "👧", "🚀", "🌟", "⭐", "🎓"])
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا (جهت اطلاع‌رسانی):")
            
            notes = st.text_area("توضیحات ویژه یا ملاحظات آموزشی/پزشکی:")
            
            submit_btn = st.form_submit_button("ثبت نهایی پرونده دانش‌آموز")
            
            if submit_btn:
                if first_name and last_name:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, avatar, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                (first_name, last_name, national_id, parent_phone, avatar, notes)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} با موفقیت در کلاس ثبت گردید.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 2. Qualitative Evaluation (7 Subjects)
# ---------------------------------------------------------
elif menu_choice == "📝 ارزشیابی کیفی-توصیفی":
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
            
        feedback_text = st.text_area("بازخورد توصیفی و راهکارهای بهبود (توصیف عملکرد):", 
                                     placeholder="مثلاً: در محاسبه کسرها مهارتی عالی دارد، اما نیاز به تمرین بیشتر در ضرب اعداد اعشاری دارد.")
        
        if st.button("ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success(f"ارزشیابی {selected_subject} برای {selected_student} با موفقیت ثبت شد.")

        st.markdown("---")
        st.subheader(f"🔍 سوابق ارزشیابی دانش‌آموز: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        try:
            with get_connection() as conn:
                eval_history = pd.read_sql_query("""
                    SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                    FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
                """, conn, params=(s_id,))
            
            if not eval_history.empty:
                st.dataframe(eval_history, use_container_width=True)
            else:
                st.info("هنوز ارزشیابی برای این دانش‌آموز ثبت نشده است.")
        except Exception:
            st.info("سابقه‌ای یافت نشد.")

# ---------------------------------------------------------
# 3. Behavior and Discipline Tracking
# ---------------------------------------------------------
elif menu_choice == "🌟 ثبت رفتار و انضباط":
    st.header("🌟 مدیریت رفتار و مشاهدات انضباطی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("لطفاً ابتدا دانش‌آموزان را در سامانه ثبت کنید.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with col2:
            title = st.text_input("عنوان رفتار (مثلاً: همکاری در گروه، تاخیر ورود، دقت در تکالیف):")
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
            st.success("مشاهده رفتاری با موفقیت ثبت شد.")
            
        st.markdown("---")
        st.subheader(f"📋 گزارش رفتار و انضباط: {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        try:
            with get_connection() as conn:
                b_history = pd.read_sql_query("""
                    SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                    FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
                """, conn, params=(s_id,))
                
            if not b_history.empty:
                st.dataframe(b_history, use_container_width=True)
            else:
                st.info("هیچ مورد رفتاری ثبت نشده است.")
        except Exception:
            st.info("سابقه‌ای یافت نشد.")

# ---------------------------------------------------------
# 4. Online Quiz Creator (Teacher Side)
# ---------------------------------------------------------
elif menu_choice == "✏️ آزمون‌ساز آنلاین (معلم)":
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و مدیریت آزمون)")
    
    tab_q1, tab_q2 = st.tabs(["➕ ساخت آزمون جدید و طراحی سوالات", "📊 لیست آزمون‌ها و نتایج"])
    
    with tab_q1:
        st.subheader("۱. مشخصات آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمونک فصل اول ریاضی - کسرها):")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
            
        num_questions = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=20, value=2)
        
        st.markdown("---")
        st.subheader("۲. ورود سوالات و کلید تصحیح")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**📌 سوال شماره {i+1}:**")
            q_text = st.text_input(f"متن سوال {i+1}:", key=f"q_{i}")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                opt1 = st.text_input(f"گزینه ۱ (سوال {i+1}):", key=f"opt1_{i}")
            with c2:
                opt2 = st.text_input(f"گزینه ۲ (سوال {i+1}):", key=f"opt2_{i}")
            with c3:
                opt3 = st.text_input(f"گزینه ۳ (سوال {i+1}):", key=f"opt3_{i}")
            with c4:
                opt4 = st.text_input(f"گزینه ۴ (سوال {i+1}):", key=f"opt4_{i}")
            
            correct_opt = st.selectbox(f"گزینه صحیح برای سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
            questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt))
            st.markdown("---")
            
        if st.button("انتشار و ذخیره آزمون"):
            if quiz_title and all(q[0] for q in questions_data):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                        (quiz_title, quiz_subject, duration, datetime.date.today())
                    )
                    quiz_id = cursor.lastrowid
                    
                    for q in questions_data:
                        cursor.execute(
                            """INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5])
                        )
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' با موفقیت ساخته شد و آماده برگزاری است!")
            else:
                st.error("لطفاً عنوان آزمون و متن تمامی سوالات را وارد کنید.")

    with tab_q2:
        try:
            with get_connection() as conn:
                quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
            
            if not quizzes_df.empty:
                st.dataframe(quizzes_df, use_container_width=True)
                
                st.subheader("📈 مشاهده نتایج و کارنامه آزمون‌ها")
                selected_quiz_id = st.selectbox("انتخاب آزمون برای مشاهده نتایج:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
                
                with get_connection() as conn:
                    results_df = pd.read_sql_query("""
                        SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                               r.score AS 'نمره (تعداد درست)',
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
        except Exception:
            st.info("هنوز آزمونی ساخته نشده است.")

# ---------------------------------------------------------
# 5. Student Online Quiz Interface
# ---------------------------------------------------------
elif menu_choice == "📱 شرکت در آزمون (دانش‌آموز)":
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    quizzes_df = pd.DataFrame()
    try:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
    except Exception:
        pass
        
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
        
        # Check if already taken
        existing = None
        try:
            with get_connection() as conn:
                existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
        except Exception:
            pass
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده: {existing['percentage']:.1f}٪")
        else:
            quiz_duration = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"زمان پیشنهادی آزمون: {quiz_duration} دقیقه")
            
            # Fetch Questions
            questions = []
            try:
                with get_connection() as conn:
                    questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
            except Exception:
                pass
                
            student_answers = {}
            st.markdown("---")
            with st.form("student_quiz_form"):
                for idx, q in enumerate(questions):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    user_ans = st.radio(
                        f"پاسخ سوال {idx+1}:",
                        options=[1, 2, 3, 4],
                        format_func=lambda x: f"گزینه {x}: {options[x-1]}",
                        key=f"sq_{q['id']}"
                    )
                    student_answers[q['id']] = (user_ans, q['correct_option'])
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("پایان آزمون و دریافت نتیجه آنی")
                
                if submit_quiz:
                    correct_count = 0
                    total = len(questions)
                    for q_id_key, (ans, correct) in student_answers.items():
                        if ans == correct:
                            correct_count += 1
                            
                    pct = (correct_count / total) * 100 if total > 0 else 0
                    
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage) VALUES (?, ?, ?, ?, ?)",
                            (q_id, s_id, correct_count, total, pct)
                        )
                        conn.commit()
                        
                    st.balloons()
                    st.success(f"🎉 آزمون با موفقیت پایان یافت! نمره شما: {correct_count} از {total} (معادل {pct:.1f} درصد)")

# ---------------------------------------------------------
# 6. Dashboard and Analytical Report
# ---------------------------------------------------------
elif menu_choice == "📊 داشبورد و کارنامه جامع":
    st.header("📊 داشبورد تحلیلی و کارنامه جامع کلاس پنجم")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی برای نمایش وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه جامع:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        st.markdown(f"### 📄 کارنامه جامع و توصیفی: {selected_student}")
        
        col1, col2, col3 = st.columns(3)
        
        eval_count = 0
        beh_count = 0
        quiz_avg = None
        
        try:
            with get_connection() as conn:
                res_e = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()
                eval_count = res_e[0] if res_e else 0
                
                res_b = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()
                beh_count = res_b[0] if res_b else 0
                
                res_q = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()
                quiz_avg = res_q[0] if res_q else None
        except Exception:
            pass
            
        with col1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with col2:
            st.metric("تعداد موارد رفتاری ثبت‌شده:", beh_count)
        with col3:
            st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        
        # Tabs for details
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های درسی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها"])
        
        with tab_d1:
            try:
                with get_connection() as conn:
                    df_e = pd.read_sql_query("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
                if not df_e.empty:
                    st.dataframe(df_e, use_container_width=True)
                else:
                    st.info("ارزشیابی درسی ثبت نشده است.")
            except Exception:
                st.info("ارزشیابی درسی ثبت نشده است.")
                
        with tab_d2:
            try:
                with get_connection() as conn:
                    df_b = pd.read_sql_query("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", conn, params=(s_id,))
                if not df_b.empty:
                    st.dataframe(df_b, use_container_width=True)
                else:
                    st.info("مورد رفتاری ثبت نشده است.")
            except Exception:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            try:
                with get_connection() as conn:
                    df_q = pd.read_sql_query("""
                        SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                        FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                    """, conn, params=(s_id,))
                if not df_q.empty:
                    st.dataframe(df_q, use_container_width=True)
                else:
                    st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")
            except Exception:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")

