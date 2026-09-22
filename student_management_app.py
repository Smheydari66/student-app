import streamlit as st
import sqlite3
import pandas as pd
import datetime

# ---------------------------------------------------------
# Page Configuration & RTL Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه هوشمند مدیریت کلاس پنجم ابتدایی",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Comprehensive Custom CSS for High-Contrast, RTL, and Responsive Dropdown Menu
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    
    html, body, [class*="css"], div, span, button, input, select, textarea, label, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #0f172a !important; /* High contrast dark navy/slate for all standard text */
    }
    
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Main Header Styling */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3c72 50%, #2a5298 100%);
        color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        text-align: center !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .main-header h2, .main-header p {
        color: #ffffff !important;
    }

    /* Author Banner Card */
    .author-card {
        background-color: #ffffff;
        border: 2px solid #2a5298;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        margin: 15px 0 25px 0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .author-card h3 { color: #0f172a !important; font-weight: bold; }
    .author-card h4 { color: #1d4ed8 !important; font-weight: bold; }
    .author-card p { color: #334155 !important; font-weight: bold; }

    /* Feature Cards */
    .feature-box {
        background-color: #ffffff;
        padding: 16px 20px;
        border-radius: 12px;
        border-right: 6px solid #2a5298;
        margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .feature-box h4 { color: #1e3c72 !important; margin-bottom: 6px; font-weight: bold; }
    .feature-box p { color: #334155 !important; margin: 0; line-height: 1.6; }

    /* High Contrast Group Tags & Badges */
    .group-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
        margin: 4px;
    }
    .group-armaghan { background-color: #e0f2fe; color: #0369a1 !important; border: 1px solid #7dd3fc; }
    .group-dana { background-color: #dcfce7; color: #15803d !important; border: 1px solid #86efac; }
    .group-talash { background-color: #fef3c7; color: #b45309 !important; border: 1px solid #fde047; }
    .group-nokhbegan { background-color: #f3e8ff; color: #6b21a8 !important; border: 1px solid #d8b4fe; }
    .group-general { background-color: #f1f5f9; color: #334155 !important; border: 1px solid #cbd5e1; }

    /* Custom Input and Dropdown Menu Styling */
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label, .stRadio label {
        color: #0f172a !important;
        font-weight: bold !important;
        font-size: 1em !important;
    }

    /* Buttons Styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        color: #ffffff !important;
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1e3c72 0%, #0f172a 100%);
        color: #ffffff !important;
        transform: translateY(-1px);
    }

    /* Expander Header High Contrast Fix */
    .streamlit-expanderHeader {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        font-weight: bold !important;
        border-radius: 8px !important;
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
            group_name TEXT DEFAULT 'عمومی 📚',
            avatar TEXT DEFAULT '👨‍🎓',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Evaluations Table
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

        # Check and migrate columns if missing
        cursor.execute("PRAGMA table_info(students)")
        cols = [column[1] for column in cursor.fetchall()]
        if 'group_name' not in cols:
            cursor.execute("ALTER TABLE students ADD COLUMN group_name TEXT DEFAULT 'عمومی 📚'")
        if 'avatar' not in cols:
            cursor.execute("ALTER TABLE students ADD COLUMN avatar TEXT DEFAULT '👨‍🎓'")
        
        cursor.execute("PRAGMA table_info(questions)")
        q_cols = [column[1] for column in cursor.fetchall()]
        if 'explanation' not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT DEFAULT ''")
        conn.commit()

init_db()

# ---------------------------------------------------------
# Session State & Constants
# ---------------------------------------------------------
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

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
    "عمومی 📚",
    "گروه ارمغان 🚀",
    "گروه دانا 💡",
    "گروه تلاش 🌟",
    "گروه نخبگان 🏆"
]

STUDENT_AVATARS = ["👨‍🎓", "👦", "👧", "🚀", "💡", "🌟", "🏆"]

def load_students():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT id, avatar, first_name || ' ' || last_name AS full_name, first_name, last_name,
                       national_id, parent_phone, group_name, notes 
                FROM students ORDER BY last_name ASC
            """, conn)
        return df
    except Exception:
        return pd.DataFrame(columns=['id', 'avatar', 'full_name', 'first_name', 'last_name', 'national_id', 'parent_phone', 'group_name', 'notes'])

# ---------------------------------------------------------
# Main App Header
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>ارزشیابی کیفی-توصیفی، مدیریت گروه‌های کلاسی، آزمون‌ساز آنلاین با تصحیح آنی و کارنامه تحلیلی</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Top Navigation & Authentication Header Bar
# ---------------------------------------------------------
nav_col1, nav_col2 = st.columns([3, 1.2])

with nav_col1:
    menu_choice = st.selectbox(
        "📌 منوی اصلی کشویی (جهت جابه‌جایی بین بخش‌ها کلیک کنید):",
        [
            "🏠 صفحه اصلی و معرفی برنامه",
            "📱 شرکت در آزمون آنلاین (دانش‌آموز)",
            "📊 کارنامه جامع و نمودار رشد (دانش‌آموز/اولیا)",
            "👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (معلم)",
            "📝 ارزشیابی کیفی-توصیفی (معلم)",
            "🌟 ثبت رفتار و انضباط (معلم)",
            "✏️ آزمون‌ساز آنلاین و تصحیح (معلم)"
        ],
        index=0
    )

with nav_col2:
    with st.expander("🔑 پنل ورود/خروج آموزگار", expanded=False):
        if st.session_state['is_teacher_logged_in']:
            st.success("🟢 آموزگار وارد شده است")
            if st.button("🚪 خروج از حساب معلم"):
                st.session_state['is_teacher_logged_in'] = False
                st.rerun()
        else:
            pwd_input = st.text_input("رمز عبور معلم را وارد کنید:", type="password", key="login_pwd")
            if st.button("ورود به پنل آموزگار"):
                if pwd_input in ["1234", "مطهری", "1357"]:
                    st.session_state['is_teacher_logged_in'] = True
                    st.success("🎉 ورود با موفقیت انجام شد!")
                    st.rerun()
                else:
                    st.error("❌ رمز عبور اشتباه است.")
            st.caption("💡 *رمز پیش‌فرض: 1234*")

def check_teacher_auth():
    if not st.session_state['is_teacher_logged_in']:
        st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از کادر '🔑 پنل ورود/خروج آموزگار' در بالای صفحه رمز عبور معلم را وارد کنید (رمز پیش‌فرض: 1234).")
        st.stop()

st.markdown("---")

# ---------------------------------------------------------
# 0. Landing Page / About
# ---------------------------------------------------------
if menu_choice == "🏠 صفحه اصلی و معرفی برنامه":
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="author-card">
        <h3>🌱 طراح و توسعه‌دهنده سامانه</h3>
        <h4>سید موسی حیدری</h4>
        <p>آموزگار پایه پنجم ابتدایی دبستان شهید مطهری مهران</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 اهداف و ویژگی‌های برجسته برنامه:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="feature-box">
            <h4>1️⃣ ارزشیابی کیفی-توصیفی استاندارد</h4>
            <p>ثبت دقیق سطح عملکرد دانش‌آموزان در تمامی ۷ عنوان درسی پایه پنجم (ریاضی، علوم، فارسی، نگارش، مطالعات، هدیه‌ها و قرآن) همراه با بازخوردهای توصیفی سازنده.</p>
        </div>
        <div class="feature-box">
            <h4>2️⃣ آزمون‌ساز آنلاین با تصحیح خودکار</h4>
            <p>طراحی آزمون‌های ۴ گزینه‌ای آنلاین با زمان‌بندی مشخص، تصحیح آنی پاسخ‌ها، محاسبه نمره و درصد و ارائه پاسخ‌نامه تشریحی.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown("""
        <div class="feature-box">
            <h4>3️⃣ پایش رفتاری و گروه‌بندی کلاسی</h4>
            <p>سازمان‌دهی دانش‌آموزان در گروه‌های آموزشی (ارمغان، دانا، تلاش، نخبگان) و ثبت مشاهدات رفتاری و انضباطی جهت ارتقای تعامل با اولیا.</p>
        </div>
        <div class="feature-box">
            <h4>4️⃣ کارنامه جامع و نمودار رشد تحصیلی</h4>
            <p>ارائه داشبورد تحلیلی یکپارچه، نمودار رشد درصدی آزمون‌ها و دریافت خروجی اکسل/CSV برای بایگانی در پوشه کار فیزیکی.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.info("💡 **راهنمای استفاده:** جهت شروع کار با سامانه، از **«منوی اصلی کشویی»** در بالای صفحه بخش مورد نظر خود را انتخاب کنید.")

# ---------------------------------------------------------
# 1. Student Online Quiz Interface (Public Access)
# ---------------------------------------------------------
elif menu_choice == "📱 شرکت در آزمون آنلاین (دانش‌آموز)":
    st.header("📱 سامانه شرکت در آزمون آنلاین دانش‌آموزان")
    
    students_df = load_students()
    with get_connection() as conn:
        quizzes_df = pd.read_sql_query("SELECT id, title, subject, duration_minutes FROM quizzes ORDER BY id DESC", conn)
        
    if students_df.empty or quizzes_df.empty:
        st.warning("در حال حاضر آزمون فعال یا دانش‌آموزی در سیستم تعریف نشده است.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.selectbox("نام دانش‌آموز (خود را انتخاب کنید):", students_df['full_name'].tolist())
        with col2:
            quiz_name = st.selectbox("انتخاب آزمون فعال:", quizzes_df['title'].tolist())
            
        s_id = int(students_df[students_df['full_name'] == student_name]['id'].values[0])
        q_id = int(quizzes_df[quizzes_df['title'] == quiz_name]['id'].values[0])
        
        # Check if taken
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage, score, total_questions FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"🎉 شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده: {existing['percentage']:.1f}٪ ({existing['score']} درست از {existing['total_questions']} سوال)")
            
            # Show Answer Key & Explanations
            with st.expander("🔍 مشاهده پاسخ‌نامه تشریحی سوالات", expanded=True):
                with get_connection() as conn:
                    q_list = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(q_list):
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    st.markdown(f"- گزینه صحیح: **گزینه {q['correct_option']}**")
                    if q['explanation']:
                        st.info(f"💡 **نکته آموزشی / پاسخ تشریحی:** {q['explanation']}")
                    st.markdown("---")
        else:
            quiz_duration = int(quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0])
            st.info(f"⏱️ زمان پیشنهادی آزمون: **{quiz_duration} دقیقه** | لطفاً پاسخ‌ها را با دقت انتخاب کرده و در پایان دکمه ثبت نهایی را بزنید.")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
            student_answers = {}
            st.markdown("---")
            with st.form("student_quiz_form"):
                for idx, q in enumerate(questions):
                    st.markdown(f"##### 📌 سوال {idx+1}: {q['question_text']}")
                    options = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    user_ans = st.radio(
                        f"پاسخ سوال {idx+1}:",
                        options=[1, 2, 3, 4],
                        format_func=lambda x, opts=options: f"گزینه {x}: {opts[x-1]}",
                        key=f"sq_{q['id']}"
                    )
                    student_answers[q['id']] = (user_ans, q['correct_option'])
                    st.markdown("---")
                    
                submit_quiz = st.form_submit_button("🏁 پایان آزمون و دریافت نتیجه آنی")
                
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
                    st.success(f"🎉 آزمون با موفقیت ثبت شد! نمره شما: **{correct_count} از {total}** (معادل **{pct:.1f} درصد**)")
                    st.rerun()

# ---------------------------------------------------------
# 2. Comprehensive Student Dashboard & Growth Chart
# ---------------------------------------------------------
elif menu_choice == "📊 کارنامه جامع و نمودار رشد (دانش‌آموز/اولیا)":
    st.header("📊 کارنامه جامع و نمودار پیشرفت تحصیلی دانش‌آموز")
    
    students_df = load_students()
    if students_df.empty:
        st.warning("اطلاعاتی برای نمایش وجود ندارد.")
    else:
        selected_student = st.selectbox("انتخاب دانش‌آموز جهت مشاهده کارنامه جامع:", students_df['full_name'].tolist())
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        s_row = students_df[students_df['id'] == s_id].iloc[0]
        
        st.markdown(f"### {s_row['avatar']} کارنامه و سوابق تحصیلی: **{selected_student}** | گروه: **{s_row['group_name']}**")
        
        # Calculate Metrics
        with get_connection() as conn:
            eval_count = conn.execute("SELECT COUNT(*) FROM evaluations WHERE student_id = ?", (s_id,)).fetchone()[0]
            beh_count = conn.execute("SELECT COUNT(*) FROM behaviors WHERE student_id = ?", (s_id,)).fetchone()[0]
            quiz_avg = conn.execute("SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?", (s_id,)).fetchone()[0]
            
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("تعداد ارزشیابی‌های درسی:", eval_count)
        with c2:
            st.metric("تعداد موارد رفتاری ثبت‌شده:", beh_count)
        with c3:
            st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg else "بدون آزمون")
            
        # Digital Badges / Medals
        st.subheader("🏅 نشان‌ها و مدال‌های افتخار دانش‌آموز")
        badges_html = ""
        if quiz_avg and quiz_avg >= 90:
            badges_html += "<span class='group-badge group-nokhbegan'>🏆 مدال افتخار نخبگان (میانگین بالایی ۹۰٪)</span> "
        if quiz_avg and quiz_avg >= 75:
            badges_html += "<span class='group-badge group-armaghan'>🌟 نشان تلاش و موفقیت ممتاز</span> "
        if beh_count > 0:
            badges_html += "<span class='group-badge group-dana'>🟢 الگوی انضباط و اخلاق کلاسی</span> "
        badges_html += f"<span class='group-badge group-talash'>🚀 عضو فعال {s_row['group_name']}</span>"
        st.markdown(badges_html, unsafe_allow_html=True)
        st.markdown("---")
        
        tab_d1, tab_d2, tab_d3, tab_d4 = st.tabs(["📝 ارزشیابی‌های درسی", "🌟 سوابق رفتاری", "📊 کارنامه آزمون‌ها", "📈 نمودار پیشرفت تحصیلی"])
        
        with tab_d1:
            with get_connection() as conn:
                df_e = pd.read_sql_query("SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'توصیف عملکرد معلم', eval_date AS 'تاریخ' FROM evaluations WHERE student_id = ?", conn, params=(s_id,))
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
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره (تعداد درست)', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id WHERE r.student_id = ? ORDER BY r.id DESC
                """, conn, params=(s_id,))
            if not df_q.empty:
                st.dataframe(df_q, use_container_width=True)
                csv_data = df_q.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 دانلود فایل کارنامه آزمون‌ها (فرمت CSV/Excel)", csv_data, f"quiz_report_{s_id}.csv", "text/csv")
            else:
                st.info("نتیجه آزمونی برای این دانش‌آموز ثبت نشده است.")
                
        with tab_d4:
            st.subheader("📈 نمودار رشد درصدی آزمون‌ها")
            with get_connection() as conn:
                df_chart = pd.read_sql_query("""
                    SELECT q.title AS 'آزمون', r.percentage AS 'درصد'
                    FROM quiz_results r JOIN quizzes q ON r.quiz_id = q.id 
                    WHERE r.student_id = ? ORDER BY r.id ASC
                """, conn, params=(s_id,))
            if not df_chart.empty:
                st.line_chart(df_chart.set_index('آزمون'))
            else:
                st.info("جهت رسم نمودار پیشرفت تحصیلی، شرکت در حداقل یک آزمون آنلاین لازم است.")

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
            search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            if search_query:
                students_df = students_df[
                    students_df['full_name'].str.contains(search_query, na=False) | 
                    students_df['national_id'].str.contains(search_query, na=False)
                ]
            
            st.dataframe(students_df.rename(columns={
                'id': 'شناسه',
                'avatar': 'آیکون',
                'full_name': 'نام و نام خانوادگی',
                'national_id': 'کد ملی',
                'parent_phone': 'شماره اولیا',
                'group_name': 'گروه کلاسی',
                'notes': 'توضیحات'
            }), use_container_width=True)
            
            st.subheader("🗑️ حذف پرونده دانش‌آموز")
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
                national_id = st.text_input("کد ملی دانش‌آموز (۱۰ رقم):")
                selected_group = st.selectbox("انتخاب گروه کلاسی:", CLASS_GROUPS)
            with col2:
                last_name = st.text_input("نام خانوادگی:")
                parent_phone = st.text_input("شماره همراه اولیا:")
                selected_avatar = st.selectbox("انتخاب آیکون/آواتار دانش‌آموز:", STUDENT_AVATARS)
            
            notes = st.text_area("توضیحات ویژه یا ملاحظات آموزشی/پزشکی:")
            submit_btn = st.form_submit_button("ثبت دانش‌آموز جدید")
            
            if submit_btn:
                if first_name and last_name:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                """INSERT INTO students (first_name, last_name, national_id, parent_phone, group_name, avatar, notes) 
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (first_name, last_name, national_id, parent_phone, selected_group, selected_avatar, notes)
                            )
                            conn.commit()
                        st.success(f"دانش‌آموز {first_name} {last_name} با موفقیت در {selected_group} ثبت شد.")
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

        st.markdown("---")
        st.subheader("🔍 سوابق ارزشیابی دانش‌آموز انتخاب‌شده")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            eval_history = pd.read_sql_query("""
                SELECT subject AS 'درس', level AS 'سطح توصیفی', feedback AS 'بازخورد معلم', eval_date AS 'تاریخ'
                FROM evaluations WHERE student_id = ? ORDER BY eval_date DESC
            """, conn, params=(s_id,))
        
        if not eval_history.empty:
            st.dataframe(eval_history, use_container_width=True)
        else:
            st.info("هنوز ارزشیابی برای این دانش‌آموز ثبت نشده است.")

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
            title = st.text_input("عنوان رفتار (مثلاً: همکاری در گروه، دقت در تکالیف):")
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
            
        st.markdown("---")
        st.subheader(f"📋 گزارش رفتار و انضباط {selected_student}")
        s_id = int(students_df[students_df['full_name'] == selected_student]['id'].values[0])
        with get_connection() as conn:
            b_history = pd.read_sql_query("""
                SELECT behavior_type AS 'نوع', title AS 'عنوان', description AS 'شرح', log_date AS 'تاریخ'
                FROM behaviors WHERE student_id = ? ORDER BY log_date DESC
            """, conn, params=(s_id,))
            
        if not b_history.empty:
            st.dataframe(b_history, use_container_width=True)
        else:
            st.info("هیچ مورد رفتاری ثبت نشده است.")

# ---------------------------------------------------------
# 6. Online Quiz Creator & Explanations (Teacher Only)
# ---------------------------------------------------------
elif menu_choice == "✏️ آزمون‌ساز آنلاین و تصحیح (معلم)":
    check_teacher_auth()
    st.header("✏️ آزمون‌ساز آنلاین (طراحی، مدیریت و تحلیل آزمون)")
    
    tab_q1, tab_q2 = st.tabs(["➕ ساخت آزمون جدید و طراحی سوالات", "📊 لیست آزمون‌ها و نتایج کلاسی"])
    
    with tab_q1:
        st.subheader("۱. مشخصات کلی آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون (مثلاً: آزمونک فصل اول ریاضی - کسرها):")
        with col2:
            quiz_subject = st.selectbox("درس مربوطه:", FIFTH_GRADE_SUBJECTS)
        with col3:
            duration = st.number_input("زمان آزمون (دقیقه):", min_value=5, max_value=120, value=15)
            
        num_questions = st.number_input("تعداد سوالات ۴ گزینه‌ای:", min_value=1, max_value=20, value=2)
        
        st.markdown("---")
        st.subheader("۲. ورود سوالات، کلید تصحیح و پاسخ‌نامه تشریحی")
        
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
            explanation = st.text_area(f"نکته آموزشی / پاسخ تشریحی برای سوال {i+1} (اختیاری):", key=f"exp_{i}")
            questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt, explanation))
            st.markdown("---")
            
        if st.button("🚀 انتشار و ذخیره آزمون"):
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
                st.success(f"آزمون '{quiz_title}' با موفقیت ساخته شد و آماده برگزاری است!")
            else:
                st.error("لطفاً عنوان آزمون و متن تمامی سوالات را وارد کنید.")

    with tab_q2:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes ORDER BY id DESC", conn)
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
            st.subheader("📈 مشاهده نتایج کلاسی و کارنامه آزمون")
            selected_quiz_id = st.selectbox("انتخاب آزمون برای مشاهده نتایج:", quizzes_df['id'].tolist(), format_func=lambda x: quizzes_df[quizzes_df['id'] == x]['عنوان'].values[0])
            
            with get_connection() as conn:
                results_df = pd.read_sql_query("""
                    SELECT s.first_name || ' ' || s.last_name AS 'دانش‌آموز',
                           s.group_name AS 'گروه کلاسی',
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
                csv_data = results_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 دانلود فایل اکسل/CSV نتایج این آزمون", csv_data, f"quiz_results_{selected_quiz_id}.csv", "text/csv")
            else:
                st.info("هنوز هیچ دانش‌آموزی در این آزمون شرکت نکرده است.")
        else:
            st.info("هنوز آزمونی ساخته نشده است.")

