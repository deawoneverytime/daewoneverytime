import sqlite3
import streamlit as st
import hashlib
import re
from datetime import datetime
import os

# ✅ 페이지 설정
st.set_page_config(page_title="대원타임", page_icon="🎓", layout="wide")

# ✅ CSS 스타일링
STYLING = """
<style>
/* 기본 설정 */
* {
    -webkit-text-size-adjust: 100%;
    -moz-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}

.stApp {
    background-color: #F9F9F9;
}

/* 모바일 최적화 */
@media only screen and (max-width: 768px) {
    .block-container {
        padding: 1rem !important;
    }
    
    input, textarea, button {
        font-size: 16px !important;
    }
}

/* 제목 스타일 */
.main-title {
    font-size: 2.8em;
    font-weight: 900;
    color: #1E1E1E;
    text-align: center;
    margin-bottom: 20px;
}

.sub-header {
    font-size: 1.6em;
    font-weight: 700;
    color: #333333;
    border-left: 5px solid #4A4A4A;
    padding-left: 10px;
    margin: 20px 0 15px 0;
}

/* 버튼 스타일 */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s;
    min-height: 44px;
}

.stButton > button[kind="primary"] {
    background-color: #4A4A4A !important;
    color: white !important;
    border: none !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #333333 !important;
}

.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: #4A4A4A !important;
    border: 1px solid #E0E0E0 !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #F0F0F0 !important;
}

/* 게시글 카드 */
.post-card {
    background: white;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    border: 1px solid #E0E0E0;
    cursor: pointer;
    transition: all 0.2s;
}

.post-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-color: #4A4A4A;
}

.post-title {
    font-size: 1.1em;
    font-weight: 700;
    color: #333;
    margin-bottom: 8px;
}

.post-meta {
    font-size: 0.85em;
    color: #999;
}

.post-likes {
    color: #4A4A4A;
    font-weight: 700;
}

/* 프로필 카드 */
.profile-card {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

.profile-item {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #F0F0F0;
}

.profile-label {
    font-size: 0.9em;
    color: #666;
    margin-bottom: 5px;
}

.profile-value {
    font-size: 1.2em;
    font-weight: 700;
    color: #333;
}

/* 댓글 스타일 */
.comment-box {
    background: #F9F9F9;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 10px;
    border-left: 3px solid #4A4A4A;
}

.comment-author {
    font-weight: 700;
    color: #555;
    margin-bottom: 5px;
}

.comment-content {
    color: #333;
    margin-left: 10px;
}

.comment-time {
    font-size: 0.8em;
    color: #999;
}

/* 입력 필드 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 8px;
    border: 1px solid #E0E0E0;
}

/* 구분선 */
.divider {
    height: 1px;
    background: #E0E0E0;
    margin: 20px 0;
}

</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)

# ✅ 데이터베이스 경로 설정
DB_PATH = "daewon_time.db"

# ✅ 이메일 & 비밀번호 정규식
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# ✅ DB 초기화 (school 컬럼 추가 및 마이그레이션 로직 포함)
def init_db():
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
    
    # 사용자 테이블 (school 컬럼 추가)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        student_id TEXT NOT NULL,
        school TEXT NOT NULL DEFAULT '대원고', 
        created_at TEXT NOT NULL
    )''')
    
    # 마이그레이션: 기존 테이블에 school 컬럼이 없는 경우 추가
    try:
        # school 컬럼이 있는지 확인
        c.execute("SELECT school FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # school 컬럼이 없으면 추가 (기존 사용자에게는 기본값 '대원고' 부여)
        c.execute("ALTER TABLE users ADD COLUMN school TEXT NOT NULL DEFAULT '대원고'")

    # 게시글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        real_author TEXT NOT NULL,
        created_at TEXT NOT NULL,
        likes INTEGER DEFAULT 0
    )''')
    
    # 댓글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        author TEXT NOT NULL,
        real_author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')
    
    # 좋아요 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        username TEXT NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (username, post_id),
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')
    
    conn.commit()
    conn.close()

# ✅ 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 회원가입 (school 파라미터 추가)
def signup_user(username, password, email, student_id, school):
    if not username.strip() or not student_id.strip() or not school.strip() or school == "--- 선택 ---":
        return False, "아이디, 학번, 학교는 필수 입력 사항입니다."
    
    if not re.match(EMAIL_REGEX, email):
        return False, "올바른 이메일 형식이 아닙니다."
    
    if not re.match(PASSWORD_REGEX, password):
        return False, "비밀번호는 8자 이상, 대문자/소문자/숫자를 포함해야 합니다."
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # school 컬럼 추가에 따라 ?의 개수 6개로 변경
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", 
                  (username, hash_password(password), email, student_id, school,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True, "회원가입이 완료되었습니다!"
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 아이디 또는 이메일입니다."

# ✅ 로그인
def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row or row[0] != hash_password(password):
        return False, "아이디 또는 비밀번호가 일치하지 않습니다."
    
    return True, "로그인 성공!"

# ✅ 사용자 정보 가져오기 (school 필드 추가)
def get_user_info(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # school 컬럼 추가
    c.execute("SELECT username, email, student_id, school, created_at FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    # 반환되는 튜플: (username, email, student_id, school, created_at)
    return user

# ✅ 게시글 작성
def create_post(title, content, username, is_anonymous=False):
    author = "익명" if is_anonymous else username
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO posts (title, content, author, real_author, created_at, likes)
              VALUES (?, ?, ?, ?, ?, 0)''',
              (title, content, author, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ✅ 모든 게시글 가져오기
def get_all_posts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, author, created_at, likes FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

# ✅ 게시글 상세 정보
def get_post_detail(post_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, content, author, real_author, created_at, likes FROM posts WHERE id = ?", (post_id,))
    post = c.fetchone()
    conn.close()
    return post

# ✅ 게시글 삭제
def delete_post(post_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT real_author FROM posts WHERE id = ?", (post_id,))
    result = c.fetchone()
    
    if result and result[0] == username:
        c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

# ✅ 좋아요 토글
def toggle_like(post_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    
    if c.fetchone():
        c.execute("UPDATE posts SET likes = likes - 1 WHERE id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    else:
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        c.execute("INSERT INTO likes VALUES (?, ?, ?)",
                  (username, post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

# ✅ 좋아요 여부 확인
def check_liked(post_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    liked = c.fetchone() is not None
    conn.close()
    return liked

# ✅ 댓글 추가
def add_comment(post_id, content, username, is_anonymous=False):
    author = "익명" if is_anonymous else username
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO comments (post_id, author, real_author, content, created_at)
              VALUES (?, ?, ?, ?, ?)''',
              (post_id, author, username, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ✅ 댓글 가져오기
def get_comments(post_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT author, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments

# ===== 페이지 함수 =====

# ✅ 로그인 페이지
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-title">🎓 대원타임</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">로그인</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.form_submit_button("로그인", use_container_width=True)
            with col_b:
                if st.form_submit_button("회원가입", use_container_width=True, type="secondary"):
                    st.session_state.page = "signup"
                    st.rerun()
            
            if login_btn:
                success, msg = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.page = "home"
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# ✅ 회원가입 페이지 (학교 선택 추가)
def show_signup_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-title">🎓 대원타임</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">회원가입</div>', unsafe_allow_html=True)
        
        with st.form("signup_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password", 
                                     help="8자 이상, 대문자/소문자/숫자 포함")
            email = st.text_input("이메일")
            student_id = st.text_input("학번")
            # 학교 선택 필드 추가
            school = st.selectbox("학교 선택", ["--- 선택 ---", "대원고", "대원여고"], index=0)
            
            col_a, col_b = st.columns(2)
            with col_a:
                signup_btn = st.form_submit_button("회원가입 완료", use_container_width=True)
            with col_b:
                if st.form_submit_button("취소", use_container_width=True, type="secondary"):
                    st.session_state.page = "login"
                    st.rerun()
            
            if signup_btn:
                if school == "--- 선택 ---":
                    st.error("학교를 선택해주세요.")
                else:
                    # signup_user 함수에 school 값 전달
                    success, msg = signup_user(username, password, email, student_id, school)
                    if success:
                        st.success(msg)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)

# ✅ 홈 페이지 (게시판)
def show_home_page():
    st.markdown('<div class="sub-header">📋 자유게시판</div>', unsafe_allow_html=True)
    
    if st.button("✍️ 새 글 작성", key="write_btn"):
        st.session_state.page = "write"
        st.rerun()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    posts = get_all_posts()
    
    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해보세요!")
        return
    
    for post in posts:
        post_id, title, author, created_at, likes = post
        
        # Markdown을 클릭 가능한 요소로 사용하고 버튼으로 상세보기 링크
        post_html = f"""
        <div class="post-card">
            <div class="post-title">{title}</div>
            <div class="post-meta">
                👤 {author} | 📅 {created_at[:16]} | <span class="post-likes">🖤 {likes}</span>
            </div>
        </div>
        """
        st.markdown(post_html, unsafe_allow_html=True)
        
        # 버튼을 사용하여 페이지 이동 처리
        if st.button("자세히 보기", key=f"view_{post_id}", type="secondary", use_container_width=True):
            st.session_state.page = "detail"
            st.session_state.selected_post_id = post_id
            st.rerun()
        st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True) # 간격

# ✅ 글쓰기 페이지
def show_write_page():
    st.markdown('<div class="sub-header">✍️ 새 글 작성</div>', unsafe_allow_html=True)
    
    with st.form("write_form"):
        title = st.text_input("제목")
        content = st.text_area("내용", height=300)
        is_anonymous = st.checkbox("익명으로 작성")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_btn = st.form_submit_button("등록", use_container_width=True)
        with col2:
            if st.form_submit_button("취소", use_container_width=True, type="secondary"):
                st.session_state.page = "home"
                st.rerun()
        
        if submit_btn:
            if title.strip() and content.strip():
                create_post(title, content, st.session_state.username, is_anonymous)
                st.success("게시글이 등록되었습니다!")
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("제목과 내용을 모두 입력해주세요.")

# ✅ 게시글 상세 페이지
def show_detail_page():
    post_id = st.session_state.selected_post_id
    post = get_post_detail(post_id)
    
    if not post:
        st.error("게시글을 찾을 수 없습니다.")
        if st.button("목록으로"):
            st.session_state.page = "home"
            st.rerun()
        return
    
    pid, title, content, author, real_author, created_at, likes = post
    username = st.session_state.username
    
    # 게시글 내용
    st.markdown(f"## {title}")
    st.caption(f"👤 {author} | 📅 {created_at} | 🖤 {likes}")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.write(content)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 버튼들
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    
    with col1:
        is_liked = check_liked(post_id, username)
        like_label = "🖤 취소" if is_liked else "🤍 좋아요"
        if st.button(like_label, type="secondary", use_container_width=True):
            toggle_like(post_id, username)
            st.rerun()
    
    with col2:
        if real_author == username:
            if st.button("🗑️ 삭제", type="secondary", use_container_width=True):
                if delete_post(post_id, username):
                    st.success("삭제되었습니다.")
                    st.session_state.page = "home"
                    st.rerun()
    
    with col3:
        if st.button("🔙 목록", type="secondary", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    
    # 댓글 섹션
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### 💬 댓글")
    
    comments = get_comments(post_id)
    
    if comments:
        for comment in comments:
            c_author, c_content, c_time = comment
            comment_html = f"""
            <div class="comment-box">
                <div class="comment-author">👤 {c_author} <span class="comment-time">| {c_time}</span></div>
                <div class="comment-content">{c_content}</div>
            </div>
            """
            st.markdown(comment_html, unsafe_allow_html=True)
    else:
        st.info("아직 댓글이 없습니다.")
    
    # 댓글 작성
    st.markdown("#### 댓글 작성")
    with st.form(key=f"comment_form_{post_id}"):
        comment_content = st.text_area("댓글 내용", height=100, label_visibility="collapsed")
        
        col_a, col_b = st.columns([3, 1])
        with col_a:
            is_anon = st.checkbox("익명으로 작성")
        with col_b:
            if st.form_submit_button("등록", use_container_width=True):
                if comment_content.strip():
                    add_comment(post_id, comment_content, username, is_anon)
                    st.success("댓글이 등록되었습니다!")
                    st.rerun()
                else:
                    st.warning("댓글 내용을 입력하세요.")

# ✅ 프로필 페이지 (학교 정보 표시 추가)
def show_profile_page():
    st.markdown('<div class="sub-header">👤 내 정보</div>', unsafe_allow_html=True)
    
    user = get_user_info(st.session_state.username)
    
    if user:
        # get_user_info에서 school 필드를 추가로 받아옴
        username, email, student_id, school, created_at = user 
        
        profile_html = f"""
        <div class="profile-card">
            <h3 style="margin-top:0; color:#1E1E1E;">{username}님의 프로필</h3>
            <div style="height:2px; background:#E0E0E0; margin:15px 0;"></div>
            
            <div class="profile-item">
                <div class="profile-label">아이디</div>
                <div class="profile-value">{username}</div>
            </div>
            
            <div class="profile-item">
                <div class="profile-label">이메일</div>
                <div class="profile-value">{email}</div>
            </div>
            
            <div class="profile-item">
                <div class="profile-label">학번</div>
                <div class="profile-value">{student_id}</div>
            </div>
            
            <div class="profile-item">
                <div class="profile-label">학교</div>
                <div class="profile-value">{school}</div>
            </div>
            
            <div class="profile-item" style="border:none;">
                <div class="profile-label">가입일</div>
                <div class="profile-value">{created_at}</div>
            </div>
        </div>
        """
        st.markdown(profile_html, unsafe_allow_html=True)
    else:
        st.error("사용자 정보를 불러올 수 없습니다.")

# ===== 메인 =====
def main():
    init_db()
    
    # 세션 상태 초기화
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "login"
        st.session_state.selected_post_id = None
    
    # 사이드바
    with st.sidebar:
        st.markdown('<div style="font-size:1.5em; font-weight:700; color:#1E1E1E;">🎓 대원 커뮤니티</div>', 
                    unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        if st.session_state.logged_in:
            st.success(f"**{st.session_state.username}**님 환영합니다!")
            
            if st.button("🏠 홈 (게시판)", use_container_width=True, type="secondary"):
                st.session_state.page = "home"
                st.rerun()
            
            if st.button("✍️ 글쓰기", use_container_width=True, type="secondary"):
                st.session_state.page = "write"
                st.rerun()
            
            if st.button("👤 내 정보", use_container_width=True, type="secondary"):
                st.session_state.page = "profile"
                st.rerun()
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "login"
                st.session_state.selected_post_id = None
                st.rerun()
        else:
            st.info("로그인이 필요합니다.")
    
    # 페이지 라우팅
    if not st.session_state.logged_in:
        if st.session_state.page == "signup":
            show_signup_page()
        else:
            show_login_page()
    else:
        if st.session_state.page == "home":
            show_home_page()
        elif st.session_state.page == "write":
            show_write_page()
        elif st.session_state.page == "profile":
            show_profile_page()
        elif st.session_state.page == "detail":
            show_detail_page()
        else:
            st.session_state.page = "home"
            st.rerun()

if __name__ == "__main__":
    main()
