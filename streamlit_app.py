import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

# ✅ 페이지 설정
# 기본 Streamlit 다크 모드와 조화를 이루도록 설정
st.set_page_config(page_title="대원타임", page_icon="🎓", layout="wide")

# ✅ 학교 목록 정의 (회원가입 드롭다운에 사용)
SCHOOLS = ["대원고등학교", "대원여자고등학교", "대원외국어고등학교"]

# ✅ CSS 스타일링: 심플하고 모던한 무채색(Achromatic) 모바일 테마 적용
STYLING = """
<style>
/* 🎨 Achromatic & Mobile Theme Colors */
:root {
    --bg-dark: #1A1A1A;      /* Very Dark Gray Background */
    --bg-secondary: #2C2C2C; /* Secondary Card/Input Background */
    --accent: #BBBBBB;       /* Light Gray Accent for Primary actions & text */
    --text-light: #FFFFFF;   /* White Text */
    --metric-color: #AAAAAA; /* Subtle color for metrics (likes/views) */
    --border-subtle: #444444; /* Subtle Border */
}

/* 메인 제목 스타일 */
.main-title {
    font-size: 2.5em; /* 모바일에 적합하게 조정 */
    font-weight: 800;
    color: var(--accent); 
    text-align: center;
    margin-bottom: 25px;
    letter-spacing: -1px;
}

/* 섹션 헤더 스타일 */
.sub-header {
    font-size: 1.6em;
    font-weight: 700;
    color: var(--text-light);
    border-bottom: 2px solid var(--border-subtle);
    padding-bottom: 8px;
    margin-top: 20px;
    margin-bottom: 15px;
}

/* 게시글 목록 카드 스타일 (모바일 최적화) */
.post-row-card {
    background-color: var(--bg-secondary);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    border: 1px solid var(--border-subtle);
    transition: background-color 0.2s;
}
.post-row-card:hover {
    background-color: #383838; /* Subtle hover effect */
}
.post-title-text {
    font-size: 1.1em; 
    font-weight: 600; 
    color: var(--text-light); 
    margin-bottom: 5px;
    display: block; /* 제목이 한 줄을 차지하도록 */
}

/* 좋아요 수 표시 스타일 */
.metric-heart {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--metric-color); /* Subtle Gray */
    margin-right: 15px;
}
/* 조회수 표시 스타일 */
.metric-view {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--metric-color); /* Subtle Gray */
}

/* 추천 게시글 카드 스타일 */
.recommend-card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    padding: 12px;
    border-radius: 8px;
    margin-top: 10px;
    transition: all 0.3s;
}
.recommend-card:hover {
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    border-color: var(--accent);
}

/* Streamlit Button Primary Color Override (터치 영역 확보) */
.stButton>button[kind="primary"] {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
    color: var(--bg-dark) !important;
    font-weight: 600;
    min-height: 44px; /* 최소 터치 타겟 크기 */
}
/* Secondary 버튼도 터치 타겟 크기 확보 */
.stButton>button[kind="secondary"] {
    min-height: 44px;
}
</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)


# ✅ 이메일 & 비밀번호 정규식: 데이터 유효성 검사
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# ✅ DB 초기화: 필요한 테이블 생성 및 스키마 마이그레이션 처리
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 1. 테이블 생성 (IF NOT EXISTS)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT UNIQUE,
        school TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        author TEXT,
        real_author TEXT,
        created_at TEXT,
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0
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
    
    # 2. 스키마 마이그레이션 (기존 DB 파일에 새 컬럼 추가)
    try:
        c.execute("SELECT views FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE posts ADD COLUMN views INTEGER DEFAULT 0")
        st.info("데이터베이스 스키마를 업데이트했습니다 (posts 테이블에 views 컬럼 추가).")

    try:
        c.execute("SELECT school FROM users LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE users ADD COLUMN school TEXT")
        st.info("데이터베이스 스키마를 업데이트했습니다 (users 테이블에 school 컬럼 추가).")
    
    conn.commit()
    conn.close()

# ✅ 비밀번호 해싱 (보안)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 사용자 정의 DB 함수 (로직 변경 없음)
def get_post_by_id(post_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = c.fetchone()
    conn.close()
    return post

def increment_views(post_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

def login(username, password):
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

def create_post(title, content, is_anonymous=False):
    author = "익명" if is_anonymous else st.session_state.username
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('''INSERT INTO posts (title, content, author, real_author, created_at, likes, views)
              VALUES (?, ?, ?, ?, ?, 0, 0)''',
              (title, content, author, st.session_state.username,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT id, title, author, created_at, likes, views FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

def get_recommended_posts(current_post_id, limit=3):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(f"SELECT id, title FROM posts WHERE id != ? ORDER BY id DESC LIMIT {limit}", (current_post_id,))
    posts = c.fetchall()
    conn.close()
    return posts

def like_post(post_id, username):
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
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    liked = c.fetchone() is not None
    conn.close()
    return liked

def delete_post(post_id):
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
    # st.rerun() 대신 Streamlit의 기본 동작을 따르도록 하여 reruns 최소화

# ✅ 로그인 페이지
def show_login_page():
    # 모바일에서 중앙에 내용이 잘 보이도록 컬럼 사용 유지
    col1, col2, col3 = st.columns([0.1, 1, 0.1]) 
    with col2:
        st.markdown('<p class="main-title">대원 커뮤니티</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">로그인</p>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("아이디", key="login_user")
            password = st.text_input("비밀번호", type="password", key="login_pw")
            if st.form_submit_button("로그인", use_container_width=True, type="primary"):
                success, msg = login(username, password)
                if success:
                    st.success(msg)
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        st.markdown("계정이 없으신가요?")
        if st.button("회원가입", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# ✅ 회원가입 페이지
def show_signup_page():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    def signup(username, password, email, school):
        if not re.match(EMAIL_REGEX, email) or not re.match(PASSWORD_REGEX, password):
            return False, "입력 형식을 확인하세요. (비밀번호: 8자 이상, 대/소문자/숫자 포함)"
        try:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (
                username, hash_password(password), email, school,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            return True, "회원가입이 완료되었습니다! 로그인해 주세요."
        except sqlite3.IntegrityError:
            return False, "이미 존재하는 아이디 또는 이메일입니다."

    col1, col2, col3 = st.columns([0.1, 1, 0.1])
    with col2:
        st.markdown('<p class="main-title">대원 커뮤니티</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">회원가입</p>', unsafe_allow_html=True)

        with st.form("signup_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password", help="8자 이상, 대/소문자/숫자 포함")
            email = st.text_input("이메일")
            
            school = st.selectbox("학교를 선택하세요", options=SCHOOLS, index=0)

            if st.form_submit_button("가입 완료", use_container_width=True, type="primary"):
                success, msg = signup(username, password, email, school)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        if st.button("로그인 페이지로 돌아가기", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
    conn.close()

# ✅ 게시판 목록 페이지 (모바일 최적화)
def show_home_page():
    st.markdown('<p class="sub-header">자유 게시판</p>', unsafe_allow_html=True)

    col_write, col_spacer = st.columns([1, 6])
    with col_write:
        if st.button("새 글 작성", use_container_width=True, type="primary"):
            st.session_state.page = "write"
            st.rerun()
    st.markdown("---")

    posts = get_all_posts()
    if not posts:
        st.info("아직 게시글이 없습니다.")
        return

    # 모바일 최적화: 5열 테이블 대신, 전체 너비 카드 형태로 표시
    for post in posts:
        post_id, title, author, created_at, likes, views = post
        
        # 커스텀 CSS를 이용하여 카드 형태로 디자인하고, 클릭 액션을 처리할 숨겨진 버튼을 포함
        st.markdown(f'<div class="post-row-card" onclick="document.getElementById(\'btn_post_{post_id}\').click()" style="cursor: pointer;">', unsafe_allow_html=True)
        
        # 제목
        st.markdown(f'<span class="post-title-text">{title}</span>', unsafe_allow_html=True)
        
        # 메타데이터 (작성자 | 날짜)
        st.markdown(f'<div style="font-size: 0.9em; color: var(--accent); margin-bottom: 5px;">', unsafe_allow_html=True)
        st.markdown(f'<span>{author}</span> | <span style="margin-left: 5px;">{created_at[:10]}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 메트릭 (좋아요 | 조회수)
        st.markdown(f'<div style="font-size: 0.8em;">', unsafe_allow_html=True)
        st.markdown(f'<span class="metric-heart">❤️ {likes}</span> <span class="metric-view">👁️ {views}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 실제 Streamlit 동작을 트리거하기 위한 숨겨진 버튼
        if st.button(" ", key=f"btn_post_{post_id}"):
             go_to_detail(post_id)

        # 숨겨진 버튼의 스타일을 조정하여 시각적으로 보이지 않게 처리 (CSS에 추가)
        st.markdown(f"""
        <style>
            div[data-testid="stButton"] button[key="btn_post_{post_id}"] {{
                visibility: hidden;
                height: 0;
                width: 0;
                padding: 0;
                margin: 0;
                border: none;
                line-height: 0;
            }}
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


