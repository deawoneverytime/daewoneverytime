import sqlite3
import streamlit as st
import os
import hashlib
import re
from datetime import datetime

# Streamlit 앱 실행 환경에 맞게 현재 파일의 디렉토리를 작업 디렉토리로 설정
# data.db 파일 경로 문제 방지
if 'STREAMLIT_SERVER_NAME' in os.environ:
    # Streamlit Cloud 환경에서는 os.chdir을 사용하지 않습니다.
    pass
else:
    # 로컬 환경에서는 안전하게 경로를 설정합니다.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


# ✅ 페이지 설정
st.set_page_config(page_title="대원타임", page_icon="🎓", layout="wide")

# ✅ CSS 스타일링: 모바일과 데스크톱 동일한 UI
STYLING = """
<style>
/* 모바일 뷰포트 설정 - 확대/축소 방지 및 고정 너비 */
@viewport {
    width: device-width;
    zoom: 1.0;
    user-zoom: fixed;
}

/* 전체 앱 컨테이너 설정 */
.stApp {
    background-color: #F9F9F9;
    min-width: 100%;
    overflow-x: auto;
}

/* 모바일에서도 데스크톱 레이아웃 유지 */
@media only screen and (max-width: 768px) {
    /* Streamlit 기본 패딩 제거 */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* 사이드바 너비 고정 */
    [data-testid="stSidebar"] {
        min-width: 250px !important;
    }
    
    /* 컬럼 간격 유지 */
    [data-testid="column"] {
        min-width: fit-content !important;
    }
    
    /* 텍스트 크기 고정 (모바일 자동 확대 방지) */
    input, textarea, select, button {
        font-size: 16px !important;
        -webkit-text-size-adjust: 100%;
    }
}

/* 배경색 */
.stApp {
    background-color: #F9F9F9;
}

/* 메인 제목 스타일 */
.main-title {
    font-size: 3.5em;
    font-weight: 900;
    color: #1E1E1E;
    text-align: center;
    margin-bottom: 25px;
    letter-spacing: -1px;
}

/* 모바일에서 제목 크기 조정 */
@media only screen and (max-width: 768px) {
    .main-title {
        font-size: 2.5em;
    }
    
    .sub-header {
        font-size: 1.5em !important;
    }
}

/* 섹션 헤더 스타일 */
.sub-header {
    font-size: 1.8em;
    font-weight: 700;
    color: #333333;
    border-left: 5px solid #4A4A4A;
    padding-left: 10px;
    padding-bottom: 5px;
    margin-top: 30px;
    margin-bottom: 15px;
}

/* 네이트판 스타일: 게시글 간격을 좁게 만드는 얇은 구분선 */
.thin-divider {
    margin: 0 !important;
    border-top: 1px solid #EDEDED;
    opacity: 1;
}

/* 게시글 목록의 버튼(제목) 스타일 */
div[data-testid^="stColumn"] div.stButton > button {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #333333 !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 5px 0 !important;
    margin: 0 !important;
    cursor: pointer !important;
    width: 100%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.2s ease;
    font-size: 14px !important;
}

/* 제목 버튼 호버 시 스타일 */
div[data-testid^="stColumn"] div.stButton > button:hover {
    color: #4A4A4A !important;
    text-decoration: none !important;
    background-color: #F0F0F0 !important;
}

/* 모바일 터치 시 효과 */
@media only screen and (max-width: 768px) {
    div[data-testid^="stColumn"] div.stButton > button:active {
        background-color: #E8E8E8 !important;
    }
}

/* st.columns 세로 간격 줄이기 */
div[data-testid^="stHorizontalBlock"] {
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}

/* 좋아요 수 표시 스타일 */
.metric-heart {
    font-size: 1.0em;
    font-weight: 700;
    color: #4A4A4A;
    padding: 5px 0;
}

/* 프로필 페이지 카드 스타일링 */
.profile-card {
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    margin-bottom: 20px;
}

@media only screen and (max-width: 768px) {
    .profile-card {
        padding: 15px;
    }
}

.profile-label {
    font-weight: 500;
    color: #4A4A4A;
    font-size: 1.1em;
    margin-bottom: 5px;
}

.profile-value {
    font-weight: 700;
    color: #333333;
    font-size: 1.5em;
    margin-bottom: 20px;
    padding-bottom: 5px;
    border-bottom: 1px solid #eee;
}

@media only screen and (max-width: 768px) {
    .profile-label {
        font-size: 0.95em;
    }
    
    .profile-value {
        font-size: 1.2em;
    }
}

/* Primary 버튼 스타일 */
.stButton button[data-testid="baseButton-primary"] {
    background-color: #4A4A4A !important;
    border-color: #4A4A4A !important;
    color: white !important;
    min-height: 44px !important; /* 모바일 터치 최소 크기 */
}

.stButton button[data-testid="baseButton-primary"]:hover {
    background-color: #333333 !important;
    border-color: #333333 !important;
}

/* Secondary 버튼 스타일 */
.stButton button[data-testid="baseButton-secondary"] {
    color: #4A4A4A !important;
    border-color: #E0E0E0 !important;
    min-height: 44px !important;
}

.stButton button[data-testid="baseButton-secondary"]:hover {
    background-color: #F0F0F0 !important;
    border-color: #D0D0D0 !important;
}

/* Alert 메시지 색상 */
div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p {
    color: #1E1E1E !important;
    font-weight: 600;
}

/* 사이드바 헤더 색상 */
.sidebar-header {
    font-size: 1.5em;
    font-weight: 700;
    color:#1E1E1E;
}

/* 상세 페이지 좋아요 카운트 */
.post-likes-count {
    font-size: 1.0em;
    font-weight: 700;
    color: #4A4A4A;
}

/* 테이블 형태의 게시글 목록을 위한 스타일 */
.post-list-row {
    display: flex;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #EDEDED;
    min-height: 40px;
}

.post-list-header {
    display: flex;
    align-items: center;
    padding: 10px 0;
    font-weight: bold;
    border-bottom: 2px solid #CCCCCC;
}

/* 모바일에서 컬럼 고정 너비 유지 */
@media only screen and (max-width: 768px) {
    /* 가로 스크롤 가능하도록 설정 */
    .post-list-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    /* 최소 너비 보장 */
    div[data-testid="column"] {
        flex-shrink: 0 !important;
    }
}

/* 입력 필드 스타일 */
input[type="text"], input[type="password"], input[type="email"], textarea {
    font-size: 16px !important;
    -webkit-appearance: none;
    border-radius: 4px;
}

/* 폼 제출 버튼 */
button[kind="formSubmit"] {
    min-height: 44px !important;
}

</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)


# ✅ 이메일 & 비밀번호 정규식: 데이터 유효성 검사
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# ✅ DB 초기화: 필요한 테이블 생성
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT UNIQUE,
        student_id TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        author TEXT,
        real_author TEXT,
        created_at TEXT,
        likes INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        author TEXT,
        real_author TEXT,
        content TEXT,
        created_at TEXT,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        username TEXT,
        post_id INTEGER,
        created_at TEXT,
        PRIMARY KEY (username, post_id),
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    conn.commit()
    conn.close()

# ✅ 비밀번호 해싱 (보안)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 사용자 정의 DB 함수

def get_post_by_id(post_id):
    """특정 ID의 게시글을 가져옵니다. (컬럼 명시)"""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT id, title, content, author, real_author, created_at, likes FROM posts WHERE id = ?", (post_id,))
    post = c.fetchone()
    conn.close()
    return post

def login(username, password):
    """로그인 처리."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if not row or row[0] != hash_password(password):
        return False, "아이디 또는 비밀번호가 일치하지 않습니다."
    st.session_state.logged_in = True
    st.session_state.username = username
    return True, "로그인 성공!"

