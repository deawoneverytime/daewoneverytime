import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ✅ 페이지 설정
st.set_page_config(page_title="대원대학교 에브리타임", page_icon="🎓", layout="wide")

# ==============================================================================
# 🛠️ DB 및 유틸리티 함수
# ==============================================================================

# ✅ DB 초기화 함수
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 사용자 테이블 (school 컬럼 포함하여 생성)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        email TEXT,
        student_id TEXT,
        created_at TEXT,
        school TEXT
    )''')

    # 💡 DB 마이그레이션 체크: school 컬럼이 기존 테이블에 없을 경우 추가
    try:
        # school 컬럼을 조회해 봅니다.
        c.execute("SELECT school FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # 조회 실패 시 (school 컬럼이 없을 시) 컬럼을 추가합니다.
        c.execute("ALTER TABLE users ADD COLUMN school TEXT")

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
    
    # ✅ 게시글 좋아요 기록 테이블 (중복 좋아요 방지용)
    c.execute('''CREATE TABLE IF NOT EXISTS likes_log (
        user_id TEXT,
        post_id INTEGER,
        PRIMARY KEY (user_id, post_id),
        FOREIGN KEY(user_id) REFERENCES users(username),
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    conn.commit()
    conn.close()

# ✅ 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 학교 정보 및 스타일 가져오기
def get_school_style(school_code):
    if school_code == "여고":
        # Hot Pink
        return "대원여고", "#FF69B4"
    elif school_code == "남고":
        # Dodger Blue
        return "대원남고", "#1E90FF"
    # Fallback
    return "학교 정보 없음", "#808080"

# ✅ 특정 유저의 학교 정보 가져오기
def get_user_school(username):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT school FROM users WHERE username = ?", (username,))
    school = c.fetchone()
    conn.close()
    # 💡 수정: school이 None일 경우 에러 방지 (예: 마이그레이션으로 추가되었지만 값이 비어있는 경우)
    return school[0] if school and school[0] is not None else "여고" # 기본값을 여고로 설정

# ✅ 회원가입 (school 추가)
def signup(username, password, email, student_id, school):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "이미 존재하는 사용자명입니다."

    # school 컬럼 추가 (총 6개 값)
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (
        username,
        hash_password(password),
        email,
        student_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        school # New field
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
        c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,)) # 댓글 먼저 삭제
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,)) # 게시글 삭제
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# ✅ 게시글 좋아요 처리 (중복 방지 로직 추가)
def like_post(post_id):
    username = st.session_state.username # 현재 사용자 이름 가져오기
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # 1. 중복 좋아요 확인: likes_log에서 해당 유저가 이 게시물에 좋아요를 눌렀는지 확인
    c.execute("SELECT * FROM likes_log WHERE user_id = ? AND post_id = ?", (username, post_id))
    if c.fetchone():
        conn.close()
        # 이미 좋아요를 눌렀다면 아무것도 하지 않고 함수 종료
        st.info("이미 좋아요를 누르셨습니다.")
        return

    # 2. 좋아요 수 증가
    c.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    
    # 3. 좋아요 기록 추가 (likes_log에 기록)
    c.execute("INSERT INTO likes_log (user_id, post_id) VALUES (?, ?)", (username, post_id))

    conn.commit()
    conn.close()

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

