import streamlit as st
from datetime import datetime

st.set_page_config(page_title="학교 커뮤니티", layout="centered")

st.title("🏫 우리학교 커뮤니티")

# 게시글 데이터를 세션에 저장 (앱 실행 중 유지)
if "posts" not in st.session_state:
    st.session_state.posts = []  # [{title, content, comments: []}, ...]

# 새 글 작성
with st.expander("✏️ 새 글 작성하기", expanded=True):
    title = st.text_input("제목을 입력하세요")
    content = st.text_area("내용을 입력하세요", height=150)
    if st.button("게시하기"):
        if title and content:
            st.session_state.posts.insert(
                0,
                {
                    "title": title,
                    "content": content,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "comments": []
                }
            )
            st.success("게시글이 등록되었습니다!")
        else:
            st.warning("제목과 내용을 모두 입력하세요.")

st.markdown("---")

# 게시글 목록
if not st.session_state.posts:
    st.info("아직 작성된 게시글이 없습니다.")
else:
    for idx, post in enumerate(st.session_state.posts):
        with st.expander(f"📌 {post['title']}  ({post['time']})"):
            st.write(post["content"])
            st.markdown("---")

            # 댓글 표시
            if post["comments"]:
                st.subheader("💬 댓글")
                for cidx, comment in enumerate(post["comments"]):
                    st.write(f"- {comment['text']} ({comment['time']})")

            # 댓글 입력
            new_comment = st.text_input(f"댓글 입력_{idx}", placeholder="댓글을 입력하세요", label_visibility="collapsed")
            if st.button(f"댓글 달기_{idx}"):
                if new_comment.strip():
                    post["comments"].append({
                        "text": new_comment.strip(),
                        "time": datetime.now().strftime("%H:%M")
                    })
                    st.experimental_rerun()
