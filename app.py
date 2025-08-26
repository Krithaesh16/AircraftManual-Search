import os
import sqlite3
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from whoosh.fields import Schema, TEXT, ID, NUMERIC, STORED
from whoosh import index as whoosh_index
from whoosh.qparser import QueryParser, PhrasePlugin

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change this in production

# ---------------- DATABASE ----------------
DATABASE = "users.db"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# ---------------- LOGIN SETUP ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cur = db.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if row:
        return User(row[0], row[1])
    return None

# ---------------- WHOOSH SETUP ----------------
INDEX_DIR = "storage/index"
PDF_DIR = "storage/pdfs"

def get_index(create=True):
    schema = Schema(
        doc_id=ID(stored=True, unique=True),
        filename=STORED,
        title=TEXT(stored=True),
        page=NUMERIC(stored=True),
        content=TEXT
    )
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR, exist_ok=True)
    if create and not whoosh_index.exists_in(INDEX_DIR):
        return whoosh_index.create_in(INDEX_DIR, schema)
    return whoosh_index.open_dir(INDEX_DIR)

# ---------------- ROUTES ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)

        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
        row = cur.fetchone()

        if row and check_password_hash(row[2], password):
            user = User(row[0], row[1])
            login_user(user)
            return redirect(url_for("search_page"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- SEARCH PAGE ----------------
@app.route("/", methods=["GET"])
@login_required
def search_page():
    query = request.args.get("q", "")
    results = []

    if query:
        # Automatically wrap multi-word queries in quotes for exact phrase search
        if " " in query:
            query = f'"{query}"'

        ix = get_index(create=False)
        with ix.searcher() as searcher:
            parser = QueryParser("content", schema=ix.schema)
            parser.add_plugin(PhrasePlugin())
            q = parser.parse(query)
            res = searcher.search(q, limit=20)
            for hit in res:
                results.append({
                    "title": hit["title"],
                    "filename": hit["filename"],
                    "page": hit["page"]
                })

    return render_template("index.html", query=query, results=results)

@app.route("/pdfs/<path:filename>")
@login_required
def serve_pdf(filename):
    return send_from_directory(PDF_DIR, filename)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)

