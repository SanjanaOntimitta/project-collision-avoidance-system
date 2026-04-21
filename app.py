from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import re
import PyPDF2

app = Flask(__name__)

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


# ---------------- CLEAN LIGHT ----------------
def clean(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


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


if __name__ == "__main__":
    print("TOTAL PROJECTS LOADED:", len(projects))
    app.run(debug=True)
