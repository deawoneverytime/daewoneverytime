import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

# ✅ 페이지 설정
st.set_page_config(page_title="대원타임", page_icon="🎓", layout="wide")

# ✅ 학교 목록 정의 (회원가입 드롭다운에 사용)
SCHOOLS = ["대원고등학교", "대원여자고등학교", "대원외국어고등학교"]

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
/* 게시글 목록 제목 스타일 */
.post-list-title {
    font-weight: 600;
    color: #1E90FF;
    cursor: pointer; /* 클릭 가능한 요소임을 표시 */
}
/* 좋아요 수 표시 스타일 */
.metric-heart {
    font-size: 1.1em;
    font-weight: 700;
    color: #FF4B4B; /* Red for Likes */
    margin-right: 10px;
}
/* 조회수 표시 스타일 */
.metric-view {
    font-size: 1.1em;
    font-weight: 700;
    color: #4CAF50; /* Green for Views */
}
/* 추천 게시글 카드 스타일 */
.recommend-card {
    border: 1px solid #ddd;
    padding: 10px;
    border-radius: 8px;
    margin-top: 10px;
    transition: box-shadow 0.3s;
}
.recommend-card:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)


# ✅ 이메일 & 비밀번호 정규식: 데이터 유효성 검사
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# ✅ DB 초기화: 필요한 테이블 생성 (views 컬럼 추가, student_id -> school 변경)
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 사용자 테이블 (student_id -> school로 컬럼명 변경)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT UNIQUE,
        school TEXT,            -- 학교 선택 항목으로 변경
        created_at TEXT
    )''')

    # 게시글 테이블 (views 컬럼 추가)
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        author TEXT,
        real_author TEXT,
        created_at TEXT,
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0     -- 조회수 컬럼 추가
    )''')

    # 댓글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        author TEXT,
        real_author TEXT,
        content TEXT,
        created_at TEXT,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    # 좋아요 기록 테이블
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
    """특정 ID의 게시글을 가져옵니다."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = c.fetchone()
    conn.close()
    return post

def increment_views(post_id):
    """게시글의 조회수를 1 증가시킵니다."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

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

# ... (like_post, has_user_liked, create_post, delete_post, add_comment, get_comments 함수는 변경 없음)

