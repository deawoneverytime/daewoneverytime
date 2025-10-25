import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

# ✅ 페이지 설정
st.set_page_config(page_title="대원타임", page_icon="🎓", layout="wide")

# ✅ CSS 스타일링: 감각적인 디자인을 위한 사용자 지정 CSS
STYLING = """
<style>
/* 메인 제목 스타일 */
.main-title {
    font-size: 3em;
    font-weight: 800;
    color: #1E90FF; /* 대원 Blue Accent */
    text-align: center;
    margin-bottom: 20px;
}
/* 섹션 헤더 스타일 */
.sub-header {
    font-size: 1.5em;
    font-weight: 600;
    color: #333333;
    border-bottom: 2px solid #f0f2f6;
    padding-bottom: 5px;
    margin-top: 15px;
}

/* 네이트판 스타일: 게시글 간격을 좁게 만드는 얇은 구분선 */
.thin-divider {
    margin: 0px 0 !important; /* 마진 0 */
    border-top: 1px solid #eee;
    opacity: 0.8;
}

/* 게시글 목록의 버튼(제목) 스타일: 링크처럼 보이게 하면서 세로 간격 최소화 */
div[data-testid^="stColumn"] div.stButton > button {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #333333 !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 2px 0 !important; /* <<-- 수직 패딩 최소화 */
    margin: 0 !important;
    cursor: pointer !important;
    width: 100%;
    white-space: nowrap; 
    overflow: hidden;
    text-overflow: ellipsis;
}

/* 제목 버튼 호버 시 스타일 */
div[data-testid^="stColumn"] div.stButton > button:hover {
    color: #1E90FF !important; 
    text-decoration: underline !important;
    background-color: transparent !important;
}

/* st.columns로 생성된 수평 블록의 세로 간격을 줄입니다. */
div[data-testid^="stHorizontalBlock"] {
    /* 수평 블록 내부의 위아래 공간을 줄여 게시글 행 간격을 좁힙니다. */
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}

/* 💡 고정된 오른쪽 하단 통계 박스 스타일 */
.fixed-stats {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #ffffff;
    border: 1px solid #1E90FF;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); /* 좀 더 눈에 띄게 */
    z-index: 1000;
    width: 180px;
}
.stats-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
    font-size: 1.1em;
}

/* 💡 프로필 카드 스타일 (show_profile_page용) */
.profile-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px;
    background-color: #ffffff;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    max-width: 450px;
    margin: 30px auto;
}
.profile-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px dashed #f0f0f0;
}
.profile-item:last-child {
    border-bottom: none;
}
.profile-label {
    font-weight: 600;
    color: #555;
    width: 30%;
}
.profile-value {
    font-weight: 700;
    color: #1E90FF; /* Blue accent */
    width: 65%;
    text-align: right;
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

    # 💡 posts 테이블에 views 컬럼 추가
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        author TEXT,        -- 화면에 표시되는 작성자 (익명 또는 아이디)
        real_author TEXT,   -- 실제 작성자 (아이디, 삭제 권한 확인용)
        created_at TEXT,
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0 -- 💡 조회수 컬럼
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
    """
    특정 ID의 게시글을 가져오고, 조회수를 1 증가시킵니다.
    (id, title, content, author, real_author, created_at, likes, views) 8개 컬럼 반환
    """
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    
    # 1. 조회수 증가 (조회 행위 시점)
    c.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    conn.commit()
    
    # 2. 게시글 데이터 가져오기 (8개 컬럼)
    c.execute("SELECT id, title, content, author, real_author, created_at, likes, views FROM posts WHERE id = ?", (post_id,))
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
        # 좋아요 취소
        c.execute("UPDATE posts SET likes = likes - 1 WHERE id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    else:
        # 좋아요 추가
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
    # 💡 created_at은 실제 날짜와 시간을 정확히 반영
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    c.execute('''INSERT INTO posts (title, content, author, real_author, created_at)
                  VALUES (?, ?, ?, ?, ?)''',
              (title, content, author, st.session_state.username, current_time))
    conn.commit()
    conn.close()

def get_all_posts():
    """모든 게시글을 최신순으로 가져오기 (id, title, author, created_at, likes)."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # views 컬럼은 목록에 표시하지 않으므로 5개 컬럼만 가져옵니다.
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
            if st.form_submit_button("로그인", use_container_width=True):
                success, msg = login(username, password)
                if success:
                    st.success(msg)
                    st.balloons()
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()
        st.markdown("계정이 없으신가요? **회원가입**을 진행하세요.")
        if st.button("회원가입하기", use_container_width=True, key="go_to_signup"):
            st.session_state.page = "signup"
            st.rerun()