def like_post(post_id, username):
    """좋아요 토글 (메시지 없음)."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))

    if c.fetchone():
        c.execute("UPDATE posts SET likes = likes - 1 WHERE id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    else:
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        c.execute("INSERT INTO likes (username, post_id, created_at) VALUES (?, ?, ?)",
                  (username, post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    return True

def has_user_liked(post_id, username):
    """사용자가 좋아요를 눌렀는지 확인."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    liked = c.fetchone() is not None
    conn.close()
    return liked

def create_post(title, content, is_anonymous=False):
    """게시글 작성."""
    author = "익명" if is_anonymous else st.session_state.username
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('''INSERT INTO posts (title, content, author, real_author, created_at)
                  VALUES (?, ?, ?, ?, ?)''',
              (title, content, author, st.session_state.username,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_posts():
    """모든 게시글을 최신순으로 가져오기."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT id, title, author, created_at, likes FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

def delete_post(post_id):
    """게시글 및 관련 댓글, 좋아요 기록 삭제."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT real_author FROM posts WHERE id = ?", (post_id,))
    author = c.fetchone()
    if author and author[0] == st.session_state.username:
        c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def add_comment(post_id, content, is_anonymous=False):
    """댓글 추가."""
    author = "익명" if is_anonymous else st.session_state.username
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('''INSERT INTO comments (post_id, author, real_author, content, created_at)
                  VALUES (?, ?, ?, ?, ?)''',
              (post_id, author, st.session_state.username, content,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_comments(post_id):
    """특정 게시글의 댓글 가져오기."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT author, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments


# --- 페이지 함수 ---

def go_to_detail(post_id):
    """게시글 상세 페이지로 이동하며 ID 저장."""
    st.session_state.page = "detail"
    st.session_state.selected_post_id = post_id
    st.rerun()

# ✅ 로그인 페이지
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-title">🎓 대원타임</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">로그인</p>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("아이디", key="login_user")
            password = st.text_input("비밀번호", type="password", key="login_pw")

            if st.form_submit_button("로그인", use_container_width=True, type="primary"):
                success, msg = login(username, password)
                if success:
                    st.success(msg)
                    st.balloons()
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()
        st.markdown('<p style="color: #4A4A4A;">계정이 없으신가요? <strong>회원가입</strong>을 진행하세요.</p>', unsafe_allow_html=True)

        if st.button("회원가입하기", use_container_width=True, key="go_to_signup", type="secondary"):
            st.session_state.page = "signup"
            st.rerun()

# ✅ 회원가입 페이지
def show_signup_page():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    def signup(username, password, email, student_id):
        if not username.strip() or not student_id.strip():
            return False, "아이디와 학번은 필수 입력 사항입니다."

        if not re.match(EMAIL_REGEX, email) or not re.match(PASSWORD_REGEX, password):
            return False, "입력 형식을 확인하세요. 비밀번호는 8자 이상, 대/소문자/숫자 포함해야 합니다."
        try:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (
                username, hash_password(password), email, student_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            return True, "회원가입이 완료되었습니다!"
        except sqlite3.IntegrityError:
            return False, "이미 존재하는 아이디 또는 이메일입니다."

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-title">🎓 대원타임</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">회원가입</p>', unsafe_allow_html=True)

        with st.form("signup_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password", help="8자 이상, 대/소문자/숫자 포함")
            email = st.text_input("이메일")
            student_id = st.text_input("학번")

            if st.form_submit_button("회원가입 완료", use_container_width=True, type="primary"):
                success, msg = signup(username, password, email, student_id)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()
        if st.button("로그인 페이지로 돌아가기", use_container_width=True, type="secondary"):
            st.session_state.page = "login"
            st.rerun()
    conn.close()


# ✅ 게시판 목록 페이지
def show_home_page():
    st.markdown('<p class="sub-header">📋 자유게시판</p>', unsafe_allow_html=True)

    col_write, col_spacer = st.columns([1, 6])
    with col_write:
        if st.button("✍️ 새 글 작성", use_container_width=True, type="primary"):
            st.session_state.page = "write"
            st.rerun()
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)

    posts = get_all_posts()
    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해보세요!")
        return

    # 게시글 목록 헤더
    header_col1, header_col2, header_col3, header_col4 = st.columns([4, 1.5, 1, 0.5])
    header_col1.markdown('**제목**', unsafe_allow_html=True)
    header_col2.markdown('<div style="text-align: center;">**작성자**</div>', unsafe_allow_html=True)
    header_col3.markdown('<div style="text-align: center;">**작성일**</div>', unsafe_allow_html=True)
    header_col4.markdown('<div style="text-align: right; color: #4A4A4A;">**🖤**</div>', unsafe_allow_html=True)

    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

    # 게시글 목록
    for post in posts:
        post_id, title, author, created_at, likes = post

        col1, col2, col3, col4 = st.columns([4, 1.5, 1, 0.5])

        with col1:
            if st.button(title, key=f"post_title_{post_id}"):
                go_to_detail(post_id)

        col2.markdown(f'<div style="text-align: center; font-size: 0.9em; color: #666; padding: 5px 0;">{author}</div>', unsafe_allow_html=True)
        col3.markdown(f'<div style="text-align: center; font-size: 0.9em; color: #666; padding: 5px 0;">{created_at[:10]}</div>', unsafe_allow_html=True)
        col4.markdown(f'<div style="text-align: right;" class="metric-heart">{likes}</div>', unsafe_allow_html=True)

        st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)


# ✅ 게시글 상세 페이지
def show_post_detail(post_id):
    post = get_post_by_id(post_id)
    if not post:
        st.error("존재하지 않는 게시글입니다.")
        if st.button("목록으로 돌아가기"):
            st.session_state.page = "home"
            st.rerun()
        return

    post_id, title, content, author, real_author, created_at, likes = post
    username = st.session_state.username

    st.markdown(f'## {title}')
    st.caption(f"**작성자:** {author} | **작성일:** {created_at} | <span class='post-likes-count'>🖤 {likes}</span>", unsafe_allow_html=True)
    st.divider()

    st.write(content)
    st.divider()

    col1, col2, col3, col4 = st.columns([1, 1, 1, 4])

    with col1:
        is_liked = has_user_liked(post_id, username)
        like_label = "🖤 좋아요 취소" if is_liked else "🤍 좋아요"
        if st.button(like_label, key=f"detail_like_{post_id}", use_container_width=True, type="secondary"):
            like_post(post_id, username)
            st.rerun()

    with col2:
        if real_author == username:
            if st.button("🗑️ 삭제", key=f"detail_del_{post_id}", type="secondary", use_container_width=True):
                if delete_post(post_id):
                    st.success("게시글이 삭제되었습니다.")
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("삭제 권한이 없습니다.")

    with col3:
        if st.button("🔙 목록으로", key=f"detail_back_{post_id}", use_container_width=True, type="secondary"):
            st.session_state.page = "home"
            st.rerun()

    st.divider()

    st.markdown('### 💬 댓글')
    comments = get_comments(post_id)

    if comments:
        for c in comments:
            c_author, c_content, c_created = c
            st.markdown(f"""
            <div style="padding: 10px 0; border-bottom: 1px solid #eee;">
                <p style="margin: 0;">
                    <span style="font-weight: bold; color: #555;">👤 {c_author}</span>
                    <span style="font-size: 0.8em; color: #999;"> | {c_created}</span>
                </p>
                <p style="margin: 5px 0 0 15px; color: #333;">{c_content}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 댓글이 없습니다.")

    st.markdown('<h4 style="margin-top: 20px; color: #555;">댓글 작성</h4>', unsafe_allow_html=True)
    with st.form(key=f"comment_form_{post_id}", clear_on_submit=True):
        comment_text = st.text_area("댓글 내용을 입력하세요", key=f"comment_box_{post_id}", height=80, label_visibility="collapsed")

        colA, colB = st.columns([3, 1])
        with colA:
            st.checkbox("익명으로 작성", key=f"anon_comment_{post_id}",
                        help="익명으로 작성하면 작성자는 '익명'으로 표시됩니다.")
        with colB:
            if st.form_submit_button("등록", use_container_width=True, type="primary"):
                if comment_text.strip():
                    add_comment(post_id, comment_text, st.session_state[f"anon_comment_{post_id}"])
                    st.success("댓글이 등록되었습니다.")
                    st.rerun()
                else:
                    st.warning("댓글 내용을 입력하세요.")


# ✅ 글쓰기 페이지
def show_write_page():
    st.markdown('<p class="sub-header">✍️ 새 글 작성</p>', unsafe_allow_html=True)

    with st.form("write_post_form", clear_on_submit=True):
        title = st.text_input("제목을 입력하세요")
        content = st.text_area("내용을 입력하세요", height=400)
        anonymous = st.checkbox("익명으로 작성 (작성자: 익명)")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("등록", type="primary", use_container_width=True):
                if title.strip() and content.strip():
                    create_post(title, content, anonymous)
                    st.success("게시글이 성공적으로 작성되었습니다!")
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
        with col2:
            if st.form_submit_button("취소", use_container_width=True, type="secondary"):
                st.session_state.page = "home"
                st.rerun()

# ✅ 프로필
