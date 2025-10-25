import streamlit as st
import sqlite3
import pandas as pd
import time

# ----------------------------------------------------
# 1. SyntaxError U+00A0 해결 완료:
# 이 코드는 Streamlit 환경에서 안전하게 실행되도록 비정상적인 문자가 제거되었습니다.
# ----------------------------------------------------

# 데이터베이스 연결 초기화 및 시뮬레이션
try:
    # 이 라인에 비정상 문자가 없음을 확인했습니다.
    conn = sqlite3.connect("data.db")
    st.session_state['db_connected'] = True
    st.sidebar.success("데이터베이스 연결 성공 (시뮬레이션)")
except Exception as e:
    # 실제 앱에서는 Streamlit Cloud 환경에 맞게 DB 연결 설정을 해야 합니다.
    st.sidebar.error(f"데이터베이스 연결 오류 (시뮬레이션): {e}")
    st.session_state['db_connected'] = False


# Streamlit UI 설정
st.set_page_config(layout="centered", page_title="커뮤니티 게시판")
st.title("간단한 커뮤니티 게시판")

# 예제 게시물 데이터
sample_posts = [
    {"id": 1, "title": "첫 번째 게시글 제목", "content": "안녕하세요. UI 정렬을 테스트하기 위한 첫 번째 게시물 내용입니다.", "likes": 42, "views": 120},
    {"id": 2, "title": "두 번째 유용한 정보", "content": "Streamlit에서 커스텀 CSS를 사용하여 정렬을 지정하는 예시입니다. 좋아요와 조회수는 왼쪽 하단에 표시됩니다.", "likes": 88, "views": 250},
    {"id": 3, "title": "세 번째 테스트 게시물", "content": "모든 게시물에 대해 왼쪽 하단 정렬이 잘 적용되었는지 확인해 보세요.", "likes": 15, "views": 45},
]

# ----------------------------------------------------
# 2. 하트 및 조회수 왼쪽 하단 정렬 구현 (커스텀 CSS):
# ----------------------------------------------------

# 커스텀 CSS 정의 및 삽입
st.markdown("""
<style>
/* 게시물 전체 컨테이너 스타일 */
.post-container {
    border: 1px solid #e0e0e0;
    padding: 20px;
    margin-bottom: 25px;
    border-radius: 12px;
    background-color: #ffffff; /* 배경을 흰색으로 변경 */
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); /* 부드러운 그림자 추가 */
}

/* 좋아요/조회수 섹션 - 왼쪽 정렬 및 아이콘 간격 조정 */
.metric-footer {
    display: flex;
    justify-content: flex-start; /* 핵심: 내용을 왼쪽(시작점)에 정렬 */
    gap: 20px; /* 아이콘 사이 간격 */
    align-items: center; 
    margin-top: 20px; /* 내용과 분리 */
    padding-top: 10px;
    border-top: 1px solid #f0f0f0; /* 옅은 구분선 */
}

.metric-item {
    font-size: 1rem;
    color: #4A5568;
    display: flex;
    align-items: center;
    font-weight: 500;
}

.metric-icon {
    margin-right: 5px;
    font-size: 1.1rem;
}

/* Streamlit 기본 버튼 스타일링 (선택 사항) */
div[data-testid="stButton"] button {
    box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    border-radius: 6px;
    border: 1px solid #ddd;
    background-color: #f0f0ff;
}
</style>
""", unsafe_allow_html=True)


# 게시물 목록 출력
for post in sample_posts:
    with st.container():
        # HTML을 사용하여 전체 게시물 컨테이너 시작
        st.markdown(f'<div class="post-container">', unsafe_allow_html=True)
        
        # 게시물 제목 (Streamlit의 기본 마크다운 사용)
        st.markdown(f"### {post['title']}")
        
        # 게시물 내용
        st.write(post['content'])
        
        # 좋아요/조회수 메트릭을 왼쪽 하단에 정렬 (커스텀 HTML/CSS 적용)
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

st.sidebar.markdown("## 앱 정보")
st.sidebar.info("이 코드는 Streamlit에서 발생한 U+00A0 오류를 해결하고, 좋아요 및 조회수 표시를 왼쪽 하단에 고정하도록 CSS를 적용한 예제입니다.")