# ✅ 회원가입 페이지
def show_signup_page():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    def signup(username, password, email, student_id):
        if not re.match(EMAIL_REGEX, email) or not re.match(PASSWORD_REGEX, password):
            return False, "입력 형식을 확인하세요. 비밀번호는 8자 이상, 대/소문자/숫자 포함해야 합니다."
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (
                username, hash_password(password), email, student_id,
                current_time
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

            if st.form_submit_button("회원가입 완료", use_container_width=True):
                success, msg = signup(username, password, email, student_id)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()
        if st.button("로그인 페이지로 돌아가기", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
    conn.close()


# ✅ 게시판 목록 페이지 (수정: 클린 목록 표시 및 간격 좁게)
def show_home_page():
    st.markdown('<p class="sub-header">📋 자유게시판</p>', unsafe_allow_html=True)

    col_write, col_spacer = st.columns([1, 6])
    with col_write:
        if st.button("✍️ 글쓰기", use_container_width=True, type="primary"):
            st.session_state.page = "write"
            st.rerun()
    st.divider()

    posts = get_all_posts()
    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해보세요!")
        return

    # 게시글 목록 헤더 (항목 정렬을 위해 st.columns 사용)
    header_col1, header_col2, header_col3, header_col4 = st.columns([4, 1.5, 1, 0.5])
    header_col1.markdown('**제목**', unsafe_allow_html=True)
    header_col2.markdown('<div style="text-align: center;">**작성자**</div>', unsafe_allow_html=True)
    header_col3.markdown('<div style="text-align: center;">**작성일**</div>', unsafe_allow_html=True)
    header_col4.markdown('<div style="text-align: right;">**❤️**</div>', unsafe_allow_html=True)
    
    # 얇은 구분선 (게시물 간격 시작)
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    
    # 게시글 목록 (클린하게 표시, 간격 최소화)
    for post in posts:
        post_id, title, author, created_at, likes = post
        
        # 1. 컬럼 정의
        col1, col2, col3, col4 = st.columns([4, 1.5, 1, 0.5])
        
        # 2. 버튼 배치 (클릭 기능)
        with col1:
            # 제목을 버튼으로 사용하여 클릭 가능하게 합니다. (CSS로 링크처럼 보이도록 했습니다)
            if st.button(title, key=f"post_title_{post_id}"):
                go_to_detail(post_id)
        
        # 3. 나머지 정보 표시 (정렬 및 간격 조절을 위해 st.markdown 사용)
        # created_at[:10]으로 날짜만 표시하여 목록의 간결함을 유지합니다.
        col2.markdown(f'<div style="text-align: center; font-size: 0.9em; color: #666; padding: 5px 0;">{author}</div>', unsafe_allow_html=True)
        col3.markdown(f'<div style="text-align: center; font-size: 0.9em; color: #666; padding: 5px 0;">{created_at[:10]}</div>', unsafe_allow_html=True)
        col4.markdown(f'<div style="text-align: right; font-weight: 700; color: #FF4B4B; padding: 5px 0;">{likes}</div>', unsafe_allow_html=True)

        # 4. 구분선
        st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)


# ✅ 게시글 상세 페이지 (내용, 좋아요, 댓글 기능)
def show_post_detail(post_id):
    # get_post_by_id 함수 내에서 조회수가 1 증가됩니다.
    post = get_post_by_id(post_id) 
    if not post:
        st.error("존재하지 않는 게시글입니다.")
        if st.button("목록으로 돌아가기"):
            st.session_state.page = "home"
            st.rerun()
        return

    # 8개의 컬럼: id, title, content, author, real_author, created_at, likes, views 💡views 추가
    post_id, title, content, author, real_author, created_at, likes, views = post
    username = st.session_state.username

    st.markdown(f'## {title}')
    # 💡 작성일시 (created_at)는 정확한 시간까지 표시됩니다.
    st.caption(f"**작성자:** {author} | **작성일시:** {created_at} | **❤️ {likes}**") 
    st.divider()
    
    # 게시글 내용
    st.write(content)
    st.divider()
    
    # 💡 오른쪽 하단에 하트수와 조회수 표시 (Fixed Stats Box)
    st.markdown(f"""
    <div class="fixed-stats">
        <div style="font-weight: 700; color: #1E90FF; margin-bottom: 10px; font-size: 1.2em;">📊 통계 정보</div>
        <div class="stats-item">
            <span style="color: #FF4B4B;">❤️ 하트 수</span>
            <span style="font-weight: 800; color: #FF4B4B;">{likes}</span>
        </div>
        <div class="stats-item">
            <span style="color: #4CAF50;">👀 조회 수</span>
            <span style="font-weight: 800; color: #4CAF50;">{views}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


    col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
    
    # 좋아요 버튼
    with col1:
        is_liked = has_user_liked(post_id, username)
        like_label = "❤️ 좋아요 취소" if is_liked else "🤍 좋아요"
        if st.button(like_label, key=f"detail_like_{post_id}", use_container_width=True):
            like_post(post_id, username)
            st.rerun()
            
    # 삭제 버튼 (작성자에게만)
    with col2:
        if real_author == username:
            if st.button("🗑️ 삭제", key=f"detail_del_{post_id}", type="secondary", use_container_width=True):
                if delete_post(post_id):
                    st.success("게시글이 삭제되었습니다.")
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("삭제 권한이 없습니다.")

    # 목록으로 버튼
    with col3:
        if st.button("🔙 목록으로", key=f"detail_back_{post_id}", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    st.divider()

    # ✅ 댓글 섹션
    st.markdown('### 💬 댓글')
    comments = get_comments(post_id)
    
    # 댓글 목록 표시
    if comments:
        for c in comments:
            c_author, c_content, c_created = c
            # 댓글 표시 형식 개선
            st.markdown(f"""
            <div style="padding: 10px 0; border-bottom: 1px solid #eee;">
                <p style="margin: 0;">
                    <span style="font-weight: bold; color: #555;">👤 {c_author}</span>
                    <span style="font-size: 0.8em; color: #999;"> | {c_created}</span>
                </p>
                <p style="margin: 5px 0 0 15px;">{c_content}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 댓글이 없습니다.")

    st.markdown('#### 댓글 작성')
    # 댓글 작성 폼
    with st.form(key=f"comment_form_{post_id}", clear_on_submit=True):
        comment_text = st.text_area("댓글 내용을 입력하세요", key=f"comment_box_{post_id}", height=80, label_visibility="collapsed")
        
        colA, colB = st.columns([3, 1])
        with colA:
            anonymous = st.checkbox("익명으로 작성 (댓글 작성자: 익명)", key=f"anon_comment_{post_id}")
        with colB:
            if st.form_submit_button("댓글 등록", use_container_width=True, type="primary"):
                if comment_text.strip():
                    add_comment(post_id, comment_text, anonymous)
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
            if st.form_submit_button("등록", type="primary"):
                if title.strip() and content.strip():
                    create_post(title, content, anonymous)
                    st.success("게시글이 성공적으로 작성되었습니다!")
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
        with col2:
            if st.form_submit_button("취소"):
                st.session_state.page = "home"
                st.rerun()

# ✅ 프로필 페이지 (💡깔끔하고 센스있게 개선)
def show_profile_page():
    st.markdown('<p class="sub-header">👤 내 정보</p>', unsafe_allow_html=True)
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    
    c.execute("SELECT username, password, email, student_id, created_at FROM users WHERE username = ?", (st.session_state.username,))
    user = c.fetchone()
    conn.close()

    if user:
        # DB에서 가져온 5개 컬럼 중 password(_)를 제외하고 4개만 사용
        username, _, email, student_id, created = user
        
        # 💡 깔끔하고 센스있는 정보 표시를 위해 커스텀 HTML 카드 사용
        st.markdown(f"""
        <div class="profile-card">
            <div style="text-align: center; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #1E90FF;">
                <h3 style="font-size: 1.8em; font-weight: 800; color: #1E90FF; margin: 0;">{username}</h3>
                <p style="color: #999; font-size: 0.85em; margin-top: 5px;">가입일: {created}</p>
            </div>
            
            <div class="profile-item">
                <span class="profile-label">아이디</span>
                <span class="profile-value">{username}</span>
            </div>
            <div class="profile-item">
                <span class="profile-label">이메일</span>
                <span class="profile-value">{email}</span>
            </div>
            <div class="profile-item">
                <span class="profile-label">학번</span>
                <span class="profile-value">{student_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("사용자 정보를 불러올 수 없습니다.")
        if st.button("홈으로 돌아가기", key="profile_error_back"):
            st.session_state.page = "home"
            st.rerun()

# ✅ 메인 실행
def main():
    init_db()

    # 세션 상태 초기화
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "login"
        st.session_state.selected_post_id = None # 상세 페이지로 이동할 때 사용할 ID

    # 사이드바 (내비게이션)
    with st.sidebar:
        st.markdown('<p style="font-size: 1.5em; font-weight: 700;">🎓 대원 커뮤니티</p>', unsafe_allow_html=True)
        st.divider()

        if st.session_state.logged_in:
            st.success(f"**{st.session_state.username}**님 환영합니다!")
            
            # 메뉴 버튼
            if st.button("🏠 홈 (게시판)", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
            if st.button("✍️ 글쓰기", use_container_width=True):
                st.session_state.page = "write"
                st.rerun()
            if st.button("👤 내 정보", use_container_width=True):
                st.session_state.page = "profile"
                st.rerun()
                
            st.divider()
            if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "login"
                st.session_state.selected_post_id = None
                st.rerun()
        else:
            # 비로그인 상태일 때: 로그인/회원가입 페이지 외에는 접근할 수 없음
            st.info("로그인이 필요합니다.")
            
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
            # 기본적으로 홈 페이지로 리다이렉트
            st.session_state.page = "home"
            st.rerun()
    else:
        # 로그인되지 않은 상태에서 다른 페이지로 이동 시도 시 로그인 페이지로
        show_login_page()


if __name__ == "__main__":
    main()
