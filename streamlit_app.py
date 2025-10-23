import streamlit as st
import json
import hashlib
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="대원대학교 에브리타임", page_icon="🎓", layout="wide")

# 세션 상태로 데이터 관리
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'posts' not in st.session_state:
    st.session_state.posts = {}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 회원가입 함수
def signup(username, password, email, student_id):
    if username in st.session_state.users:
        return False, "이미 존재하는 사용자명입니다."
    
    st.session_state.users[username] = {
        'password': hash_password(password),
        'email': email,
        'student_id': student_id,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return True, "회원가입이 완료되었습니다!"

# 로그인 함수
def login(username, password):
    if username not in st.session_state.users:
        return False, "존재하지 않는 사용자입니다."
    
    if st.session_state.users[username]['password'] != hash_password(password):
        return False, "비밀번호가 일치하지 않습니다."
    
    st.session_state.logged_in = True
    st.session_state.username = username
    return True, "로그인 성공!"

# 게시글 작성 함수
def create_post(title, content, is_anonymous=False):
    post_id = str(len(st.session_state.posts) + 1)
    author = "익명" if is_anonymous else st.session_state.username
    
    st.session_state.posts[post_id] = {
        'title': title,
        'content': content,
        'author': author,
        'real_author': st.session_state.username,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'comments': [],
        'likes': 0
    }
    
    return True

# 댓글 작성 함수
def add_comment(post_id, comment_text, is_anonymous=False):
    if post_id not in st.session_state.posts:
        return False
    
    author = "익명" if is_anonymous else st.session_state.username
    
    comment = {
        'author': author,
        'real_author': st.session_state.username,
        'content': comment_text,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.posts[post_id]['comments'].append(comment)
    return True

# 좋아요 함수
def like_post(post_id):
    if post_id in st.session_state.posts:
        st.session_state.posts[post_id]['likes'] += 1

# 게시글 삭제 함수
def delete_post(post_id):
    if post_id in st.session_state.posts:
        if st.session_state.posts[post_id]['real_author'] == st.session_state.username:
            del st.session_state.posts[post_id]
            return True
    return False

# 메인 UI
def main():
    # 사이드바
    with st.sidebar:
        st.title("🎓 대원대학교 에브리타임")
        
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
            
            # 통계 정보
            st.metric("📝 전체 게시글", len(st.session_state.posts))
            st.metric("👥 회원 수", len(st.session_state.users))
            
            st.divider()
            
            if st.button("🚪 로그아웃", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = 'home'
                st.rerun()
        else:
            st.info("로그인이 필요합니다.")
            st.markdown("---")
            st.caption("💡 테스트용 커뮤니티입니다")
    
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
        st.title("🎓 대원대학교 에브리타임")
        st.subheader("학생 커뮤니티 플랫폼")
        
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            st.subheader("로그인")
            login_username = st.text_input("사용자명", key="login_username", placeholder="아이디를 입력하세요")
            login_password = st.text_input("비밀번호", type="password", key="login_password", placeholder="비밀번호를 입력하세요")
            
            if st.button("로그인", use_container_width=True, type="primary"):
                if login_username and login_password:
                    success, message = login(login_username, login_password)
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("모든 필드를 입력해주세요.")
        
        with tab2:
            st.subheader("회원가입")
            signup_username = st.text_input("사용자명", key="signup_username", placeholder="아이디를 입력하세요")
            signup_password = st.text_input("비밀번호", type="password", key="signup_password", placeholder="비밀번호를 입력하세요")
            signup_email = st.text_input("이메일", key="signup_email", placeholder="example@daewon.ac.kr")
            signup_student_id = st.text_input("학번", key="signup_student_id", placeholder="20241234")
            
            if st.button("회원가입", use_container_width=True, type="primary"):
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
    st.title("📋 자유게시판")
    
    if not st.session_state.posts:
        st.info("🎉 첫 게시글을 작성해보세요!")
        if st.button("✍️ 첫 글쓰기", type="primary"):
            st.session_state.page = 'write'
            st.rerun()
        return
    
    # 게시글을 최신순으로 정렬
    sorted_posts = sorted(st.session_state.posts.items(), key=lambda x: x[1]['created_at'], reverse=True)
    
    for post_id, post in sorted_posts:
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.subheader(f"📝 {post['title']}")
                st.caption(f"✍️ {post['author']} | 🕐 {post['created_at']}")
            
            with col2:
                st.metric("❤️", post['likes'])
            
            with st.expander("게시글 보기 👀"):
                st.write(post['content'])
                
                st.markdown("---")
                
                # 버튼 영역
                col1, col2, col3 = st.columns([1, 1, 4])
                
                with col1:
                    if st.button(f"❤️ 좋아요", key=f"like_{post_id}"):
                        like_post(post_id)
                        st.rerun()
                
                with col2:
                    # 내가 쓴 글이면 삭제 버튼 표시
                    if post['real_author'] == st.session_state.username:
                        if st.button(f"🗑️ 삭제", key=f"delete_{post_id}"):
                            if delete_post(post_id):
                                st.success("게시글이 삭제되었습니다!")
                                st.rerun()
                
                st.divider()
                
                # 댓글 표시
                st.subheader(f"💬 댓글 ({len(post['comments'])})")
                
                if post['comments']:
                    for idx, comment in enumerate(post['comments']):
                        with st.container():
                            st.text(f"👤 {comment['author']} | 🕐 {comment['created_at']}")
                            st.write(comment['content'])
                            if idx < len(post['comments']) - 1:
                                st.markdown("---")
                else:
                    st.info("첫 댓글을 작성해보세요!")
                
                # 댓글 작성
                st.markdown("---")
                st.subheader("💭 댓글 작성")
                comment_text = st.text_area("댓글 내용", key=f"comment_{post_id}", height=100, placeholder="댓글을 입력하세요...")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    comment_anonymous = st.checkbox("🎭 익명으로 작성", key=f"anon_comment_{post_id}")
                
                with col2:
                    if st.button("작성", key=f"submit_comment_{post_id}", type="primary", use_container_width=True):
                        if comment_text.strip():
                            add_comment(post_id, comment_text, comment_anonymous)
                            st.success("댓글이 작성되었습니다!")
                            st.rerun()
                        else:
                            st.warning("댓글 내용을 입력해주세요.")
            
            st.divider()

# 글쓰기 페이지
def show_write_page():
    st.title("✍️ 게시글 작성")
    
    with st.form("post_form"):
        title = st.text_input("제목", placeholder="제목을 입력하세요")
        content = st.text_area("내용", height=300, placeholder="내용을 입력하세요...")
        is_anonymous = st.checkbox("🎭 익명으로 작성")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("✅ 작성 완료", use_container_width=True, type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ 취소", use_container_width=True)
        
        if submitted:
            if title.strip() and content.strip():
                create_post(title, content, is_anonymous)
                st.success("게시글이 작성되었습니다!")
                st.session_state.page = 'home'
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해주세요.")
        
        if cancelled:
            st.session_state.page = 'home'
            st.rerun()

# 프로필 페이지
def show_profile_page():
    st.title("👤 내 정보")
    
    user_data = st.session_state.users.get(st.session_state.username, {})
    
    # 회원 정보 카드
    with st.container():
        st.subheader("📋 회원 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**👤 사용자명**  \n{st.session_state.username}")
            st.info(f"**📧 이메일**  \n{user_data.get('email', 'N/A')}")
        
        with col2:
            st.info(f"**🎓 학번**  \n{user_data.get('student_id', 'N/A')}")
            st.info(f"**📅 가입일**  \n{user_data.get('created_at', 'N/A')}")
    
    st.divider()
    
    # 활동 통계
    my_posts = {pid: post for pid, post in st.session_state.posts.items() 
                if post['real_author'] == st.session_state.username}
    
    total_likes = sum(post['likes'] for post in my_posts.values())
    total_comments = sum(len(post['comments']) for post in my_posts.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 작성한 게시글", len(my_posts))
    with col2:
        st.metric("❤️ 받은 좋아요", total_likes)
    with col3:
        st.metric("💬 받은 댓글", total_comments)
    
    st.divider()
    
    # 내가 쓴 게시글
    st.subheader("📝 내가 쓴 게시글")
    
    if my_posts:
        for post_id, post in sorted(my_posts.items(), key=lambda x: x[1]['created_at'], reverse=True):
            with st.expander(f"📄 {post['title']} - {post['created_at']}"):
                st.write(post['content'])
                st.caption(f"💬 댓글: {len(post['comments'])}개 | ❤️ 좋아요: {post['likes']}개")
                
                if st.button("🗑️ 삭제하기", key=f"profile_delete_{post_id}"):
                    if delete_post(post_id):
                        st.success("게시글이 삭제되었습니다!")
                        st.rerun()
    else:
        st.info("아직 작성한 게시글이 없습니다. 첫 게시글을 작성해보세요!")
        if st.button("✍️ 글쓰기", type="primary"):
            st.session_state.page = 'write'
            st.rerun()

if __name__ == "__main__":
    main()
