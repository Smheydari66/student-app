import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random
import base64
from PIL import Image
import io

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
    }
    
    .stApp {
        background-color: #f8f9fa;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center !important;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-right: 5px solid #2a5298;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #2a5298;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
        white-space: nowrap !important;
    }
    
    .stButton>button:hover {
        background-color: #1e3c72;
        color: white;
    }
    
    .welcome-box {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    
    .quote-box {
        background: linear-gradient(135deg, #fff9e6 0%, #fff3cc 100%);
        border-right: 6px solid #f59e0b;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    .security-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database Initialization & Auto Migration
# ---------------------------------------------------------
DB_FILE = "class_management.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def safe_read_sql(query, params=()):
    try:
        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception:
        init_db()
        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

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
            pin_code TEXT DEFAULT '1234',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Add pin_code column if missing
        cursor.execute("PRAGMA table_info(students)")
        cols = [column[1] for column in cursor.fetchall()]
        if 'pin_code' not in cols:
            cursor.execute("ALTER TABLE students ADD COLUMN pin_code TEXT DEFAULT '1234'")
        
        # Qualitative Evaluations Table
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
        
        # Behaviors Table
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
            face_image TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        """)
        
        cursor.execute("PRAGMA table_info(quiz_results)")
        q_cols = [column[1] for column in cursor.fetchall()]
        if 'face_image' not in q_cols:
            cursor.execute("ALTER TABLE quiz_results ADD COLUMN face_image TEXT")
            
        conn.commit()

init_db()

# ---------------------------------------------------------
# Helper Functions
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

def load_students():
    return safe_read_sql("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, pin_code, notes FROM students")

# ---------------------------------------------------------
# Navigation State Management (Welcome Screen vs Main App)
# ---------------------------------------------------------
if "show_welcome" not in st.session_state:
    st.session_state["show_welcome"] = True

# Header & Top Navigation
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("""
    <div class="main-header">
        <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
        <p>دبستان شهید مطهری مهران — آموزگار: سید موسی حیدری</p>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    if st.button("🏠 صفحه خوش‌آمدگویی", key="btn_toggle_welcome"):
        st.session_state["show_welcome"] = not st.session_state["show_welcome"]
        st.rerun()

# ---------------------------------------------------------
# WELCOME SPLASH PAGE
# ---------------------------------------------------------
if st.session_state["show_welcome"]:
    st.markdown("""
    <div class="welcome-box">
        <h2 style="color: #1e3c72; text-align: center; margin-bottom: 15px;">🌸 به سامانه هوشمند مدیریت کلاس و آزمون آنلاین خوش آمدید 🌸</h2>
        <p style="font-size: 1.1rem; line-height: 1.8; color: #334155; text-align: justify;">
            با حمد و ثنای الهی، جهت ارتقای کیفیت یادگیری، پایش دقیق آموزشی و ارتباط موثرتر میان مدرسه و اولیاء محترم، 
            <b>«سامانه هوشمند مدیریت کلاس پایه پنجم ابتدایی»</b> دبستان شهید مطهری مهران با بهره‌گیری از جدیدترین ابزارهای نرم‌افزاری و امنیتی طراحی و راه‌اندازی گردید.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="quote-box">
        <h4 style="color: #92400e; margin-bottom: 10px;">📜 فرمایشات مقام معظم رهبری (حضرت آیت‌الله خامنه‌ای مدظله‌العالی) در باب فناوری و آموزش:</h4>
        <p style="font-size: 1.15rem; line-height: 2.0; color: #78350f; font-weight: bold; text-align: justify; font-style: italic;">
            «استفاده از ابزارهای نوين علمی و فناوری‌های هوشمند، مسیر یادگیری را برای دانش‌آموزان جذاب‌تر، عمیق‌تر و کارآمدتر می‌سازد. 
            آموزش و پرورش ما باید مجهز به آخرین دستاوردهای علمی و تکنولوژی روز باشد تا نسل جوان ما برای آینده‌ای روشن و سراسر افتخار آماده شود.»
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="color: #2a5298;">🎯 اهداف اصلی سامانه</h3>
            <ul style="font-size: 1.05rem; line-height: 2.0; color: #1e293b;">
                <li><b>ارتقای کیفیت یادگیری:</b> برگزاری آزمون‌های آنلاین هوشمند با تصحیح آنی، ارائه تحلیل آموزشی و تثبیت آموخته‌ها.</li>
                <li><b>شفافیت و آگاهی اولیا:</b> دسترسی سریع خانواده‌ها به پوشه کار دیجیتال، نمرات و نمودارهای رشد تحصیلی فرزندان.</li>
                <li><b>تقویت روحیه همکاری:</b> گروه‌بندی ۲۹ دانش‌آموز در ۵ گروه کلاسی متوازن و ثبت نشان‌های افتخار و موارد انضباطی.</li>
                <li><b>احراز هویت امن چندلایه:</b> ورود با رمز اختصاصی ۴ رقمی، ترتیب تصلاحی سوالات، ثبت عکس چهره و قفل خودکار آزمون.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="color: #2a5298;">🇮🇷 مطابقت با برنامه‌های وزارت آموزش و پرورش</h3>
            <ul style="font-size: 1.05rem; line-height: 2.0; color: #1e293b;">
                <li><b>انطباق با سند تحول بنیادین:</b> تحقق ساحت‌های شش‌گانه تربیت به‌ویژه ساحت علمی-فناوری و ساحت اجتماعی-اخلاقی.</li>
                <li><b>ارزشیابی کیفی-توصیفی:</b> پوشش کامل ۷ عنوان درسی پایه پنجم مطابق با دستورالعمل‌های رسمی دفتر دبیرخانه کشوری ابتدایی.</li>
                <li><b>توسعه عدالت آموزشی:</b> ایجاد فرصت برابر برای تمامی دانش‌آموزان جهت استفاده از ابزارهای مدرن سنجش و یادگیری.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 ورود به سامانه هوشمند مدیریت کلاس", key="btn_enter_app"):
        st.session_state["show_welcome"] = False
        st.rerun()

else:
    # ---------------------------------------------------------
    # MAIN APPLICATION NAVIGATION (RADIO NAVIGATION FOR DESKTOP)
    # ---------------------------------------------------------
    st.sidebar.image("https://img.icons8.com/illustrations/100/teacher.png", width=80)
    st.sidebar.title("📌 منوی بخش‌های سامانه")
    
    menu_choice = st.sidebar.radio(
        "انتخاب بخش:",
        [
            "👨‍🎓 مدیریت دانش‌آموزان و رمز اختصاصی",
            "📝 ثبت ارزشیابی کیفی-توصیفی",
            "🌟 مدیریت رفتار و مشاهدات انضباطی",
            "✏️ آزمون‌ساز آنلاین و بانک سوالات",
            "📱 شرکت در آزمون آنلاین (دانش‌آموز)",
            "📊 پوشه کار و کارنامه جامع"
        ]
    )

    # ---------------------------------------------------------
    # 1. Student Profile & PIN Management
    # ---------------------------------------------------------
    if menu_choice == "👨‍🎓 مدیریت دانش‌آموزان و رمز اختصاصی":
        st.header("👨‍🎓 مدیریت دانش‌آموزان و رمزهای اختصاصی ۴ رقمی (۲۹ نفر)")
        
        tab1, tab2 = st.tabs(["📋 لیست دانش‌آموزان و رمزها", "➕ ثبت دانش‌آموز جدید"])
        
        with tab1:
            students_df = load_students()
            if not students_df.empty:
                st.dataframe(students_df.rename(columns={
                    'id': 'شناسه',
                    'full_name': 'نام و نام خانوادگی',
                    'national_id': 'کد ملی',
                    'parent_phone': 'شماره همراه اولیا',
                    'pin_code': 'رمز اختصاصی (PIN)',
                    'notes': 'توضیحات'
                }), use_container_width=True)
                
                st.markdown("---")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.subheader("🔑 ویرایش رمز اختصاصی دانش‌آموز")
                    st_selected = st.selectbox("انتخاب دانش‌آموز:", students_df['full_name'].tolist(), key="select_st_pin")
                    new_pin = st.text_input("رمز ۴ رقمی جدید:", max_chars=4, key="new_pin_val")
                    if st.button("ذخیره رمز جدید"):
                        if new_pin and len(new_pin) == 4:
                            s_id = int(students_df[students_df['full_name'] == st_selected]['id'].values[0])
                            with get_connection() as conn:
                                conn.execute("UPDATE students SET pin_code = ? WHERE id = ?", (new_pin, s_id))
                                conn.commit()
                            st.success(f"رمز اختصاصی برای {st_selected} به {new_pin} تغییر یافت.")
                            st.rerun()
                        else:
                            st.error("لطفاً یک رمز ۴ رقمی وارد کنید.")

                with col_e2:
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
                st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. از زبانه 'ثبت دانش‌آموز جدید' استفاده کنید.")

        with tab2:
            with st.form("add_student_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("نام:")
                    national_id = st.text_input("کد ملی دانش‌آموز:")
                with col2:
                    last_name = st.text_input("نام خانوادگی:")
                    parent_phone = st.text_input("شماره همراه اولیا:")
                
                pin_code = st.text_input("رمز ۴ رقمی اختصاصی دانش‌آموز (پیش‌فرض 1234):", value="1234", max_chars=4)
                notes = st.text_area("توضیحات ویژه یا ملاحظات آموزشی:")
                
                submit_btn = st.form_submit_button("ثبت پرونده دانش‌آموز")
                
                if submit_btn:
                    if first_name and last_name:
                        try:
                            with get_connection() as conn:
                                conn.execute(
                                    "INSERT INTO students (first_name, last_name, national_id, parent_phone, pin_code, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                    (first_name, last_name, national_id, parent_phone, pin_code, notes)
                                )
                                conn.commit()
                            st.success(f"دانش‌آموز {first_name} {last_name} با موفقیت ثبت شد.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("کد ملی وارد شده تکراری است.")
                    else:
                        st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

    # ---------------------------------------------------------
    # 2. Qualitative Evaluation
    # ---------------------------------------------------------
    elif menu_choice == "📝 ثبت ارزشیابی کیفی-توصیفی":
        st.header("📝 ثبت ارزشیابی کیفی-توصیفی (۷ درس پایه پنجم)")
        
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
                
            feedback_text = st.text_area("بازخورد توصیفی و راهکارهای بهبود عملکرد:", 
                                         placeholder="توصیف عملکرد و راهکار رشد آموزشی...")
            
            if st.button("ثبت ارزشیابی توصیفی"):
                s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO evaluations (student_id, subject, level, feedback, eval_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, selected_subject, selected_level, feedback_text, eval_date)
                    )
                    conn.commit()
                st.success(f"ارزشیابی {selected_subject} برای {selected_student} ثبت شد.")

            st.markdown("---")
            st.subheader("🔍 سوابق ارزشیابی دانش‌آموز انتخاب‌شده")
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            eval_history = safe_read_sql("""
                SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, params=(s_id,))
            
            if not eval_history.empty:
                st.dataframe(eval_history, use_container_width=True)
            else:
                st.info("هنوز ارزشیابی برای این دانش‌آموز ثبت نشده است.")

    # ---------------------------------------------------------
    # 3. Behavior Management
    # ---------------------------------------------------------
    elif menu_choice == "🌟 مدیریت رفتار و مشاهدات انضباطی":
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
            
            if st.button("ثبت مورد رفتاری"):
                s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO behaviors (student_id, behavior_type, title, description, log_date) VALUES (?, ?, ?, ?, ?)",
                        (s_id, b_type, title, desc, log_date)
                    )
                    conn.commit()
                st.success("مشاهده رفتاری ثبت شد.")
                
            st.markdown("---")
            st.subheader(f"📋 گزارش رفتار {selected_student}")
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            b_history = safe_read_sql("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
            """, params=(s_id,))
                
            if not b_history.empty:
                st.dataframe(b_history, use_container_width=True)
            else:
                st.info("هیچ مورد رفتاری ثبت نشده است.")

    # ---------------------------------------------------------
    # 4. Online Quiz Creator
    # ---------------------------------------------------------
    elif menu_choice == "✏️ آزمون‌ساز آنلاین و بانک سوالات":
        st.header("✏️ آزمون‌ساز آنلاین و طراحی سوالات")
        
        tab_q1, tab_q2 = st.tabs(["➕ ساخت آزمون جدید", "📊 نتایج و تصویر چهره دانش‌آموزان"])
        
        with tab_q1:
            st.subheader("۱. مشخصات کلی آزمون")
            col1, col2, col3 = st.columns(3)
            with col1:
                quiz_title = st.text_input("عنوان آزمون:")
            with col2:
                quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
            with col3:
                duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
                
            num_questions = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=20, value=2)
            
            st.markdown("---")
            st.subheader("۲. ورود سوالات و گزینه‌ها")
            
            questions_data = []
            for i in range(int(num_questions)):
                st.markdown(f"**📌 سوال شماره {i+1}:**")
                q_text = st.text_input(f"متن سوال {i+1}:", key=f"q_{i}")
                c1, c2, c3, c4 = st.columns(4)
                with c1: opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
                with c2: opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
                with c3: opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
                with c4: opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
                
                correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
                questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt))
                st.markdown("---")
                
            if st.button("انتشار آزمون در سامانه"):
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
                    st.success(f"آزمون '{quiz_title}' با موفقیت ساخته شد و منتشر گردید!")
                else:
                    st.error("لطفاً عنوان آزمون و متن تمامی سوالات را کامل کنید.")

        with tab_q2:
            quizzes_df = safe_read_sql("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت', created_at AS 'تاریخ' FROM quizzes")
            
            if not quizzes_df.empty:
                st.dataframe(quizzes_df, use_container_width=True)
                st.markdown("---")
                st.subheader("📸 نتایج آزمون همراه با احراز هویت تصویری دانش‌آموزان")
                selected_quiz_id = st.selectbox("انتخاب آزمون:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
                
                results_df = safe_read_sql("""
                    SELECT r.id, s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           r.score AS 'نمره درست', r.total_questions AS 'کل سوالات',
                           r.percentage AS 'درصد ٪', r.face_image, r.submitted_at AS 'زمان ثبت'
                    FROM quiz_results r
                    JOIN students s ON r.student_id = s.id
                    WHERE r.quiz_id = ? ORDER BY r.percentage DESC
                """, params=(selected_quiz_id,))
                    
                if not results_df.empty:
                    for idx, row in results_df.iterrows():
                        col_r1, col_r2, col_r3 = st.columns([2, 2, 2])
                        with col_r1:
                            st.markdown(f"**👤 دانش‌آموز:** {row['دانش‌آموز']}")
                            st.markdown(f"**📊 نمره:** {row['نمره درست']} از {row['کل سوالات']} ({row['درصد ٪']:.1f}٪)")
                            st.markdown(f"**🕒 زمان:** {row['زمان ثبت']}")
                        with col_r2:
                            if row['face_image']:
                                try:
                                    img_bytes = base64.b64decode(row['face_image'])
                                    st.image(img_bytes, caption=f"تصویر چهره ثبت‌شده: {row['دانش‌آموز']}", width=150)
                                except Exception:
                                    st.info("تصویر قابل بارگذاری نیست.")
                            else:
                                st.warning("تصویر چهره ثبت نشده است.")
                        st.markdown("---")
                else:
                    st.info("هنوز هیچ دانش‌آموزی در این آزمون شرکت نکرده است.")
            else:
                st.info("هنوز آزمونی ساخته نشده است.")

    # ---------------------------------------------------------
    # 5. Student Quiz Interface (4-LAYER SECURITY IMPLEMENTED)
    # ---------------------------------------------------------
    elif menu_choice == "📱 شرکت در آزمون آنلاین (دانش‌آموز)":
        st.header("📱 سامانه آنلاین شرکت در آزمون (ویژه دانش‌آموزان)")
        
        st.markdown("""
        <div class="security-badge">
            🔒 سامانه مجهز به احراز هویت چندلایه: رمز ۴ رقمی اختصاصی | ترتیب تصادفی سوالات | ثبت تصویر چهره | قفل خودکار آزمون
        </div>
        """, unsafe_allow_html=True)
        
        students_df = load_students()
        quizzes_df = safe_read_sql("SELECT id, title, subject, duration_minutes FROM quizzes")
            
        if students_df.empty or quizzes_df.empty:
            st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.selectbox("۱. نام و نام خانوادگی خود را انتخاب کنید:", students_df['full_name'].tolist())
            with col2:
                quiz_name = st.selectbox("۲. انتخاب آزمون:", quizzes_df['title'].tolist())
                
            selected_student_row = students_df[students_df['full_name'] == student_name].iloc[0]
            s_id = int(selected_student_row['id'])
            correct_pin = str(selected_student_row['pin_code'])
            q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
            
            # PIN AUTHENTICATION
            entered_pin = st.text_input("🔑 ۳. رمز ۴ رقمی اختصاصی خود را وارد کنید:", type="password", max_chars=4, key="st_pin_auth")
            
            if entered_pin:
                if entered_pin != correct_pin:
                    st.error("❌ رمز اختصاصی واردشده اشتباه است! لطفاً رمز ۴ رقمی صحیح خود را وارد کنید.")
                else:
                    st.success("✅ احراز هویت با موفقیت انجام شد.")
                    
                    # LAYER 3: CHECK IF ALREADY TAKEN (ONE-TIME LOCK)
                    with get_connection() as conn:
                        existing = conn.execute("SELECT id, percentage, face_image FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
                        
                    if existing:
                        st.warning(f"🔒 این آزمون قبلاً توسط شما ارسال شده و قفل گردیده است. امکان شرکت مجدد وجود ندارد.")
                        st.info(f"درصد کسب‌شده شما در این آزمون: {existing['percentage']:.1f}٪")
                        if existing['face_image']:
                            try:
                                img_bytes = base64.b64decode(existing['face_image'])
                                st.image(img_bytes, caption="تصویر چهره ثبت‌شده شما هنگام آزمون", width=160)
                            except Exception:
                                pass
                    else:
                        st.info(f"⏱️ زمان آزمون: {quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0]} دقیقه")
                        
                        # LAYER 2: RANDOM QUESTION SHUFFLING
                        with get_connection() as conn:
                            raw_questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                            
                        # Use deterministic seed per student and quiz so order remains stable across re-renders
                        q_list = list(raw_questions)
                        random.seed(s_id * 1000 + q_id)
                        random.shuffle(q_list)
                        
                        student_answers = {}
                        st.markdown("---")
                        
                        # LAYER 4: FACIAL PHOTO CAPTURE
                        st.subheader("📸 ۴. احراز هویت تصویری (گرفتن عکس چهره)")
                        st.write("لطفاً جهت ثبت آزمون، تصویر چهره خود را با دوربین ثبت کنید:")
                        camera_photo = st.camera_input("گرفتن عکس چهره برای تحویل آزمون", key="camera_quiz_capture")
                        
                        st.markdown("---")
                        st.subheader("📝 پاسخگویی به سوالات آزمون:")
                        
                        with st.form("student_quiz_form"):
                            for idx, q in enumerate(q_list):
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
                                
                            submit_quiz = st.form_submit_button("🏁 پایان آزمون و ارسال نهایی پاسخ‌ها")
                            
                            if submit_quiz:
                                if camera_photo is None:
                                    st.error("⚠️ ثبت تصویر چهره جهت احراز هویت و تحویل آزمون الزامی است. لطفاً دکمه 'Take Photo' را بزنید.")
                                else:
                                    correct_count = 0
                                    total = len(q_list)
                                    for q_id_key, (ans, correct) in student_answers.items():
                                        if ans == correct:
                                            correct_count += 1
                                            
                                    pct = (correct_count / total) * 100 if total > 0 else 0
                                    
                                    # Convert captured photo to base64
                                    bytes_data = camera_photo.getvalue()
                                    img_b64 = base64.b64encode(bytes_data).decode('utf-8')
                                    
                                    with get_connection() as conn:
                                        conn.execute(
                                            "INSERT INTO quiz_results (quiz_id, student_id, score, total_questions, percentage, face_image) VALUES (?, ?, ?, ?, ?, ?)",
                                            (q_id, s_id, correct_count, total, pct, img_b64)
                                        )
                                        conn.commit()
                                        
                                    st.balloons()
                                    st.success(f"🎉 آزمون با موفقیت ثبت و قفل گردید! نمره شما: {correct_count} از {total} (معادل {pct:.1f} درصد)")
                                    st.rerun()

    # ---------------------------------------------------------
    # 6. Dashboard & Portfolio
    # ---------------------------------------------------------
    elif menu_choice == "📊 پوشه کار و کارنامه جامع":
        st.header("📊 داشبورد تحلیلی و پوشه کار جامع دانش‌آموز")
        
        students_df = load_students()
        if students_df.empty:
            st.warning("اطلاعاتی برای نمایش وجود ندارد.")
        else:
            selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه:", students_df['full_name'].tolist())
            s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
            
            st.markdown(f"### 📄 کارنامه جامع و توصیفی: {selected_student}")
            
            col1, col2, col3 = st.columns(3)
            
            with get_connection() as conn:
                eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
                beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
                quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
                
            with col1: st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
            with col2: st.metric("تعداد موارد رفتاری ثبت‌شده:", beh_count)
            with col3: st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
                
            st.markdown("---")
            
            tab_d1, tab_d2, tab_d3 = st.tabs(["📝 ارزشیابی‌های درسی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها و احراز هویت"])
            
            with tab_d1:
                df_e = safe_read_sql("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", params=(s_id,))
                if not df_e.empty:
                    st.dataframe(df_e, use_container_width=True)
                else:
                    st.info("ارزشیابی درسی ثبت نشده است.")
                    
            with tab_d2:
                df_b = safe_read_sql("SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ' FROM behaviors WHERE student_id = ?", params=(s_id,))
                if not df_b.empty:
                    st.dataframe(df_b, use_container_width=True)
                else:
                    st.info("مورد رفتاری ثبت نشده است.")
                    
            with tab_d3:
                df_q = safe_read_sql("""
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره',
                           r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.face_image, r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, params=(s_id,))
                if not df_q.empty:
                    for idx, row in df_q.iterrows():
                        col_q1, col_q2 = st.columns([3, 1])
                        with col_q1:
                            st.markdown(f"**📌 {row['عنوان آزمون']} ({row['درس']})**")
                            st.markdown(f"نمره: {row['نمره']} از {row['کل سوالات']} ({row['درصد ٪']:.1f}٪) — زمان: {row['زمان']}")
                        with col_q2:
                            if row['face_image']:
                                try:
                                    img_bytes = base64.b64decode(row['face_image'])
                                    st.image(img_bytes, caption="تصویر چهره", width=120)
                                except Exception:
                                    pass
                        st.markdown("---")
                else:
                    st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")

