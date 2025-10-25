import streamlit as st
import sqlite3
import hashlib
import re  # ✅ 이메일 형식 검증용
from datetime import datetime

# ✅ 페이지 설정
st.set_page_config(page_title="대원대학교 에브리타임", page_icon="🎓", layout="wide")

# ✅ 이메일 형식 정규식
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# ✅ DB 초기화 함수
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 사용자 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT,
        student_id TEXT,
        created_at TEXT
    )''')

    # 게시글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        author TEXT,
        real_author TEXT,
        created_at TEXT,
        likes INTEGER DEFAULT 0
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

    conn.commit()
    conn.close()

# ✅ 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 회원가입 (이메일 검증 포함)
def signup(username, password, email, student_id):
    # 이메일 형식 검증
    if not re.match(EMAIL_REGEX, email):
        return False, "잘못된 이메일 형식입니다. (예: example@domain.com)"

    # 비밀번호 길이 검증
    if len(password) < 6:
        return False, "비밀번호는 6자 이상이어야 합니다."

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "이미 존재하는 사용자명입니다."

    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (
        username,
        hash_password(password),
        email,
        student_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    return True, "회원가입이 완료되었습니다!"

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
    c.execute("SELECT * FROM posts ORDER BY id DESC")
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

# ✅ 좋아요 기능
def like_post(post_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

# ✅ 로그인 페이지
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🎓 대원대학교 에브리타임")
        st.subheader("로그인 / 회원가입")

        tab1, tab2 = st.tabs(["로그인", "회원가입"])

        with tab1:
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            if st.button("로그인", use_container_width=True):
                success, msg = login(username, password)
                if success:
                    st.success(msg)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

        with tab2:
            username = st.text_input("아이디", key="signup_user")
            password = st.text_input("비밀번호", type="password", key="signup_pw")
            email = st.text_input("이메일")
            student_id = st.text_input("학번")

            if st.button("회원가입", use_container_width=True):
                success, msg = signup(username, password, email, student_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ✅ 나머지 페이지 함수들 (게시판/글쓰기/프로필 등)
# 👉 그대로 유지 (변경 없음)
# ... [생략: show_home_page(), show_write_page(), show_profile_page(), main() 등 기존 그대로]

# ✅ 메인 실행
def main():
    init_db()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "home"

    with st.sidebar:
        st.title("🎓 대원대학교 커뮤니티")

        if st.session_state.logged_in:
            st.success(f"{st.session_state.username}님 환영합니다!")
            if st.button("🏠 홈"):
                st.session_state.page = "home"
                st.rerun()
            if st.button("✍️ 글쓰기"):
                st.session_state.page = "write"
                st.rerun()
            if st.button("👤 내 정보"):
                st.session_state.page = "profile"
                st.rerun()
            st.divider()
            if st.button("🚪 로그아웃"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "home"
                st.rerun()
        else:
            st.info("로그인이 필요합니다.")

    # 페이지 라우팅
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.page == "home":
            show_home_page()
        elif st.session_state.page == "write":
            show_write_page()
        elif st.session_state.page == "profile":
            show_profile_page()

if __name__ == "__main__":
    main()