# ✅ 게시글 상세 페이지
def show_post_detail(post_id):
    increment_views(post_id)
    
    post = get_post_by_id(post_id)
    if not post:
        st.error("존재하지 않는 게시글입니다.")
        if st.button("목록으로 돌아가기", type="primary"):
            st.session_state.page = "home"
            st.rerun()
        return

    post_id, title, content, author, real_author, created_at, likes, views = post
    username = st.session_state.username

    st.markdown(f'## {title}')
    st.caption(f"**작성자:** {author} | **작성일:** {created_at}")
    st.markdown("---")
    
    # 게시글 내용
    st.text_area("본문", value=content, height=300, disabled=True, label_visibility="collapsed")
    
    # 좋아요 및 조회수 표시
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<span class="metric-heart">❤️ 좋아요 {likes}</span> <span class="metric-view">👁️ 조회수 {views}</span>', unsafe_allow_html=True)
    st.markdown("---")

    # 액션 버튼 영역 (모바일에서 버튼이 한 줄에 꽉 차도록 3개만 나열)
    col1, col2, col3 = st.columns(3)
    
    # 좋아요 버튼
    with col1:
        is_liked = has_user_liked(post_id, username)
        # 이모지 최소화: 🤍 -> 좋아요, ❤️ -> 좋아요 취소
        like_label = "❤️ 취소" if is_liked else "🤍 좋아요"
        if st.button(like_label, key=f"detail_like_{post_id}", use_container_width=True, type="secondary"):
            like_post(post_id, username)
            st.rerun()
            
    # 삭제 버튼 (작성자에게만)
    with col2:
        if real_author == username:
            if st.button("삭제", key=f"detail_del_{post_id}", use_container_width=True, type="secondary"):
                if delete_post(post_id):
                    st.success("게시글이 삭제되었습니다.")
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("삭제 권한이 없습니다.")
        else:
            # 삭제 권한이 없으면 빈 공간을 만들어 레이아웃 유지
            st.markdown('<div style="height: 44px;"></div>', unsafe_allow_html=True)

    # 목록으로 버튼
    with col3:
        if st.button("목록으로", key=f"detail_back_{post_id}", use_container_width=True, type="primary"):
            st.session_state.page = "home"
            st.rerun()

    st.markdown("---")

    # ✅ 댓글 섹션
    st.markdown('### 댓글')
    comments = get_comments(post_id)
    
    if comments:
        for c in comments:
            c_author, c_content, c_created = c
            # 모바일 가독성을 위해 댓글 영역 배경을 다르게 설정
            st.markdown(f"""
            <div style="background-color: #242424; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
            <p style="margin: 0;"><b>{c_author}</b> <small style='color: #777777;'>({c_created})</small></p>
            <p style="margin: 5px 0 0 0; word-wrap: break-word;">{c_content}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 댓글이 없습니다. 첫 댓글을 남겨보세요.")

    st.markdown('#### 댓글 작성')
    with st.form(key=f"comment_form_{post_id}", clear_on_submit=True):
        comment_text = st.text_area("댓글 내용을 입력하세요", key=f"comment_box_{post_id}", height=80, label_visibility="collapsed")
        
        # 버튼을 아래로 분리하여 모바일에서 터치하기 쉽게
        colA, colB = st.columns([1, 1])
        with colA:
            anonymous = st.checkbox("익명으로 작성", help="익명으로 댓글을 작성합니다.")
        with colB:
            if st.form_submit_button("등록", use_container_width=True, type="primary"):
                if comment_text.strip():
                    add_comment(post_id, comment_text, anonymous)
                    st.success("댓글이 등록되었습니다.")
                    st.rerun()
                else:
                    st.warning("댓글 내용을 입력하세요.")

    st.markdown("---")
    
    # 📌 추천 게시물 섹션
    st.markdown('### 추천 게시물')
    recommended_posts = get_recommended_posts(post_id, limit=3)
    
    if recommended_posts:
        # 모바일에서는 1열 또는 2열로 표시하는 것이 적합
        cols = st.columns(min(len(recommended_posts), 2)) 
        for i, (rec_id, rec_title) in enumerate(recommended_posts):
            with cols[i % min(len(recommended_posts), 2)]:
                st.markdown(f'<div class="recommend-card">', unsafe_allow_html=True)
                st.markdown(f"**{rec_title}**", unsafe_allow_html=True)
                # '보기' 버튼도 터치 타겟 크기를 확보
                if st.button("보기", key=f"rec_btn_{rec_id}", use_container_width=True, type="secondary"):
                    st.session_state.selected_post_id = rec_id
                    st.rerun()
                st.markdown(f'</div>', unsafe_allow_html=True)
    else:
        st.info("다른 게시글이 없습니다.")


# ✅ 글쓰기 페이지
def show_write_page():
    st.markdown('<p class="sub-header">새 글 작성</p>', unsafe_allow_html=True)
    
    with st.form("write_post_form", clear_on_submit=True):
        title = st.text_input("제목")
        content = st.text_area("내용", height=400)
        anonymous = st.checkbox("익명으로 작성")
        
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
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
            if st.form_submit_button("취소", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()

# ✅ 프로필 페이지
def show_profile_page():
    st.markdown('<p class="sub-header">내 정보</p>', unsafe_allow_html=True)
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT username, email, school, created_at FROM users WHERE username = ?", (st.session_state.username,))
    user = c.fetchone()
    conn.close()

    if user:
        username, email, school, created = user
        st.subheader("계정 정보")
        # 깔끔하게 정보 표시
        st.markdown(f"""
        <div style="background-color: var(--bg-secondary); padding: 15px; border-radius: 8px;">
            <p style="margin: 0 0 5px 0;"><b>아이디:</b> {username}</p>
            <p style="margin: 5px 0;"><b>이메일:</b> {email}</p>
            <p style="margin: 5px 0;"><b>소속 학교:</b> {school or '정보 없음'}</p>
            <p style="margin: 5px 0 0 0;"><b>가입일:</b> {created}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("사용자 정보를 불러올 수 없습니다.")

# ✅ 메인 실행
def main():
    init_db()

    # 세션 상태 초기화
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "login"
        st.session_state.selected_post_id = None

    # 사이드바 (내비게이션)
    with st.sidebar:
        st.markdown('<p style="font-size: 1.8em; font-weight: 700; color: var(--accent);">대원 커뮤니티</p>', unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.logged_in:
            st.markdown(f"환영합니다, **{st.session_state.username}**님.", unsafe_allow_html=True)
            st.markdown("---")
            
            # 메뉴 버튼 (모바일 환경에서 클릭하기 쉽도록)
            if st.button("홈 (게시판)", use_container_width=True, key="nav_home"):
                st.session_state.page = "home"
                st.rerun()
            if st.button("새 글 작성", use_container_width=True, key="nav_write"):
                st.session_state.page = "write"
                st.rerun()
            if st.button("내 정보", use_container_width=True, key="nav_profile"):
                st.session_state.page = "profile"
                st.rerun()
                
            st.markdown("---")
            if st.button("로그아웃", use_container_width=True, type="secondary", key="nav_logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "login"
                st.session_state.selected_post_id = None
                st.rerun()
        else:
            st.info("로그인 후 이용해 주세요.")
            
    # 페이지 라우팅
    if st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "signup":
        show_signup_page()
    elif st.session_state.logged_in:
        if st.session_state.page == "home":
            show_home_page()
        elif st.session_state.page == "write":
            show_write_page()
        elif st.session_state.page == "profile":
            show_profile_page()
        elif st.session_state.page == "detail" and st.session_state.selected_post_id is not None:
            show_post_detail(st.session_state.selected_post_id)
        else:
            st.session_state.page = "home"
            st.rerun()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
