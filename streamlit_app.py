import streamlit as st

st.set_page_config(page_title="우리학교 미니 커뮤니티")

# 세션 상태에 게시글/댓글 데이터 저장
if 'posts' not in st.session_state:
    st.session_state.posts = []

# 메뉴 탭
tabs = st.tabs(["게시판", "시간표", "급식"])

with tabs[0]:
    st.header("게시판")
    nickname = st.text_input("닉네임", value="", max_chars=20)
    content = st.text_area("내용을 입력하세요", height=100)
    if st.button("올리기"):
        if content.strip() == "":
            st.warning("내용을 입력해주세요")
        else:
            st.session_state.posts.insert(0, {
                "nickname": nickname if nickname.strip() != "" else "익명",
                "content": content,
                "comments": []
            })
            st.experimental_rerun()

    # 게시글과 댓글 출력
    for idx, post in enumerate(st.session_state.posts):
        st.markdown(f"### {post['nickname']}")
        st.write(post['content'])
        # 댓글 리스트
        for cmt in post['comments']:
            st.markdown(f"- {cmt}")
        # 댓글 입력창
        comment_key = f"comment_input_{idx}"
        comment_input = st.text_input("댓글을 입력하세요", key=comment_key)
        comment_button_key = f"comment_button_{idx}"
        if st.button("등록", key=comment_button_key):
            if comment_input.strip() != "":
                st.session_state.posts[idx]['comments'].append(comment_input)
                st.experimental_rerun()

with tabs[1]:
    st.header("🗓️ 시간표")
    timetableData = {
        "1-1": {"월":"수학","화":"영어","수":"과학","목":"체육","금":"미술"},
        "1-2": {"월":"국어","화":"영어","수":"과학","목":"음악","금":"체육"},
        "2-1": {"월":"수학","화":"영어","수":"과학","목":"역사","금":"체육"},
        "2-2": {"월":"국어","화":"수학","수":"과학","목":"영어","금":"체육"}
    }
    grade = st.selectbox("학년/반 선택", options=list(timetableData.keys()))
    data = timetableData[grade]

    st.table({
        day: [subject] for day, subject in data.items()
    })

with tabs[2]:
    st.header("🍽️ 급식")
    mealData = {
        "월": "김밥, 된장국, 과일",
        "화": "볶음밥, 미트볼, 샐러드",
        "수": "라면, 계란말이, 김치",
        "목": "비빔밥, 미소국, 오이무침",
        "금": "돈까스, 밥, 샐러드"
    }
    day = st.selectbox("요일 선택", options=list(mealData.keys()))
    st.write(mealData[day])
