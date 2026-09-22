import streamlit as st
import sqlite3
import pandas as pd
import datetime

# ---------------------------------------------------------
# Page Configuration & RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس و آزمون آنلاین - پایه پنجم",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High Contrast Persian / RTL CSS
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
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3c72 50%, #2a5298 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    }
    
    .main-header h2, .main-header p {
        color: #ffffff !important;
        word-break: keep-all;
    }

    /* Cards & Container Styling */
    .author-card {
        background-color: #ffffff;
        border: 2px solid #0284c7;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.08);
    }
    
    .feature-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        border-right: 6px solid #0284c7;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .badge-card {
        background-color: #f0fdf4;
        border: 2px dashed #16a34a;
        padding: 12px;
        border-radius: 12px;
        text-align: center;
        margin: 8px;
    }

    .badge-card-gold {
        background-color: #fefce8;
        border: 2px solid #eab308;
        padding: 12px;
        border-radius: 12px;
        text-align: center;
        margin: 8px;
    }

    /* High Contrast Buttons */
    .stButton>button {
        width: 100%;
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: bold !important;
        border: none !important;
        font-size: 1.05em !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        background-color: #0369a1 !important;
        color: #ffffff !important;
    }
    
    /* Input labels high contrast */
    label, .stMarkdown {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization (Teacher Authentication)
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از بالای صفحه روی دکمه '🔑 ورود معلم' کلیک کرده و رمز عبور را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

# ---------------------------------------------------------
# Database Initialization & Schema Upgrades
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
            group_name TEXT DEFAULT 'گروه عمومی',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Ensure group_name column exists if upgraded from older DB
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN group_name TEXT DEFAULT 'گروه عمومی'")
        except sqlite3.OperationalError:
            pass # Column already exists
        
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
    "گروه عمومی 📚"
]

def load_students():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS full_name, national_id, parent_phone, group_name, notes FROM students", conn)
        return df
    except Exception:
        init_db()
        return pd.DataFrame()

# ---------------------------------------------------------
# Header Section
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2 style="margin: 0; padding-bottom: 8px;">🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم</h2>
    <p style="margin: 0; font-size: 1.05em; opacity: 0.95;">دبستان شهید مطهری مهران - ارزشیابی توصیفی، تحلیل عملکرد، آزمون‌ساز و پرونده انضباطی</p>
