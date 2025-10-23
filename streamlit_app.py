import streamlit as st
import json
import hashlib
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="대학 커뮤니티", page_icon="🎓", layout="wide")

# 데이터 파일 경로
USERS_FILE = "users.json"
POSTS_FILE = "posts.json"

# 데이터 로드 함수
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 데이터 저장 함수
def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# 회원가입 함수
def signup(username, password, email, student_id):
    users = load_data(USERS_FILE)
    
    if username in users:
        return False, "이미 존재하는 사용자명입니다."
    
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'student_id': student_id,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_data(USERS_FILE, users)
    return True, "회원가입이 완료되었습니다!"

# 로그인 함수
def login(username, password):
    users = load_data(USERS_FILE)
    
    if username not in users:
        return False, "존재하지 않는 사용자입니다."
    
    if users[username]['password'] != hash_password(password):
        return False, "비밀번호가 일치하지 않습니다."
    
    st.session_state.logged_in = True
    st.session_state.username = username
    return True, "로그인 성공!"

# 게시글 작성 함수
def create_post(title, content, is_anonymous=False):
    posts = load_data(POSTS_FILE)
    
    post_id = str(len(posts) + 1)
    author = "익명" if is_anonymous else st.session_state.username
    
    posts[post_id] = {
        'title': title,
        'content': content,
        'author': author,
        'real_author': st.session_state.username,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'comments': [],
        'likes': 0
    }
    
    save_data(POSTS_FILE, posts)
    return True

