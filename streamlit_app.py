import streamlit as st
from streamlit_option_menu import option_menu
import datetime

# 앱 기본 설정
st.set_page_config(page_title="학교 커뮤니티", layout="wide")

# 상단 메뉴
selected = option_menu(
    menu_title=None,
    options=["커뮤니티", "시간표", "급식표", "공지사항", "내 정보"],
    icons=["chat-dots", "calendar-week", "utensils", "megaphone", "person-circle"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

# ───────────────────────────────
# 1️⃣ 커뮤니티
# ───────────────────────────────
if selected == "커뮤니티":
    st.title("📢 커뮤니티 게시판")
    st.subheader("자유롭게 의견을 나눠보세요!")

    # 글 목록 저장용 세션
    if "posts" not in st.session_state:
        st.session_state["posts"] = []

    # 글쓰기
    with st.form("new_post_form"):
        author = st.text_input("작성자 이름")
        content = st.text_area("내용을 입력하세요")
        submit_post = st.form_submit_button("게시하기")

        if submit_post and author and content:
            post = {
                "author": author,
                "content": content,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state["posts"].insert(0, post)
            st.success("게시글이 등록되었습니다!")

    st.divider()
    st.write("### 📄 게시글 목록")
    for post in st.session_state["posts"]:
        st.markdown(f"**{post['author']}** | 🕒 {post['time']}")
        st.write(post["content"])
        st.write("---")

# ───────────────────────────────
# 2️⃣ 시간표
# ───────────────────────────────
elif selected == "시간표":
    st.title("📅 학급별 시간표")

    grade = st.selectbox("학년 선택", [1, 2, 3])
    classroom = st.selectbox("반 선택", [1, 2, 3, 4, 5, 6, 7, 8, 9])

    # 예시 데이터 (나중에 CSV나 DB로 교체 가능)
    timetable = {
        (1, 1): ["국어", "수학", "영어", "체육", "역사", "과학", "미술"],
        (2, 3): ["물리", "화학", "수학", "영어", "국어", "체육", "음악"],
        (3, 2): ["프로그래밍", "수학", "AI", "국어", "영어", "진로", "체육"]
    }

    if (grade, classroom) in timetable:
        st.table({f"{i+1}교시": [timetable[(grade, classroom)][i]] for i in range(7)})
    else:
        st.warning("아직 시간표가 등록되지 않았습니다.")

# ───────────────────────────────
# 3️⃣ 급식표
# ───────────────────────────────
elif selected == "급식표":
    st.title("🍱 오늘의 급식")

    today = datetime.date.today()
    st.write(f"📅 {today.strftime('%Y-%m-%d')} 급식표")

    # (실제 NEIS API 연동 가능, 지금은 예시)
    sample_menu = ["쌀밥", "된장국", "치킨가라아게", "오이무침", "김치"]
    st.write("🍽️ " + " / ".join(sample_menu))

# ───────────────────────────────
# 4️⃣ 공지사항
# ───────────────────────────────
elif selected == "공지사항":
    st.title("📢 공지사항")
    st.info("아직 등록된 공지사항이 없습니다.")

# ───────────────────────────────
# 5️⃣ 내
