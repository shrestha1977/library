from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database setup
def init_db():
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            genre TEXT,
            link TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            rating INTEGER,
            comment TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
    ''')
    conn.commit()
    conn.close()

# Insert sample books if not present
def insert_sample_books():
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books")
    if cur.fetchone()[0] == 0:
        books = [
            ("The Great Gatsby", "Fiction", "https://www.planetebook.com/free-ebooks/the-great-gatsby.pdf"),
            ("Pride and Prejudice", "Romance", "https://www.planetebook.com/free-ebooks/pride-and-prejudice.pdf"),
            ("1984", "Sci-Fi", "https://www.planetebook.com/free-ebooks/1984.pdf")
        ]
        cur.executemany("INSERT INTO books (title, genre, link) VALUES (?, ?, ?)", books)
    conn.commit()
    conn.close()

@app.route('/')
def home():
    search = request.args.get('search', '').lower()
    genre = request.args.get('genre', 'all')

    conn = sqlite3.connect('library.db')
    cur = conn.cursor()

    query = "SELECT * FROM books"
    cur.execute(query)
    books = cur.fetchall()

    if search:
        books = [b for b in books if search in b[1].lower()]
    if genre != 'all':
        books = [b for b in books if genre == b[2]]

    return render_template("index.html", books=books, user=session.get("user"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect('library.db')
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (uname, pwd))
            conn.commit()
            return redirect('/login')
        except:
            return "Username already exists!"
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect('library.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (uname, pwd))
        user = cur.fetchone()
        if user:
            session['user'] = {'id': user[0], 'username': user[1]}
            return redirect('/')
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/feedback', methods=['POST'])
def feedback():
    if 'user' not in session:
        return "Login required"
    user_id = session['user']['id']
    book_id = request.form['book_id']
    rating = request.form['rating']
    comment = request.form['comment']

    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (user_id, book_id, rating, comment) VALUES (?, ?, ?, ?)",
                (user_id, book_id, rating, comment))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    if not os.path.exists('library.db'):
        init_db()
        insert_sample_books()
    app.run(debug=True)
