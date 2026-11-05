import os
import smtplib
from email.message import EmailMessage
import os
import sqlite3
import secrets
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

os.makedirs("instance", exist_ok=True)
DATABASE = os.path.join("instance", "research_app.db")


PAPERS = [
    {
        "title": "Machine Learning for Healthcare",
        "year": 2024,
        "abstract": "Machine learning artificial intelligence healthcare medical diagnosis disease prediction patient data.",
        "url": "https://arxiv.org/search/?query=machine+learning+healthcare&searchtype=all"
    },
    {
        "title": "Deep Learning for Image Recognition",
        "year": 2023,
        "abstract": "Deep learning neural networks computer vision image classification object detection.",
        "url": "https://arxiv.org/search/?query=deep+learning+image+recognition&searchtype=all"
    },
    {
        "title": "Natural Language Processing with Transformers",
        "year": 2024,
        "abstract": "Natural language processing NLP transformers text classification language models.",
        "url": "https://arxiv.org/search/?query=natural+language+processing+transformers&searchtype=all"
    },
    {
        "title": "Artificial Intelligence in Agriculture",
        "year": 2024,
        "abstract": "Artificial intelligence agriculture crop disease detection farming plant classification.",
        "url": "https://arxiv.org/search/?query=artificial+intelligence+agriculture&searchtype=all"
    },
    {
        "title": "Cybersecurity Using Machine Learning",
        "year": 2023,
        "abstract": "Cybersecurity network security intrusion detection machine learning cyber attacks.",
        "url": "https://arxiv.org/search/?query=cybersecurity+machine+learning&searchtype=all"
    },
    {
        "title": "Recommendation Systems Using AI",
        "year": 2024,
        "abstract": "Recommendation systems artificial intelligence collaborative filtering content based recommendations.",
        "url": "https://arxiv.org/search/?query=recommendation+systems+AI&searchtype=all"
    },
    {
        "title": "Data Mining and Big Data Analytics",
        "year": 2022,
        "abstract": "Data mining big data analytics data processing information extraction.",
        "url": "https://arxiv.org/search/?query=big+data+analytics&searchtype=all"
    },
    {
        "title": "Blockchain Technology and Security",
        "year": 2023,
        "abstract": "Blockchain technology distributed ledger cryptography security smart contracts.",
        "url": "https://arxiv.org/search/?query=blockchain+security&searchtype=all"
    },
    {
        "title": "Cloud Computing and Edge Computing",
        "year": 2024,
        "abstract": "Cloud computing edge computing distributed systems storage and services.",
        "url": "https://arxiv.org/search/?query=cloud+edge+computing&searchtype=all"
    },
    {
        "title": "Internet of Things Applications",
        "year": 2023,
        "abstract": "Internet of Things IoT sensors smart devices connected networks.",
        "url": "https://arxiv.org/search/?query=Internet+of+Things&searchtype=all"
    },
    {
        "title": "Explainable Artificial Intelligence",
        "year": 2024,
        "abstract": "Explainable AI interpretable machine learning transparency artificial intelligence models.",
        "url": "https://arxiv.org/search/?query=explainable+artificial+intelligence&searchtype=all"
    },
    {
        "title": "Natural Language Processing for Fake News Detection",
        "year": 2023,
        "abstract": "Fake news detection natural language processing text classification machine learning.",
        "url": "https://arxiv.org/search/?query=fake+news+detection&searchtype=all"
    },
    {
        "title": "Autonomous Vehicles Using Deep Learning",
        "year": 2024,
        "abstract": "Autonomous vehicles self driving cars computer vision deep learning robotics.",
        "url": "https://arxiv.org/search/?query=autonomous+vehicles+deep+learning&searchtype=all"
    },
    {
        "title": "Sentiment Analysis Using NLP",
        "year": 2022,
        "abstract": "Sentiment analysis opinion mining natural language processing text classification.",
        "url": "https://arxiv.org/search/?query=sentiment+analysis+NLP&searchtype=all"
    },
    {
        "title": "Predictive Analytics Using Machine Learning",
        "year": 2024,
        "abstract": "Predictive analytics forecasting machine learning regression data science.",
        "url": "https://arxiv.org/search/?query=predictive+analytics+machine+learning&searchtype=all"
    }
]


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


def recommend_papers(query):
    documents = [
        paper["title"] + " " + paper["abstract"]
        for paper in PAPERS
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(documents + [query])

    similarities = cosine_similarity(
        matrix[-1], matrix[:-1]
    ).flatten()

    ranked = sorted(
        zip(PAPERS, similarities),
        key=lambda item: item[1],
        reverse=True
    )

    results = []
    for paper, score in ranked[:6]:
        if score > 0:
            results.append({
                **paper,
                "score": round(float(score) * 100, 1)
            })

    return results


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        else:
            hashed_password = generate_password_hash(password)

            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                        (name, email, hashed_password)
                    )
                flash("Registration successful. Please login.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("This email is already registered.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

def send_reset_email(receiver_email, reset_link):

    sender_email = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        raise RuntimeError("Gmail settings are missing")

    msg = EmailMessage()
    msg["Subject"] = "ResearchAI - Password Reset"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    msg.set_content(f"""
Hello,

We received a request to reset your ResearchAI password.

Click the link below to create a new password:

{reset_link}

This link expires in 30 minutes.

If you did not request this, please ignore this email.

Thank you,
ResearchAI Team
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

            if user:
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode()).hexdigest()

                expiry = (
                    datetime.utcnow() + timedelta(minutes=30)
                ).isoformat()

                db.execute(
                    "DELETE FROM password_resets WHERE email = ?",
                    (email,)
                )

                db.execute(
                    """INSERT INTO password_resets
                    (email, token_hash, expires_at)
                    VALUES (?, ?, ?)""",
                    (email, token_hash, expiry)
                )

                reset_link = url_for(
                    "reset_password",
                    token=token,
                    _external=True
                )

        if user:
            try:
                send_reset_email(email, reset_link)
                print("Password reset email sent successfully.")

            except Exception as e:
                print("Email sending failed:", str(e))

        flash(
            "If the email is registered, a password reset link "
            "will be sent to your inbox.",
            "success"
        )

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with get_db() as db:
        reset = db.execute(
            """SELECT * FROM password_resets
               WHERE token_hash = ?""",
            (token_hash,)
        ).fetchone()

    valid = (
        reset is not None
        and datetime.fromisoformat(reset["expires_at"]) > datetime.utcnow()
    )

    if not valid:
        flash("This reset link is invalid or expired.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            hashed_password = generate_password_hash(password)

            with get_db() as db:
                db.execute(
                    "UPDATE users SET password = ? WHERE email = ?",
                    (hashed_password, reset["email"])
                )
                db.execute(
                    "DELETE FROM password_resets WHERE email = ?",
                    (reset["email"],)
                )

            flash("Password reset successful. Please login.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if query:
            results = recommend_papers(query)

    return render_template(
        "dashboard.html",
        results=results,
        query=query,
        papers_count=len(PAPERS)
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("home"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)