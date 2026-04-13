from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import PyPDF2

app = Flask(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')
THRESHOLD = 0.7

with open("projects.json") as f:
    projects = json.load(f)

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

def get_status(score):
    percent = score * 100
    if percent > 85:
        return "⚠️ High Similarity"
    elif percent >= 70:
        return "⚡ Moderate Similarity"
    else:
        return "✅ Low Similarity"

@app.route("/check", methods=["POST"])
def check():
    text = request.form.get("text", "").strip()
    file = request.files.get("file")

    abstract = extract_text(file)

    if not text and not abstract:
        return jsonify({"results": []})

    combined = " ".join([t for t in [text, abstract] if t])

    user_embedding = model.encode([combined])

    stored_texts = [
        p["title"] + " " + p["abstract"] for p in projects
    ]

    stored_embeddings = model.encode(stored_texts)

    similarities = cosine_similarity(user_embedding, stored_embeddings)[0]

    results = []

    for i, score in enumerate(similarities):
        if score >= THRESHOLD:
            results.append({
                "title": projects[i]["title"],
                "similarity": round(score * 100, 2),
                "status": get_status(score)
            })

    results = sorted(results, key=lambda x: x["similarity"], reverse=True)

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True)