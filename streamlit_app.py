import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

# ✅ 페이지 설정
st.set_page_config(page_title="대원타임", page_icon="🎓", layout="wide")

# CSS를 사용하여 Streamlit 앱의 디자인 개선 (제목 색상 등)
# Streamlit은 사용자 정의 CSS에 제한이 있지만, Markdown을 통해 일부 스타일을 적용합니다.
STYLING = """
<style>
.main-title {
    font-size: 3em;
    font-weight: 800;
    color: #1E90FF; /* Daewon Blue Accent */
    text-align: center;
    margin-bottom: 20px;
}
.sub-header {
    font-size: 1.5em;
    font-weight: 600;
    color: #333333;
    border-bottom: 2px solid #f0f2f6;
    padding-bottom: 5px;
    margin-top: 15px;
}
.post-title {
    font-size: 1.5em;
    font-weight: 700;
    color: #333333;
}
.post-card {
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.metric-heart {
    font-size: 1.2em;
    font-weight: 700;
    color: #FF4B4B; /* Red for Likes */
}
</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)


# ✅ 이메일 & 비밀번호 정규식
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# ✅ DB 초기화
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

    # 좋아요 기록 테이블 (사용자당 1회 제한을 위한 테이블)
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        username TEXT,
        post_id INTEGER,
        created_at TEXT,
        PRIMARY KEY (username, post_id),
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    conn.commit()
    conn.close()

# ✅ 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 회원가입
def signup(username, password, email, student_id):
    if not re.match(EMAIL_REGEX, email):
        return False, "잘못된 이메일 형식입니다. (예: example@domain.com)"
    if not re.match(PASSWORD_REGEX, password):
        return False, (
            "비밀번호는 8자 이상이어야 하며, "
            "대문자, 소문자, 숫자를 각각 최소 1개 이상 포함해야 합니다."
        )

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "이미 존재하는 아이디입니다."

    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "이미 등록된 이메일입니다."

    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (
        username,
        hash_password(password),
        email,
        student_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    return True, "회원가입이 완료되었습니다! 로그인해 주세요."

# ✅ 로그인
def login(username, password):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False, "존재하지 않는 사용자입니다."

    if row[0] != hash_password(password):
        return False, "비밀번호가 일치하지 않습니다."

    st.session_state.logged_in = True
    st.session_state.username = username
    return True, "로그인 성공!"

# ✅ 좋아요 기능 (좋아요/취소 토글) - 메시지 출력 제거
def like_post(post_id, username):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 1. 좋아요 중복 확인
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    if c.fetchone():
        # 좋아요 기록이 있다면 -> 좋아요 취소
        c.execute("UPDATE posts SET likes = likes - 1 WHERE id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    else:
        # 좋아요 기록이 없다면 -> 좋아요 추가
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        c.execute("INSERT INTO likes (username, post_id, created_at) VALUES (?, ?, ?)",
                  (username, post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    return True # 좋아요/취소 상태만 반환

# ✅ 사용자가 해당 게시물에 좋아요를 눌렀는지 확인
def has_user_liked(post_id, username):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
    liked = c.fetchone() is not None
    conn.close()
    return liked

# (게시글 작성, 불러오기, 삭제, 댓글 추가, 불러오기 함수는 변경 없음)

# ✅ 게시글 작성
def create_post(title, content, is_anonymous=False):
    author = "익명" if is_anonymous else st.session_state.username
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('''INSERT INTO posts (title, content, author, real_author, created_at)
              VALUES (?, ?, ?, ?, ?)''',
              (title, content, author, st.session_state.username,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ✅ 게시글 불러오기
def get_all_posts():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # 📌 수정: SELECT * 대신 7개의 컬럼만 명시적으로 선택하여 언패킹 에러를 방지합니다.
    c.execute("SELECT id, title, content, author, real_author, created_at, likes FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

# ✅ 게시글 삭제
def delete_post(post_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT real_author FROM posts WHERE id = ?", (post_id,))
    author = c.fetchone()
    if author and author[0] == st.session_state.username:
        # 댓글도 함께 삭제
        c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# ✅ 댓글 추가
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

# ✅ 댓글 불러오기
def get_comments(post_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT author, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments


# --- 페이지 함수 재구성 및 디자인 개선 ---

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

        st.markdown("---")
        st.markdown("계정이 없으신가요? **회원가입**을 진행하세요.")
        if st.button("회원가입하기", use_container_width=True, key="go_to_signup"):
            st.session_state.page = "signup"
            st.rerun()

# ✅ 회원가입 페이지 (분리)
def show_signup_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-title">🎓 대원타임</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">회원가입</p>', unsafe_allow_html=True)

        with st.form("signup_form"):
            username = st.text_input("아이디", key="signup_user_p2")
            password = st.text_input("비밀번호", type="password", key="signup_pw_p2",
                                     help="8자 이상, 대문자, 소문자, 숫자 포함")
            email = st.text_input("이메일", key="signup_email_p2")
            student_id = st.text_input("학번", key="signup_sid_p2")

            if st.form_submit_button("회원가입 완료", use_container_width=True, key="signup_btn_p2"):
                success, msg = signup(username, password, email, student_id)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        if st.button("로그인 페이지로 돌아가기", key="go_to_login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ✅ 게시판 페이지
def show_home_page():
    st.markdown('<p class="sub-header">📋 자유게시판</p>', unsafe_allow_html=True)

    # 글쓰기 버튼을 우측 상단에 배치
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

    for post in posts:
        # post가 이제 7개 요소만 포함하도록 보장됩니다.
        post_id, title, content, author, real_author, created_at, likes = post
        
        # 현재 사용자가 좋아요를 눌렀는지 확인
        is_liked = has_user_liked(post_id, st.session_state.username)

        with st.container(border=True): # 게시글 카드 디자인
            
            # 게시글 헤더
            st.markdown(f'<p class="post-title">📝 {title}</p>', unsafe_allow_html=True)
            st.caption(f"**작성자:** {author} | **작성일:** {created_at}")

            st.markdown("---")
            
            # 게시글 내용 (최대 4줄까지만 보여주고 이후는 줄임)
            st.text_area("내용", content, height=100, disabled=True, label_visibility="collapsed")
            
            # 좋아요 및 액션 버튼 영역
            col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
            
            with col1:
                st.markdown(f'<p class="metric-heart">❤️ {likes}</p>', unsafe_allow_html=True)

            with col2:
                like_label = "❤️ 좋아요 취소" if is_liked else "🤍 좋아요"
                if st.button(like_label, key=f"like_{post_id}", use_container_width=True):
                    like_post(post_id, st.session_state.username)
                    st.rerun() # 즉시 반영

            with col3:
                if real_author == st.session_state.username:
                    if st.button("🗑️ 삭제", key=f"del_{post_id}", type="secondary", use_container_width=True):
                        delete_post(post_id)
                        st.success("게시글이 삭제되었습니다.")
                        st.rerun()

            st.markdown("---")
            
            # 댓글 영역을 Expander로 숨겨서 깔끔하게 유지
            comments = get_comments(post_id)
            with st.expander(f"💬 댓글 보기 ({len(comments)})"):
                if comments:
                    for c in comments:
                        c_author, c_content, c_created = c
                        st.markdown(f"**👤 {c_author}** | <small>_{c_created}_</small>", unsafe_allow_html=True)
                        st.write(f"💬 {c_content}")
                        st.markdown("---")
                else:
                    st.markdown("아직 댓글이 없습니다.")

                # 댓글 작성 폼
                comment_text = st.text_area("댓글 작성", key=f"comment_box_{post_id}", height=80, label_visibility="collapsed")
                colA, colB = st.columns([3, 1])
                with colA:
                    anonymous = st.checkbox("익명으로 작성", key=f"anon_{post_id}")
                with colB:
                    if st.button("댓글 등록", key=f"submit_comment_{post_id}", use_container_width=True, type="primary"):
                        if comment_text.strip():
                            add_comment(post_id, comment_text, anonymous)
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

# ✅ 프로필 페이지
def show_profile_page():
    st.markdown('<p class="sub-header">👤 내 정보</p>', unsafe_allow_html=True)
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (st.session_state.username,))
    user = c.fetchone()
    conn.close()

    if user:
        username, _, email, student_id, created = user
        
        st.metric(label="아이디", value=username)
        st.metric(label="이메일", value=email)
        st.metric(label="학번", value=student_id)
        st.metric(label="가입일", value=created)
    else:
        st.error("사용자 정보를 불러올 수 없습니다.")

# ✅ 메인 실행
def main():
    init_db()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "login"

    # 사이드바 (내비게이션)
    with st.sidebar:
        st.markdown('<p style="font-size: 1.5em; font-weight: 700;">🎓 대원 커뮤니티</p>', unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.logged_in:
            st.success(f"**{st.session_state.username}**님 환영합니다!")
            
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
                st.rerun()
        else:
            st.info("로그인이 필요합니다.")
            if st.button("로그인 페이지로 이동", use_container_width=True, type="primary"):
                st.session_state.page = "login"
                st.rerun()
            
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

if __name__ == "__main__":
    main()
