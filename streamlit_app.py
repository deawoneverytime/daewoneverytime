import streamlit as st
import json
import hashlib
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(
    page_title="익명 커뮤니티",
    page_icon="💬",
    layout="wide"
)

# CSS 스타일
st.markdown("""
    <style>
    .main {
        background-color: #f9fafb;
    }
    .stButton>button {
        width: 100%;
    }
    .post-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .comment-card {
        background-color: #f3f4f6;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        margin-left: 20px;
    }
    .user-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 데이터 파일 경로
DATA_FILE = 'community_data.json'

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': {}, 'posts': []}

# 데이터 저장 함수
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 비밀번호 해시 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 익명 이름 생성 함수
def get_anonymous_name(username, post_id):
    hash_value = hashlib.md5(f"{username}{post_id}".encode()).hexdigest()
    return f"익명{int(hash_value[:6], 16) % 1000}"

# 시간 포맷 함수
def format_time(timestamp):
    post_time = datetime.fromisoformat(timestamp)
    now = datetime.now()
    diff = now - post_time
    
    if diff.seconds < 60:
        return "방금 전"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}분 전"
    elif diff.seconds < 86400:
        return f"{diff.seconds // 3600}시간 전"
    else:
        return f"{diff.days}일 전"

# 세션 스테이트 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# 로그인/회원가입 페이지
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💬 익명 커뮤니티</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b7280;'>자유롭게 소통하는 공간</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("사용자명", key="login_username")
                password = st.text_input("비밀번호", type="password", key="login_password")
                submit = st.form_submit_button("로그인", use_container_width=True)
                
                if submit:
                    data = st.session_state.data
                    if username in data['users']:
                        if data['users'][username] == hash_password(password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("비밀번호가 올바르지 않습니다.")
                    else:
                        st.error("존재하지 않는 사용자입니다.")
        
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("사용자명", key="signup_username")
                new_password = st.text_input("비밀번호", type="password", key="signup_password")
                confirm_password = st.text_input("비밀번호 확인", type="password", key="confirm_password")
                submit = st.form_submit_button("회원가입", use_container_width=True)
                
                if submit:
                    if not new_username or not new_password:
                        st.error("사용자명과 비밀번호를 입력해주세요.")
                    elif new_password != confirm_password:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif new_username in st.session_state.data['users']:
                        st.error("이미 존재하는 사용자명입니다.")
                    else:
                        st.session_state.data['users'][new_username] = hash_password(new_password)
                        save_data(st.session_state.data)
                        st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인해주세요.")

# 메인 커뮤니티 페이지
def main_page():
    # 헤더
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1>💬 익명 커뮤니티</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: right; padding-top: 20px;'><span class='user-badge'>👤 {st.session_state.username}</span></div>", unsafe_allow_html=True)
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    st.markdown("---")
    
    # 새 게시글 작성
    st.markdown("### ✍️ 새 글 작성")
    with st.form("new_post_form", clear_on_submit=True):
        post_content = st.text_area("익명으로 글을 작성해보세요...", height=150, key="new_post")
        submit = st.form_submit_button("게시하기", use_container_width=True)
        
        if submit and post_content:
            new_post = {
                'id': str(datetime.now().timestamp()),
                'content': post_content,
                'author': st.session_state.username,
                'timestamp': datetime.now().isoformat(),
                'likes': 0,
                'liked_by': [],
                'comments': []
            }
            st.session_state.data['posts'].insert(0, new_post)
            save_data(st.session_state.data)
            st.success("게시글이 작성되었습니다!")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📝 게시글")
    
    # 게시글 표시
    if not st.session_state.data['posts']:
        st.info("아직 게시글이 없습니다. 첫 번째 글을 작성해보세요!")
    
    for idx, post in enumerate(st.session_state.data['posts']):
        with st.container():
            st.markdown("<div class='post-card'>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([4, 1])
            with col1:
                anonymous_name = get_anonymous_name(post['author'], post['id'])
                st.markdown(f"**{anonymous_name}** • {format_time(post['timestamp'])}")
            
            st.markdown(f"<p style='margin: 15px 0;'>{post['content']}</p>", unsafe_allow_html=True)
            
            # 좋아요 및 댓글 버튼
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                has_liked = st.session_state.username in post['liked_by']
                like_emoji = "❤️" if has_liked else "🤍"
                if st.button(f"{like_emoji} {post['likes']}", key=f"like_{idx}"):
                    if has_liked:
                        post['likes'] -= 1
                        post['liked_by'].remove(st.session_state.username)
                    else:
                        post['likes'] += 1
                        post['liked_by'].append(st.session_state.username)
                    save_data(st.session_state.data)
                    st.rerun()
            
            with col2:
                st.markdown(f"💬 {len(post['comments'])}")
            
            # 댓글 섹션
            with st.expander(f"댓글 보기 ({len(post['comments'])})"):
                # 댓글 작성
                with st.form(f"comment_form_{idx}"):
                    comment_content = st.text_input("댓글을 입력하세요...", key=f"comment_{idx}")
                    submit_comment = st.form_submit_button("댓글 달기")
                    
                    if submit_comment and comment_content:
                        new_comment = {
                            'id': str(datetime.now().timestamp()),
                            'content': comment_content,
                            'author': st.session_state.username,
                            'timestamp': datetime.now().isoformat()
                        }
                        post['comments'].append(new_comment)
                        save_data(st.session_state.data)
                        st.rerun()
                
                # 댓글 표시
                for comment in post['comments']:
                    st.markdown("<div class='comment-card'>", unsafe_allow_html=True)
                    anonymous_comment_name = get_anonymous_name(comment['author'], post['id'])
                    st.markdown(f"**{anonymous_comment_name}** • {format_time(comment['timestamp'])}")
                    st.markdown(f"<p style='margin-top: 8px;'>{comment['content']}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

# 메인 실행
if st.session_state.logged_in:
    main_page()
else:
    login_page()ㅍ
