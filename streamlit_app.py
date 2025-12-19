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

st.title(" 👾대원 에타 게시판")
st.caption("익명으로 자유롭게 한마디를 남겨주세요‼️")