</div>
""", unsafe_allow_html=True)

# Top Authentication Status Bar
auth_col1, auth_col2 = st.columns([3, 1])
with auth_col2:
    if st.session_state['is_teacher_logged_in']:
        if st.button("🔒 خروج از مدیریت معلم"):
            st.session_state['is_teacher_logged_in'] = False
            st.rerun()
    else:
        with st.popover("🔑 ورود معلم"):
            pwd = st.text_input("رمز عبور معلم:", type="password")
            if st.button("تایید ورود"):
                if pwd == "1234" or pwd == "مطهری":
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("ورود موفقیت‌آمیز معلم")
                    st.rerun()
                else:
                    st.error("رمز عبور اشتباه است (رمز پیش‌فرض: 1234)")

# ---------------------------------------------------------
# Responsive Navigation Menu
# ---------------------------------------------------------
menu_choice = st.radio(
    "📌 منوی اصلی سامانه:",
    [
        "🏠 صفحه اصلی",
        "📱 شرکت در آزمون (دانش‌آموز)",
        "📊 کارنامه و نمودار رشد",
        "👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (معلم)",
        "📝 ارزشیابی کیفی-توصیفی (معلم)",
        "🌟 ثبت رفتار و انضباط (معلم)",
        "✏️ آزمون‌ساز آنلاین (معلم)"
    ],
    horizontal=True
)

st.markdown("---")

# ---------------------------------------------------------
# 0. Landing Page / About
# ---------------------------------------------------------
if menu_choice == "🏠 صفحه اصلی":
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
        
        st.markdown("""
        <div class="feature-card">
            <h4 style="color: #0284c7; margin-top: 0;">1️⃣ ارزشیابی کیفی-توصیفی و پرونده تحصیلی</h4>
            <p>ثبت دقیق سطوح عملکرد در تمامی ۷ درس اصلی پایه پنجم همراه با امکان خروجی فایل برای پوشه کار دانش‌آموز.</p>
        </div>
        
        <div class="feature-card">
            <h4 style="color: #0284c7; margin-top: 0;">2️⃣ آزمون‌ساز آنلاین و تحلیل هوشمند</h4>
            <p>طراحی آزمون با زمان‌بندی، تصحیح آنی، نمایش پاسخ‌نامه تشریحی و اعطای مدال‌های افتخار دیجیتال به دانش‌آموزان.</p>
        </div>
        
        <div class="feature-card">
            <h4 style="color: #0284c7; margin-top: 0;">3️⃣ گروه‌بندی کلاسی و نمودار رشد اولیا</h4>
            <p>سازماندهی دانش‌آموزان در گروه‌های تیمی و ارائه نمودار خطی پیشرفت تحصیلی برای اطلاع لحظه‌ای خانواده‌ها.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown("""
        <div class="author-card">
            <h3 style="color: #0f172a; margin-top:0;">🌱 طراح و توسعه‌دهنده</h3>
            <h4 style="color: #0284c7; margin-bottom: 5px;">سید موسی حیدری</h4>
            <p style="font-size: 1.05em; font-weight: bold; color: #334155;"> آموزگار پایه پنجم ابتدایی<br>دبستان شهید مطهری مهران</p>
            <hr style="border-color: #e2e8f0;">
            <p style="font-size: 0.9em; color: #64748b;">طراحی‌شده با پایتون و استریم‌لیت جهت ارتقای هوشمندسازی مدارس</p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. Student Online Quiz Interface & Gamification & Detailed Answer Key
# ---------------------------------------------------------
elif menu_choice == "📱 شرکت در آزمون (دانش‌آموز)":
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with c2:
            quiz_name = st.selectbox("انتخاب آزمون:", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        # Check if already taken
        with get_connection() as conn:
            existing = conn.execute("SELECT id, score, total_questions, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. نمره شما: {existing['score']} از {existing['total_questions']} (معادل {existing['percentage']:.1f}٪)")
            
            # Show Answer Key review
            with st.expander("🔍 مشاهده پاسخ‌نامه تشریحی و راهنمای سوالات"):
                with get_connection() as conn:
                    questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(questions):
                    opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    st.info(f"✅ گزینه صحیح: گزینه {q['correct_option']} ({opts[q['correct_option']-1]})")
                    if q['explanation']:
                        st.caption(f"💡 توضیحات راهنما: {q['explanation']}")
                    st.markdown("---")
        else:
            quiz_duration = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پیشنهادی آزمون: {quiz_duration} دقیقه")
            
            # Fetch Questions
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_answers = {}
            st.markdown("---")
            with st.form("student_quiz_form"):
                for idx, q in enumerate(questions):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    user_ans = st.radio(
                        f"پاسخ شما برای سوال {idx+1}:",
                        options=[1, 2, 3, 4],
                        format_func=lambda x: f"گزینه {x}: {options[x-1]}",
                        key=f"sq_{q['id']}"
                    )
                    student_answers[q['id']] = (user_ans, q['correct_option'], q['question_text'], options, q['explanation'])
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و دریافت نتیجه آنی")
                
                if submit_quiz:
                    correct_count = 0
                    total = len(questions)
                    for q_id_key, item in student_answers.items():
                        ans, correct = item[0], item[1]
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
                    
                    # Award Digital Badges
                    if pct == 100:
                        st.markdown("""
                        <div class="badge-card-gold">
                            <h3>🏆 مدال افتخار نخبگان (درصد ۱۰۰٪)</h3>
                            <p>آفرین به هوش و دقت شما! شما عملکردی بی‌نظیر و کامل داشتید.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif pct >= 80:
                        st.markdown("""
                        <div class="badge-card">
                            <h3>🌟 نشان تلاش و موفقیت ممتاز</h3>
                            <p>عملکرد بسیار عالی! شما به اکثر سوالات پاسخ درست دادید.</p>
                        </div>
                        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Dashboard, Growth Line Chart & Student Badges
# ---------------------------------------------------------
elif menu_choice == "📊 کارنامه و نمودار رشد":
    st.header("📊 کارنامه جامع تحصیلی و نمودار پیشرفت دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی برای نمایش وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه جامع:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['id'] == s_id].iloc[0]['id']) if 's_id' in locals() else int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        student_row = students_df[students_df['id'] == s_id].iloc[0]
        
        st.markdown(f"### 📄 کارنامه جامع و توصیفی: **{selected_student}** (عضو {student_row['group_name']})")
        
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
        
        # Badges section for student
        st.subheader("🏅 مدال‌ها و نشان‌های افتخار کسب‌شده:")
        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            if quiz_avg and quiz_avg >= 90:
                st.markdown("<div class='badge-card-gold'>🌟 **قهرمان آزمون‌های کلاسی**</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='badge-card'>🎯 **دانش‌آموز کوشا**</div>", unsafe_allow_html=True)
        with b_col2:
            if beh_count >= 2:
                st.markdown("<div class='badge-card-gold'>🏆 **الگوی انضباط و اخلاق**</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='badge-card'>🌱 **همیار منظم کلاس**</div>", unsafe_allow_html=True)
        with b_col3:
            st.markdown(f"<div class='badge-card'>🚀 **عضو فعال {student_row['group_name']}**</div>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Tabs for details
        tab_d1, tab_d2, tab_d3, tab_d4 = st.tabs(["📝 ارزشیابی‌های درسی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها", "📈 نمودار پیشرفت تحصیلی"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = pd.read_sql_query("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
            if not df_e.empty:
                st.dataframe(df_e, use_container_width=True)
                csv = df_e.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 دانلود فایل کارنامه توصیفی (CSV/Excel)", csv, f"evaluations_{selected_student}.csv", "text/csv")
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
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ?
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
                csv_q = df_q.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 دانلود سوابق آزمون‌ها (CSV)", csv_q, f"quizzes_{selected_student}.csv", "text/csv")
            else:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")
                
        with tab_d4:
            st.subheader("📈 نمودار رشد و روند درصدی آزمون‌ها")
            with get_connection() as conn:
                df_chart = pd.read_sql_query("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
            if not df_chart.empty:
                st.line_chart(df_chart.set_index('آزمون'))
            else:
                st.info("جهت رسم نمودار رشد، شرکت در حداقل یک آزمون لازم است.")

# ---------------------------------------------------------
# 3. Student Management & Grouping (Teacher Only)
# ---------------------------------------------------------
elif menu_choice == "👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (معلم)":
    check_teacher_auth()
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی")
    
    tab1, tab2 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "➕ ثبت دانش‌آموز جدید"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            st.dataframe(students_df.rename(columns={
                'id': 'شناسه',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره همراه اولیا',
                'group_name': 'گروه کلاسی',
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
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است.")

    with tab2:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("نام:")
                national_id = st.text_input("کد ملی دانش‌آموز:")
                group_name = st.selectbox("انتخاب گروه کلاسی:", CLASS_GROUPS)
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا:")
            
            notes = st.text_area("توضیحات ویژه یا ملاحظات آموزشی:")
            submit_btn = st.form_submit_button("ثبت دانش‌آموز")
            
            if submit_btn:
                if first_name and last_name:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO students (first_name, last_name, national_id, parent_phone, group_name, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                (first_name, last_name, national_id, parent_phone, group_name, notes)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} با موفقیت در {group_name} ثبت شد.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("کد ملی وارد شده تکراری است.")
                else:
                    st.warning("لطفاً نام و نام خانوادگی را وارد کنید.")

# ---------------------------------------------------------
# 4. Qualitative Evaluation (Teacher Only)
# ---------------------------------------------------------
elif menu_choice == "📝 ارزشیابی کیفی-توصیفی (معلم)":
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
            st.success(f"ارزشیابی {selected_subject} برای {selected_student} ثبت شد.")

# ---------------------------------------------------------
# 5. Behavior Tracking (Teacher Only)
# ---------------------------------------------------------
elif menu_choice == "🌟 ثبت رفتار و انضباط (معلم)":
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
            title = st.text_input("عنوان رفتار (مثلاً: همکاری در گروه، تاخیر ورود):")
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
# 6. Online Quiz Creator (Teacher Only)
# ---------------------------------------------------------
elif menu_choice == "✏️ آزمون‌ساز آنلاین (معلم)":
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و مدیریت آزمون)")
    
    tab_q1, tab_q2 = st.tabs(["➕ ساخت آزمون جدید و پاسخ‌نامه تشریحی", "📊 لیست آزمون‌ها و نتایج"])
    
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
        st.subheader("۲. ورود سوالات، کلید و راهنمای تشریحی")
        
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
            
            c_opt1, c_opt2 = st.columns([1, 2])
            with c_opt1:
                correct_opt = st.selectbox(f"گزینه صحیح برای سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
            with c_opt2:
                explanation = st.text_input(f"توضیحات راهنما / پاسخ‌نامه تشریحی (سوال {i+1}):", key=f"exp_{i}")
                
            questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt, explanation))
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
                            """INSERT INTO questions (quiz_id, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6])
                        )
                    conn.commit()
                st.success(f"آزمون '{quiz_title}' با پاسخ‌نامه تشریحی با موفقیت ساخته شد!")
            else:
                st.error("لطفاً عنوان آزمون و متن تمامی سوالات را وارد کنید.")

    with tab_q2:
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

