from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secretkey"
DB_NAME = "community.db"

# ---------- 데이터베이스 초기화 ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 회원 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # 게시글 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL
        )
    """)
    # 댓글 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            author TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------- 홈 ----------
@app.route('/')
def home():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()

    html = '''
    <h1>📢 커뮤니티</h1>
    {% if 'user' in session %}
        <p>환영합니다, {{session['user']}}님!</p>
        <a href="/logout">로그아웃</a> | <a href="/write">글쓰기</a>
    {% else %}
        <a href="/login">로그인</a> | <a href="/register">회원가입</a>
    {% endif %}
    <hr>
    {% for post in posts %}
        <h3><a href="/post/{{post[0]}}">{{post[1]}}</a></h3>
        <p>작성자: {{post[3]}}</p>
        <hr>
    {% endfor %}
    '''
    return render_template_string(html, posts=posts)


# ---------- 회원가입 ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                      (username, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "<h3>이미 존재하는 이메일입니다.</h3><a href='/register'>뒤로가기</a>"
        conn.close()
        return redirect(url_for('login'))
    return render_template_string('''
        <h2>회원가입</h2>
        <form method="POST">
            이름: <input name="username" required><br>
            이메일: <input name="email" required><br>
            비밀번호: <input type="password" name="password" required><br>
            <input type="submit" value="가입하기">
        </form>
        <a href="/login">로그인하기</a>
    ''')


# ---------- 로그인 ----------
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
            session['user'] = user[1]
            return redirect(url_for('home'))
        else:
            return "<h3>이메일 또는 비밀번호가 잘못되었습니다.</h3><a href='/login'>다시 시도</a>"

    return render_template_string('''
        <h2>로그인</h2>
        <form method="POST">
            이메일: <input name="email" required><br>
            비밀번호: <input type="password" name="password" required><br>
            <input type="submit" value="로그인">
        </form>
        <a href="/register">회원가입</a>
    ''')


# ---------- 로그아웃 ----------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


# ---------- 글쓰기 ----------
@app.route('/write', methods=['GET', 'POST'])
def write():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['user']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, content, author) VALUES (?, ?, ?)",
                  (title, content, author))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    return render_template_string('''
        <h2>글쓰기</h2>
        <form method="POST">
            제목: <input name="title" required><br>
            내용:<br>
            <textarea name="content" rows="5" cols="40" required></textarea><br>
            <input type="submit" value="등록">
        </form>
        <a href="/">홈으로</a>
    ''')


# ---------- 게시글 보기 + 댓글 ----------
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = c.fetchone()

    if request.method == 'POST' and 'user' in session:
        comment = request.form['comment']
        c.execute("INSERT INTO comments (post_id, author, content) VALUES (?, ?, ?)",
                  (post_id, session['user'], comment))
        conn.commit()

    c.execute("SELECT author, content FROM comments WHERE post_id=?", (post_id,))
    comments = c.fetchall()
    conn.close()

    html = '''
        <h2>{{post[1]}}</h2>
        <p>{{post[2]}}</p>
        <p>작성자: {{post[3]}}</p>
        <hr>
        <h4>💬 댓글</h4>
        {% for c in comments %}
            <p><b>{{c[0]}}</b>: {{c[1]}}</p>
        {% endfor %}
        {% if 'user' in session %}
        <form method="POST">
            <textarea name="comment" required></textarea><br>
            <input type="submit" value="댓글 작성">
        </form>
        {% else %}
            <a href="/login">댓글 작성하려면 로그인하세요</a>
        {% endif %}
        <br><a href="/">홈으로</a>
    '''
    return render_template_string(html, post=post, comments=comments)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
