import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="축제 게시판")

def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# 앱 시작할 때 DB 준비
init_db()
def add_post(content):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO posts (content, created_at) VALUES (?, ?)",
        (content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()


st.title(" 👾대원 에타 게시판")
st.divider()

content = st.text_area("💬 한마디 남기기", height=100)

if st.button("등록"):
    if content.strip():
        add_post(content)
        st.success("저장됐어!")
        st.rerun()
    else:
        st.warning("내용을 입력해줘!")

st.caption("익명으로 자유롭게 한마디를 남겨주세요‼️")
