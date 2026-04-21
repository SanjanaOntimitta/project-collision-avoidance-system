<<<<<<< HEAD
from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import re
=======
from flask import Flask, request, jsonify, render_template, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
>>>>>>> 9cd494a (ready for deployment)
import PyPDF2

app = Flask(__name__)

<<<<<<< HEAD
MODEL_NAME = "all-MiniLM-L6-v2"
BOOSTER_TEXT = "project system application software web platform solution management"
model = None
model_load_error = None


# ---------------- LOAD DATASET ----------------
try:
    with open("data/projects.json", encoding="utf-8") as f:
        raw_projects = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    raw_projects = []
=======
# ---------------- LOGIN ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    with open("users.json") as f:
        users = json.load(f)
    for u in users:
        if str(u["id"]) == str(user_id):
            return User(u["id"], u["email"], u["password"])
    return None

# ---------------- LOAD PROJECTS ----------------
try:
    with open("data/projects.json") as f:
        projects = json.load(f)
except:
    projects = []

def clean(text):
    return text.lower().strip()

def extract_text(file):
    text = ""
    if file and file.filename != "":
        if file.filename.endswith(".txt"):
            text = file.read().decode("utf-8")
        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += " " + t
    return text

def get_status(score):
    percent = score * 100
    if percent > 80:
        return "⚠️ High Similarity"
    elif percent >= 50:
        return "⚡ Moderate Similarity"
    else:
        return "✅ Low Similarity"
>>>>>>> 9cd494a (ready for deployment)

# ---------------- MODEL ----------------
model = SentenceTransformer('all-MiniLM-L6-v2')

