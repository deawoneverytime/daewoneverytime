from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret123'  # 세션용 비밀키 (아무 문자열 가능)

DB_NAME = 'users.db'


# --- DB 초기화 ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# --- 홈 화면 ---
@app.route('/')
def home():
    if 'user' in session:
        return render_template_string('''
            <h1>환영합니다, {{session['user']}}님!</h1>
            <a href="/logout">로그아웃</a><br>
            <a href="/admin">회원 목록 보기</a>
        ''')
    else:
        return redirect(url_for('login'))


# --- 회원가입 ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "<h3>이미 존재하는 이메일입니다.</h3><a href='/register'>뒤로가기</a>"
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template_string('''
        <h2>회원가입</h2>
        <form method="POST">
            이름: <input type="text" name="name" required><br>
            이메일: <input type="email" name="email" required><br>
            비밀번호: <input type="password" name="password" required><br>
            <input type="submit" value="가입하기">
        </form>
        <a href="/login">로그인하기</a>
    ''')


# --- 로그인 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = user[1]  # 이름 저장
            return redirect(url_for('home'))
        else:
            return "<h3>이메일 또는 비밀번호가 잘못되었습니다.</h3><a href='/login'>다시 시도</a>"

    return render_template_string('''
        <h2>로그인</h2>
        <form method="POST">
            이메일: <input type="email" name="email" required><br>
            비밀번호: <input type="password" name="password" required><br>
            <input type="submit" value="로그인">
        </form>
        <a href="/register">회원가입</a>
    ''')


# --- 로그아웃 ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# --- 회원 관리 페이지 ---
@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM users")
    users = c.fetchall()
    conn.close()

    user_list_html = ''.join([f"<li>{u[1]} ({u[2]})</li>" for u in users])
    return f'''
        <h2>회원 목록</h2>
        <ul>{user_list_html}</ul>
        <a href="/">홈으로</a>
    '''


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
