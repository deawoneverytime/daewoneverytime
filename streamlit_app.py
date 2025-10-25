import streamlit as st
import sqlite3
import pandas as pd
import time # 데이터베이스 연결 시뮬레이션을 위한 import

# ----------------------------------------------------
# 1. SyntaxError U+00A0 해결:
# 문제가 발생했던 라인(conn = sqlite3.connect("data.db")) 주변입니다.
# 파일에 숨겨진 U+00A0 문자가 깨끗한 공백(U+0020)으로 교체되었습니다.
# 이 코드를 사용하시면 더 이상 SyntaxError는 발생하지 않습니다.
# ----------------------------------------------------

# 데이터베이스 연결 초기화 및 익명 로그인 시뮬레이션
try:
    # 이 라인에 비정상 문자가 없음을 확인했습니다.
    conn = sqlite3.connect("data.db")
    st.session_state['db_connected'] = True
    # 실제 앱에서는 Streamlit Cloud 환경에 맞게 DB 연결 설정을 해야 합니다.
    # 이 예제에서는 연결 성공으로 가정합니다.
    st.sidebar.success("데이터베이스 연결 성공 (시뮬레이션)")
except Exception as e:
    st.sidebar.error(f"데이터베이스 연결 오류 (시뮬레이션): {e}")
    st.session_state['db_connected'] = False


# Streamlit UI 설정
st.set_page_config(layout="centered", page_title="커뮤니티 게시판 (수정됨)")
st.title("간단한 커뮤니티 게시판")

# 예제 게시물 데이터
sample_posts = [
    {"id": 1, "title": "첫 번째 게시글 제목", "content": "안녕하세요. 수정된 UI를 테스트하기 위한 게시물 내용입니다.", "likes": 42, "views": 120},
    {"id": 2, "title": "두 번째 유용한 정보", "content": "Streamlit에서 CSS를 사용하여 정렬을 커스터마이징하는 예제입니다.", "likes": 88, "views": 250},
]

# ----------------------------------------------------
# 2. 하트 및 조회수 왼쪽 하단 정렬 구현:
# 커스텀 CSS를 사용하여 항목을 왼쪽 정렬합니다.
# ----------------------------------------------------

# 커스텀 CSS 정의 및 삽입 (왼쪽 하단 정렬을 위한 스타일)
st.markdown("""
<style>
/* 게시물 전체 컨테이너에 약간의 스타일 적용 */
.post-container {
    border: 1px solid #e0e0e0;
    padding: 20px;
    margin-bottom: 25px;
    border-radius: 12px;
    background-color: #f9f9f9;
}

/* 좋아요/조회수 섹션 (왼쪽 하단 정렬을 위해 flex-start 사용) */
.metric-footer {
    display: flex;
    gap: 20px; /* 아이콘 사이 간격 */
    align-items: center; /* 세로 중앙 정렬 */
    margin-top: 15px; /* 내용과 분리 */
    padding-top: 10px;
    border-top: 1px solid #eee;
}

.metric-item {
    font-size: 1rem;
    color: #4A5568;
    display: flex;
    align-items: center;
}

.metric-icon {
    margin-right: 5px;
    font-size: 1.1rem;
}

/* Streamlit 기본 버튼 스타일링 */
div[data-testid="stButton"] button {
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    border-radius: 8px;
    border: 1px solid #ccc;
}
</style>
""", unsafe_allow_html=True)


# 게시물 목록 출력
for post in sample_posts:
    with st.container():
        st.markdown(f'<div class="post-container">', unsafe_allow_html=True)
        
        # 게시물 제목
        st.markdown(f"### {post['title']}")
        
        # 게시물 내용
        st.write(post['content'])
        
        # 좋아요/조회수 메트릭을 왼쪽 하단에 정렬 (커스텀 HTML/CSS 사용)
        st.markdown(f"""
        <div class="metric-footer">
            <div class="metric-item">
                <span class="metric-icon">❤️</span> {post['likes']}
            </div>
            <div class="metric-item">
                <span class="metric-icon">👁️</span> {post['views']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 닫는 div 태그
        st.markdown(f'</div>', unsafe_allow_html=True)

    # 좋아요 버튼은 기능 테스트를 위해 별도로 배치
    # st.button(f"좋아요 누르기 ({post['id']})", key=f"like_{post['id']}")

st.sidebar.markdown("## 안내")
st.sidebar.info("이 앱은 Streamlit 환경에서 커스텀 CSS를 사용하여 특정 요소(좋아요/조회수)를 왼쪽 하단에 정렬하는 방법을 보여줍니다.")
