from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import PyPDF2
import re
import numpy as np

app = Flask(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')

# 🔥 LOWER THRESHOLD (MAIN FIX)
THRESHOLD = 0.25


# ---------------- CLEAN TEXT ----------------
def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ---------------- LOAD DATASET ----------------
try:
    with open("data/projects.json") as f:
        projects = json.load(f)
except FileNotFoundError:
    projects = []


# 🔥 PRE-ENCODE DATASET (IMPORTANT FIX)
stored_texts = [
    clean(p["title"] + " " + p["abstract"])
    for p in projects
]

stored_embeddings = model.encode(stored_texts)


# ---------------- EXTRACT PDF TEXT ----------------
def extract_text(file):
    text = ""
    if file and file.filename != "":
        if file.filename.endswith(".txt"):
            text = file.read().decode("utf-8")

        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text()

    return text


# ---------------- STATUS ----------------
def get_status(score):
    percent = score * 100
    if percent > 85:
        return "⚠️ High Similarity"
    elif percent >= 60:
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

    abstract = extract_text(file)

    if not text and not abstract:
        return jsonify({"results": []})

    if len(projects) == 0:
        return jsonify({"results": []})

    # 🔥 CLEAN INPUT
    combined = clean((text + " " + abstract) * 2)

    user_embedding = model.encode([combined])

    similarities = cosine_similarity(user_embedding, stored_embeddings)[0]

    print("MAX SIMILARITY:", max(similarities))  # DEBUG

    results = []

    for i, score in enumerate(similarities):
        if score >= THRESHOLD:
            results.append({
                "title": projects[i]["title"],
                "similarity": round(float(score) * 100, 2),
                "status": get_status(score)
            })

    results = sorted(results, key=lambda x: x["similarity"], reverse=True)

    return jsonify({"results": results})


if __name__ == "__main__":
    print("TOTAL PROJECTS:", len(projects))
    app.run(debug=True)