# 댓글 작성 함수
def add_comment(post_id, comment_text, is_anonymous=False):
    posts = load_data(POSTS_FILE)
    
    if post_id not in posts:
        return False
    
    author = "익명" if is_anonymous else st.session_state.username
    
    comment = {
        'author': author,
        'real_author': st.session_state.username,
        'content': comment_text,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    posts[post_id]['comments'].append(comment)
    save_data(POSTS_FILE, posts)
    return True

# 좋아요 함수
def like_post(post_id):
    posts = load_data(POSTS_FILE)
    if post_id in posts:
        posts[post_id]['likes'] += 1
        save_data(POSTS_FILE, posts)

# 메인 UI
def main():
    # 사이드바
    with st.sidebar:
        st.title("🎓 대학 커뮤니티")
        
        if st.session_state.logged_in:
            st.success(f"환영합니다, {st.session_state.username}님!")
            
            if st.button("🏠 홈", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()
            
            if st.button("✍️ 글쓰기", use_container_width=True):
                st.session_state.page = 'write'
                st.rerun()
            
            if st.button("👤 내 정보", use_container_width=True):
                st.session_state.page = 'profile'
                st.rerun()
            
            st.divider()
            
            if st.button("🚪 로그아웃", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = 'home'
                st.rerun()
        else:
            st.info("로그인이 필요합니다.")
    
    # 메인 컨텐츠
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.page == 'home':
            show_home_page()
        elif st.session_state.page == 'write':
            show_write_page()
        elif st.session_state.page == 'profile':
            show_profile_page()

# 로그인/회원가입 페이지
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🎓 대학 커뮤니티")
        
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            st.subheader("로그인")
            login_username = st.text_input("사용자명", key="login_username")
            login_password = st.text_input("비밀번호", type="password", key="login_password")
            
            if st.button("로그인", use_container_width=True):
                if login_username and login_password:
                    success, message = login(login_username, login_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("모든 필드를 입력해주세요.")
        
        with tab2:
            st.subheader("회원가입")
            signup_username = st.text_input("사용자명", key="signup_username")
            signup_password = st.text_input("비밀번호", type="password", key="signup_password")
            signup_email = st.text_input("이메일", key="signup_email")
            signup_student_id = st.text_input("학번", key="signup_student_id")
            
            if st.button("회원가입", use_container_width=True):
                if signup_username and signup_password and signup_email and signup_student_id:
                    success, message = signup(signup_username, signup_password, signup_email, signup_student_id)
                    if success:
                        st.success(message)
                        st.info("로그인 탭으로 이동하여 로그인해주세요.")
                    else:
                        st.error(message)
                else:
                    st.warning("모든 필드를 입력해주세요.")

# 홈 페이지 (게시글 목록)
def show_home_page():
    st.title("📋 게시판")
    
    posts = load_data(POSTS_FILE)
    
    if not posts:
        st.info("아직 게시글이 없습니다. 첫 게시글을 작성해보세요!")
        return
    
    # 게시글을 최신순으로 정렬
    sorted_posts = sorted(posts.items(), key=lambda x: x[1]['created_at'], reverse=True)
    
    for post_id, post in sorted_posts:
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.subheader(f"📝 {post['title']}")
                st.caption(f"작성자: {post['author']} | {post['created_at']}")
            
            with col2:
                st.metric("👍", post['likes'])
            
            with st.expander("게시글 보기"):
                st.write(post['content'])
                
                # 좋아요 버튼
                if st.button(f"👍 좋아요", key=f"like_{post_id}"):
                    like_post(post_id)
                    st.rerun()
                
                st.divider()
                
                # 댓글 표시
                st.subheader(f"💬 댓글 ({len(post['comments'])})")
                
                for idx, comment in enumerate(post['comments']):
                    st.text(f"👤 {comment['author']} | {comment['created_at']}")
                    st.write(comment['content'])
                    if idx < len(post['comments']) - 1:
                        st.markdown("---")
                
                # 댓글 작성
                st.subheader("댓글 작성")
                comment_text = st.text_area("댓글 내용", key=f"comment_{post_id}", height=100)
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    comment_anonymous = st.checkbox("익명으로 작성", key=f"anon_comment_{post_id}")
                
                with col2:
                    if st.button("댓글 달기", key=f"submit_comment_{post_id}"):
                        if comment_text:
                            add_comment(post_id, comment_text, comment_anonymous)
                            st.success("댓글이 작성되었습니다!")
                            st.rerun()
                        else:
                            st.warning("댓글 내용을 입력해주세요.")
            
            st.divider()

# 글쓰기 페이지
def show_write_page():
    st.title("✍️ 게시글 작성")
    
    title = st.text_input("제목")
    content = st.text_area("내용", height=300)
    is_anonymous = st.checkbox("익명으로 작성")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("작성 완료", use_container_width=True):
            if title and content:
                create_post(title, content, is_anonymous)
                st.success("게시글이 작성되었습니다!")
                st.session_state.page = 'home'
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해주세요.")
    
    with col2:
        if st.button("취소", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()

# 프로필 페이지
def show_profile_page():
    st.title("👤 내 정보")
    
    users = load_data(USERS_FILE)
    user_data = users.get(st.session_state.username, {})
    
    st.subheader("회원 정보")
    st.write(f"**사용자명:** {st.session_state.username}")
    st.write(f"**이메일:** {user_data.get('email', 'N/A')}")
    st.write(f"**학번:** {user_data.get('student_id', 'N/A')}")
    st.write(f"**가입일:** {user_data.get('created_at', 'N/A')}")
    
    st.divider()
    
    # 내가 쓴 게시글
    st.subheader("📝 내가 쓴 게시글")
    posts = load_data(POSTS_FILE)
    my_posts = {pid: post for pid, post in posts.items() if post['real_author'] == st.session_state.username}
    
    if my_posts:
        for post_id, post in sorted(my_posts.items(), key=lambda x: x[1]['created_at'], reverse=True):
            with st.expander(f"{post['title']} - {post['created_at']}"):
                st.write(post['content'])
                st.caption(f"댓글: {len(post['comments'])}개 | 좋아요: {post['likes']}개")
    else:
        st.info("작성한 게시글이 없습니다.")

if __name__ == "__main__":
    main()