<<<<<<< HEAD
# ---------------- CLEAN LIGHT ----------------
def clean(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()
=======
stored_texts = [clean(p["title"] + " " + p["abstract"]) for p in projects]
stored_embeddings = model.encode(stored_texts, normalize_embeddings=True) if stored_texts else []
>>>>>>> 9cd494a (ready for deployment)

# ---------------- ROUTES ----------------

<<<<<<< HEAD
def is_valid_project(project):
    title = clean(project.get("title", ""))
    abstract = clean(project.get("abstract", ""))
    combined = f"{title} {abstract}"

    if len(title) < 10 or len(abstract) < 80:
        return False

    if len(title.split()) < 3 or len(abstract.split()) < 15:
        return False

    if title.startswith(".") or any(symbol in combined for symbol in ["|", ";"]):
        return False

    alpha_chars = sum(ch.isalpha() for ch in combined)
    if alpha_chars < max(40, int(len(combined) * 0.6)):
        return False

    return True


projects = [
    {
        "title": clean(project.get("title", "")),
        "abstract": clean(project.get("abstract", "")),
    }
    for project in raw_projects
    if is_valid_project(project)
]


def get_model():
    global model, model_load_error

    if model is not None:
        return model

    if model_load_error is not None:
        raise RuntimeError(model_load_error)

    try:
        cache_dir = os.environ.get("SENTENCE_TRANSFORMERS_HOME")
        model = SentenceTransformer(MODEL_NAME, cache_folder=cache_dir)
        return model
    except Exception as exc:
        model_load_error = f"Unable to load similarity model '{MODEL_NAME}': {exc}"
        raise RuntimeError(model_load_error) from exc


def build_stored_embeddings():
    if not projects:
        return []

    current_model = get_model()
    stored_texts = [
        clean(f"{project['title']} {project['abstract']}")
        for project in projects
    ]
    return current_model.encode(stored_texts, normalize_embeddings=True)


stored_embeddings = None


def get_stored_embeddings():
    global stored_embeddings

    if stored_embeddings is not None:
        return stored_embeddings

    embeddings = build_stored_embeddings()
    if len(embeddings) != len(projects):
        raise RuntimeError("Project dataset and embeddings are out of sync.")

    stored_embeddings = embeddings
    return stored_embeddings


# ---------------- EXTRACT FILE TEXT ----------------
def extract_text(file):
    text = ""

    if file and file.filename != "":
        filename = file.filename.lower()

        if filename.endswith(".txt"):
            text = file.read().decode("utf-8", errors="ignore")

        elif filename.endswith(".pdf"):
            try:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += " " + page_text
            except Exception:
                return ""

    return text


# ---------------- STATUS ----------------
def get_status(score):
    percent = score * 100
    if percent > 80:
        return "⚠️ High Similarity"
    elif percent >= 50:
        return "⚡ Moderate Similarity"
    else:
        return "✅ Low Similarity"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")
=======
@app.route("/")
def home():
    return render_template("home.html")
>>>>>>> 9cd494a (ready for deployment)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

<<<<<<< HEAD
# ---------------- CHECK API ----------------
@app.route("/check", methods=["POST"])
def check():
    text = request.form.get("text", "").strip()
    file = request.files.get("file")

    if not projects:
        return jsonify({
            "results": [],
            "message": "No valid projects are available to compare yet. Rebuild the dataset and try again."
        }), 503

    try:
        current_model = get_model()
        current_embeddings = get_stored_embeddings()
    except RuntimeError as exc:
        return jsonify({"results": [], "message": str(exc)}), 503

    file_text = extract_text(file)

    # ---------------- SMART MERGE ----------------
    parts = []

    if text:
        parts.append(text)

    if file_text:
        parts.append(file_text)

    if len(parts) == 0:
        return jsonify({"results": []})

    combined = clean(" ".join(parts))

    # 🔥 IMPORTANT FIX: boost short text input
    if len(combined.split()) < 5:
        combined = f"{combined} {BOOSTER_TEXT}".strip()

    # ---------------- EMBEDDING ----------------
    user_embedding = current_model.encode([combined], normalize_embeddings=True)

    similarities = cosine_similarity(user_embedding, current_embeddings)[0]

    if len(similarities) == 0:
        return jsonify({"results": []})

    # ---------------- TOP RESULTS ----------------
    top_k = similarities.argsort()[::-1][:5]

    results = []

    for i in top_k:
        score = similarities[i]

        results.append({
            "title": projects[i]["title"],
            "similarity": round(float(score) * 100, 2),
            "status": get_status(score)
        })

    return jsonify({"results": results})
=======
        if not email.endswith("@cvr.ac.in"):
            return "❌ Use only @cvr.ac.in email"

        with open("users.json") as f:
            users = json.load(f)

        for u in users:
            if u["email"] == email:
                return "⚠️ User already exists"

        users.append({
            "id": len(users) + 1,
            "email": email,
            "password": generate_password_hash(password)
        })

        with open("users.json", "w") as f:
            json.dump(users, f)

        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with open("users.json") as f:
            users = json.load(f)

        for u in users:
            if u["email"] == email and check_password_hash(u["password"], password):
                login_user(User(u["id"], u["email"], u["password"]))
                return redirect("/dashboard")

        return "❌ Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")
>>>>>>> 9cd494a (ready for deployment)

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

<<<<<<< HEAD
if __name__ == "__main__":
    print("TOTAL PROJECTS LOADED:", len(projects))
    app.run(debug=True)
=======
@app.route("/check", methods=["POST"])
@login_required
def check():
    text = request.form.get("text", "").strip()
    file = request.files.get("file")

    file_text = extract_text(file)

    if not text or not file_text:
        return jsonify({"results": [], "error": "⚠️ Provide BOTH text and file"})

    combined = clean(text + " " + file_text)

    user_embedding = model.encode([combined], normalize_embeddings=True)
    similarities = cosine_similarity(user_embedding, stored_embeddings)[0]

    top_k = similarities.argsort()[::-1][:5]

    results = []
    for i in top_k:
        score = similarities[i]
        results.append({
            "title": projects[i]["title"],
            "similarity": round(float(score) * 100, 2),
            "status": get_status(score)
        })

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
>>>>>>> 9cd494a (ready for deployment)
