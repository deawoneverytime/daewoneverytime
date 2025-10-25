import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

# ✅ 페이지 설정
st.set_page_config(page_title="대원대학교 에브리타임", page_icon="🎓", layout="wide")

# ✅ 정규식 설정
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'  # 8자 이상, 대소문자+숫자 포함

# ✅ DB 초기화
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

# ✅ 회원가입
def signup(username, password, email, student_id):
    # 아이디 길이 검증
    if len(username) < 5:
        return False, "아이디가 너무 짧습니다. (5자 이상 입력해주세요.)"

    # 이메일 형식 검증
    if not re.match(EMAIL_REGEX, email):
        return False, "잘못된 이메일 형식입니다. (예: example@domain.com)"

    # 비밀번호 강도 검증
    if not re.match(PASSWORD_REGEX, password):
        return False, (
            "비밀번호는 8자 이상이어야 하며, "
            "영문 대문자, 소문자, 숫자를 모두 포함해야 합니다."
        )

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 중복 확인
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "이미 등록된 이메일입니다."

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "이미 사용 중인 아이디입니다."

    # 회원정보 저장
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

# ✅ 로그인 / 회원가입 페이지
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

# ✅ 홈 페이지
def show_home_page():
    st.title("🏠 커뮤니티 게시판")

    posts = get_all_posts()
    if not posts:
        st.info("아직 게시글이 없습니다. 글을 작성해보세요!")
        return

    for post in posts:
        st.markdown(f"### {post[1]}")
        st.write(post[2])
        st.caption(f"작성자: {post[3]} | 작성일: {post[5]} | ❤️ {post[6]}개")
        if st.button(f"좋아요 ❤️ ({post[6]})", key=f"like_{post[0]}"):
            like_post(post[0])
            st.rerun()
        st.divider()

# ✅ 글쓰기 페이지
def show_write_page():
    st.title("✍️ 글쓰기")
    title = st.text_input("제목")
    content = st.text_area("내용")
    anonymous = st.checkbox("익명으로 작성")

    if st.button("등록"):
        if title.strip() == "" or content.strip() == "":
            st.error("제목과 내용을 모두 입력해주세요.")
        else:
            create_post(title, content, anonymous)
            st.success("게시글이 등록되었습니다.")
            st.rerun()

# ✅ 프로필 페이지
def show_profile_page():
    st.title("👤 내 정보")
    st.write(f"아이디: {st.session_state.username}")

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
