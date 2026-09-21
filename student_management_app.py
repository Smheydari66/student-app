import streamlit as st
import sqlite3
import pandas as pd
import datetime

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم - دبستان شهید مطهری",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapsed by default so top-menu takes priority
)

# ---------------------------------------------------------
# 2. Ultra-Responsive Modern RTL CSS Design
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    /* Base Reset & Typography */
    html, body, [class*="css"], div, span, button, input, select, textarea {
        font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        box-sizing: border-box;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Responsive Main Header Bar */
    .app-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: #FFFFFF !important;
        padding: 24px 20px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
    }
    .app-header h1 {
        color: #FFFFFF !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        margin: 0 0 8px 0 !important;
        line-height: 1.4 !important;
        white-space: normal !important;
    }
    .app-header p {
        color: #E0E7FF !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
        line-height: 1.5 !important;
    }
    
    /* Designer Info Badge */
    .designer-badge {
        background-color: #FFFFFF;
        border: 2px solid #3B82F6;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .designer-badge .title {
        color: #64748B !important;
        font-size: 0.85rem !important;
        margin-bottom: 4px;
    }
    .designer-badge .name {
        color: #1E293B !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        margin-bottom: 4px;
    }
    .designer-badge .school {
        color: #2563EB !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }
    
    /* Top Horizontal Navigation Container */
    .top-nav-box {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Card Styles */
    .custom-card {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .card-header-blue {
        border-right: 5px solid #2563EB;
    }
    .card-header-green {
        border-right: 5px solid #10B981;
    }
    .card-header-purple {
        border-right: 5px solid #8B5CF6;
    }
    .card-title {
        color: #1E293B !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-bottom: 12px !important;
    }
    
    /* Input Form Enhancements */
    .stTextInput > div > div > input, .stTextArea textarea, .stSelectbox select {
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea textarea:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }
    
    /* Primary Button */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Radio Horizontal Pills */
    div[data-testid="stHorizontalBlock"] > div {
        align-items: center;
    }
    
    /* Status Badges */
    .badge-success {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .badge-info {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SQLite Database Engine
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
            avatar_icon TEXT DEFAULT '👨‍🎓',
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

init_db()

# ---------------------------------------------------------
# 4. Helper Functions & Constants
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

AVATAR_ICONS = ["👨‍🎓", "👦", "👧", "🚀", "🌟", "📚", "🎨", "⚽"]

def load_students():
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT id, avatar_icon || ' ' || first_name || ' ' || last_name AS full_name, first_name, last_name, national_id, parent_phone, notes, avatar_icon FROM students ORDER BY last_name ASC", 
            conn
        )
    return df

# ---------------------------------------------------------
# 5. Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="app-header">
    <h1>🎓 سامانه مدیریت هوشمند کلاس پنجم ابتدایی</h1>
    <p>پلتفرم جامع ارزشیابی کیفی-توصیفی، پرونده تحصیلی و آزمون‌ساز آنلاین با تصحیح خودکار</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. Prominent Top Navigation Bar (Mobile & Desktop Friendly)
# ---------------------------------------------------------
MENU_OPTIONS = [
    "🏠 صفحه اصلی",
    "👨‍🎓 ثبت و مدیریت دانش‌آموزان",
    "📝 ارزشیابی کیفی-توصیفی",
    "🌟 انضباط و رفتار",
    "✏️ آزمون‌ساز آنلاین",
    "📱 شرکت در آزمون",
    "📊 کارنامه جامع"
]

st.markdown('<div class="top-nav-box">', unsafe_allow_html=True)
nav_col1, nav_col2 = st.columns([1, 3])

with nav_col1:
    st.markdown("<p style='font-weight:700; color:#1E293B; margin-top:6px;'>📌 بخش‌های سامانه:</p>", unsafe_allow_html=True)

with nav_col2:
    selected_menu = st.selectbox(
        "انتخاب بخش:",
        options=MENU_OPTIONS,
        index=0,
        label_visibility="collapsed"
    )
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE 0: Landing Page & Designer Info
# ---------------------------------------------------------
if selected_menu == "🏠 صفحه اصلی":
    st.markdown("""
    <div class="designer-badge">
        <div class="title">طراحی و توسعه سامانه توسط:</div>
        <div class="name">🌱 سید موسی حیدری</div>
        <div class="school"> آموزگار کلاس پنجم ابتدایی - دبستان شهید مطهری مهران</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 امکانات و قابلیت‌های اصلی سامانه:")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown("""
        <div class="custom-card card-header-blue">
            <div class="card-title">👨‍🎓 ثبت و پرونده الکترونیک دانش‌آموزان</div>
            <p style="color:#475569; font-size:0.9rem;">
            ورود سریع اطلاعات شخصی، کد ملی، شماره اولیا، ثبت توضیحات خاص آموزشی و اختصاص آیکون کاربری برای هر دانش‌آموز.
            </p>
        </div>
        
        <div class="custom-card card-header-green">
            <div class="card-title">📝 ارزشیابی کیفی-توصیفی ۷ درس</div>
            <p style="color:#475569; font-size:0.9rem;">
            ثبت سطح عملکرد (خیلی خوب تا نیاز به تلاش) برای کلیه دروس پایه پنجم همراه با بازخورد توصیفی معلم.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_f2:
        st.markdown("""
        <div class="custom-card card-header-purple">
            <div class="card-title">✏️ آزمون‌ساز آنلاین با تصحیح خودکار</div>
            <p style="color:#475569; font-size:0.9rem;">
            طراحی آسان آزمونک‌های ۴ گزینه‌ای، تعیین مدت زمان آزمون، تصحیح خودکار پاسخ‌ها و محاسبه نمره و درصد آنی.
            </p>
        </div>
        
        <div class="custom-card card-header-blue">
            <div class="card-title">📊 کارنامه جامع و تحلیلی</div>
            <p style="color:#475569; font-size:0.9rem;">
            مشاهده پرونده کامل، سوابق رفتاری، نمرات آزمون‌ها و کارنامه توصیفی هر دانش‌آموز جهت ارائه به اولیا.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE 1: Enhanced Student Registration & Profile Management
# ---------------------------------------------------------
elif selected_menu == "👨‍🎓 ثبت و مدیریت دانش‌آموزان":
    st.subheader("👨‍🎓 ورود اطلاعات و مدیریت پرونده دانش‌آموزان")
    
    tab_add, tab_list = st.tabs(["➕ فرم ثبت دانش‌آموز جدید", "📋 لیست و ویرایش دانش‌آموزان"])
    
    with tab_add:
        st.markdown("""
        <div class="custom-card card-header-blue">
            <div class="card-title">📝 فرم ثبت‌نام دانش‌آموز جدید</div>
            <p style="color:#64748B; font-size:0.85rem; margin-bottom:15px;">
            اطلاعات دانش‌آموز را با دقت وارد کنید. تمامی فیلدها جهت آمار دقیق کلاس ذخیره می‌شوند.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("modern_student_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            
            with f_col1:
                first_name = st.text_input("نام دانش‌آموز:*", placeholder="مثلاً: علی")
                national_id = st.text_input("کد ملی ۱۰ رقمی:*", placeholder="مثلاً: 5800123456", max_chars=10)
                avatar = st.selectbox("انتخاب نماد دانش‌آموز:", AVATAR_ICONS, index=0)
                
            with f_col2:
                last_name = st.text_input("نام خانوادگی:*", placeholder="مثلاً: حسینی")
                parent_phone = st.text_input("شماره همراه اولیا (جهت SMS/شاد):*", placeholder="مثلاً: 09181234567", max_chars=11)
            
            notes = st.text_area("ملاحظات آموزشی، پزشکی یا اخلاقی (اختیاری):", placeholder="مثلاً: صندلی ردیف اول قرار گیرد. علاقه زیادی به درس علوم دارد.")
            
            btn_submit = st.form_submit_button("✨ ثبت پرونده دانش‌آموز")
            
            if btn_submit:
                if not first_name.strip() or not last_name.strip():
                    st.error("⚠️ لطفاً نام و نام خانوادگی دانش‌آموز را وارد کنید.")
                elif len(national_id.strip()) != 10 or not national_id.isdigit():
                    st.error("⚠️ کد ملی باید دقیقاً ۱۰ رقم عددی باشد.")
                else:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, avatar_icon, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                (first_name.strip(), last_name.strip(), national_id.strip(), parent_phone.strip(), avatar, notes.strip())
                            )
                            conn.commit()
                        st.success(f"🎉 پرونده دانش‌آموز {avatar} {first_name} {last_name} با موفقیت ثبت گردید.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ این کد ملی قبلاً در سیستم ثبت شده است.")

    with tab_list:
        students_df = load_students()
        if not students_df.empty:
            st.markdown(f"**تعداد کل دانش‌آموزان ثبت‌شده:** `{len(students_df)} نفر`")
            
            # Search Bar
            search_query = st.text_input("🔍 جستجوی سریع نام یا کد ملی:", placeholder="نام یا کد ملی را تایپ کنید...")
            
            filtered_df = students_df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['full_name'].str.contains(search_query) | 
                    filtered_df['national_id'].str.contains(search_query)
                ]
            
            st.dataframe(
                filtered_df[['id', 'avatar_icon', 'first_name', 'last_name', 'national_id', 'parent_phone', 'notes']].rename(columns={
                    'id': 'شناسه',
                    'avatar_icon': 'آیکون',
                    'first_name': 'نام',
                    'last_name': 'نام خانوادگی',
                    'national_id': 'کد ملی',
                    'parent_phone': 'شماره اولیا',
                    'notes': 'توضیحات'
                }), 
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            st.subheader("🗑️ مدیریت یا حذف دانش‌آموز")
            student_to_delete = st.selectbox("انتخاب دانش‌آموز جهت حذف کامل از کلاس:", students_df['full_name'].tolist(), key="del_student_select")
            
            if st.button("❌ حذف پرونده دانش‌آموز انتخاب‌شده"):
                s_id = int(students_df[students_df['full_name'] == student_to_delete]['id'].values[0])
                with get_connection() as conn:
                    conn.execute("DELETE FROM students WHERE id = ?", (s_id,))
                    conn.commit()
                st.success(f"پرونده {student_to_delete} حذف گردید.")
                st.rerun()
        else:
            st.info("هنوز هیچ دانش‌آموزی در کلاس ثبت نشده است. از زبانه 'ثبت دانش‌آموز جدید' استفاده نمایید.")

# ---------------------------------------------------------
# PAGE 2: Qualitative Evaluation (7 Subjects)
# ---------------------------------------------------------
elif selected_menu == "📝 ارزشیابی کیفی-توصیفی":
    st.subheader("📝 ثبت و ثبت سوابق ارزشیابی کیفی-توصیفی (پایه پنجم)")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("⚠️ لطفاً ابتدا دانش‌آموزان را در بخش پرونده ثبت کنید.")
    else:
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:*", students_df['full_name'].tolist())
            selected_subject = st.selectbox("انتخاب درس:*", FIFTH_GRADE_SUBJECTS)
        with e_col2:
            selected_level = st.selectbox("سطح توصیفی عملکرد:*", EVALUATION_LEVELS)
            eval_date = st.date_input("تاریخ ارزشیابی:", datetime.date.today())
            
        feedback_text = st.text_area(
            "توصیف عملکرد و بازخورد معلم (توصیفی):", 
            placeholder="مثلاً: در فرآیند جمع و تفریق کسرها دقت عالی دارد. نیاز به تمرین بیشتر در ساده‌کردن کسرها احساس می‌شود."
        )
        
        if st.button("✨ ثبت ارزشیابی توصیفی"):
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                    (s_id, selected_subject, selected_level, feedback_text, eval_date)
                )
                conn.commit()
            st.success(f"ارزشیابی درس {selected_subject} برای {selected_student} با موفقیت ذخیره شد.")

        st.markdown("---")
        st.subheader(f"🔍 سوابق ارزشیابی {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            eval_history = pd.read_sql_query("""
                SELECT subject AS 'عنوان درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, conn, params=(s_id,))
        
        if not eval_history.empty:
            st.dataframe(eval_history, use_container_width=True, hide_index=True)
        else:
            st.info("هنوز هیچ ارزشیابی توصیفی برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# PAGE 3: Behavior & Discipline
# ---------------------------------------------------------
elif selected_menu == "🌟 انضباط و رفتار":
    st.subheader("🌟 ثبت مشاهدات رفتاری و انضباطی")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("⚠️ لطفاً ابتدا دانش‌آموزان را ثبت کنید.")
    else:
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            selected_student = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist())
            b_type = st.selectbox("نوع مشاهده:", ["تشویق / رفتار مثبت 🟢", "پیگیری / نیاز به توجه 🔴"])
        with b_col2:
            title = st.text_input("عنوان رفتار:", placeholder="مثلاً: مسئولیت‌پذیری در گروه، رعایت نظم، دقت در تکالیف")
            log_date = st.date_input("تاریخ ثبت:", datetime.date.today())
            
        desc = st.text_area("شرح دقیق رفتار و اقدام انجام‌شده:")
        
        if st.button("✨ ثبت مورد رفتاری"):
            if title.strip():
                s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, b_type, title.strip(), desc.strip(), log_date)
                    )
                    conn.commit()
                st.success("مشاهده رفتاری ذخیره شد.")
                st.rerun()
            else:
                st.error("لطفاً عنوان رفتار را وارد نمایید.")
            
        st.markdown("---")
        st.subheader(f"📋 گزارش رفتار و انضباط {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            b_history = pd.read_sql_query("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'توضیحات تکمیلی', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
            """, conn, params=(s_id,))
            
        if not b_history.empty:
            st.dataframe(b_history, use_container_width=True, hide_index=True)
        else:
            st.info("هیچ مورد رفتاری برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# PAGE 4: Quiz Creator
# ---------------------------------------------------------
elif selected_menu == "✏️ آزمون‌ساز آنلاین":
    st.subheader("✏️ آزمون‌ساز آنلاین معلم (طراحی آزمون ۴ گزینه‌ای)")
    
    tab_q1, tab_q2 = st.tabs(["➕ طراحی آزمون جدید", "📊 آزمون‌های برگزارشده و نتایج"])
    
    with tab_q1:
        q_col1, q_col2, q_col3 = st.columns(3)
        with q_col1:
            quiz_title = st.text_input("عنوان آزمون:", placeholder="مثلاً: آزمونک فصل اول ریاضی (کسرها)")
        with q_col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with q_col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
            
        num_questions = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=15, value=2)
        
        st.markdown("---")
        st.markdown("##### 📌 ورود متن سوالات و پاسخ صحیح:")
        
        questions_data = []
        for i in range(int(num_questions)):
            st.markdown(f"**سوال شماره {i+1}:**")
            q_text = st.text_input(f"متن سوال {i+1}:", key=f"q_{i}")
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
            questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt))
            st.markdown("---")
            
        if st.button("🚀 انتشار و فعال‌سازی آزمون"):
            if quiz_title.strip() and all(q[0].strip() for q in questions_data):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO quizzes (title, subject, duration_minutes, created_at) VALUES (?, ?, ?, ?)",
                        (quiz_title.strip(), quiz_subject, duration, datetime.date.today())
                    )
                    quiz_id = cursor.lastrowid
                    
                    for q in questions_data:
                        cursor.execute(
                            """INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5])
                        )
                    conn.commit()
                st.success(f"🎉 آزمون '{quiz_title}' ساخته شد و آماده پاسخ‌دهی دانش‌آموزان است.")
            else:
                st.error("⚠️ لطفاً عنوان آزمون و متن کلیه سوالات را تکمیل کنید.")

    with tab_q2:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📈 مشاهده نتایج دانش‌آموزان در آزمون")
            selected_quiz_id = st.selectbox(
                "انتخاب آزمون جهت مشاهده نمرات:", 
                quizzes_df['id'].tolist(), 
                format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0]
            )
            
            with get_connection() as conn:
                results_df = pd.read_sql_query("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'پاسخ صحیح',
                           r.total_questions AS 'کل سوالات',
                           r.percentage AS 'درصد ٪',
                           r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r
                    JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, conn, params=(selected_quiz_id,))
                
            if not results_df.empty:
                st.dataframe(results_df, use_container_width=True, hide_index=True)
            else:
                st.info("هنوز دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز آزمونی ثبت نشده است.")

# ---------------------------------------------------------
# PAGE 5: Student Exam Interface
# ---------------------------------------------------------
elif selected_menu == "📱 شرکت در آزمون":
    st.subheader("📱 سامانه پاسخ‌دهی آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("⚠️ در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        sq_col1, sq_col2 = st.columns(2)
        with sq_col1:
            student_name = st.selectbox("نام خود را انتخاب کنید:*", students_df['full_name'].tolist())
        with sq_col2:
            quiz_name = st.selectbox("آزمون مورد نظر را انتخاب کنید:*", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        # Check if taken
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"✅ شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده شما: {existing['percentage']:.1f}٪")
        else:
            quiz_dur = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پیشنهادی پاسخ‌دهی: {quiz_dur} دقیقه")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_answers = {}
            st.markdown("---")
            with st.form("student_quiz_submission"):
                for idx, q in enumerate(questions):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    user_ans = st.radio(
                        f"انتخاب پاسخ برای سوال {idx+1}:",
                        options=[1, 2, 3, 4],
                        format_func=lambda x: f"گزینه {x}: {options[x-1]}",
                        key=f"sq_{q['id']}"
                    )
                    student_answers[q['id']] = (user_ans, q['correct_option'])
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و ثبت نهایی")
                
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
                    st.success(f"🎉 آزمون با موفقیت ثبت شد! نتیجه شما: {correct_count} پاسخ صحیح از {total} (معادل {pct:.1f} درصد)")

# ---------------------------------------------------------
# PAGE 6: Comprehensive Report Card
# ---------------------------------------------------------
elif selected_menu == "📊 کارنامه جامع":
    st.subheader("📊 کارنامه جامع و تحلیلی عملکرد دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی در سیستم موجود نیست.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت صدور کارنامه:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        
        st.markdown(f"### 📄 پرونده تحصیلی و کارنامه: {selected_student}")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        with m_col1:
            st.metric("ارزشیابی‌های درسی ثبت‌شده", f"{eval_count} مورد")
        with m_col2:
            st.metric("موارد انضباطی / رفتاری", f"{beh_count} مورد")
        with m_col3:
            st.metric("میانگین درصد آزمون‌های آنلاین", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3 = st.tabs(["📝 توصیف عملکرد درسی", "🌟 سوابق رفتاری", "📊 نمرات آزمون‌ها"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = pd.read_sql_query("SELECT subject AS 'عنوان درس', level AS 'سطح عملکرد', feedback AS 'توصیف معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("ارزشیابی توصیفی ثبت نشده است.")
                
        with tab_d2:
            with get_connection() as conn:
                df_b = pd.read_sql_query("SELECT behavior_type AS 'نوع', title AS 'عنوان رفتار', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", conn, params=(s_id,))
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
            else:
                st.info("مورد رفتاری ثبت نشده است.")
                
        with tab_d3:
            with get_connection() as conn:
                df_q = pd.read_sql_query("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'تعداد درست', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True, hide_index=True)
            else:
                st.info("هیچ آزمون آنلاینی ثبت نشده است.")