# ✅ 댓글 불러오기 (real_author 추가)
def get_comments(post_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # real_author도 함께 불러와서 학교 정보를 조회할 수 있도록 함
    c.execute("SELECT author, real_author, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments


# ==============================================================================
# 🖥️ 페이지 렌더링 함수
# ==============================================================================

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
            st.markdown("### 📝 회원 정보 입력")
            username = st.text_input("아이디", key="signup_user")
            password = st.text_input("비밀번호", type="password", key="signup_pw")
            email = st.text_input("이메일")
            student_id = st.text_input("학번")
            
            # 학교 선택 UI 추가
            school = st.radio(
                "학교 선택",
                ["여고", "남고"],
                index=0,
                key="signup_school",
                horizontal=True
            )

            if st.button("회원가입", use_container_width=True):
                if username and password and email and student_id:
                    success, msg = signup(username, password, email, student_id, school)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("모든 항목을 입력해주세요.")

# ✅ 게시판 페이지
def show_home_page():
    st.title("📋 자유게시판")
    
    # 글쓰기 버튼을 위에 배치
    if st.button("✍️ 글쓰기", type="primary"):
        st.session_state.page = "write"
        st.rerun()

    posts = get_all_posts()
    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해보세요!")
        return

    for post in posts:
        post_id, title, content, author, real_author, created_at, likes = post
        
        # 💡 학교 정보 및 색상 가져오기
        school_code = get_user_school(real_author)
        school_name, school_color = get_school_style(school_code)

        with st.container(border=True):
            st.subheader(f"📝 {title}")
            
            # 💡 학교 정보를 포함하여 스타일링된 캡션 표시
            caption_html = f'''
                <div style="font-size: small; color: #808080; margin-bottom: 10px;">
                    {author} | 
                    <span style="color: {school_color}; font-weight: bold;">{school_name}</span> | 
                    {created_at}
                </div>
            '''
            st.markdown(caption_html, unsafe_allow_html=True)
            
            st.write(content)
            
            st.metric("❤️ 좋아요", likes)

            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("❤️ 좋아요", key=f"like_{post_id}"):
                    like_post(post_id)
                    st.rerun()
            with col2:
                if real_author == st.session_state.username:
                    if st.button("🗑️ 게시글 삭제", key=f"del_{post_id}", type="secondary"):
                        delete_post(post_id)
                        st.success("게시글 및 관련 댓글이 모두 삭제 완료!")
                        st.rerun()

            st.divider()
            
            # 💬 댓글 표시
            comments = get_comments(post_id)
            st.subheader(f"💬 댓글 ({len(comments)})")

            for c in comments:
                comment_author, comment_real_author, comment_content, comment_created = c
                
                # 💡 댓글 작성자의 학교 정보 및 색상 가져오기
                comment_school_code = get_user_school(comment_real_author)
                comment_school_name, comment_school_color = get_school_style(comment_school_code)
                school_display = f'<span style="color: {comment_school_color}; font-weight: bold;">{comment_school_name}</span>'

                comment_html = f'''
                    <div style="margin-bottom: 5px;">
                        <span style="font-weight: bold;">👤 {comment_author}</span> | 
                        {school_display} | 
                        <span style="font-size: small; color: #808080;">{comment_created}</span>
                    </div>
                    <div style="margin-left: 15px;">🗨️ {comment_content}</div>
                '''
                st.markdown(comment_html, unsafe_allow_html=True)
                st.markdown('<hr style="margin: 5px 0 5px 0; border-top: 1px solid #eee;">', unsafe_allow_html=True)

            # 📝 댓글 작성 UI
            st.markdown("---")
            comment_text = st.text_area("댓글 작성", key=f"comment_box_{post_id}", height=80)
            colA, colB = st.columns([3, 1])
            with colA:
                anonymous = st.checkbox("익명으로 작성", key=f"anon_{post_id}")
            with colB:
                if st.button("댓글 등록", key=f"submit_comment_{post_id}", use_container_width=True):
                    if comment_text.strip():
                        add_comment(post_id, comment_text, anonymous)
                        st.success("댓글이 작성되었습니다!")
                        st.rerun()
                    else:
                        st.warning("댓글 내용을 입력하세요.")

# ✅ 글쓰기 페이지
def show_write_page():
    st.title("✍️ 글쓰기")
    st.markdown("---")
    
    title = st.text_input("제목")
    content = st.text_area("내용을 적어주세요.", height=300)
    anonymous = st.checkbox("익명으로 작성")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("등록", type="primary", use_container_width=True):
            if title.strip() and content.strip():
                create_post(title, content, anonymous)
                st.success("게시글이 작성되었습니다!")
                st.session_state.page = "home"
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해주세요.")
    with col2:
        if st.button("취소", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

# ✅ 프로필 페이지
def show_profile_page():
    st.title("👤 내 정보")
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (st.session_state.username,))
    user = c.fetchone()
    conn.close()

    if user:
        username, _, email, student_id, created, school_code = user # school_code 추가
        
        school_name, school_color = get_school_style(school_code)

        st.info(f"**아이디:** {username}")
        
        # 💡 학교 정보 표시
        st.markdown(f'**학교:** <span style="color: {school_color}; font-weight: bold;">{school_name}</span>', unsafe_allow_html=True)
        
        st.info(f"**이메일:** {email}")
        st.info(f"**학번:** {student_id}")
        st.info(f"**가입일:** {created}")
    else:
        st.error("사용자 정보를 불러올 수 없습니다.")

# ==============================================================================
# 🚀 메인 실행
# ==============================================================================
def main():
    init_db()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "home"

    # 사이드바 메뉴
    with st.sidebar:
        st.title("🎓 대원대학교 커뮤니티")

        if st.session_state.logged_in:
            st.success(f"👋 {st.session_state.username}님 환영합니다!")
            st.divider()
            
            # 네비게이션 버튼
            if st.button("🏠 자유게시판"):
                st.session_state.page = "home"
                st.rerun()
            if st.button("✍️ 글쓰기"):
                st.session_state.page = "write"
                st.rerun()
            if st.button("👤 내 정보"):
                st.session_state.page = "profile"
                st.rerun()
                
            st.divider()
            if st.button("🚪 로그아웃", type="secondary"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "home"
                st.success("로그아웃되었습니다.")
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
