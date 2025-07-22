from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        genre TEXT,
        link TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        book_id INTEGER,
        comment TEXT,
        rating INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    genre_filter = request.args.get('genre')
    search_query = request.args.get('search')
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    if search_query:
        c.execute("SELECT * FROM books WHERE title LIKE ?", ('%' + search_query + '%',))
    elif genre_filter:
        c.execute("SELECT * FROM books WHERE genre = ?", (genre_filter,))
    else:
        c.execute("SELECT * FROM books")
    books = c.fetchall()
    c.execute("SELECT DISTINCT genre FROM books")
    genres = c.fetchall()
    conn.close()
    return render_template('index.html', books=books, genres=genres)

@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = c.fetchone()

    if request.method == 'POST':
        comment = request.form['comment']
        rating = request.form['rating']
        user = session.get('username', 'Anonymous')
        c.execute("INSERT INTO comments (user, book_id, comment, rating) VALUES (?, ?, ?, ?)",
                  (user, book_id, comment, rating))
        conn.commit()

    c.execute("SELECT user, comment, rating FROM comments WHERE book_id = ?", (book_id,))
    comments = c.fetchall()
    conn.close()
    return render_template('book.html', book=book, comments=comments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid login"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "User already exists"
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