def create_post(title, content, is_anonymous=False):
    """게시글 작성."""
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
    """모든 게시글을 최신순으로 가져오기 (홈 화면에 필요한 필드만)."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT id, title, author, created_at, likes, views FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

def get_recommended_posts(current_post_id, limit=3):
    """현재 게시글을 제외한 최신 게시물 N개를 가져옵니다."""
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # 최신 순으로 정렬하고 현재 ID를 제외
    c.execute(f"SELECT id, title FROM posts WHERE id != ? ORDER BY id DESC LIMIT {limit}", (current_post_id,))
    posts = c.fetchall()
    conn.close()
    return posts

# ... (이하 나머지 DB 함수는 변경 없음)

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

# ✅ 로그인 페이지 (변경 없음)
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

        st.markdown("---")
        st.markdown("계정이 없으신가요? **회원가입**을 진행하세요.")
        if st.button("회원가입하기", use_container_width=True, key="go_to_signup"):
            st.session_state.page = "signup"
            st.rerun()

# ✅ 회원가입 페이지 (학교 선택 드롭다운으로 변경)
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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-title">🎓 대원타임</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">회원가입</p>', unsafe_allow_html=True)

        with st.form("signup_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password", help="8자 이상, 대/소문자/숫자 포함")
            email = st.text_input("이메일")
            
            # 📌 학번 입력 대신 학교 선택 드롭다운 사용
            school = st.selectbox("학교를 선택하세요", options=SCHOOLS, index=0)

            if st.form_submit_button("회원가입 완료", use_container_width=True):
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

# ✅ 게시판 목록 페이지 (조회수 컬럼 추가)
def show_home_page():
    st.markdown('<p class="sub-header">📋 자유게시판</p>', unsafe_allow_html=True)

    col_write, col_spacer = st.columns([1, 6])
    with col_write:
        if st.button("✍️ 글쓰기", use_container_width=True, type="primary"):
            st.session_state.page = "write"
            st.rerun()
    st.markdown("---")

    posts = get_all_posts()
    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해보세요!")
        return

    # 게시글 목록 헤더 (조회수 추가)
    header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([4, 1.5, 1, 0.5, 0.5])
    header_col1.markdown('**제목**', unsafe_allow_html=True)
    header_col2.markdown('**작성자**', unsafe_allow_html=True)
    header_col3.markdown('**작성일**', unsafe_allow_html=True)
    header_col4.markdown('**❤️**', unsafe_allow_html=True)
    header_col5.markdown('**👀**', unsafe_allow_html=True) # 조회수 헤더
    st.markdown("---")
    
    # 게시글 목록 (간소화)
    for post in posts:
        # DB에서 가져오는 순서: id, title, author, created_at, likes, views
        post_id, title, author, created_at, likes, views = post
        
        col1, col2, col3, col4, col5 = st.columns([4, 1.5, 1, 0.5, 0.5])
        
        # 제목을 클릭하면 상세 페이지로 이동
        with col1:
            if st.button(title, key=f"post_title_{post_id}", use_container_width=True):
                go_to_detail(post_id)
        
        col2.write(author)
        col3.write(created_at[:10]) # 날짜만 표시
        col4.write(likes)
        col5.write(views) # 조회수 표시


# ✅ 게시글 상세 페이지 (좋아요, 조회수 표시 위치 및 추천 게시글 추가)
def show_post_detail(post_id):
    # 📌 상세 페이지 진입 시 조회수 증가
    increment_views(post_id)
    
    post = get_post_by_id(post_id)
    if not post:
        st.error("존재하지 않는 게시글입니다.")
        if st.button("목록으로 돌아가기"):
            st.session_state.page = "home"
            st.rerun()
        return

    # DB에서 가져오는 순서: id, title, content, author, real_author, created_at, likes, views
    post_id, title, content, author, real_author, created_at, likes, views = post
    username = st.session_state.username

    st.markdown(f'## {title}')
    st.caption(f"**작성자:** {author} | **작성일:** {created_at}")
    st.markdown("---")
    
    # 게시글 내용
    st.write(content)
    st.markdown("---")

    # 📌 좋아요 및 조회수 표시 (내용 아래쪽)
    col_metrics, col_spacer = st.columns([3, 7])
    with col_metrics:
        st.markdown(f'<span class="metric-heart">❤️ 좋아요 {likes}</span> <span class="metric-view">👀 조회수 {views}</span>', unsafe_allow_html=True)

    st.markdown("---")

    # 액션 버튼 영역
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

    st.markdown("---")

    # ✅ 댓글 섹션
    st.markdown('### 💬 댓글')
    comments = get_comments(post_id)
    
    if comments:
        for c in comments:
            c_author, c_content, c_created = c
            st.markdown(f"**👤 {c_author}** | <small>_{c_created}_</small>", unsafe_allow_html=True)
            st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{c_content}")
            st.markdown("---")
    else:
        st.info("아직 댓글이 없습니다.")

    st.markdown('#### 댓글 작성')
    # clear_on_submit=True를 사용하여 제출 후 텍스트 영역을 자동으로 비웁니다.
    with st.form(key=f"comment_form_{post_id}", clear_on_submit=True):
        comment_text = st.text_area("댓글 내용을 입력하세요", key=f"comment_box_{post_id}", height=80, label_visibility="collapsed")
        
        colA, colB = st.columns([3, 1])
        with colA:
            anonymous = st.checkbox("익명으로 작성", key=f"anon_comment_{post_id}")
        with colB:
            if st.form_submit_button("댓글 등록", use_container_width=True, type="primary"):
                if comment_text.strip():
                    add_comment(post_id, comment_text, anonymous)
                    st.success("댓글이 등록되었습니다.")
                    st.rerun() # 댓글 목록 업데이트를 위해 페이지 새로고침
                else:
                    st.warning("댓글 내용을 입력하세요.")

    st.markdown("---")
    
    # 📌 추천 게시물 섹션
    st.markdown('### 🌟 추천 게시물')
    recommended_posts = get_recommended_posts(post_id, limit=3)
    
    if recommended_posts:
        cols = st.columns(len(recommended_posts))
        for i, (rec_id, rec_title) in enumerate(recommended_posts):
            with cols[i]:
                # 추천 게시글 카드
                st.markdown(f'<div class="recommend-card">', unsafe_allow_html=True)
                st.markdown(f"**{rec_title}**")
                
                # 버튼을 클릭하면 해당 게시물 상세 페이지로 이동
                if st.button("보러가기", key=f"rec_btn_{rec_id}", use_container_width=True):
                    go_to_detail(rec_id)
                st.markdown(f'</div>', unsafe_allow_html=True)
    else:
        st.info("다른 게시글이 없습니다.")


# ✅ 글쓰기 페이지 (변경 없음)
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

# ✅ 프로필 페이지 (학교 정보 표시로 변경)
def show_profile_page():
    st.markdown('<p class="sub-header">👤 내 정보</p>', unsafe_allow_html=True)
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # DB에서 사용자 정보 조회 (school 필드 포함)
    c.execute("SELECT username, email, school, created_at FROM users WHERE username = ?", (st.session_state.username,))
    user = c.fetchone()
    conn.close()

    if user:
        username, email, school, created = user
        st.metric(label="아이디", value=username)
        st.metric(label="이메일", value=email)
        st.metric(label="소속 학교", value=school) # 학교 정보 표시
        st.metric(label="가입일", value=created)
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
        st.markdown('<p style="font-size: 1.5em; font-weight: 700;">🎓 대원 커뮤니티</p>', unsafe_allow_html=True)
        st.markdown("---")

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
                
            st.markdown("---")
            if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "login"
                st.session_state.selected_post_id = None
                st.rerun()
        else:
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
            st.session_state.page = "home"
            st.rerun()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
