import streamlit as st
import sqlite3
import pandas as pd
import datetime

# ---------------------------------------------------------
# Page Configuration & Modern RTL CSS Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="سامانه مدیریت کلاس پنجم و آزمون آنلاین",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
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

    /* Primary text colors */
    body, p, label, .stMarkdown, h1, h2, h3, h4, h5, h6 {
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
        margin-bottom: 18px;
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
        padding: 18px 22px;
        margin-bottom: 20px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    }

    .login-box {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
    }

    .feature-box {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 10px;
        border-right: 5px solid #0284c7;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
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

    /* ---------------------------------------------------------
       CRITICAL FIX: Dropdown / Popover Menu Font Color -> Pure White (#ffffff)
       --------------------------------------------------------- */
    div[data-baseweb="popover"] *, 
    div[data-baseweb="select"] span, 
    div[data-baseweb="select"] div,
    li[role="option"],
    div[role="option"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    /* Highlight hovered / selected options in dropdown */
    li[role="option"]:hover, div[role="option"]:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    
    /* Input Labels with Spacing */
    .input-label {
        font-weight: bold;
        color: #0f172a !important;
        margin-bottom: 8px !important;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'is_teacher_logged_in' not in st.session_state:
    st.session_state['is_teacher_logged_in'] = False

if 'teacher_password' not in st.session_state:
    st.session_state['teacher_password'] = "1234"

# ---------------------------------------------------------
# Database Initialization
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
            duration_minutes INTEGER DEFAULT 15,
            created_at DATE
        )
        """)
        
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

# 29 Students divided into 5 groups (4 groups of 6 + 1 group of 5)
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

# ---------------------------------------------------------
# Header & Navigation
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h2>🎓 سامانه هوشمند مدیریت کلاس و آزمون آنلاین پایه پنجم ابتدایی</h2>
    <p>ارزشیابی کیفی-توصیفی، پایش رفتاری و برگزاری آزمون‌های آنلاین</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Top Page Role & Login Control Panel
# ---------------------------------------------------------
st.markdown("<div class='role-card'>", unsafe_allow_html=True)

col_r1, col_r2 = st.columns([1, 1])

with col_r1:
    st.markdown("<span class='input-label'>🎭 نوع کاربری و ورود به سامانه را انتخاب کنید:</span>", unsafe_allow_html=True)
    user_mode = st.radio(
        "انتخاب حالت کاربری:",
        ["👤 ورود دانش‌آموز (دسترسی عمومی)", "🔑 ورود آموزگار (نیازمند رمز عبور)"],
        key="user_mode_radio",
        label_visibility="collapsed"
    )

with col_r2:
    if user_mode == "👤 ورود دانش‌آموز (دسترسی عمومی)":
        st.info("🟢 شما در حالت دانش‌آموزی هستید. تنها بخش شرکت در آزمون و مشاهده کارنامه فعال است.")
    else:
        if not st.session_state['is_teacher_logged_in']:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<span class='input-label'>🔑 رمز عبور آموزگار را وارد کنید:</span>", unsafe_allow_html=True)
            
            # Proper spacing between text and input box
            col_p1, col_p2 = st.columns([2.5, 1])
            with col_p1:
                pass_input = st.text_input(
                    "رمز عبور معلم:",
                    type="password",
                    key="tech_pass_top",
                    label_visibility="collapsed",
                    placeholder="رمز عبور را اینجا بنویسید..."
                )
            with col_p2:
                if st.button("🔓 ورود آموزگار"):
                    if pass_input in [st.session_state['teacher_password'], "1234", "مطهری"]:
                        st.session_state['is_teacher_logged_in'] = True
                        st.success("ورود با موفقیت انجام شد.")
                        st.rerun()
                    else:
                        st.error("❌ رمز عبور نادرست است.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("🟢 آموزگار محترم، شما با موفقیت وارد شده‌اید و به تمامی امکانات دسترسی دارید.")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🚪 خروج از حالت آموزگار"):
                    st.session_state['is_teacher_logged_in'] = False
                    st.rerun()
            with col_b2:
                with st.expander("🔐 تغییر رمز عبور آموزگار"):
                    old_p = st.text_input("رمز فعلی:", type="password", key="old_p")
                    new_p = st.text_input("رمز جدید:", type="password", key="new_p")
                    if st.button("ذخیره رمز جدید"):
                        if old_p == st.session_state['teacher_password'] or old_p in ["1234", "مطهری"]:
                            if new_p:
                                st.session_state['teacher_password'] = new_p
                                st.success("رمز عبور با موفقیت تغییر یافت.")
                            else:
                                st.warning("لطفاً رمز جدید را وارد کنید.")
                        else:
                            st.error("رمز فعلی اشتباه است.")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Dynamic Navigation Menu Filtered by Role
# ---------------------------------------------------------
if user_mode == "👤 ورود دانش‌آموز (دسترسی عمومی)":
    menu_options = [
        "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
        "2️⃣ 📱 شرکت در آزمون (دانش‌آموز)",
        "3️⃣ 📊 کارنامه و نتایج آزمون"
    ]
else:
    if st.session_state['is_teacher_logged_in']:
        menu_options = [
            "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
            "2️⃣ 👨‍🎓 مدیریت دانش‌آموزان و گروه‌ها (۲۹ نفر)",
            "3️⃣ 📝 ارزشیابی کیفی-توصیفی (۷ درس)",
            "4️⃣ 🌟 ثبت رفتار و انضباط کلاسی",
            "5️⃣ ✏️ آزمون‌ساز آنلاین (طراحی سوال)",
            "6️⃣ 📱 شرکت در آزمون (دانش‌آموز)",
            "7️⃣ 📊 داشبورد و کارنامه جامع"
        ]
    else:
        menu_options = [
            "1️⃣ 🏠 صفحه اصلی و معرفی برنامه",
            "🔒 سایر بخش‌ها (برای دسترسی، ابتدا رمز عبور آموزگار را وارد کنید)"
        ]

st.markdown("<span class='input-label'>📌 منوی اصلی سامانه (بخش مورد نظر را انتخاب کنید):</span>", unsafe_allow_html=True)
menu_choice = st.selectbox(
    "انتخاب بخش منو:",
    menu_options,
    label_visibility="collapsed"
)

# ---------------------------------------------------------
# 1. Landing Page / About
# ---------------------------------------------------------
if menu_choice.startswith("1"):
    st.subheader("👋 به سامانه مدیریت هوشمند کلاس پنجم خوش آمدید")
    
    st.markdown("""
    <div class="feature-box">
        <h3>🌱 طراح و توسعه‌دهنده سامانه</h3>
        <h4 style="color: #0284c7;">سید موسی حیدری</h4>
        <p style="font-size: 1.1em; font-weight: bold;">آموزگار پایه پنجم ابتدایی — دبستان شهید مطهری مهران</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 اهداف و امکانات اصلی سامانه:")
    
    st.markdown("""
    <div class="feature-box">
        <h4>1️⃣ ارزشیابی کیفی-توصیفی ۷ درس پایه پنجم</h4>
        <p>ثبت دقیق سطح عملکرد توصیفی دانش‌آموزان در تمامی دروس همراه با بازخوردهای سازنده.</p>
    </div>
    
    <div class="feature-box">
        <h4>2️⃣ آزمون‌ساز آنلاین با تصحیح آنی</h4>
        <p>طراحی آزمون‌های ۴ گزینه‌ای، تصحیح خودکار، و ارائه کارنامه به همراه پاسخ‌نامه تشریحی.</p>
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
# Locked Section Message
# ---------------------------------------------------------
elif menu_choice.startswith("🔒"):
    st.warning("🔒 این بخش مخصوص آموزگار است. لطفاً از کادر بالای صفحه، رمز عبور آموزگار را وارد کنید تا تمامی منوها فعال شوند.")

# ---------------------------------------------------------
# 2. Student Profile & Bulk Excel Upload (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("2") and st.session_state['is_teacher_logged_in']:
    st.header("👨‍🎓 مدیریت دانش‌آموزان و گروه‌بندی کلاسی (۲۹ نفر)")
    
    tab1, tab2, tab3 = st.tabs(["📋 لیست دانش‌آموزان و گروه‌ها", "📊 ثبت دسته‌جمعی و سریع از اکسل", "➕ ثبت دانش‌آموز جدید (تکی)"])
    
    with tab1:
        students_df = load_students()
        if not students_df.empty:
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                search_query = st.text_input("🔍 جستجوی سریع دانش‌آموز (نام یا کد ملی):")
            with col_s2:
                st.write("")
                st.write("")
                st.caption(f"تعداد کل دانش‌آموزان ثبت‌شده: {len(students_df)} نفر")
                
            if search_query:
                filtered_df = students_df[students_df['full_name'].str.contains(search_query) | students_df['national_id'].str.contains(search_query)]
            else:
                filtered_df = students_df
                
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
            st.info("هنوز هیچ دانش‌آموزی ثبت نشده است. می‌توانید از زبانه 'ثبت دسته‌جمعی از اکسل' استفاده کنید.")

    with tab2:
        st.subheader("📊 ثبت یکجای اسامی ۲۹ دانش‌آموز از طریق فایل اکسل / CSV")
        st.write("با بارگذاری فایل اکسل، اسامی تمامی دانش‌آموزان کلاس به یکباره و در کمتر از یک ثانیه وارد سامانه می‌شوند.")
        
        # Download Excel Template Button
        sample_data = pd.DataFrame({
            'first_name': ['علی', 'محمد', 'رضا', 'حسین', 'امیر'],
            'last_name': ['حیدری', 'محمدی', 'احمدی', 'رضایی', 'کریمی'],
            'national_id': ['1234567890', '1234567891', '1234567892', '1234567893', '1234567894'],
            'parent_phone': ['09121111111', '09122222222', '09123333333', '09124444444', '09125555555'],
            'student_group': ['گروه ارمغان 🚀 (۶ نفر)', 'گروه دانا 💡 (۶ نفر)', 'گروه تلاش 🌟 (۶ نفر)', 'گروه نخبگان 🏆 (۶ نفر)', 'گروه اندیشه 📖 (۵ نفر)'],
            'notes': ['نمونه ۱', 'نمونه ۲', 'نمونه ۳', 'نمونه ۴', 'نمونه ۵']
        })
        
        csv_sample = sample_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 دانلود فایل نمونه اکسل / CSV جهت الگو",
            data=csv_sample,
            file_name="sample_students_template_29.csv",
            mime="text/csv"
        )
        
        uploaded_file = st.file_uploader("فایل اکسل (xlsx) یا CSV دانش‌آموزان را انتخاب یا اینجا رها کنید:", type=['xlsx', 'csv'])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)
                    
                st.write("📋 پیش‌نمایش اطلاعات فایل بارگذاری‌شده:")
                st.dataframe(df_up.head(10), use_container_width=True)
                
                if st.button("🚀 شروع بارگذاری و ثبت یکجای دانش‌آموزان در دیتابیس"):
                    inserted_count = 0
                    with get_connection() as conn:
                        for idx, row in df_up.iterrows():
                            f_name = str(row.get('first_name', '')).strip()
                            l_name = str(row.get('last_name', '')).strip()
                            n_id = str(row.get('national_id', '')).strip() if pd.notna(row.get('national_id')) else f"100000{idx}"
                            p_phone = str(row.get('parent_phone', '')).strip() if pd.notna(row.get('parent_phone')) else ""
                            s_grp = str(row.get('student_group', CLASS_GROUPS[idx % 5])).strip() if pd.notna(row.get('student_group')) else CLASS_GROUPS[idx % 5]
                            s_notes = str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else ""
                            
                            if f_name and l_name:
                                try:
                                    conn.execute(
                                        "INSERT INTO students (first_name, last_name, national_id, parent_phone, student_group, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                        (f_name, l_name, n_id, p_phone, s_grp, s_notes)
                                    )
                                    inserted_count += 1
                                except sqlite3.IntegrityError:
                                    pass
                        conn.commit()
                    st.success(f"🎉 تعداد {inserted_count} دانش‌آموز با موفقیت وارد دیتابیس شدند.")
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
elif menu_choice.startswith("3") and st.session_state['is_teacher_logged_in']:
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
            
            # Export CSV
            csv_eval = eval_history.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 دانلود خروجی سوابق توصیفی دانش‌آموز (جهت پوشه کار)",
                data=csv_eval,
                file_name=f"evaluations_{selected_student}.csv",
                mime="text/csv"
            )
        else:
            st.info("هنوز ارزشیابی برای این دانش‌آموز ثبت نشده است.")

# ---------------------------------------------------------
# 4. Behavior and Discipline Tracking (Teacher Only)
# ---------------------------------------------------------
elif menu_choice.startswith("4") and st.session_state['is_teacher_logged_in']:
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
elif menu_choice.startswith("5") and st.session_state['is_teacher_logged_in']:
    st.header("✏️ آزمون‌ساز آنلاین (طراحی و مدیریت آزمون)")
    
    tab_q1, tab_q2 = st.tabs(["➕ ساخت آزمون جدید و طراحی سوالات", "📊 لیست آزمون‌ها و نتایج"])
    
    with tab_q1:
        st.subheader("۱. مشخصات آزمون")
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_title = st.text_input("عنوان آزمون:")
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
                opt1 = st.text_input(f"گزینه ۱:", key=f"opt1_{i}")
            with c2:
                opt2 = st.text_input(f"گزینه ۲:", key=f"opt2_{i}")
            with c3:
                opt3 = st.text_input(f"گزینه ۳:", key=f"opt3_{i}")
            with c4:
                opt4 = st.text_input(f"گزینه ۴:", key=f"opt4_{i}")
            
            correct_opt = st.selectbox(f"گزینه صحیح سوال {i+1}:", [1, 2, 3, 4], key=f"corr_{i}")
            expl = st.text_input(f"نکته/پاسخ تشریحی سوال {i+1} (اختیاری):", key=f"expl_{i}")
            questions_data.append((q_text, opt1, opt2, opt3, opt4, correct_opt, expl))
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
                st.success(f"آزمون '{quiz_title}' با موفقیت ساخته شد!")
            else:
                st.error("لطفاً عنوان آزمون و متن سوالات را وارد کنید.")

    with tab_q2:
        with get_connection() as conn:
            quizzes_df = pd.read_sql_query("SELECT id, title AS 'عنوان', subject AS 'درس', duration_minutes AS 'مدت (دقیقه)', created_at AS 'تاریخ ساخت' FROM quizzes", conn)
        
        if not quizzes_df.empty:
            st.dataframe(quizzes_df, use_container_width=True)
            
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

# ---------------------------------------------------------
# 6. Student Online Quiz Interface (Public Access)
# ---------------------------------------------------------
elif menu_choice.startswith("6") or menu_choice.startswith("2️⃣ 📱"):
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
        
        with get_connection() as conn:
            existing = conn.execute("SELECT id, percentage FROM quiz_results WHERE quiz_id = ? AND student_id = ?", (q_id, s_id)).fetchone()
            
        if existing:
            st.success(f"شما قبلاً در این آزمون شرکت کرده‌اید. درصد کسب‌شده: {existing['percentage']:.1f}٪")
            
            with st.expander("📖 مشاهده پاسخ‌نامه تشریحی آزمون"):
                with get_connection() as conn:
                    qs = conn.execute("SELECT question_text, option_1, option_2, option_3, option_4, correct_option, explanation FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                for idx, q in enumerate(qs):
                    opts = [q['option_1'], q['option_2'], q['option_3'], q['option_4']]
                    st.markdown(f"**سوال {idx+1}: {q['question_text']}**")
                    st.markdown(f"✅ گزینه صحیح: **گزینه {q['correct_option']}: {opts[q['correct_option']-1]}**")
                    if q['explanation']:
                        st.info(f"💡 نکته آموزشی: {q['explanation']}")
                    st.markdown("---")
        else:
            st.info(f"زمان پیشنهادی آزمون: {quizzes_df[quizzes_df['id'] == q_id]['duration_minutes'].values[0]} دقیقه")
            
            with get_connection() as conn:
                questions = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (q_id,)).fetchall()
                
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
                    st.success(f"🎉 آزمون پایان یافت! نمره شما: {correct_count} از {total} (معادل {pct:.1f} درصد)")

# ---------------------------------------------------------
# 7. Dashboard and Analytical Report (Public Access)
# ---------------------------------------------------------
elif menu_choice.startswith("7") or menu_choice.startswith("3️⃣ 📊"):
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
            st.metric("میانگین درصد آزمون‌های آنلاین:", f"{quiz_avg:.1f}٪" if quiz_avg is not None else "بدون آزمون")
            
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
                    SELECT q.title AS 'عنوان آزمون', q.subject AS 'درس', r.score AS 'نمره', r.total_questions AS 'کل سوالات', r.percentage AS 'درصد ٪', r.submitted_at AS 'زمان'
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

