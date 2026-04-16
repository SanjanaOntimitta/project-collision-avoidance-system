from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import PyPDF2
import re

app = Flask(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')


# ---------------- LOAD DATASET ----------------
try:
    with open("data/projects.json") as f:
        projects = json.load(f)
except FileNotFoundError:
    projects = []


# ---------------- CLEAN (LIGHTWEIGHT ONLY) ----------------
def clean(text):
    return text.lower().strip()


# ---------------- EXTRACT TEXT ----------------
def extract_text(file):
    text = ""

    if file and file.filename != "":
        if file.filename.endswith(".txt"):
            text = file.read().decode("utf-8")

        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += " " + page_text

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


# ---------------- PRE-ENCODE DATASET (IMPORTANT FIX) ----------------
stored_texts = [
    clean(p["title"] + " " + p["abstract"])
    for p in projects
]

stored_embeddings = model.encode(stored_texts, normalize_embeddings=True)


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- CHECK API ----------------
@app.route("/check", methods=["POST"])
def check():
    text = request.form.get("text", "").strip()
    file = request.files.get("file")

    file_text = extract_text(file)

    # 🔥 SMART MERGE
    parts = []

    if text:
        parts.append(text)

    if file_text:
        parts.append(file_text)

    if len(parts) == 0:
        return jsonify({"results": []})

    combined = clean(" ".join(parts))

    # 🔥 BOOST FOR SHORT TEXT (IMPORTANT)
    if len(combined.split()) < 5:
        combined += " project system application software"

    # 🔥 USER EMBEDDING (NORMALIZED)
    user_embedding = model.encode([combined], normalize_embeddings=True)

    similarities = cosine_similarity(user_embedding, stored_embeddings)[0]

    print("\nMAX SIMILARITY:", max(similarities))

    # 🔥 TOP 5 RESULTS
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